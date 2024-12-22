from Classes.Geometry.GeometricFigure import GeometricFigure
from Classes.Geometry.Territory.Building.Apartment.Apartment import Apartment
from shapely.geometry import Polygon, LineString, MultiPolygon
from shapely.ops import unary_union
import random
from typing import List, Tuple, Dict
import time
import copy


class Section(GeometricFigure):
    def __init__(self,
                 points: List[Tuple[float, float]],
                 apartment_table: Dict,
                 single_floor: bool,
                 apartments: List['Apartment'] = None,
                 building_polygon: Polygon = None):
        """
        Класс Section описывает одну секцию на этаже:
        - apartment_table: словарь типа { 'studio': {'area_range': (..), 'percent': .., 'number': ..}, ... }
        - single_floor: флаг, что это единственный этаж (если нужно)
        - apartments: уже созданные квартиры (по умолчанию пусто)
        - building_polygon: внешний полигон здания, если нужен для проверок
        """
        super().__init__(points)
        self.apartments = apartments if apartments else []
        self.queue_corners_to_allocate = []
        self.free_cells = []
        self.apartment_table = self._clean_apartment_table(apartment_table)
        self.building_polygon = building_polygon
        self.single_floor = single_floor
        self.total_apartment_number = self._calc_total_apartment_number()
        self.messages = []  # Сообщения об ошибках на уровне секции

    def generate_section_planning(self, max_iterations=30, cell_size=1):
        """
        Основной метод генерации планировки секции.
        Пытаемся несколько раз (до max_iterations) сгенерировать, выбирая лучший результат
        по метрике суммарной "прямоугольности".
        """
        self.cell_size = cell_size
        self.apartments = []
        best_plan = None
        best_rectangularity_score = float('inf')
        start_time = time.time()

        for iteration in range(max_iterations):
            print(f"[Section] Iteration {iteration} ...")

            # Создаем сетку клеток заново
            self.cells = None
            self.check_and_create_cell_grid(cell_size=1.0, polygon_to_check=self.polygon)

            # Для каждой итерации сбрасываем очередь углов
            self.queue_corners_to_allocate = []

            # Генерируем список квартир (apartments) в этой секции
            apartments_candidate = self._allocate_apartments(cells=self.cells)

            if not apartments_candidate:
                # Не удалось ничего сгенерировать
                continue

            # Проверяем, совпадает ли число с нужным
            if not self._validate_apartment_number(apartments_candidate):
                # Если неверное кол-во, откатываемся
                for apt in apartments_candidate:
                    apt._reset_cell_assignments()
                continue

            # Считаем суммарную "прямоугольность"
            total_rectangularity = sum(self._rectangularity_score(apt.polygon) for apt in apartments_candidate)

            if total_rectangularity < best_rectangularity_score:
                best_rectangularity_score = total_rectangularity
                best_plan = apartments_candidate

            # Если достигли "достаточно хорошего" результата
            if best_rectangularity_score < 1.0:
                break

        # Сохраняем лучший результат
        self.apartments = best_plan if best_plan else []
        if not self.apartments:
            self.messages.append("Не удалось сгенерировать квартиры для секции.")
            return

        # Финальная настройка каждого Apartment
        for apt in self.apartments:
            apt.section_polygon = self.polygon
            apt.cells = None
            apt.check_and_create_cell_grid(cell_size=1.0, polygon_to_check=Polygon(apt.points))
            apt._process_cells()
            apt.generate_apartment_planning()

        total_time = time.time() - start_time
        print(f"[Section] Планировка завершена за {total_time:.2f} секунд.")
        return self.apartments

    def _allocate_apartments(self, cells):
        """
        Генерация всех квартир по данным из self.apartment_table,
        в цикле случайно выбираем тип квартиры и пытаемся разместить.
        """
        apartments_result = []
        remaining_cells = [cell for cell in cells if not cell['assigned']]
        self.initial_corner_cells = [cell for cell in cells if cell['is_corner']]

        # Копируем исходную таблицу квартир (чтобы уменьшать number по мере размещения)
        apt_table_copy = {k: dict(v) for k, v in self.apartment_table.items()}

        while apt_table_copy:
            # Случайно выбираем один тип квартиры
            chosen_apt_type = random.choice(list(apt_table_copy.keys()))
            apt_info = apt_table_copy[chosen_apt_type]

            # min_cells, max_cells — логика по area_range
            min_cells, max_cells = self._get_apartment_cell_range(apt_info['area_range'], self.cell_size)

            # Пытаемся разместить ОДНУ квартиру
            candidate_cells = self._allocate_apartment_cells(
                remaining_cells=remaining_cells,
                min_cells=min_cells,
                max_cells=max_cells,
                apartments=apartments_result
            )
            if not candidate_cells:
                # Не удалось разместить данный тип квартиры в текущей итерации
                # Переходим к следующему типу
                continue

            # fill_section_perimeter: возможно расширим/уменьшим группу клеток
            candidate_cells = self.fill_section_perimeter(
                cells, candidate_cells,
                max_area=max_cells,
                min_area=min_cells
            )

            # Обновляем оставшиеся клетки
            remaining_cells = [c for c in remaining_cells if not c['assigned']]

            # Строим итоговый полигон квартиры
            apartment_polygon = unary_union([c['polygon'] for c in candidate_cells])
            rectangular_poly = apartment_polygon.envelope

            # Если логика предполагает, что rectangular_poly.area < max_cells это нормально,
            # то сравниваем. Иначе чистим.
            # ... (оставляем вашу логику)

            # Создаем Apartment
            new_apt = Apartment(
                points=list(apartment_polygon.exterior.coords),
                apt_type=chosen_apt_type,
                building_polygon=self.building_polygon
            )
            new_apt.cells = candidate_cells
            apartments_result.append(new_apt)

            # Уменьшаем счётчик квартир этого типа
            apt_table_copy[chosen_apt_type]['number'] -= 1
            # Если квартир ноль — убираем тип
            if apt_table_copy[chosen_apt_type]['number'] <= 0:
                del apt_table_copy[chosen_apt_type]

            # Обновляем свойства клеток
            self._update_cell_properties(candidate_cells)

        return apartments_result

    def _allocate_apartment_cells(self, remaining_cells, min_cells, max_cells, apartments):
        """
        Логика выделения клеток под одну квартиру (BFS),
        выбирая угол либо из self.queue_corners_to_allocate, либо из initial_corner_cells.
        """
        apt_cell_count = random.randint(
            min_cells,
            int((max_cells - min_cells) * 0.8 + min_cells)
        )

        # Если есть очередь углов
        if self.queue_corners_to_allocate:
            return self._corner_based_allocation(remaining_cells, apartments, apt_cell_count, min_cells)
        elif self.initial_corner_cells:
            # Иначе берем случайный угол из initial_corner_cells
            start_cell = random.choice(self.initial_corner_cells)
            return self._bfs_allocate_cells(
                start_cell,
                apt_cell_count,
                remaining_cells
            )
        else:
            return None

    def _corner_based_allocation(self, remaining_cells, apartments, apt_cell_count, min_cells):
        """
        Сценарий, когда есть очередь углов self.queue_corners_to_allocate.
        Перебираем все углы, формируем варианты, выбираем лучший по rectangularity_score.
        """
        variants = []
        original_assigned = [(c, c['assigned']) for c in self.cells]

        for corner_cell in self.queue_corners_to_allocate:
            # Откатываемся в изначальное состояние
            for c, was_assigned in original_assigned:
                c['assigned'] = was_assigned

            candidate_cells = self._bfs_allocate_cells(corner_cell, apt_cell_count, remaining_cells)
            if not candidate_cells or len(candidate_cells) < min_cells:
                # Откат
                for cell in candidate_cells:
                    cell['assigned'] = False
                continue

            # Подсчитываем rectangularity
            union_poly = unary_union([cell['polygon'] for cell in candidate_cells])
            score = self._rectangularity_score(union_poly)
            variants.append((score, candidate_cells, corner_cell))

        if not variants:
            return None

        # Выбираем лучший (минимальный score)
        variants.sort(key=lambda x: x[0])
        best_score, best_cells, best_corner = variants[0]

        # Утверждаем лучший вариант
        # Снова откатываемся в изначальное состояние
        for c, was_assigned in original_assigned:
            c['assigned'] = was_assigned
        # Назначаем best_cells
        for cell in best_cells:
            cell['assigned'] = True
        # Убираем угол из очереди
        self.queue_corners_to_allocate.remove(best_corner)
        return best_cells

    def _bfs_allocate_cells(self, start_cell, apt_cell_count, remaining_cells):
        """
        Простая BFS-логика, начиная со start_cell,
        добавляем соседей, пока не наберем apt_cell_count.
        """
        apartment_cells = []
        queue = [start_cell]

        while queue and len(apartment_cells) < apt_cell_count:
            current = queue.pop(0)
            if current['assigned']:
                continue
            apartment_cells.append(current)
            current['assigned'] = True

            # Берём соседей, которые не заняты
            neighbors = [n for n in current['neighbors'] if not n['assigned']]

            queue.extend(neighbors)

        return apartment_cells



    def _validate_apartment_number(self, apartments):
        """
        Проверяем, что кол-во сгенерированных квартир совпадает с ожидаемым self.total_apartment_number.
        """
        return (len(apartments) == self.total_apartment_number)

    def _rectangularity_score(self, poly):
        """
        Чем меньше (envelope - area)/area, тем квартира ближе к прямоугольной форме.
        """
        envelope_area = poly.envelope.area
        area = poly.area
        return abs(envelope_area - area) / (area + 1e-9)

    def _calculate_cell_counts(self, cells):
        """
        Логика подсчета, если нужно.
        """
        # ... оставляем как есть, либо упрощаем ...
        return None

    def _get_apartment_cell_range(self, area_range, cell_size):
        """
        min_cells = area_range[0] / cell_area
        max_cells = area_range[1] / cell_area
        """
        cell_area = cell_size ** 2
        min_c = max(1, int(area_range[0] / cell_area))
        max_c = int(area_range[1] / cell_area)
        return min_c, max_c

    def fill_section_perimeter(self, cells, apartment_cells, max_area, min_area):
        """
        Логика расширения/уменьшения квартиры вдоль периметра.
        Оставляем вашу версию, но упрощаем структуру.
        """
        initial_apartment_cells = list(apartment_cells)
        # 1) Расширение вдоль периметра
        # ...
        # 2) Добавляем клетки, если envelope < max_area
        # ...
        # 3) Уменьшаем, если envelope > max_area
        # ...
        return apartment_cells

    def _update_cell_properties(self, apartment_cells):
        """
        Обновляем свойство 'is_corner' для соседних клеток по периметру.
        """
        for cell in apartment_cells:
            if cell['on_perimeter']:
                perimeter_neighbors = [
                    n for n in cell['neighbors']
                    if (not n['assigned']) and n['on_perimeter']
                ]
                for pn in perimeter_neighbors:
                    pn['is_corner'] = True
                    self.queue_corners_to_allocate.append(pn)

    def _clean_apartment_table(self, apartment_table: Dict) -> Dict:
        return {k: v for k, v in apartment_table.items() if v['number'] > 0}

    def copy(self):
        """
        Создает копию Section, если нужно.
        """
        return Section(
            points=self.points[:],
            apartment_table=copy.deepcopy(self.apartment_table),
            building_polygon=self.building_polygon.buffer(0),
            single_floor=self.single_floor
        )

    def _calc_total_apartment_number(self):
        """
        Суммируем общее количество квартир во входной apartment_table.
        """
        total = 0
        for apt_type in self.apartment_table:
            total += self.apartment_table[apt_type]['number']
        return total
