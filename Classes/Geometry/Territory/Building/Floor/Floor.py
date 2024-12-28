from Classes.Geometry.GeometricFigure import GeometricFigure
from Classes.Geometry.Territory.Building.Floor.Section import Section
from shapely.geometry import Polygon
from typing import List, Tuple, Dict
import random
from math import floor

class Floor(GeometricFigure):
    def __init__(self, points: List[Tuple[float, float]],
                 sections_list: List[List[Tuple[float, float]]],
                 apartment_table: Dict,
                 building_polygon: Polygon = None,
                 single_floor: bool = False,
                 to_adjust: bool = False):
        super().__init__(points)  # Передаем points в конструктор родительского класса
        self.apartment_table = self._clean_apartment_table(apartment_table)  # Таблица квартир, переданная в класс

        # Создание секций
        self.sections_list = sections_list
        self.sections = []
        self.building_polygon = building_polygon
        self.single_floor = single_floor
        self.to_adjust = to_adjust

    def generate_floor_planning(self, cell_size=1, is_copy=False):
        """
        Генерирует планировку этажа, распределяя квартиры по секциям.
        """
        print(self.apartment_table)
        self.cells = None
        self.check_and_create_cell_grid(cell_size=cell_size)
        if len(self.sections_list) == 1:
            # Если секция одна, таблица остаётся неизменной
            section = Section(points=self.sections_list[0],
                              apartment_table=self.apartment_table,
                              building_polygon=self.building_polygon,
                              to_adjust=self.to_adjust)
            self.sections.append(section)
            if not is_copy:
                section.cells = None
                section.check_and_create_cell_grid(cell_size=1, polygon_to_check=section.polygon)
                section.generate_section_planning(max_iterations=50)
        else:
            # Распределение квартир по секциям
            section_tables = self._distribute_apartment_table_among_sections()
            for i, (points, section_table) in enumerate(zip(self.sections_list, section_tables)):
                section = Section(points=points,
                                  apartment_table=section_table,
                                  building_polygon=self.building_polygon,
                                  to_adjust=self.to_adjust)
                self.sections.append(section)
                if not is_copy:
                    section.cells = None
                    section.check_and_create_cell_grid(cell_size=1, polygon_to_check=section.polygon)
                    section.generate_section_planning(max_iterations=20)

    def _distribute_apartment_table_among_sections(self):
        """
        Распределяет квартиры по секциям на основе их площадей.
        Остаток квартир передается последней секции.
        """
        # Проверка на пустые секции
        if not self.sections_list:
            print("Ошибка: Список секций пуст. Невозможно распределить квартиры.")
            return None
        total_area = sum(Polygon(points).area for points in self.sections_list)
        section_areas = [Polygon(points).area for points in self.sections_list]

        # Инициализация таблиц для каждой секции
        section_tables = [{} for _ in self.sections_list]

        for apt_type, apt_info in self.apartment_table.items():
            total_number = apt_info['number']
            distributed_numbers = [0] * len(self.sections_list)  # Изначально все 0
            remaining = total_number  # Остаток квартир

            # Шаг 1: Первичное распределение с floor
            for idx in range(len(self.sections_list) - 1):  # Все, кроме последней секции
                proportioned_number = floor(total_number * (section_areas[idx] / total_area))
                distributed_numbers[idx] = proportioned_number
                remaining -= proportioned_number  # Вычитаем распределенное количество

            # Шаг 2: Остаток передаем последней секции
            distributed_numbers[-1] = remaining

            # Шаг 3: Заполняем таблицы секций
            for idx, number in enumerate(distributed_numbers):
                section_tables[idx][apt_type] = {
                    'area_range': apt_info['area_range'],
                    'percent': apt_info['percent'],
                    'number': number
                }

        return section_tables

    def _clean_apartment_table(self, apartment_table: Dict) -> Dict:
        """
        Удаляет из apartment_table типы квартир, у которых number = 0.
        """
        return {apt_type: data for apt_type, data in apartment_table.items() if data['number'] > 0}