from Classes.Geometry.GeometricFigure import GeometricFigure
from Classes.Geometry.Territory.Apartment.Apartment import Apartment
from Classes.Geometry.Territory.Floor.Elevator import Elevator
from Classes.Geometry.Territory.Floor.Stair import Stair
from shapely.geometry import Polygon, Point, LineString
from shapely.ops import unary_union, linemerge
import random
from typing import List, Tuple
import math
import time

class Floor(GeometricFigure):
    def __init__(self, points: List[Tuple[float, float]], apartments: List['Apartment'] = [], elevators: List['Elevator'] = [], stairs: List['Stair'] = []):
        super().__init__(points)
        self.apartments = apartments  # Список квартир на этаже
        self.elevators = elevators  # Список лифтов на этаже
        self.stairs = stairs  # Список лестниц на этаже

    def generatePlanning(self, apartment_table, max_iterations=5):
        best_plan = None
        best_score = float('inf')  # Чем меньше, тем лучше
        start_time = time.time()

        for iteration in range(max_iterations):
            # Создаем сетку ячеек
            cells, cell_dict = self._create_cell_grid(cell_size=2)

            # Предварительная обработка ячеек
            self._process_cells(cells, cell_dict)

            # Распределяем ячейки по квартирам
            apartments = self._allocate_apartments(cells, apartment_table)

            # Вычисляем ошибку распределения
            total_error = self._calculate_total_error(apartments, apartment_table)

            # Обновляем лучший план, если текущий лучше
            if total_error < best_score:
                best_score = total_error
                best_plan = apartments
                print(f"Итерация {iteration + 1}: найден лучший план с ошибкой {best_score:.2f}%")

            if best_score == 0:
                break

        self.apartments = best_plan  # Сохраняем лучшую сгенерированную планировку
        total_time = time.time() - start_time
        print(f"Генерация планировки завершена за {total_time:.2f} секунд.")

        return self.apartments

    def _create_cell_grid(self, cell_size):
        """Создает сетку ячеек, покрывающих полигон этажа."""
        minx, miny, maxx, maxy = self.polygon.bounds
        num_cells_x = int(math.ceil((maxx - minx) / cell_size))
        num_cells_y = int(math.ceil((maxy - miny) / cell_size))

        cells = []
        cell_dict = {}
        for i in range(num_cells_x):
            for j in range(num_cells_y):
                x1 = minx + i * cell_size
                y1 = miny + j * cell_size
                x2 = x1 + cell_size
                y2 = y1 + cell_size
                cell_polygon = Polygon([
                    (x1, y1),
                    (x2, y1),
                    (x2, y2),
                    (x1, y2)
                ])
                if self.polygon.intersects(cell_polygon):
                    intersection = self.polygon.intersection(cell_polygon)
                    if intersection.area > 0.5 * cell_polygon.area:
                        cells.append({
                            'polygon': cell_polygon,
                            'assigned': False,
                            'neighbors': [],
                            'id': (i, j),
                            'on_perimeter': False
                        })
                        cell_dict[(i, j)] = cells[-1]
        return cells, cell_dict

    def _process_cells(self, cells, cell_dict):
        """Определяет соседей ячеек и отмечает ячейки на периметре."""
        exterior = self.polygon.exterior
        for cell in cells:
            i, j = cell['id']
            cell_polygon = cell['polygon']

            # Проверяем, граничит ли ячейка с внешней стеной
            if cell_polygon.exterior.intersects(exterior):
                cell['on_perimeter'] = True

            neighbors = []
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                ni, nj = i + dx, j + dy
                neighbor = cell_dict.get((ni, nj))
                if neighbor and not neighbor['assigned']:
                    neighbors.append(neighbor)
            cell['neighbors'] = neighbors

    def _allocate_apartments(self, cells, apartment_table):
        """Распределяет ячейки по квартирам согласно заданным параметрам."""
        random.shuffle(cells)
        apartments = []
        remaining_cells = [cell for cell in cells if not cell['assigned']]

        # Вычисляем количество ячеек для каждого типа квартиры
        cell_counts, remaining_cell_counts = self._calculate_cell_counts(apartment_table, cells)

        for apt_type, apt_info in apartment_table.items():
            min_cells, max_cells = self._get_apartment_cell_range(apt_info['area_range'], cell_size=2)
            allocated_cell_count = remaining_cell_counts[apt_type]

            while allocated_cell_count >= min_cells:
                apartment_cells = self._allocate_apartment_cells(remaining_cells, min_cells, max_cells)

                if not apartment_cells:
                    break

                # Проверяем, граничит ли квартира с периметром
                apartment_polygon = unary_union([cell['polygon'] for cell in apartment_cells])
                if not apartment_polygon.exterior.intersects(self.polygon.exterior):
                    for cell in apartment_cells:
                        cell['assigned'] = False
                    continue

                # Сохраняем информацию о квартире
                apartment_area = apartment_polygon.area
                apartment = {
                    'type': apt_type,
                    'area': apartment_area,
                    'geometry': apartment_polygon
                }
                apartments.append(apartment)
                allocated_cell_count -= len(apartment_cells)
                remaining_cell_counts[apt_type] = allocated_cell_count

                # Обновляем список оставшихся ячеек
                remaining_cells = [cell for cell in remaining_cells if not cell['assigned']]

        return apartments

    def _calculate_cell_counts(self, apartment_table, cells):
        """Вычисляет количество ячеек для каждого типа квартиры."""
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
        """Определяет минимальное и максимальное количество ячеек для квартиры."""
        min_cells = max(1, int(area_range[0] / (cell_size ** 2)))
        max_cells = int(area_range[1] / (cell_size ** 2))
        return min_cells, max_cells

    def _allocate_apartment_cells(self, remaining_cells, min_cells, max_cells):
        """Аллоцирует ячейки для одной квартиры."""
        apt_cell_count = random.randint(min_cells, max_cells)
        available_perimeter_cells = [cell for cell in remaining_cells if not cell['assigned'] and cell['on_perimeter']]
        if not available_perimeter_cells:
            return None

        start_cell = random.choice(available_perimeter_cells)
        queue = [start_cell]
        apartment_cells = []
        visited_cells = set()

        while queue and len(apartment_cells) < apt_cell_count:
            current_cell = queue.pop(0)
            if current_cell['assigned']:
                continue
            cell_id = current_cell['id']
            if cell_id in visited_cells:
                continue
            visited_cells.add(cell_id)
            apartment_cells.append(current_cell)
            current_cell['assigned'] = True

            # Добавляем соседей в очередь
            neighbors = current_cell['neighbors']
            random.shuffle(neighbors)
            queue.extend(neighbors)

        if len(apartment_cells) >= min_cells:
            return apartment_cells
        else:
            # Отменяем назначение ячеек, если не удалось сформировать квартиру
            for cell in apartment_cells:
                cell['assigned'] = False
            return None

    def _calculate_total_error(self, apartments, apartment_table):
        """Вычисляет суммарную ошибку распределения квартир по типам."""
        total_allocated_area = sum(apt['area'] for apt in apartments)
        actual_percentages = {}
        for apt_type in apartment_table.keys():
            total_type_area = sum(apt['area'] for apt in apartments if apt['type'] == apt_type)
            actual_percent = (total_type_area / total_allocated_area) * 100 if total_allocated_area > 0 else 0
            actual_percentages[apt_type] = actual_percent

        total_error = sum(abs(apartment_table[apt_type]['percent'] - actual_percentages.get(apt_type, 0)) for apt_type in apartment_table.keys())
        return total_error
