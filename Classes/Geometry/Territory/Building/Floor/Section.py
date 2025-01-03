from shapely.geometry.multilinestring import MultiLineString
from shapely.set_operations import intersection

from Classes.Geometry.GeometricFigure import GeometricFigure
from Classes.Geometry.Territory.Building.Apartment.Apartment import Apartment
from Classes.Geometry.Territory.Building.Elevator import Elevator
from Classes.Geometry.Territory.Building.Stair import Stair
from Classes.Geometry.Territory.RLAgent import RLAgent
from shapely.geometry import Polygon, LineString, MultiPolygon, Point
from shapely import union_all
import random
from typing import List, Tuple, Dict
import time
import copy
from shapely.affinity import translate


class Section(GeometricFigure):
    def __init__(self, points: List[Tuple[float, float]],
                 apartment_table: Dict,
                 apartments: List['Apartment'] = None,
                 building_polygon: Polygon = None,
                 to_adjust: bool = False):
        super().__init__(points)
        self.apartments = apartments if apartments is not None else []  # List of Apartment objects
        self.queue_corners_to_allocate = []
        self.free_cells = []
        self.apartment_table = self._clean_apartment_table(apartment_table)
        self.building_polygon = building_polygon
        self.messages = []
        self.total_apartment_number = self._calc_total_apartment_number()
        self.agent = RLAgent()
        self.initial_corner_cells = []
        self.otladka = []
        self.simple_plan = False
        self.temporary_cells = []
        self.to_adjust = to_adjust
        print(self.apartment_table)
        self.plan_done = False

    def generate_section_planning(self, max_iterations=30, cell_size=1):
        self.cell_size = cell_size
        """Generates a floor plan by allocating apartments according to the given apartment table."""
        self.apartments = []  # Initialize as empty list
        best_plan = None
        best_score = float('inf')  # The lower, the better
        start_time = time.time()
        skip_number_validation = False
        alternative_plan = []
        if not self.apartment_table:
            return
        # Create the cell grid once
        for iteration in range(max_iterations):
            print(f"Итерация {iteration}")
            if best_plan and iteration % 4 == 0:
                self.apartments = best_plan
                if not self.apartments:
                    print("Не нашел планировку")
                for apt in self.apartments:
                    apt.section_polygon = self.polygon
                    apt.cells = None
                    apt.check_and_create_cell_grid(cell_size=1.0, polygon_to_check=Polygon(apt.points))
                    apt._process_cells()
                    apt.generate_apartment_planning()
                for apt in self.apartments:
                    cutted_polygon = Polygon(apt.points).simplify(tolerance=0.01,
                                                                  preserve_topology=True).intersection(
                        self.polygon.simplify(tolerance=0.01, preserve_topology=True))
                    if isinstance(cutted_polygon, MultiPolygon):
                        cutted_polygon = max(cutted_polygon.geoms, key=lambda a: a.area)
                    apt.points = list(cutted_polygon.exterior.coords)
                    apt.polygon = Polygon(apt.points)
                    for room in apt.rooms:
                        cutted_polygon = Polygon(room.points).simplify(tolerance=0.01,
                                                                       preserve_topology=True).intersection(
                            apt.polygon.simplify(tolerance=0.01, preserve_topology=True))
                        if isinstance(cutted_polygon, Polygon):
                            room.points = list(cutted_polygon.exterior.coords)
                            room.polygon = Polygon(room.points)
                    apt._generate_windows()
                self.plan_done = True
                break
            if not best_plan and iteration == 12 and alternative_plan:
                if self.to_adjust:
                    print('this case')
                    self.apartments = alternative_plan
                    if not self.apartments:
                        print("Не нашел планировку")
                    print(len(self.apartments))
                    for apt in self.apartments:
                        apt.section_polygon = self.polygon
                        apt.cells = None
                        apt.check_and_create_cell_grid(cell_size=1.0, polygon_to_check=Polygon(apt.points))
                        apt._process_cells()
                        apt.generate_apartment_planning()
                    for apt in self.apartments:
                        cutted_polygon = Polygon(apt.points).simplify(tolerance=0.01,
                                                                      preserve_topology=True).intersection(
                            self.polygon.simplify(tolerance=0.01, preserve_topology=True))
                        if isinstance(cutted_polygon, MultiPolygon):
                            cutted_polygon = max(cutted_polygon.geoms, key=lambda a: a.area)
                        apt.points = list(cutted_polygon.exterior.coords)
                        apt.polygon = Polygon(apt.points)
                        for room in apt.rooms:
                            cutted_polygon = Polygon(room.points).simplify(tolerance=0.01,
                                                                           preserve_topology=True).intersection(
                                apt.polygon.simplify(tolerance=0.01, preserve_topology=True))
                            if isinstance(cutted_polygon, Polygon):
                                room.points = list(cutted_polygon.exterior.coords)
                                room.polygon = Polygon(room.points)
                        apt._generate_windows()
                    skip_number_validation = True
                    self.plan_done = True
                    break

            if not best_plan and iteration == 16:
                self.simple_plan = True
            # Reset the cell assignments between iterations
            self.cells = None
            self.check_and_create_cell_grid(cell_size=1.0)
            self.queue_corners_to_allocate = []
            # self._reset_cell_assignments()
            # Allocate apartments using the cell grid
            apartments = self._allocate_apartments(self.cells)
            best_rectangularity = float('inf')

            # **Validation**: Validate apartments for free sides
            if not apartments:
                for apart in apartments:
                    apart._reset_cell_assignments()
                    self._process_cells()
                continue  # No apartments allocated in this iteration
            if self.to_adjust and len(apartments) > len(alternative_plan):
                alternative_plan = apartments
            if not self._validate_apartment_number(apartments) and not skip_number_validation:
                # Если неверное кол-во, откатываемся
                for apt in apartments:
                    apt._reset_cell_assignments()
                continue

            total_rectangularity_error = sum(self._rectangularity_score(apt.polygon) for apt in apartments)

            # Сравнение с лучшей найденной планировкой
            if total_rectangularity_error < best_rectangularity:
                best_rectangularity = total_rectangularity_error
                best_plan = apartments
            if best_rectangularity < 0.01:
                break

            # Early exit if perfect plan is found
            if best_score == 0:
                break



        self.apartments = best_plan if best_plan is not None else []  # Save the best generated plan
        if not self.apartments:
            print("Не нашел планировку")
        self.validate_apartment_connectivity(self.apartments, last_validation=True)
        if not self.plan_done and self.apartments:
            for apt in self.apartments:
                apt.section_polygon = self.polygon
                apt.cells = None
                apt.check_and_create_cell_grid(cell_size=1.0, polygon_to_check=Polygon(apt.points))
                apt._process_cells()
                apt.generate_apartment_planning()
            for apt in self.apartments:
                cutted_polygon = Polygon(apt.points).simplify(tolerance=0.01,
                                                               preserve_topology=True).intersection(
                    self.polygon.simplify(tolerance=0.01, preserve_topology=True))
                if isinstance(cutted_polygon, MultiPolygon):
                    cutted_polygon = max(cutted_polygon.geoms, key=lambda a: a.area)
                apt.points = list(cutted_polygon.exterior.coords)
                apt.polygon = Polygon(apt.points)
                for room in apt.rooms:
                    cutted_polygon = Polygon(room.points).simplify(tolerance=0.01,
                                                                   preserve_topology=True).intersection(
                        apt.polygon.simplify(tolerance=0.01, preserve_topology=True))
                    if isinstance(cutted_polygon, Polygon):
                        room.points = list(cutted_polygon.exterior.coords)
                        room.polygon = Polygon(room.points)
                apt._generate_windows()

        total_time = time.time() - start_time
        print(f"Section planning completed in {total_time:.2f} seconds.")
        return self.apartments

    def _rectangularity_score(self, poly):
        """
        Рассчитывает прямоугольность полигона.

        Args:
            poly (Polygon): Полигон.

        Returns:
            float: Оценка прямоугольности (чем меньше, тем лучше).
        """
        extended_area = poly.envelope.area
        area = poly.area
        return abs(extended_area - area) / area

    def _reset_cell_assignments(self):
        """Resets the 'assigned' status of all cells in the grid."""
        for cell in self.cells:
            cell['assigned'] = False

    def _allocate_apartments(self, cells):
        """Allocates cells to apartments according to the specified parameters."""
        free_cells = [cell['polygon'] for cell in self.cells if not cell['assigned']]
        apartments = []
        remaining_cells = [cell for cell in cells if not cell['assigned']]
        self.initial_corner_cells = [cell for cell in cells if cell['is_corner'] and cell['polygon'].intersects(self.building_polygon.exterior)]
        self.otladka = self.initial_corner_cells

        # Создаем копию apartment_table
        apartment_table_copy = copy.deepcopy(self.apartment_table)
        while_start_time = time.time()
        next_preserve_cells = []
        while apartment_table_copy:
            if time.time() - while_start_time > 5:
                break
            # Выбираем случайный тип квартиры из доступных
            sorted_types = sorted(apartment_table_copy.keys())
            state_tuple = tuple(apartment_table_copy[t]['number'] for t in sorted_types)
            # 2) possible_actions = список apt_types
            possible_actions = list(apartment_table_copy.keys())

            # 3) вызываем агент
            apt_type = self.agent.act(state_tuple, possible_actions)

            # 4) берем данные
            apt_info = apartment_table_copy[apt_type]
            min_cells, max_cells = self._get_apartment_cell_range(apt_info['area_range'], cell_size=self.cell_size)



            # Пытаемся разместить квартиру
            apartment_cells = self._allocate_apartment_cells(remaining_cells, min_cells, max_cells, apartments)
            if not apartment_cells:
                new_sorted_types = sorted(apartment_table_copy.keys())
                new_state_tuple = tuple(apartment_table_copy[t]['number'] for t in new_sorted_types)
                self.agent.store_transition(
                    reward=-1.0,  # карательный штраф
                    new_state=new_state_tuple,
                    done=False
                )
                continue

            # apartment_cells = self.fill_section_perimeter(self.cells, apartment_cells, max_cells, min_cells)
            remaining_cells = [cell for cell in remaining_cells if not cell['assigned']]

            # Создаем полигон для квартиры
            apartment_polygon = union_all([cell['polygon'] for cell in apartment_cells])
            # Проверяем с учетом буфера
            is_contained = self.polygon.contains(apartment_polygon)
            if isinstance(apartment_polygon, Polygon):
                points = list(apartment_polygon.exterior.coords)
            elif isinstance(apartment_polygon, MultiPolygon):
                for cell in apartment_cells:
                    cell['assigned'] = False
                remaining_cells = [cell for cell in remaining_cells if not cell['assigned']]
                continue
            # Создаем объект Apartment
            apartment = Apartment(points=points, apt_type=apt_type, building_polygon=self.building_polygon)
            apartment.cells = apartment_cells
            apartments.append(apartment)
            fail = False
            has_outsiders, outsiders = self.validate_apartment_connectivity(apartments)
            if has_outsiders and not self.simple_plan:
                self._update_cell_properties(apartment_cells)
                for cell in apartment.cells:
                    cell['assigned'] = False
                new_sorted_types = sorted(apartment_table_copy.keys())
                new_state_tuple = tuple(apartment_table_copy[t]['number'] for t in new_sorted_types)
                self.agent.store_transition(
                    reward=-2.0,  # карательный штраф
                    new_state=new_state_tuple,
                    done=False
                )
                apartments.remove(apartment)
                fail = True

            if fail:
                continue
            self._update_cell_properties(apartment_cells)
            reward = 2
            # Уменьшаем количество квартир данного типа
            apartment_table_copy[apt_type]['number'] -= 1
            if apartment_table_copy[apt_type]['number'] == 0:
                del apartment_table_copy[apt_type]
            new_sorted_types = sorted(apartment_table_copy.keys())
            new_state_tuple = tuple(apartment_table_copy[t]['number'] for t in new_sorted_types)
            self.agent.store_transition(
                reward=reward,
                new_state=new_state_tuple,
                done=False
            )

        return apartments

    def _validate_apartment_perimeter_adjacency(self, apartment_polygon):
        """First validation: Checks if the apartment has at least one side adjacent to the external perimeter."""
        return apartment_polygon.exterior.intersects(self.polygon.exterior)

    def _validate_apartments_free_sides(self):
        """Second validation: Checks that each apartment has at least one free side.

        A free side is a side not adjacent to the external perimeter or any other apartment.
        Returns True if all apartments have at least one free side, False otherwise.
        """
        all_valid = True
        aparts_to_remove = []
        for i, apt in enumerate(self.apartments):
            apartment_polygon = intersection(apt.polygon, self.polygon)
            has_free_side = False
            # Get the exterior coordinates as pairs of points
            if isinstance(apartment_polygon, Polygon):
                coords = list(apartment_polygon.exterior.coords)
            else:
                return None
            # Create LineStrings for each side
            sides = [LineString([coords[j], coords[j + 1]]) for j in
                     range(len(coords) - 1)]  # last point is same as first
            free_sides = []
            building_perimeter_sides = []
            for side in sides:
                side_touches_section_perimeter = self.polygon.exterior.intersects(side)
                side_touches_building_perimeter = self.building_polygon.exterior.intersects(side)
                side_outside_section = not self.polygon.contains(side)
                side_touches_other_apartment = False
                # Check if side intersects with any other apartment
                for k, other_apt in enumerate(self.apartments):
                    if k == i:
                        continue
                    if other_apt.polygon.exterior.intersects(side):
                        side_touches_other_apartment = True
                        break  # Side touches another apartment

                if not side_touches_other_apartment and not side_touches_section_perimeter and not side_outside_section:
                    free_sides.append(side)
                if side_touches_building_perimeter:
                    building_perimeter_sides.append(side)

            apt.free_sides = free_sides
            apt.building_perimeter_sides = building_perimeter_sides
        return aparts_to_remove

    def _validate_apartment_number(self, apartments):
        """
        Проверяем, что кол-во сгенерированных квартир соответствует ожидаемому
        total_apartment_number за вычетом удаленных квартир.
        """
        return len(apartments) == self.total_apartment_number

    def _calculate_cell_counts(self, cells):
        """Calculates the number of cells to allocate for each apartment type."""
        total_area = self.polygon.area
        cell_area = cells[0]['polygon'].area if cells else 0
        cell_counts = {}
        total_area_min = {apt_type: 0 for apt_type in self.apartment_table.keys()}
        total_area_max = {apt_type: 0 for apt_type in self.apartment_table.keys()}
        for apt_type, apt_info in self.apartment_table.items():
            number = apt_info['number']
            area_range = apt_info['area_range']
            min_cells = area_range[0]
            max_cells = area_range[1]
            total_area_min[apt_type] += number * min_cells
            total_area_max[apt_type] += number * max_cells
        for apt_type, apt_info in self.apartment_table.items():
            number = apt_info['number']
            percent = apt_info['percent']
            allocated_area_min = sum(total_area_min.values()) * percent / 100
            allocated_area_max = sum(total_area_max.values()) * percent / 100
            if allocated_area_min < allocated_area_max:
                allocated_area = random.randint(allocated_area_min, allocated_area_max)
            else:
                allocated_area = allocated_area_min
            allocated_cell_count = int(allocated_area / cell_area)
            cell_counts[apt_type] = allocated_cell_count
        remaining_cell_counts = cell_counts.copy()
        return cell_counts, remaining_cell_counts

    def _get_apartment_cell_range(self, area_range, cell_size):
        """Determines the minimum and maximum number of cells for an apartment based on the area range."""
        cell_area = cell_size ** 2  # Area of a single cell
        min_cells = max(1, int(area_range[0] / cell_area))
        max_cells = int(area_range[1] / cell_area)
        return min_cells, max_cells

    def _allocate_apartment_cells(self, remaining_cells, min_cells, max_cells, apartments):
        """Allocates cells for a single apartment using BFS to ensure contiguity.

        Modification: Adds neighbors to the queue based on the number of their free neighbors.
        Cells with more free neighbors are prioritized.
        """

        apt_cell_count = max_cells

        # Выбираем случайную стартовую клетку из доступных угловых клеток
        apartment_cells = []
        visited_cells = set()

        if self.queue_corners_to_allocate:
            temp_apartment_cells = []
            # self.process_corner_cell(self.queue_corners_to_allocate[-1], apartments)
            # print(len(self.temporary_cells))
            queue = [self.queue_corners_to_allocate.pop()]
            while queue and len(temp_apartment_cells) < apt_cell_count:
                current_cell = queue.pop(0)
                if current_cell['assigned']:
                    continue
                visited_cells.add(current_cell['id'])
                temp_apartment_cells.append(current_cell)

                current_cell['assigned'] = True
                remaining_cells = [cell for cell in remaining_cells if not cell['assigned']]

                # Получаем не назначенные соседние клетки
                neighbors = [neighbor for neighbor in current_cell['neighbors'] if not neighbor['assigned']]

                # Сортируем соседей по убыванию количества их свободных соседей
                neighbors_sorted = sorted(
                    neighbors,
                    key=lambda cell: len([n for n in cell['neighbors'] if not n['assigned']])
                )

                # Добавляем отсортированных соседей в очередь
                queue.extend(neighbors_sorted)

                if min_cells <= len(temp_apartment_cells) <= max_cells:
                    apt_polygon = union_all([cell['polygon'] for cell in temp_apartment_cells])
                    if self._rectangularity_score(apt_polygon) == 0:
                        return temp_apartment_cells
            return temp_apartment_cells


        elif len([cell for cell in self.initial_corner_cells if not cell['assigned']]) > 0:
            queue = [random.choice([cell for cell in self.initial_corner_cells if not cell['assigned']])]
            while queue and len(apartment_cells) < apt_cell_count:
                current_cell = queue.pop(0)
                if current_cell['assigned']:
                    continue
                visited_cells.add(current_cell['id'])
                apartment_cells.append(current_cell)

                current_cell['assigned'] = True
                remaining_cells = [cell for cell in remaining_cells if not cell['assigned']]

                # Получаем не назначенные соседние клетки
                neighbors = [neighbor for neighbor in current_cell['neighbors'] if not neighbor['assigned']]

                # Сортируем соседей по убыванию количества их свободных соседей
                neighbors_sorted = sorted(
                    neighbors,
                    key=lambda cell: len([n for n in cell['neighbors'] if not n['assigned']])
                )
                # Добавляем отсортированных соседей в очередь
                queue.extend(neighbors_sorted)

                if min_cells <= len(apartment_cells) <= max_cells:
                    apt_polygon = union_all([cell['polygon'] for cell in apartment_cells])
                    if self._rectangularity_score(apt_polygon) == 0:
                        return apartment_cells
            return apartment_cells

        elif len([cell for cell in self.cells if cell['on_perimeter'] and not cell['assigned']]) > 0:
            cells_to_choose = []
            for apart in apartments:
                cells_to_choose.extend([cell for cell in self.cells if cell['on_perimeter'] and not cell['assigned']
                                        and not cell['polygon'].intersects(apart.polygon)])
            if cells_to_choose:
                queue = [random.choice(cells_to_choose)]
            else:
                queue = [random.choice([cell for cell in self.cells if cell['on_perimeter'] and not cell['assigned']])]
            while queue and len(apartment_cells) < apt_cell_count:
                current_cell = queue.pop(0)
                if current_cell['assigned']:
                    continue
                visited_cells.add(current_cell['id'])
                apartment_cells.append(current_cell)

                current_cell['assigned'] = True
                remaining_cells = [cell for cell in remaining_cells if not cell['assigned']]

                # Получаем не назначенные соседние клетки
                neighbors = [neighbor for neighbor in current_cell['neighbors'] if not neighbor['assigned']]

                # Сортируем соседей по убыванию количества их свободных соседей
                neighbors_sorted = sorted(
                    neighbors,
                    key=lambda cell: len([n for n in cell['neighbors'] if not n['assigned']])
                )
                # Добавляем отсортированных соседей в очередь
                queue.extend(neighbors_sorted)
                if min_cells <= len(apartment_cells) <= max_cells:
                    apt_polygon = union_all([cell['polygon'] for cell in apartment_cells])
                    if self._rectangularity_score(apt_polygon) == 0:
                        return apartment_cells
            return apartment_cells

    def _update_cell_properties(self, apartment_cells):
        """Updates the properties of cells based on the allocated apartment cells."""
        for cell in apartment_cells:
            if cell['on_perimeter']:
                perimeter_neighbors_for_new_corner = [neighbor for neighbor in cell['neighbors'] if
                                                      neighbor['assigned'] == False and neighbor['on_perimeter']
                                                      and cell['polygon'].intersects(self.building_polygon.exterior)]
                if len(perimeter_neighbors_for_new_corner) > 0:
                    for cell_for_new_corner in perimeter_neighbors_for_new_corner:
                        cell_for_new_corner['is_corner'] = True  # Reset is_corner before checking
                        self.queue_corners_to_allocate.append(cell_for_new_corner)

    def fill_section_perimeter(self, cells, apartment_cells, max_area, min_area):
        """
        Расширяет apartment_cells, заполняя периметр секции, если осталось меньше 5 свободных клеток
        и добавляет клетки в apartment_cells, если площадь их контура меньше max_area.

        Args:
            cells (list): Список всех клеток секции.
            apartment_cells (list): Список клеток, уже принадлежащих квартире.
            max_area (float): Максимально допустимая площадь контура.
        """
        # Находим периметр секции
        initial_apartment_cells = apartment_cells.copy()
        section_sides = [LineString([self.polygon.exterior.coords[i], self.polygon.exterior.coords[i + 1]])
                         for i in range(len(self.polygon.exterior.coords) - 1)]

        # Список клеток, которые еще не заняты
        unassigned_cells = [cell for cell in cells if not cell['assigned']]
        added_cells = []
        # Найдем стороны секции, пересекающиеся с apartment_cells
        intersecting_sides = []
        apartment_cells_union = union_all([cell['polygon'] for cell in apartment_cells])

        for side in section_sides:
            if apartment_cells_union.intersects(side) and not apartment_cells_union.touches(side):
                intersecting_sides.append(side)
        # Расширяем apartment_cells вдоль периметра, если осталось менее 5 свободных клеток
        for side in intersecting_sides:
            adjacent_unassigned = [
                cell for cell in unassigned_cells
                if cell['polygon'].intersects(side)
            ]
            if len(adjacent_unassigned) < 6:
                for cell in adjacent_unassigned:
                    cell['assigned'] = True
                    apartment_cells.append(cell)
                    added_cells.append(cell)

        # Проверяем площадь envelope и добавляем клетки из envelope
        apartment_cells_union = union_all([cell['polygon'] for cell in apartment_cells])
        apartment_envelope = apartment_cells_union.envelope

        if apartment_envelope.area < max_area:
            for cell in unassigned_cells:
                if apartment_envelope.contains(cell['polygon']):
                    cell['assigned'] = True
                    apartment_cells.append(cell)
                    added_cells.append(cell)
            return apartment_cells
        else:
            last_cells = self._shrink_if_needed(apartment_cells, max_area, min_area, initial_apartment_cells)
            for cell in added_cells:
                cell['assigned'] = False
            return last_cells

    def _clean_apartment_table(self, apartment_table: Dict) -> Dict:
        """
        Удаляет из apartment_table типы квартир, у которых number = 0.
        """
        return {apt_type: data for apt_type, data in apartment_table.items() if data['number'] > 0}

    def copy(self):
        """Создает копию объекта Section."""
        return Section(
            points=self.points[:],  # Копируем список точек
            apartment_table=copy.deepcopy(self.apartment_table),  # Глубокая копия таблицы квартир
            building_polygon=self.building_polygon.buffer(0),  # Копия полигона
        )

    def _calc_total_apartment_number(self):
        """
        Суммируем общее количество квартир во входной apartment_table.
        """
        total = 0
        for apt_type in self.apartment_table:
            total += self.apartment_table[apt_type]['number']
        return total

    def validate_apartment_connectivity(self, apartments: List[Apartment], last_validation=False):
        """
        Проверяет, пересекается ли каждая квартира с полигоном оставшихся свободных клеток.
        Если нет пересечения, квартира удаляется из списка, а в removed_apartments_table
        добавляется одна удаленная квартира соответствующего типа.
        """
        # Проверяем тип self.free_polygon
        free_polygon = union_all([cell['polygon'] for cell in self.cells if not cell['assigned']])
        # Проверяем тип self.free_polygon
        if isinstance(free_polygon, MultiPolygon):
            # Выбираем самый большой полигон из MultiPolygon
            free_polygon = max(free_polygon.geoms, key=lambda p: p.area)
        # Генерируем список квартир, не пересекающихся с полигоном
        outsiders = []
        for apartment in apartments:
            # Проверяем пересечение с self.free_polygon
            inter = apartment.polygon.simplify(tolerance=0.01, preserve_topology=True).exterior.intersection(free_polygon)
            if inter.is_empty or isinstance(inter, Point):
                outsiders.append(apartment)
            elif inter.length < 2:
                outsiders.append(apartment)
            elif (isinstance(inter, LineString) or isinstance(inter, MultiLineString)) and last_validation:
                apartment.free_sides.append(inter)
        if outsiders:
            return True, outsiders
        return False, outsiders


    def _shrink_if_needed(self, apartment_cells, max_area, min_area, initial_cells):
        """
        Если envelope слишком большой (area > max_area) или маленький (area < min_area),
        пытаемся убрать 'ряды' клеток вдоль стороны envelope, чтобы уменьшить площадь.
        Если не удается привести к нужному диапазону, откатываемся к initial_cells.
        """
        union_poly = union_all([cell['polygon'] for cell in apartment_cells])
        envelope_poly = union_poly.envelope

        iteration_count = 0
        while min_area <= envelope_poly.area <= max_area and iteration_count < 3:
            # Ищем сторону envelope, которую можно 'срезать',
            # если она не соприкасается с периметром секции
            # и не пересекает уже имеющиеся квартиры (self.apartments).
            envelope_sides = [
                LineString([envelope_poly.exterior.coords[i], envelope_poly.exterior.coords[i + 1]])
                for i in range(len(envelope_poly.exterior.coords) - 1)
            ]
            for side in envelope_sides:
                if (not side.touches(self.polygon.exterior)
                        and not any(side.intersects(apt.polygon) for apt in self.apartments)):
                    removable_side = side
                    break

            if not removable_side:
                break  # не нашли сторону для удаления

            # Удаляем клетки, centroid которых очень близко к side
            to_remove = [c for c in apartment_cells if removable_side.distance(c['polygon'].centroid) < 1e-6]
            for c in to_remove:
                c['assigned'] = False
                apartment_cells.remove(c)

            # Пересчитываем envelope
            union_poly = union_all([cell['polygon'] for cell in apartment_cells])
            envelope_poly = union_poly.envelope
            iteration_count += 1

        # Если после всех итераций (area < min_area) или (area > max_area),
        # то откатываемся
        final_area = envelope_poly.area
        if not (min_area <= final_area <= max_area):
            # откат
            for c in apartment_cells:
                if c not in initial_cells:
                    c['assigned'] = False
            return initial_cells

        return apartment_cells

    def process_corner_cell(self, queue_cell, apartments):
        """
        Обрабатывает заданную клетку из queue_corners_to_allocate.
        Расширяет сторону последнего apartment, к которой клетка прилегает, и отмечает подходящие клетки.

        Args:
            queue_cell (dict): Клетка из queue_corners_to_allocate.
            apartments (list): Список apartments.
            assigned_cells (list): Список уже назначенных клеток.
        """
        # Получаем последний apartment
        if not apartments:
            return
        if self.temporary_cells:
            for cell in self.temporary_cells:
                cell['assigned'] = False
            self.temporary_cells.clear()
        last_apartment = apartments[-1]
        apartment_polygon = last_apartment.polygon.simplify(tolerance=0.01, preserve_topology=True)

        # Проверяем стороны квартиры
        apartment_sides = [
            LineString([apartment_polygon.exterior.coords[i], apartment_polygon.exterior.coords[i + 1]])
            for i in range(len(apartment_polygon.exterior.coords) - 1)
        ]

        # Находим сторону, к которой прилегает клетка
        cell_polygon = queue_cell['polygon']
        touching_side = None
        for side in apartment_sides:
            if cell_polygon.intersects(side) and isinstance(intersection(side, self.polygon), LineString):
                touching_side = side
                break
        print(touching_side)
        if not touching_side:
            return  # Нет подходящей стороны

        # Расширяем найденную сторону на 3 единицы в обе стороны
        coords = list(touching_side.coords)
        start, end = Point(coords[0]), Point(coords[1])
        direction = (end.x - start.x, end.y - start.y)

        # Вычисляем расширенные точки
        expanded_start = translate(start, xoff=-3 * direction[0], yoff=-3 * direction[1])
        expanded_end = translate(end, xoff=3 * direction[0], yoff=3 * direction[1])

        expanded_side = LineString([expanded_start, expanded_end])

        # Вычисляем вектор противоположного направления относительно клетки
        cell_center = cell_polygon.centroid
        side_center = touching_side.centroid
        relative_direction = (cell_center.x - side_center.x, cell_center.y - side_center.y)

        # Инвертируем вектор направления
        opposite_direction = (-relative_direction[0], -relative_direction[1])

        # Находим клетки, которые касаются expanded_side и находятся в нужном направлении
        for cell in [c for c in self.cells if not c['assigned'] and c['polygon'].intersects(touching_side)]:
            neighbor_center = cell['polygon'].centroid
            vector_to_neighbor = (neighbor_center.x - cell_center.x, neighbor_center.y - cell_center.y)

            # Проверяем направление вектора
            if vector_to_neighbor[0] * opposite_direction[0] + vector_to_neighbor[1] * opposite_direction[1] > 0:
                if cell['polygon'].intersects(expanded_side):
                    cell['assigned'] = True
                    self.temporary_cells.append(cell)

