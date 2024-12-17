from Classes.Geometry.GeometricFigure import GeometricFigure
from Classes.Geometry.Territory.Building.Apartment.Apartment import Apartment
from Classes.Geometry.Territory.Building.Elevator import Elevator
from Classes.Geometry.Territory.Building.Stair import Stair
from shapely.geometry import Polygon, LineString, MultiPolygon
from shapely.ops import unary_union
import random
from typing import List, Tuple, Dict
import time



class Section(GeometricFigure):
    def __init__(self, points: List[Tuple[float, float]],
                 apartment_table: Dict,
                 apartments: List['Apartment'] = None,
                 building_polygon: Polygon = None):
        super().__init__(points)
        self.apartments = apartments if apartments is not None else []  # List of Apartment objects
        self.queue_corners_to_allocate = []
        self.free_cells = []
        self.apartment_table = apartment_table
        self.building_polygon = building_polygon

    def generate_section_planning(self, max_iterations=30, cell_size=1):
        self.cell_size = cell_size
        """Generates a floor plan by allocating apartments according to the given apartment table."""
        self.apartments = []  # Initialize as empty list
        best_plan = None
        best_score = float('inf')  # The low3   2er, the better
        start_time = time.time()

        # Create the cell grid once

        for iteration in range(max_iterations):
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

            if not self._validate_apartments_free_sides(apartments):
                # Allocation is invalid, skip to next iteration
                for apart in apartments:
                    apart.check_and_create_cell_grid(cell_size=1)
                    apart._reset_cell_assignments()
                    self._process_cells()
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
        for apt in self.apartments:
            apt.section_polygon = self.polygon
            apt.check_and_create_cell_grid(cell_size=1.0, polygon_to_check=Polygon(apt.points))
            apt._process_cells()
            apt.generate_apartment_planning()

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

        apartments = []
        remaining_cells = [cell for cell in cells if not cell['assigned']]
        self.initial_corner_cells = [cell for cell in cells if cell['is_corner']]

        # Calculate the number of cells for each apartment type
        cell_counts, remaining_cell_counts = self._calculate_cell_counts(cells)

        for apt_type, apt_info in reversed(self.apartment_table.items()):

            min_cells, max_cells = self._get_apartment_cell_range(apt_info['area_range'], cell_size=self.cell_size)
            allocated_cell_count = remaining_cell_counts[apt_type]
            number = apt_info['number']
            minimum = min_cells * number
            while number > 0 or allocated_cell_count > minimum:
                apartment_cells = self._allocate_apartment_cells(remaining_cells, min_cells, max_cells)
                if not apartment_cells:
                    break  # No more apartments of this type can be allocated
                apartment_cells = self.fill_section_perimeter(self.cells, apartment_cells, max_cells)
                remaining_cells = [cell for cell in remaining_cells if not cell['assigned']]

                # Create the apartment polygon
                apartment_polygon = unary_union([cell['polygon'] for cell in apartment_cells])
                rectangular_apartment_polygon = apartment_polygon.envelope
                if rectangular_apartment_polygon.area < max_cells:
                    for cell in remaining_cells:
                        if not cell['assigned'] and rectangular_apartment_polygon.contains(cell['polygon']):
                            apartment_cells.append(cell)
                            cell['assigned'] = True
                    remaining_cells = [cell for cell in remaining_cells if not cell['assigned']]
                    rectangular_apartment_polygon = unary_union([cell['polygon'] for cell in apartment_cells])
                    if isinstance(rectangular_apartment_polygon, Polygon):  # Если это Polygon
                        points = list(rectangular_apartment_polygon.exterior.coords)

                    elif isinstance(rectangular_apartment_polygon, MultiPolygon):  # Если это MultiPolygon
                        for cell in apartment_cells:
                            cell['assigned'] = False
                        remaining_cells = [cell for cell in remaining_cells if not cell['assigned']]
                        continue
                # Проверяем тип полигона
                else:
                    for i in range(3):
                        new_apartment_polygon = unary_union([cell['polygon'] for cell in apartment_cells[:(-1 - i)]])
                        if new_apartment_polygon.area == apartment_polygon.envelope.area:
                            apartment_polygon = new_apartment_polygon.copy()
                            for cell in apartment_cells[(-1 - i):]:
                                cell['assigned'] = False
                            apartment_cells = apartment_cells[(-1 - i):]
                            break
                    if isinstance(apartment_polygon, Polygon):  # Если это Polygon
                        points = list(apartment_polygon.boundary.coords)
                    elif isinstance(apartment_polygon, MultiPolygon):  # Если это MultiPolygon
                        for cell in apartment_cells:
                            cell['assigned'] = False
                        remaining_cells = [cell for cell in remaining_cells if not cell['assigned']]
                        continue

                # if self._check_intersection_with_structures(points):
                #     for cell in apartment_cells:
                #         cell['assigned'] = False
                #     remaining_cells = [cell for cell in remaining_cells if not cell['assigned']]
                #     continue
                self._update_cell_properties(apartment_cells)
                
                apartment = Apartment(points=points, apt_type=apt_type, building_polygon=self.building_polygon)
                apartments.append(apartment)
                allocated_cell_count -= len(apartment_cells)
                remaining_cell_counts[apt_type] = allocated_cell_count
                number -= 1


        return apartments

    def _validate_apartment_perimeter_adjacency(self, apartment_polygon):
        """First validation: Checks if the apartment has at least one side adjacent to the external perimeter."""
        return apartment_polygon.exterior.intersects(self.polygon.exterior)

    def _validate_apartments_free_sides(self, apartments):
        """Second validation: Checks that each apartment has at least one free side.

        A free side is a side not adjacent to the external perimeter or any other apartment.
        Returns True if all apartments have at least one free side, False otherwise.
        """
        all_valid = True
        for i, apt in enumerate(apartments):
            apartment_polygon = apt.polygon
            has_free_side = False
            # Get the exterior coordinates as pairs of points
            coords = list(apartment_polygon.exterior.coords)
            # Create LineStrings for each side
            sides = [LineString([coords[j], coords[j + 1]]) for j in
                     range(len(coords) - 1)]  # last point is same as first
            free_sides = []
            building_perimeter_sides = []
            for side in sides:
                side_touches_section_perimeter = self.polygon.exterior.intersects(side)
                side_touches_building_perimeter = self.building_polygon.exterior.intersects(side)
                side_touches_other_apartment = False
                # Check if side intersects with any other apartment
                for k, other_apt in enumerate(apartments):
                    if k == i:
                        continue
                    if other_apt.polygon.exterior.intersects(side):
                        side_touches_other_apartment = True
                        break  # Side touches another apartment
                if not side_touches_other_apartment and not side_touches_section_perimeter:
                    has_free_side = True
                    free_sides.append(side)
                if side_touches_building_perimeter:
                    building_perimeter_sides.append(side)
            if not has_free_side:
                all_valid = False

            apt.free_sides = free_sides
            apt.building_perimeter_sides = building_perimeter_sides
        return all_valid

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

    def _allocate_apartment_cells(self, remaining_cells, min_cells, max_cells):
        """Allocates cells for a single apartment using BFS to ensure contiguity.

        Modification: Adds neighbors to the queue based on the number of their free neighbors.
        Cells with more free neighbors are prioritized.
        """

        apt_cell_count = random.randint(min_cells, (max_cells-min_cells) * 0.8 + min_cells)

        # Выбираем случайную стартовую клетку из доступных угловых клеток
        apartment_cells = []
        visited_cells = set()
        if self.queue_corners_to_allocate is not None and len(self.queue_corners_to_allocate) >= 1:
            start_cell = random.choice(self.queue_corners_to_allocate)
            self.queue_corners_to_allocate.remove(start_cell)  # Удаляем выбранный элемент из списка
        elif len(self.initial_corner_cells) > 0:
            start_cell = random.choice(self.initial_corner_cells)
            self.initial_corner_cells.remove(start_cell)  # Удаляем выбранный элемент из списка
        elif len([cell for cell in remaining_cells if cell['on_perimeter'] and not cell['assigned']]) > 0:
            start_cell = random.choice(
                [cell for cell in remaining_cells if cell['on_perimeter'] and not cell['assigned']])
        else:
            return None
        queue = [start_cell]
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
                key=lambda cell: len([n for n in cell['neighbors'] if not n['assigned']]),
                reverse=True
            )

            # Добавляем отсортированных соседей в очередь
            queue.extend(neighbors_sorted)

        # Проверка, удалось ли выделить нужное количество клеток
        if len(apartment_cells) < min_cells:
            # Если выделено меньше минимально необходимого, снимаем назначение и возвращаем None
            for cell in apartment_cells:
                cell['assigned'] = False
            return None

        return apartment_cells

    def _update_cell_properties(self, apartment_cells):
        """Updates the properties of cells based on the allocated apartment cells."""
        for cell in apartment_cells:
            if cell['on_perimeter']:
                perimeter_neighbors_for_new_corner = [neighbor for neighbor in cell['neighbors'] if
                                                      neighbor['assigned'] == False and neighbor['on_perimeter']]
                if len(perimeter_neighbors_for_new_corner) > 0:
                    for cell_for_new_corner in perimeter_neighbors_for_new_corner:
                        cell_for_new_corner['is_corner'] = True  # Reset is_corner before checking
                        self.queue_corners_to_allocate.append(cell_for_new_corner)





    def fill_section_perimeter(self, cells, apartment_cells, max_area):
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

        # Найдем стороны секции, пересекающиеся с apartment_cells
        intersecting_sides = []
        apartment_cells_union = unary_union([cell['polygon'] for cell in apartment_cells])

        for side in section_sides:
            if apartment_cells_union.intersects(side):
                intersecting_sides.append(side)

        # Расширяем apartment_cells вдоль периметра, если осталось менее 5 свободных клеток
        for side in intersecting_sides:
            adjacent_unassigned = [
                cell for cell in unassigned_cells
                if cell['polygon'].intersects(side)
            ]
            if len(adjacent_unassigned) < 3:
                for cell in adjacent_unassigned:
                    cell['assigned'] = True
                    apartment_cells.append(cell)

        # Проверяем площадь envelope и добавляем клетки из envelope
        apartment_cells_union = unary_union([cell['polygon'] for cell in apartment_cells])
        apartment_envelope = apartment_cells_union.envelope

        if apartment_envelope.area < max_area:
            for cell in unassigned_cells:
                if apartment_envelope.contains(cell['polygon']):
                    cell['assigned'] = True
                    apartment_cells.append(cell)
        else:
            return initial_apartment_cells
        return apartment_cells


