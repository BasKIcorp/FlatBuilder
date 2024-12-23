from Classes.Geometry.GeometricFigure import GeometricFigure
from Classes.Geometry.Territory.Building.Apartment.Apartment import Apartment
from Classes.Geometry.Territory.RLAgent import RLAgent
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
        self.agent = RLAgent()

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
            if best_rectangularity_score < 1.5:
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
        apartments = []
        remaining_cells = [cell for cell in cells if not cell['assigned']]
        self.initial_corner_cells = [cell for cell in cells if cell['is_corner']]

        # Копируем таблицу
        apartment_table_copy = {apt_type: dict(info) for apt_type, info in self.apartment_table.items()}

        # Пока есть квартиры
        while apartment_table_copy:
            # 1) формируем state
            #    Пусть это кортеж чисел (sorted по имени типа, или другой вариант)
            #    Например: state = ( number_1, number_2, ... )
            #    *Важно, чтобы порядок типов был фиксированный.*
            sorted_types = sorted(apartment_table_copy.keys())
            state_tuple = tuple(apartment_table_copy[t]['number'] for t in sorted_types)

            # 2) possible_actions = список apt_types
            possible_actions = list(apartment_table_copy.keys())

            # 3) вызываем агент
            chosen_apt_type = self.agent.act(state_tuple, possible_actions)

            # 4) берем данные
            apt_info = apartment_table_copy[chosen_apt_type]
            min_cells, max_cells = self._get_apartment_cell_range(apt_info['area_range'], cell_size=self.cell_size)

            # Пытаемся разместить квартиру
            candidate_cells = self._allocate_apartment_cells(remaining_cells, min_cells, max_cells, apartments)

            if candidate_cells:
                # Успешно разместили
                # fill_section_perimeter и т.д.
                candidate_cells = self.fill_section_perimeter(cells, candidate_cells, max_cells, min_cells)
                remaining_cells = [c for c in remaining_cells if not c['assigned']]

                # Собираем apartment_polygon
                apartment_polygon = unary_union([c['polygon'] for c in candidate_cells])
                rectangular_apartment_polygon = apartment_polygon.envelope
                if (rectangular_apartment_polygon.area < max_cells and
                        rectangular_apartment_polygon.area != apartment_polygon.area):
                    for cell in remaining_cells:
                        if not cell['assigned'] and rectangular_apartment_polygon.contains(cell['polygon']):
                            candidate_cells.append(cell)
                            cell['assigned'] = True
                    remaining_cells = [cell for cell in remaining_cells if not cell['assigned']]
                    rectangular_apartment_polygon = unary_union([cell['polygon'] for cell in candidate_cells])
                    if isinstance(rectangular_apartment_polygon, Polygon):  # Если это Polygon
                        points = list(rectangular_apartment_polygon.exterior.coords)
                    elif isinstance(rectangular_apartment_polygon, MultiPolygon):  # Если это MultiPolygon
                        for cell in candidate_cells:
                            cell['assigned'] = False
                        remaining_cells = [cell for cell in remaining_cells if not cell['assigned']]
                        continue
                # Проверяем тип полигона
                else:
                    for i in range(10):
                        # Проверяем можно ли уменьшить квартиру, убрав последние клетки
                        if len(candidate_cells) <= min_cells:
                            break
                        new_apartment_cells = candidate_cells[:(-1 - i)]
                        if len(new_apartment_cells) < min_cells:
                            break
                        new_apartment_polygon = unary_union([cell['polygon'] for cell in new_apartment_cells])
                        if new_apartment_polygon.envelope.area < apartment_polygon.envelope.area:
                            apartment_polygon = new_apartment_polygon.buffer(0)
                            for cell in candidate_cells[(-1 - i):]:
                                cell['assigned'] = False
                            candidate_cells = new_apartment_cells
                            break

                    if isinstance(apartment_polygon, Polygon):  # Если это Polygon
                        points = list(apartment_polygon.exterior.coords)
                    elif isinstance(apartment_polygon, MultiPolygon):  # Если это MultiPolygon
                        for cell in candidate_cells:
                            cell['assigned'] = False
                        remaining_cells = [cell for cell in remaining_cells if not cell['assigned']]
                        continue

                new_apt = Apartment(
                    points=points,
                    apt_type=chosen_apt_type,
                    building_polygon=self.building_polygon
                )
                new_apt.cells = candidate_cells
                free_cells_num = self._calc_free_cells(apartments, Polygon(points))
                w = 1
                reward = w * free_cells_num
                apartments.append(new_apt)

                # Уменьшаем количество
                apartment_table_copy[chosen_apt_type]['number'] -= 1
                if apartment_table_copy[chosen_apt_type]['number'] <= 0:
                    del apartment_table_copy[chosen_apt_type]

                self._update_cell_properties(candidate_cells)

                # 5) Делаем шаг обучения:
                #    reward = 0 (промежуточный),
                #    new_state - новое распределение
                new_sorted_types = sorted(apartment_table_copy.keys())
                new_state_tuple = tuple(apartment_table_copy[t]['number'] for t in new_sorted_types)
                self.agent.store_transition(
                    reward=reward,
                    new_state=new_state_tuple,
                    done=False
                )
            else:
                # Не удалось разместить выбранный тип квартиры
                # Можно дать небольшой отрицательный reward
                # и продолжить (или break)
                new_sorted_types = sorted(apartment_table_copy.keys())
                new_state_tuple = tuple(apartment_table_copy[t]['number'] for t in new_sorted_types)
                self.agent.store_transition(
                    reward=-1.0,  # карательный штраф
                    new_state=new_state_tuple,
                    done=False
                )
                # Переходим к следующему шагу while
                # (агент снова выберет apt_type и т.д.)
                continue

        # Когда вышли из while -> все квартиры размещены
        # Можно вызвать self.agent.on_episode_end(final_reward),
        # где final_reward ~ -прямоугольность_или_ошибка
        final_reward = -1.0 * sum(self._rectangularity_score(apt.polygon) for apt in apartments)
        self.agent.on_episode_end(final_reward)

        return apartments

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
        1) Расширяет apartment_cells вдоль периметра, если осталось меньше 5 свободных клеток.
        2) Добавляет клетки в apartment_cells, если площадь их envelope < max_area.
        3) Если envelope > max_area, пытается уменьшить квартиру, удаляя клетки.

        Args:
            cells (list): все клетки секции.
            apartment_cells (list): текущие клетки, принадлежащие квартире.
            max_area (float): верхний порог (число клеток или площадь).
            min_area (float): нижний порог (число клеток или площадь).
        """
        # ШАГ 0: Сохраняем копию начального состояния
        initial_apartment_cells = apartment_cells.copy()

        # -- Расширение вдоль периметра ---
        self._expand_along_perimeter(cells, apartment_cells)

        # -- Добавляем клетки внутри envelope, если есть свободные
        self._add_cells_inside_envelope(apartment_cells)

        # -- Пытаемся уменьшить квартиру, если envelope слишком велик
        apartment_cells = self._shrink_if_needed(apartment_cells, max_area, min_area, initial_apartment_cells)

        return apartment_cells

    def _expand_along_perimeter(self, all_cells, apartment_cells):
        """
        Расширяем apartment_cells вдоль периметра секции, если осталось меньше 5 свободных клеток.
        Ищем стороны секции, пересекающиеся с apartment_cells, и добавляем смежные свободные клетки.
        """
        section_sides = [
            LineString([self.polygon.exterior.coords[i], self.polygon.exterior.coords[i + 1]])
            for i in range(len(self.polygon.exterior.coords) - 1)
        ]
        unassigned = [c for c in all_cells if not c['assigned']]
        union_poly = unary_union([c['polygon'] for c in apartment_cells])

        # Находим стороны, которые пересекают текущий union квартиры
        intersecting_sides = [side for side in section_sides if union_poly.intersects(side)]

        # Для каждой такой стороны ищем свободные клетки
        for side in intersecting_sides:
            adjacent_unassigned = [c for c in unassigned if c['polygon'].intersects(side)]
            # Если свободных клеток < 5, считаем, что нужно добавить их
            if len(adjacent_unassigned) < 5:
                for cell in adjacent_unassigned:
                    cell['assigned'] = True
                    apartment_cells.append(cell)

    def _add_cells_inside_envelope(self, apartment_cells):
        """
        Добавляем в apartment_cells те свободные клетки, которые полностью внутри
        envelope текущего набора.
        """
        union_poly = unary_union([c['polygon'] for c in apartment_cells])
        envelope_poly = union_poly.envelope

        # Добавляем все незанятые клетки из self.cells, которые
        # лежат внутри envelope
        for cell in [c for c in self.cells if not c['assigned']]:
            if envelope_poly.contains(cell['polygon']):
                cell['assigned'] = True
                apartment_cells.append(cell)

    def _shrink_if_needed(self, apartment_cells, max_area, min_area, initial_cells):
        """
        Если envelope слишком большой (area > max_area) или маленький (area < min_area),
        пытаемся убрать 'ряды' клеток вдоль стороны envelope, чтобы уменьшить площадь.
        Если не удается привести к нужному диапазону, откатываемся к initial_cells.
        """
        union_poly = unary_union([cell['polygon'] for cell in apartment_cells])
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
            removable_side = None
            for side in envelope_sides:
                if (not side.touches(self.polygon.exterior)
                        and not any(side.intersects(apt.polygon) for apt in self.apartments)):
                    removable_side = side
                    break

            if removable_side is None:
                break  # не нашли сторону для удаления

            # Удаляем клетки, centroid которых очень близко к side
            to_remove = [c for c in apartment_cells if removable_side.distance(c['polygon'].centroid) < 1e-6]
            for c in to_remove:
                c['assigned'] = False
                apartment_cells.remove(c)

            # Пересчитываем envelope
            union_poly = unary_union([cell['polygon'] for cell in apartment_cells])
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

    def _calc_free_cells(self, apartments, apartment_polygon):
        """
        Возвращает (difference_of_sides, free_cells),
        где:
          difference_of_sides - разница между длиной стороны здания, к которой
                                прилегала corner_cell, и соответствующей стороной
                                новой квартиры
          free_cells          - кол-во оставшихся свободных клеток в секции
        """
        if not apartments:
            return 1
        intersecting_apartments = []
        for apartment in apartments:
            if apartment_polygon.exterior.intersects(apartment.polygon.exterior):
                intersecting_apartments.append(apartment)
        free_cell_count = 0
        for apartment in intersecting_apartments:
            for cell in self.cells:
                if cell['polygon'].exterior.intersects(apartment.polygon.exterior) and not cell['assigned']:
                    free_cell_count += 1
        return free_cell_count