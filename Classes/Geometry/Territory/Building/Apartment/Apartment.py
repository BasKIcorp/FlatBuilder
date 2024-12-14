from turtledemo.penrose import start

from Classes.Geometry.GeometricFigure import GeometricFigure
from Classes.Geometry.Territory.Building.Apartment.Room import Room

from typing import List, Tuple
import random
import time
from shapely.geometry import Polygon, MultiPolygon
from shapely.ops import unary_union
import math


# Класс для квартиры, содержащей комнаты, мокрые зоны и балконы
class Apartment(GeometricFigure):
    def __init__(self, points: List[Tuple[float, float]],
                 apt_type: str, rooms: List['Room'] = None,
                 cell_size: float = 1.0):
        super().__init__(points)
        self.type = apt_type  # Тип квартиры
        self.area = self.polygon.area  # Площадь квартиры, вычисленная из геометрии
        self.rooms = rooms if rooms is not None else []  # Список комнат в квартире
        self.cell_size = cell_size
        room_table = self.get_room_types_by_apartment_type(self.type)
        self.total_rooms = sum(count for room_type, count in room_table)
        self.free_sides = []
        self.building_perimeter_sides = []

    def generate_apartment_planning(self):
        self.cells = None
        self.check_and_create_cell_grid(cell_size=1)
        self._process_cells()
        self.rooms = []
        room_table = self.get_room_types_by_apartment_type(self.type)
        self.starting_corner_cells = [cell for cell in self.cells if cell['is_corner']]
        remaining_cells = [cell for cell in self.cells if not cell['assigned']]  # Все доступные ячейки
        room_number = 0

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
                                                                          cell_size=self.cell_size)
                        # Выделяем ячейки для комнаты
                        room_cells = self._allocate_room_cells(remaining_cells, min_cells, max_cells, room_type)
                room_polygon = unary_union([cell['polygon'] for cell in room_cells])
                rectangular_room_polygon = room_polygon.envelope
                if rectangular_room_polygon.area < max_cells:
                    for cell in self.cells:
                        if not cell['assigned'] and rectangular_room_polygon.contains(cell['polygon']):
                            room_cells.append(cell)
                            cell['assigned'] = True
                    rectangular_room_polygon = unary_union([cell['polygon'] for cell in room_cells])
                    if isinstance(rectangular_room_polygon, Polygon):
                        points = list(rectangular_room_polygon.exterior.coords)
                    elif isinstance(rectangular_room_polygon, MultiPolygon):
                        points = list(rectangular_room_polygon.geoms[0].exterior.coords)
                    else:
                        continue
                else:
                    if isinstance(room_polygon, Polygon):
                        points = list(room_polygon.exterior.coords)
                    elif isinstance(room_polygon, MultiPolygon):
                        points = list(room_polygon.geoms[0].exterior.coords)
                    else:
                        continue
                # Создаем объект Room с соответствующим типом
                room = Room(points=points, room_type=room_type)
                room.cells = room_cells
                self.rooms.append(room)


        # Добавить не назначенные клетки к ближайшей комнате
        # self._assign_remaining_cells_to_rooms(remaining_cells)

    # def _assign_remaining_cells_to_rooms(self, remaining_cells):
    #     """Добавляет не назначенные клетки к ближайшей комнате."""
    #     for cell in remaining_cells:
    #         if not cell['assigned']:
    #             # Найдем ближайшую комнату
    #             closest_room = None
    #             closest_distance = float('inf')
    #
    #             for room in self.rooms:
    #                 distance = room.polygon.distance(cell['polygon'])  # Используем расстояние до полигона комнаты
    #                 if distance < closest_distance:
    #                     closest_distance = distance
    #                     closest_room = room
    #
    #             if closest_room:
    #                 closest_room.cells.append(cell)  # Добавляем клетку в ближайшую комнату
    #                 closest_room.polygon = unary_union(
    #                     [closest_room.polygon, cell['polygon']])  # Обновляем полигон комнаты
    #                 # Обновляем points для передачи в room
    #                 if isinstance(closest_room.polygon, Polygon):
    #                     closest_room.points = list(closest_room.polygon.exterior.coords)
    #                 elif isinstance(closest_room.polygon, MultiPolygon):
    #                     closest_room.points = list(closest_room.polygon.geoms[0].exterior.coords)
    #                 cell['assigned'] = True  # Помечаем клетку как назначенную

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
        elif self.type != 'studio':
            return_cells = []
            for side in self.building_perimeter_sides:
                return_cells.extend([cell for cell in self.starting_corner_cells if cell['polygon'].intersects(side)])
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
                reverse=True
            )

            # Добавляем отсортированных соседей в очередь
            queue.extend(neighbors_sorted)
        return room_cells



    def _get_rooms_cell_range(self, room_table, room_number, cell_size):
        """Определяет минимальное и максимальное количество ячеек для комнаты на основе диапазона площади."""
        cell_area = cell_size ** 2  # Площадь одной ячейки
        total_rooms = sum(count for room_type, count in room_table) - room_number
        min_cells = int(0.5 * self.polygon.area / total_rooms)
        max_cells = int(self.polygon.area / total_rooms)
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

        if room_type in ['living_room', 'bedroom']:
            return_cells = []
            for side in self.building_perimeter_sides:
                return_cells.extend([cell for cell in corner_cells if cell['polygon'].intersects(side)])
            if len(return_cells) > 0:
                return random.choice(return_cells)

        elif room_type == 'kitchen':
            return_cells = []
            for side in self.building_perimeter_sides:
                return_cells.extend([cell for cell in corner_cells if cell['polygon'].intersects(side)])
            if len(return_cells) > 0:
                return random.choice(return_cells)
            else:
                return random.choice(corner_cells)
        return random.choice(corner_cells)