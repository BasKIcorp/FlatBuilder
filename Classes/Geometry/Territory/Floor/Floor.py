from turtledemo.penrose import start

from Classes.Geometry.GeometricFigure import GeometricFigure
from Classes.Geometry.Territory.Apartment.Apartment import Apartment
from Classes.Geometry.Territory.Apartment.Room import Room
from Classes.Geometry.Territory.Apartment.WetArea import WetArea
from Classes.Geometry.Territory.Apartment.Balcony import Balcony
from Classes.Geometry.Territory.Floor.Elevator import Elevator
from Classes.Geometry.Territory.Floor.Stair import Stair
from shapely.geometry import Polygon, LineString, box, MultiPolygon
from shapely.ops import unary_union
from shapely.prepared import prep
from shapely.vectorized import contains
import random
from typing import List, Tuple
import math
import time
import numpy as np
from collections import deque




class Floor(GeometricFigure):
    def __init__(self, points: List[Tuple[float, float]], apartments: List['Apartment'] = None,
                 elevators: List['Elevator'] = None, stairs: List['Stair'] = None):
        super().__init__(points)
        self.apartments = apartments if apartments is not None else []  # List of Apartment objects
        self.elevators = elevators if elevators is not None else []
        self.stairs = stairs if stairs is not None else []
        self.queue_corners_to_allocate = []
        self.elevators_stairs_cells = []

    def generatePlanning(self, apartment_table, max_iterations=10, cell_size=1):
        if len(self.elevators) > 0 or len(self.stairs) >0:
            self.elevators_stairs_cells = [cell for cell in self.cells if cell['assigned_for_elevators_stairs']]
        self.check_and_create_cell_grid(cell_size=1)
        self.cell_size = cell_size
        print(len([cell for cell in self.cells]))
        """Generates a floor plan by allocating apartments according to the given apartment table."""
        self.apartments = []  # Initialize as empty list
        best_plan = None
        best_score = float('inf')  # The low3   2er, the better
        start_time = time.time()

        # Create the cell grid once


        for iteration in range(max_iterations):
            # Reset the cell assignments between iterations


            # self._reset_cell_assignments()
            # Allocate apartments using the cell grid
            apartments = self._allocate_apartments(self.cells, apartment_table)

            # **Validation**: Validate apartments for free sides
            if not apartments:
                for apart in apartments:
                    apart._reset_cell_assignments()
                    self._process_cells()
                continue  # No apartments allocated in this iteration

            if not self._validate_apartments_free_sides(apartments):
                # Allocation is invalid, skip to next iteration
                # print(f"Iteration {iteration + 1}: Allocation rejected due to lack of free sides.")
                for apart in apartments:
                    apart._reset_cell_assignments()
                    self._process_cells()
                continue

            # if len(self.stairs) > 0 or len(self.elevators) > 0:
            #     if not self.find_path_to_lifts_or_stairs(apartments):
            #         for apart in apartments:
            #             apart._reset_cell_assignments()
            #         continue

            # Calculate distribution error
            total_error = self._calculate_total_error(apartments, apartment_table)

            # Update the best plan if current is better
            if total_error < best_score:
                best_score = total_error
                best_plan = apartments
                print(f"Iteration {iteration + 1}: Found a better plan with error {best_score:.2f}%")
            for apart in apartments:
                apart._reset_cell_assignments()
                self._process_cells()

            # Early exit if perfect plan is found
            if best_score == 0:
                break

        self.apartments = best_plan if best_plan is not None else []  # Save the best generated plan
        for apt in self.apartments:
            apt.generate_apartment_planning()

        total_time = time.time() - start_time
        print(f"Floor planning completed in {total_time:.2f} seconds.")

        return self.apartments

    def _reset_cell_assignments(self):
        """Resets the 'assigned' status of all cells in the grid."""
        for cell in self.cells:
            cell['assigned'] = False

    def _allocate_apartments(self, cells, apartment_table):
        """Allocates cells to apartments according to the specified parameters."""

        apartments = []
        remaining_cells = [cell for cell in cells if not cell['assigned']]
        self.initial_corner_cells = [cell for cell in cells if cell['is_corner']]

        # Calculate the number of cells for each apartment type
        cell_counts, remaining_cell_counts = self._calculate_cell_counts(apartment_table, cells)

        for apt_type, apt_info in reversed(apartment_table.items()):

            min_cells, max_cells = self._get_apartment_cell_range(apt_info['area_range'], cell_size=self.cell_size)
            allocated_cell_count = remaining_cell_counts[apt_type]

            while allocated_cell_count >= min_cells:
                apartment_cells = self._allocate_apartment_cells(remaining_cells, min_cells, max_cells)
                if not apartment_cells:
                    break  # No more apartments of this type can be allocated
                remaining_cells = [cell for cell in remaining_cells if not cell['assigned']]
                self._update_cell_properties(apartment_cells)

                # Create the apartment polygon
                apartment_polygon = unary_union([cell['polygon'] for cell in apartment_cells])

                # Проверяем тип полигона
                if isinstance(apartment_polygon, Polygon):  # Если это Polygon
                    points = list(apartment_polygon.exterior.coords)
                elif isinstance(apartment_polygon, MultiPolygon):  # Если это MultiPolygon
                    # Вы можете обработать все полигоны или выбрать один из них
                    # Для примера выбираем первый
                    points = list(apartment_polygon.geoms[0].exterior.coords)
                else:
                    continue  # Если ни то, ни другое, пропускаем

                if self._check_intersection_with_structures(points):
                    for cell in apartment_cells:
                        cell['assigned'] = False
                    continue

                # Создаем объект Apartment
                rooms = []  # Плейсхолдер для комнат
                wet_areas = []  # Плейсхолдер для мокрых зон
                balconies = []  # Плейсхолдер для балконов

                apartment = Apartment(points=points, apt_type=apt_type, rooms=rooms, wet_areas=wet_areas,
                                      balconies=balconies)
                apartment.cells = apartment_cells
                apartments.append(apartment)
                allocated_cell_count -= len(apartment_cells)
                remaining_cell_counts[apt_type] = allocated_cell_count

        return apartments

    def _validate_apartment_perimeter_adjacency(self, apartment_polygon):
        """First validation: Checks if the apartment has at least one side adjacent to the external perimeter."""
        return apartment_polygon.exterior.intersects(self.polygon.exterior)

    def _validate_apartments_free_sides(self, apartments):
        """Second validation: Checks that each apartment has at least one free side.

        A free side is a side not adjacent to the external perimeter or any other apartment.
        Returns True if all apartments have at least one free side, False otherwise.
        """
        for i, apt in enumerate(apartments):
            apartment_polygon = apt.polygon
            has_free_side = False
            # Get the exterior coordinates as pairs of points
            coords = list(apartment_polygon.exterior.coords)
            # Create LineStrings for each side
            sides = [LineString([coords[j], coords[j + 1]]) for j in
                     range(len(coords) - 1)]  # last point is same as first

            for side in sides:
                # Check if side intersects with external perimeter
                if self.polygon.exterior.intersects(side):
                    continue
                # Check if side intersects with any other apartment
                for k, other_apt in enumerate(apartments):
                    if k == i:
                        continue
                    if other_apt.polygon.exterior.intersects(side):
                        break  # Side touches another apartment
                else:
                    # Side does not touch external perimeter or any other apartment
                    has_free_side = True
                    break

            if not has_free_side:
                # Apartment does not have any free sides
                return False
        return True

    def _calculate_cell_counts(self, apartment_table, cells):
        """Calculates the number of cells to allocate for each apartment type."""
        total_area = self.polygon.area
        cell_area = cells[0]['polygon'].area if cells else 0
        cell_counts = {}
        for apt_type, apt_info in apartment_table.items():
            percent = apt_info['percent']
            allocated_area = total_area * (percent / 100)
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

        apt_cell_count = random.randint(min_cells, max_cells)
        if not self.initial_corner_cells:
            return None  # Нет доступных угловых клеток для начала апартамента

        # Выбираем случайную стартовую клетку из доступных угловых клеток
        apartment_cells = []
        visited_cells = set()
        if self.queue_corners_to_allocate is not None and len(self.queue_corners_to_allocate) >= 1:
            random_index = random.randint(0, len(self.queue_corners_to_allocate) - 1)
            start_cell = self.queue_corners_to_allocate.pop(random_index)
        elif len(self.initial_corner_cells) > 0:
            random_index = random.randint(0, len(self.initial_corner_cells) - 1)
            start_cell = self.initial_corner_cells.pop(random_index)
        else:
            start_cell = random.choice([cell for cell in remaining_cells if cell['on_perimeter']])
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

    def _calculate_total_error(self, apartments, apartment_table):
        """Calculates the total error in apartment type distribution among allocated area."""
        # Calculate the total allocated area
        total_allocated_area = sum(apt.area for apt in apartments)

        # Calculate actual percentages among allocated area
        actual_percentages = {}
        for apt_type in apartment_table.keys():
            total_type_area = sum(apt.area for apt in apartments if apt.type == apt_type)
            actual_percent = (total_type_area / total_allocated_area) * 100 if total_allocated_area > 0 else 0
            actual_percentages[apt_type] = actual_percent

        # Calculate total desired percentage
        total_desired_percent = sum(apt_info['percent'] for apt_info in apartment_table.values())

        # Normalize desired percentages to sum up to 100%
        normalized_desired_percentages = {}
        for apt_type, apt_info in apartment_table.items():
            normalized_percent = (apt_info['percent'] / total_desired_percent) * 100 if total_desired_percent > 0 else 0
            normalized_desired_percentages[apt_type] = normalized_percent

        # Calculate total error based on normalized desired percentages
        total_error = sum(
            abs(normalized_desired_percentages[apt_type] - actual_percentages.get(apt_type, 0))
            for apt_type in apartment_table.keys()
        )
        return total_error

    def _inside_polygon_coords(self, coords: List[Tuple[float, float]]) -> Polygon:
        """Создает полигон из заданных координат и проверяет, входит ли он в общий полигон этажа."""
        polygon = Polygon(coords)
        if self.polygon.contains(polygon.exterior):  # Проверяем, что созданный полигон целиком находится в полигоне этажа
            return polygon
        else:
            # Если полигон не входит, можно вернуть None или выдать предупреждение
            print("Полигон не входит в общий полигон этажа.")
            return None

    def set_elevator(self, coords: List[Tuple[float, float]]):
        """Создает лифт и назначает соответствующие клетки как занятые."""
        self.check_and_create_cell_grid(cell_size=1)
        elevator_polygon = self._inside_polygon_coords(coords)
        if elevator_polygon is not None:
            elevator = Elevator(coords)
            self.elevators.append(elevator)  # Добавляем лифт как объект
            # Применяем логику для назначения клеток лифту
            for cell in self.cells:
                if elevator_polygon.intersects(cell['polygon'].exterior):
                    cell['assigned'] = True  # Помечаем клетку как занятою
                    cell['assigned_for_elevators_stairs'] = True


    def set_stairs(self, coords: List[Tuple[float, float]]):
        """Создает лестницу и назначает соответствующие клетки как занятые."""
        self.check_and_create_cell_grid(cell_size=1)
        stair_polygon = self._inside_polygon_coords(coords)
        if stair_polygon is not None:
            stair = Stair(coords)
            self.stairs.append(stair)  # Добавляем лестницу как объект
            # Применяем логику для назначения клеток лестнице
            for cell in self.cells:
                if stair_polygon.intersects(cell['polygon'].exterior):
                    cell['assigned'] = True  # Помечаем клетку как занятою
                    cell['assigned_for_elevators_stairs'] = True

    # def find_path_to_lifts_or_stairs(self, apartments):
    #     """Находит путь от квартир до лифтов или лестниц на этаже."""
    #
    #     # Создаем очередь для BFS
    #
    #     # Собираем клетки с квартирами и добавляем их в очередь
    #     for apartment in apartments:
    #         queue = deque()
    #         visited = set()  # Чтобы отслеживать посетенные клетки
    #         for cell in apartment.cells:
    #             for neighbor in cell["neighbors"]:
    #                 if not neighbor['assigned']:  # Если клетка свободна
    #                     queue.append(neighbor)
    #                     visited.add(neighbor['id'])  # Помечаем как посещенную
    #         # BFS для поиска пути
    #         while queue:
    #             current_cell = queue.popleft()
    #
    #             # Проверяем, находится ли текущая клетка на лифте или лестнице
    #             if len(self.elevators) > 0:
    #                 for elevator in self.elevators:
    #                     if current_cell["polygon"].exterior.intersects(elevator.polygon.exterior):
    #                         break  # Путь найден
    #
    #             if len(self.stairs) > 0:
    #                 for stair in self.stairs:
    #                     if current_cell["polygon"].exterior.intersects(stair.polygon.exterior):
    #                         break  # Путь найден
    #
    #             # Проверяем соседние клетки
    #             for neighbor in current_cell['neighbors']:
    #                 if not neighbor['assigned'] and neighbor['id'] not in visited:
    #                     visited.add(neighbor['id'])  # Помечаем соседнюю клетку как посещенную
    #                     queue.append(neighbor)
    #         else:
    #             # Путь не найден
    #             print('No Way')
    #             return False
    #     print('Find a Way')
    #     return True

    def _check_intersection_with_structures(self, points):
        """Проверяет, пересекаются ли выделенные клетки с лифтами или лестницами."""
        polygon_apt = Polygon(points)
        for cell in self.elevators_stairs_cells:
            if cell["polygon"].exterior.intersects(polygon_apt):
                return True
        return False





