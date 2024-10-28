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

# Класс для этажа, содержащего квартиры, лифты и лестницы
class Floor(GeometricFigure):
    def __init__(self, points: List[Tuple[float, float]], apartments: List['Apartment'] = [], elevators: List['Elevator'] = [], stairs: List['Stair'] = []):
        super().__init__(points)
        self.apartments = apartments  # Список квартир на этаже
        self.elevators = elevators  # Список лифтов на этаже
        self.stairs = stairs  # Список лестниц на этаже

    def generatePlanning(self, apartment_table, max_iterations=5):
        from shapely.geometry import Polygon, Point, LineString
        from shapely.ops import unary_union, linemerge
        import math
        import time

        best_plan = None
        best_score = float('inf')  # Чем меньше, тем лучше
        start_time = time.time()

        for iteration in range(max_iterations):
            # Здесь начинается одна итерация генерации планировки
            # Создаем сетку ячеек 1x1 метр, покрывающую полигон этажа
            minx, miny, maxx, maxy = self.polygon.bounds

            cell_size = 1  # Размер ячеек 1x1 метр

            # Вычисляем количество ячеек по оси X и Y
            num_cells_x = int(math.ceil((maxx - minx) / cell_size))
            num_cells_y = int(math.ceil((maxy - miny) / cell_size))

            # Создаем список ячеек, находящихся внутри полигона этажа
            cells = []
            cell_dict = {}
            for i in range(num_cells_x):
                for j in range(num_cells_y):
                    # Координаты ячейки
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
                    # Проверяем, пересекается ли ячейка с полигоном этажа
                    if self.polygon.intersects(cell_polygon):
                        intersection = self.polygon.intersection(cell_polygon)
                        if intersection.area > 0.5 * cell_polygon.area:  # Ячейка должна быть более чем на 50% внутри
                            cells.append({
                                'polygon': cell_polygon,
                                'assigned': False,  # Флаг, назначена ли ячейка квартире
                                'neighbors': [],
                                'id': (i, j),
                                'on_perimeter': False  # Флаг, граничит ли ячейка с внешней стеной
                            })
                            cell_dict[(i, j)] = cells[-1]

            # Предварительное вычисление соседей и определение ячеек на периметре
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

            # Случайно перемешиваем ячейки для равномерного распределения
            random.shuffle(cells)

            # Распределяем ячейки по квартирам
            apartments = []
            remaining_cells = [cell for cell in cells if not cell['assigned']]

            # Вычисляем количество ячеек для каждого типа квартиры
            cell_counts = {}
            for apt_type, apt_info in apartment_table.items():
                percent = apt_info['percent']
                allocated_area = self.polygon.area * (percent / 100)
                allocated_cell_count = int(allocated_area / (cell_size * cell_size))
                cell_counts[apt_type] = allocated_cell_count

            # Создаем копию cell_counts для отслеживания оставшихся ячеек для каждого типа
            remaining_cell_counts = cell_counts.copy()

            for apt_type, apt_info in apartment_table.items():
                area_range = apt_info['area_range']
                min_cells = max(1, int(area_range[0] / (cell_size * cell_size)))
                max_cells = int(area_range[1] / (cell_size * cell_size))
                allocated_cell_count = remaining_cell_counts[apt_type]

                while allocated_cell_count >= min_cells:
                    # Определяем размер квартиры в ячейках
                    apt_cell_count = random.randint(min_cells, min(max_cells, allocated_cell_count))

                    # Выбираем случайную ячейку на периметре, которая не назначена
                    available_perimeter_cells = [cell for cell in remaining_cells if not cell['assigned'] and cell['on_perimeter']]
                    if not available_perimeter_cells:
                        break

                    start_cell = random.choice(available_perimeter_cells)

                    # Используем алгоритм BFS для формирования квартиры
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

                    # Проверяем, граничит ли квартира с периметром
                    apartment_polygon = unary_union([cell['polygon'] for cell in apartment_cells])
                    if not apartment_polygon.exterior.intersects(exterior):
                        # Если квартира не граничит с периметром, снимаем назначение ячеек и пробуем снова
                        for cell in apartment_cells:
                            cell['assigned'] = False
                        continue

                    # Если удалось сформировать квартиру нужного размера
                    if len(apartment_cells) >= min_cells:
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

                    else:
                        # Если не удалось сформировать квартиру нужного размера, помечаем ячейки как не назначенные
                        for cell in apartment_cells:
                            cell['assigned'] = False
                        break  # Выходим, если больше нет возможности сформировать квартиру нужного размера

            # После распределения квартир в этой итерации вычисляем, насколько распределение близко к желаемому
            total_allocated_area = sum(apt['area'] for apt in apartments)
            actual_percentages = {}
            for apt_type in apartment_table.keys():
                total_type_area = sum(apt['area'] for apt in apartments if apt['type'] == apt_type)
                actual_percent = (total_type_area / total_allocated_area) * 100 if total_allocated_area > 0 else 0
                actual_percentages[apt_type] = actual_percent

            # Вычисляем суммарную ошибку распределения
            total_error = sum(abs(apartment_table[apt_type]['percent'] - actual_percentages.get(apt_type, 0)) for apt_type in apartment_table.keys())

            # Если текущий план лучше, сохраняем его
            if total_error < best_score:
                best_score = total_error
                best_plan = apartments
                print(f"Итерация {iteration + 1}: найден лучший план с ошибкой {best_score:.2f}%")

            # Если ошибка равна нулю, прерываем цикл
            if best_score == 0:
                break

        # Если не удалось найти планировку, соответствующую требованиям, возвращаем лучший найденный вариант
        self.apartments = best_plan  # Сохраняем лучшую сгенерированную планировку

        total_time = time.time() - start_time
        print(f"Генерация планировки завершена за {total_time:.2f} секунд.")

        return self.apartments
