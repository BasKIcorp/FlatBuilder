

from Classes.Geometry.GeometricFigure import GeometricFigure
from Classes.Geometry.Territory.Building.Apartment.Room import Room
from Classes.Geometry.Territory.Building.Apartment.Window import Window
from typing import List, Tuple
import random
import time
from shapely.geometry import Polygon, MultiPolygon, LineString, MultiLineString, Point
from shapely.ops import unary_union
import math
from shapely import union_all


# Класс для квартиры, содержащей комнаты, мокрые зоны и балконы
class Apartment(GeometricFigure):
    def __init__(self, points: List[Tuple[float, float]],
                 apt_type: str,
                 building_polygon: Polygon,
                 rooms: List['Room'] = None,
                 cell_size: float = 1.0):
        super().__init__(points)
        self.type = apt_type  # Тип квартиры
        self.area = self.polygon.area  # Площадь квартиры, вычисленная из геометрии
        self.rooms = rooms if rooms is not None else []  # Список комнат в квартире
        self.cell_size = cell_size
        room_table = self.get_room_types_by_apartment_type(self.type)
        self.total_rooms = sum(count for room_type, count in room_table)
        self.free_sides = []
        self.windows = []
        self.section_polygon = None
        self.building_polygon = building_polygon
        self.messages = []

    def generate_apartment_planning(self):
        self.points = list(Polygon(self.points).simplify(tolerance=0.01,preserve_topology=True).exterior.coords)
        max_iterations = 12
        best_plan = None
        best_score = float('inf')
        failure = False
        for i in range(max_iterations):
            rooms = []
            room_number = 0
            self.cells = None
            self.check_and_create_cell_grid(cell_size=1, polygon_to_check=Polygon(self.points))
            room_table = self.get_room_types_by_apartment_type(self.type)
            self.starting_corner_cells = [cell for cell in self.cells if cell['is_corner']]
            remaining_cells = [cell for cell in self.cells if not cell['assigned']]  # Все доступные ячейки
            # Распределение комнат, учитывая последнее условие
            for index, (room_type, count) in enumerate(room_table):
                for _ in range(count):
                    if index == len(room_table) - 1 and _ == count - 1:
                        room_cells = [cell for cell in self.cells if not cell['assigned']]
                    else:
                        if self.type == 'studio':
                            min_cells = 6
                            max_cells = 10
                            room_cells = self._allocate_room_cells(remaining_cells, min_cells, max_cells, room_type)

                        else:
                            min_cells, max_cells = self._get_rooms_cell_range(room_table=room_table, room_number=room_number,
                                                                              cell_size=self.cell_size,
                                                                              room_type=room_type, rooms=rooms)

                            # Выделяем ячейки для комнаты
                            room_cells = self._allocate_room_cells(remaining_cells, min_cells, max_cells, room_type)
                    if not self.aspect_ratio_ok(room_cells) and room_type in ['living room', 'bedroom']:
                        failure = True
                        break

                    room_polygon = union_all([cell['polygon'] for cell in room_cells])
                    rectangular_room_polygon = room_polygon.envelope
                    if rectangular_room_polygon.area <= max_cells:
                        for cell in self.cells:
                            if not cell['assigned'] and rectangular_room_polygon.contains(cell['polygon']):
                                room_cells.append(cell)
                                cell['assigned'] = True
                        rectangular_room_polygon = union_all([cell['polygon'] for cell in room_cells])
                        if isinstance(rectangular_room_polygon, Polygon):
                            points = list(rectangular_room_polygon.exterior.coords)
                        elif isinstance(rectangular_room_polygon, MultiPolygon):
                            points = list(rectangular_room_polygon.geoms[0].exterior.coords)
                        else:
                            continue
                    else:
                        for i in range(3):
                            new_room_polygon = union_all([cell['polygon'] for cell in room_cells[:(-1-i)]])
                            if new_room_polygon.area == room_polygon.envelope.area:
                                room_polygon = new_room_polygon.copy()
                                for cell in room_cells[(-1-i):]:
                                    cell['assigned'] = False
                                room_cells = room_cells[(-1-i):]
                                break
                        if isinstance(room_polygon, Polygon):
                            points = list(room_polygon.exterior.coords)
                        elif isinstance(room_polygon, MultiPolygon):
                            points = list(room_polygon.geoms[0].exterior.coords)
                        else:
                            continue
                    # Создаем объект Room с соответствующим типом
                    room = Room(points=points, room_type=room_type)
                    room.cells = room_cells
                    rooms.append(room)
                    # rooms = self.post_processing(rooms)


                if failure:
                    break
            if failure:
                continue
            total_error = self._calc_total_error(rooms[:-1])
            if total_error < best_score and sum(room.area for room in rooms) == self.area:
                best_score = total_error
                best_plan = rooms

        self.rooms = best_plan if best_plan is not None else []  # Save the best generated plan
        if self.rooms:
            self._generate_windows()
            return
        if not self.rooms:
            self.messages.append('Не нашел планировку на уровне квартир')

    def _generate_windows(self):
        """Генерирует окна для комнат на внешних сторонах здания."""
        buffer_tolerance = 0.01  # Буфер для корректировки угловых пересечений

        for room in self.rooms:
            if room.type not in ['living room', 'bedroom', 'kitchen']:
                continue  # Только для определенных типов комнат
            cutted_polygon = Polygon(room.points).simplify(tolerance=0.01,
                                                      preserve_topology=True).intersection(
                self.building_polygon.simplify(tolerance=0.01, preserve_topology=True))
            if not isinstance(cutted_polygon, Polygon):
                continue
            # Получаем стороны комнаты
            room_sides = [
                LineString([cutted_polygon.exterior.coords[i], cutted_polygon.exterior.coords[i + 1]])
                for i in range(len(cutted_polygon.exterior.coords) - 1)
            ]

            for room_side in room_sides:
                # Проверяем пересечение стороны комнаты с периметром здания
                intersection = room_side.intersection(self.building_polygon.exterior)

                # Если пересечение слишком маленькое или точка, применяем буфер
                if isinstance(intersection, Point) or \
                        (isinstance(intersection, LineString) and intersection.length < 0.5):
                    # Буферизация стороны для улучшения пересечения
                    buffered_room_side = room_side.buffer(buffer_tolerance).intersection(self.building_polygon.exterior)
                    intersection = buffered_room_side

                # Проверяем пересечение после буфера
                if isinstance(intersection, MultiLineString):
                    # Объединяем MultiLineString в один LineString
                    intersection = LineString([coord for line in intersection.geoms for coord in line.coords])

                if isinstance(intersection, LineString) and intersection.length > 0:
                    # Проверяем длину пересечения
                    if intersection.length < 0.5:
                        continue

                    # Находим центр пересечения
                    midpoint = intersection.interpolate(0.5, normalized=True)

                    # Вычисляем две точки на расстоянии 0.75 метра в обе стороны от центра
                    start_distance = max(0, intersection.project(midpoint) - 0.5)
                    end_distance = min(intersection.length, intersection.project(midpoint) + 0.5)

                    if end_distance <= start_distance:
                        continue

                    # Находим точки начала и конца окна
                    start_point = intersection.interpolate(start_distance)
                    end_point = intersection.interpolate(end_distance)

                    # Создаем LineString длиной 1.5 метра
                    window_line = LineString([start_point, end_point])

                    # Добавляем окно в комнату
                    self.windows.append(Window(window_line))
                    break  # Переходим к следующей комнате

    def _calc_total_error(self, rooms):
        def rectangularity_score(poly):
            extended_area = poly.envelope.area
            area = poly.area
            return abs(extended_area - area) / area
        score = 0
        for room in rooms:
            score += rectangularity_score(room.polygon)
        return score


    def get_room_types_by_apartment_type(self, apt_type: str):
        """Возвращает таблицу комнат в зависимости от типа квартиры."""
        room_table = []

        if apt_type == 'studio':
            room_table = [('bathroom', 1), ('bedroom', 1)]

        elif apt_type == '1 room':
            room_table = [('bedroom', 1), ('kitchen', 1), ('bathroom', 1), ('hall', 1)]

        elif apt_type == '2 room':
            room_table = [('bedroom', 1), ('living room', 1), ('kitchen', 1), ('bathroom', 1), ('hall', 1)]

        elif apt_type == '3 room':
            room_table = [('bedroom', 2), ('living room', 1), ('kitchen', 1), ('bathroom', 1), ('hall', 1)]

        elif apt_type == '4 room':
            room_table = [('bedroom', 3), ('living room', 1), ('kitchen', 1), ('bathroom', 1), ('hall', 1)]

        return room_table

    def _allocate_room_cells(self, remaining_cells, min_cells, max_cells, room_type):
        """Выделяет ячейки для одной комнаты, гарантируя, что все ячейки будут заполнены."""
        room_cells = []
        visited_cells = set()
        room_cell_count = random.randint(min_cells, max_cells)
        if len([c for c in self.cells if c['assigned']]) > 0:
            start_cell = self._get_next_start_cell(room_type)
            if not start_cell:
                # Если стартовая ячейка не найдена, выходим из текущей итерации
                return []
        elif self.type != 'studio':
            return_cells = []
            return_cells.extend([cell for cell in self.starting_corner_cells if cell['polygon'].intersects(self.building_polygon.exterior)])
            if len(return_cells) > 0:
                start_cell = random.choice(return_cells)
            else:
                start_cell = random.choice(self.starting_corner_cells)
        else:
            start_cell = random.choice(self.starting_corner_cells)
        # if self.starting_corner_cells and len(self.starting_corner_cells) >= 1:
        #     start_cell = self.starting_corner_cells.pop()
        # else:
        #     start_cell = random.choice(remaining_cells)
        queue = [start_cell]
        bool_variants = [True, False]
        growing_method = random.choice(bool_variants)
        while queue and len(room_cells) < room_cell_count:
            current_cell = queue.pop(0)
            if current_cell['assigned']:
                continue
            visited_cells.add(current_cell['id'])
            room_cells.append(current_cell)

            current_cell['assigned'] = True

            # Получаем не назначенные соседние клетки
            neighbors = [neighbor for neighbor in current_cell['neighbors'] if not neighbor['assigned']]

            # Сортируем соседей по убыванию количества их свободных соседей
            neighbors_sorted = sorted(
                neighbors,
                key=lambda cell: len([n for n in cell['neighbors'] if not n['assigned']]),
                reverse=growing_method
            )

            # Добавляем отсортированных соседей в очередь
            queue.extend(neighbors_sorted)
        return room_cells



    def _get_rooms_cell_range(self, room_table, room_number, cell_size, room_type, rooms):
        """Определяет минимальное и максимальное количество ячеек для комнаты на основе диапазона площади."""
        cell_area = cell_size ** 2  # Площадь одной ячейки
        allocated_area = sum(room.area for room in rooms)
        if room_type in ['bedroom', 'living room']:
            min_cells = 11
            max_cells = 20
            return min_cells, max_cells
        else:
            if room_type == 'kitchen':
                min_cells = int(0.9 * (self.polygon.area - allocated_area) / 3)
                max_cells = int((self.polygon.area - allocated_area) / 3)
                return min_cells, max_cells
            elif room_type == 'bathroom':
                min_cells = int(0.8 * (self.polygon.area - allocated_area) / 2)
                max_cells = int((self.polygon.area - allocated_area) / 2)
                return min_cells, max_cells

    def _get_next_start_cell(self, room_type):
        corner_cells = []
        for cell in [cell for cell in self.cells if cell['assigned'] and cell['on_perimeter']]:
            perimeter_neighbors_for_new_corner = [neighbor for neighbor in cell['neighbors'] if
                                                  neighbor['assigned'] == False and neighbor['on_perimeter']]
            if len(perimeter_neighbors_for_new_corner) > 0:
                for cell_for_new_corner in perimeter_neighbors_for_new_corner:
                    cell_for_new_corner['is_corner'] = True  # Reset is_corner before checking
                    corner_cells.append(cell_for_new_corner)

        if room_type in ['living room', 'bedroom']:
            return_cells = []
            return_cells.extend([cell for cell in corner_cells if cell['polygon'].overlaps(self.building_polygon.exterior)])
            return_cells.extend([cell for cell in corner_cells if cell['polygon'].intersects(self.building_polygon.exterior)])

            if return_cells:
                return random.choice(return_cells)
            elif corner_cells:
                return random.choice(corner_cells)

        elif room_type == 'kitchen':
            return_cells = []
            return_cells.extend(
                [cell for cell in corner_cells if cell['polygon'].overlaps(self.building_polygon.exterior)])
            return_cells.extend(
                [cell for cell in corner_cells if cell['polygon'].intersects(self.building_polygon.exterior)])
            if return_cells:
                return random.choice(return_cells)
            elif corner_cells:
                return random.choice(corner_cells)

        elif room_type == 'bathroom':
            return_cells = []
            return_cells.extend(
                [cell for cell in corner_cells if cell['polygon'].overlaps(self.building_polygon.exterior)])
            return_cells.extend(
                [cell for cell in corner_cells if cell['polygon'].intersects(self.building_polygon.exterior)])
            if return_cells:
                return random.choice(return_cells)
            elif corner_cells:
                return random.choice(corner_cells)
        # Если corner_cells пуст, используем любые свободные клетки на периметре
        if not corner_cells:
            available_cells = [cell for cell in self.cells if cell['on_perimeter'] and not cell['assigned']]
            if available_cells:
                return random.choice(available_cells)

        # Если ничего не найдено, возвращаем None
        return None

    def aspect_ratio_ok(self, cells, max_aspect_ratio=1.5):
        # Проверка соотношения сторон комнаты
        polys = [c['polygon'] for c in cells]
        union_poly = unary_union(polys)
        bbox = union_poly.envelope

        # Если bbox - это точка, соотношение сторон не имеет смысла
        if isinstance(bbox, Point):
            return False, 0  # Соотношение невозможно вычислить

        coords = list(bbox.exterior.coords)
        side_lengths = []
        for i in range(4):
            x1, y1 = coords[i]
            x2, y2 = coords[(i + 1) % 4]
            dist = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
            side_lengths.append(dist)
        side_lengths.sort()
        shorter, longer = side_lengths[0], side_lengths[2]
        ratio = longer / (shorter + 1e-9)
        return ratio <= max_aspect_ratio, ratio


    #
    # def post_processing(self, rooms):
    #     def replace_element(lst, old_value, new_value):
    #         return [new_value if x == old_value else x for x in lst]
    #     free_polygon = union_all([cell['polygon'] for cell in self.cells if not cell['assigned']])
    #     if isinstance(free_polygon, Polygon):
    #         for room in rooms:
    #             if room.polygon.intersects(free_polygon):
    #                 new_polygon = room.polygon.union(free_polygon)
    #                 points = list(new_polygon.exterior.coords)
    #                 new_room = Room(points=points,
    #                                 room_type=room.type)
    #                 return replace_element(rooms, room, new_room)
    #     if isinstance(free_polygon, MultiPolygon):
    #         new_rooms = rooms
    #         for geom in free_polygon.geoms:
    #
    #             for room in rooms:
    #                 if room.polygon.intersects(geom):
    #                     new_polygon = room.polygon.union(geom)
    #                     points = list(new_polygon.exterior.coords)
    #                     new_room = Room(points=points,
    #                                     room_type=room.type)
    #                     new_rooms = replace_element(rooms, room, new_room)
    #         return new_rooms
