from copy import deepcopy

from Classes.Geometry.GeometricFigure import GeometricFigure
from Classes.Geometry.Territory.Building.Floor.Floor import Floor
from Classes.Geometry.Territory.Building.Floor.Section import Section
from Classes.Geometry.Territory.Building.Elevator import Elevator
from Classes.Geometry.Territory.Building.Stair import Stair
from typing import List, Tuple, Dict
import copy
from shapely import Polygon
from math import floor
import random


class Building(GeometricFigure):
    def __init__(self, points: List[Tuple[float, float]],
                 sections: List[List[Tuple[float, float]]],
                 num_floors: int,
                 apartment_table: Dict):
        super().__init__(points)
        self.floors = []  # Список этажей в здании
        self.num_floors = num_floors  # Количество этажей
        self.sections = sections
        self.apartment_table = self._clean_apartment_table(apartment_table)
        self.message = []  # Для сообщений об ошибках

        # Создаем глубокую копию apartment_table для работы
        self.apartment_table_copy = deepcopy(self.apartment_table)

    def _clean_apartment_table(self, apartment_table: Dict) -> Dict:
        """
        Удаляет из apartment_table типы квартир, у которых number = 0.

        Args:
            apartment_table (dict): Исходная таблица с типами квартир.

        Returns:
            dict: Очищенная таблица.
        """
        return {apt_type: data for apt_type, data in apartment_table.items() if data['number'] > 0}

    def generate_floors(self):
        """Генерирует этажи, добавляя их в список floors."""
        if self.num_floors == 1:
            self._generate_single_floor()
            return
        # Шаг 1: Создаем floor_tables и выполняем первичную и вторичную обработку
        floor_tables = self._initialize_empty_floor_tables()
        floor_tables = self.primary_processing(floor_tables)  # Работаем с копией таблицы
        if self.num_floors >= 2:
            self.secondary_processing(floor_tables=floor_tables)  # Работаем с floor_tables

        # Шаг 2: Создаем уникальные паттерны этажей
        floor_patterns = self.create_unique_floor_pattern(floor_tables)
        # Шаг 3: Генерируем этажи
        self._generate_upper_floors(floor_patterns)
        self._generate_first_floor(floor_patterns[0])  # Используем первый кортеж

    def _generate_single_floor(self):
        """Генерация единственного этажа."""
        floor = Floor(points=self.points,
                      sections_list=self.sections,
                      apartment_table=self.apartment_table,
                      building_polygon=self.polygon,
                      single_floor=True)
        floor.generate_floor_planning()
        self.floors.append(floor)

    def _generate_upper_floors(self, floor_patterns: List[Tuple[Dict, int]]):
        """Генерирует верхние этажи на основе паттернов."""
        previous_floor = None

        # Берем второй этаж из первого паттерна
        second_floor_pattern_dict = floor_patterns[1][0]

        for pattern_dict, repeat_count in floor_patterns[1:]:
            if previous_floor is None:
                # Создаем второй этаж на основе первого паттерна
                floor = self._create_new_floor(second_floor_pattern_dict)
            else:
                # Копируем предыдущий этаж и модифицируем его
                floor = self.copy_floor(previous_floor, pattern_dict)

                # Модифицируем секции для удаления квартир
                self._modify_existing_floor_sections(floor, pattern_dict, second_floor_pattern_dict)

            # Добавляем текущий этаж в список floors
            for _ in range(repeat_count):
                self.floors.append(floor)

            # Обновляем previous_floor
            previous_floor = floor

    def _generate_first_floor(self, first_pattern: Tuple[Dict, int]):
        """
        Генерация первого этажа на основе первого паттерна,
        но при этом обнуляем число квартир (number=0),
        чтобы этаж был полностью пустым.
        """
        base_pattern, _ = first_pattern  # первый словарь и количество повторений

        # Создаём "пустой" паттерн с number=0
        empty_pattern = {}
        for apt_type, apt_info in self.apartment_table.items():
            new_info = dict(apt_info)
            new_info["number"] = 0
            empty_pattern[apt_type] = new_info

        # Создаём этаж, передав пустой паттерн
        first_floor = Floor(points=self.points,
                            sections_list=self.sections,
                            apartment_table=empty_pattern,
                            building_polygon=self.polygon)
        first_floor.generate_floor_planning()
        # Ставим этот этаж первым
        self.floors.insert(0, first_floor)

    def _modify_existing_floor_sections(self, floor: Floor, current_pattern: Dict, base_pattern: Dict):
        """
        Модифицирует секции этажа, уменьшая количество квартир заданного типа.

        Args:
            floor (Floor): Этаж, в котором будут изменены секции.
            current_pattern (Dict): Новый паттерн для модификации этажа.
            base_pattern (Dict): Базовый паттерн для сравнения.
        """
        for apt_type, apt_info in base_pattern.items():
            base_number = apt_info['number']
            current_number = current_pattern[apt_type]['number']
            difference = base_number - current_number

            if difference > 0:
                self._remove_apartments_from_floor(floor, apt_type, difference)

    def _remove_apartments_from_floor(self, floor: Floor, apt_type: str, count: int):
        """
        Удаляет заданное количество квартир определенного типа из секций этажа.

        Args:
            floor (Floor): Этаж, в котором будут удаляться квартиры.
            apt_type (str): Тип квартир для удаления.
            count (int): Количество квартир для удаления.
        """
        for section in floor.sections:
            # Находим секцию с максимальным количеством квартир заданного типа
            max_section = max(
                floor.sections,
                key=lambda s: sum(1 for apt in s.apartments if apt.type == apt_type),
                default=None
            )
            if not max_section:
                continue

            # Удаляем квартиры с конца списка
            removed_count = 0
            for apartment in reversed(max_section.apartments):
                if apartment.type == apt_type:
                    max_section.apartments.remove(apartment)
                    removed_count += 1
                    if removed_count >= count:
                        break

            # Если удалили достаточно квартир, выходим
            count -= removed_count
            if count <= 0:
                break

    def _initialize_empty_floor_tables(self):
        """
        Создает список floor_tables с нулевыми значениями количества квартир для каждого этажа.

        Returns:
            list: Список словарей для каждого этажа, аналогичный self.apartment_table.
        """
        clean_table = self._clean_apartment_table(self.apartment_table_copy)
        return [
            {apt_type: {'area_range': apt_info['area_range'], 'percent': apt_info['percent'], 'number': 0}
             for apt_type, apt_info in clean_table.items()}
            for _ in range(self.num_floors)
        ]

    def primary_processing(self, floor_tables: List[Dict]):
        """
        Выполняет первичное распределение квартир по этажам.
        """
        total_area = Polygon(self.points).area

        for apt_type, apt_info in self.apartment_table_copy.items():  # Используем копию
            total_number = apt_info['number']
            min_area, max_area = apt_info['area_range']
            mean_area = (min_area + max_area) / 2
            if self.num_floors >= 2:
                base_number = total_number // (self.num_floors - 1)
            else:
                base_number = total_number // self.num_floors
            remaining_number = total_number

            for floor_index in range(1, self.num_floors):
                floor_tables[floor_index][apt_type]['number'] += base_number
                remaining_number -= base_number

            self.apartment_table_copy[apt_type]['number'] = remaining_number  # Обновляем только копию

        return floor_tables

    def secondary_processing(self, floor_tables: List[Dict]):
        """
        Выполняет вторичное распределение квартир по этажам.
        """
        while any(apt_info['number'] > 0 for apt_info in self.apartment_table_copy.values()):  # Используем копию
            max_remaining = max(
                (apt_info['number'], apt_type)
                for apt_type, apt_info in self.apartment_table_copy.items()  # Используем копию
                if apt_info['number'] > 0
            )
            max_number, max_apt_type = max_remaining

            if max_number == 0:
                break

            for n in range(1, self.num_floors):
                divided_number = max_number // (self.num_floors - n)
                if divided_number > 0:
                    break

            num_floors_to_allocate = self.num_floors - n

            for floor_index in range(1, num_floors_to_allocate + 1):
                floor_tables[floor_index][max_apt_type]['number'] += divided_number

            self.apartment_table_copy[max_apt_type][
                'number'] -= divided_number * num_floors_to_allocate  # Изменяем только копию

    def create_unique_floor_pattern(self, floor_tables: List[Dict]) -> List[Tuple[Dict, int]]:
        """
        Создает список уникальных паттернов этажей с их количеством повторений.
        Первый кортеж всегда соответствует первому этажу.
        """
        unique_patterns = []
        seen_patterns = {}

        # Добавляем первый этаж в список
        first_floor_pattern = floor_tables[0]
        unique_patterns.append((first_floor_pattern, 1))

        # Обрабатываем остальные этажи
        for floor_table in floor_tables[1:]:
            pattern_tuple = tuple((apt_type, tuple(apt_info.items())) for apt_type, apt_info in floor_table.items())

            if pattern_tuple in seen_patterns:
                seen_patterns[pattern_tuple] += 1
            else:
                seen_patterns[pattern_tuple] = 1

        # Добавляем остальные уникальные паттерны
        for pattern_tuple, count in seen_patterns.items():
            pattern_dict = {apt_type: dict(apt_info) for apt_type, apt_info in pattern_tuple}
            unique_patterns.append((pattern_dict, count))

        # Сортируем по убыванию суммы 'number', кроме первого элемента
        unique_patterns[1:] = sorted(
            unique_patterns[1:],
            key=lambda x: sum(info["number"] for info in x[0].values()),
            reverse=True
        )

        return unique_patterns

    def _create_new_floor(self, floor_pattern: Dict) -> Floor:
        """
        Создает новый этаж на основе заданного паттерна.

        Args:
            floor_pattern (Dict): Паттерн для нового этажа.

        Returns:
            Floor: Новый этаж, созданный на основе указанного паттерна.
        """
        floor = Floor(
            points=self.points,
            sections_list=self.sections,
            apartment_table=floor_pattern,
            building_polygon=self.polygon
        )
        floor.generate_floor_planning()
        return floor

    def copy_floor(self, floor: Floor, apartment_table: Dict) -> Floor:
        """
        Копирует этаж, создавая новый с обновленной таблицей квартир.

        Args:
            floor (Floor): Исходный этаж для копирования.
            apartment_table (Dict): Таблица квартир для нового этажа.

        Returns:
            Floor: Новый этаж с копированными данными.
        """

        # Создаем новый объект этажа с секциями и новой таблицей квартир
        new_floor = Floor(
            points=self.points,
            sections_list=self.sections,
            apartment_table=apartment_table,
            building_polygon=self.polygon  # Копия полигона здания
        )
        new_floor.generate_floor_planning(is_copy=True)
        for i, section in enumerate(new_floor.sections):
            new_floor.sections[i].apartments = deepcopy(floor.sections[i].apartments)

        return new_floor

    def validate_initial_planning(self):
        """
        Проверяет, возможно ли планирование по изначальной таблице квартир apartment_table.
        Если площадь средняя между минимальной и потенциальной площадью меньше 0.7 * allocatable_area,
        отправляет сообщение с требованием уменьшить количество квартир или площадь.
        """
        # Шаг 1: Расчет минимальной и максимальной потенциальной площади
        min_potential_area = sum(apt_info['area_range'][0] * apt_info['number']
                                 for apt_info in self.apartment_table.values())
        max_potential_area = sum(apt_info['area_range'][1] * apt_info['number']
                                 for apt_info in self.apartment_table.values())
        avg_potential_area = (min_potential_area + max_potential_area) / 2
        if self.num_floors == 1:
            threshold_area = avg_potential_area
            if not threshold_area < self.polygon.area * 0.65:
                min_area_to_reduce = threshold_area - self.polygon.area * 0.65
                self.message.append(min_area_to_reduce)
                return False  # Планирование невозможно
        else:
            tables_for_floor = self._initialize_empty_floor_tables()
            tables_for_floor = self.primary_processing(tables_for_floor)  # Работаем с копией таблицы
            self.secondary_processing(floor_tables=tables_for_floor)  # Работаем с floor_tables
            min_potential_area = sum(apt_info['area_range'][0] * apt_info['number']
                                     for apt_info in tables_for_floor[1].values())
            max_potential_area = sum(apt_info['area_range'][1] * apt_info['number']
                                     for apt_info in tables_for_floor[1].values())
            avg_potential_area = (min_potential_area + max_potential_area) / 2
            if not avg_potential_area < self.polygon.area * 0.65:
                # Шаг 5: Расчет минимальной площади для уменьшения
                min_area_to_reduce = avg_potential_area - self.polygon.area * 0.65
                # Формирование сообщения
                self.message.append(min_area_to_reduce)
                return False  # Планирование невозможно
        return True

