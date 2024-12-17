from Classes.Geometry.GeometricFigure import GeometricFigure
from Classes.Geometry.Territory.Building.Floor.Section import Section
from Classes.Geometry.Territory.Building.Elevator import Elevator
from Classes.Geometry.Territory.Building.Stair import Stair
from shapely.geometry import Polygon
from shapely.ops import unary_union
from typing import List, Tuple, Dict
import random
from math import floor

class Floor(GeometricFigure):
    def __init__(self, points: List[Tuple[float, float]], sections: List[List[Tuple[float, float]]],
                 apartment_table: Dict,
                 building_polygon: Polygon = None):
        super().__init__(points)  # Передаем points в конструктор родительского класса
        self.apartment_table = apartment_table  # Таблица квартир, переданная в класс

        # Создание секций
        self.sections_points = sections
        self.sections = []
        self.building_polygon = building_polygon

    def generate_floor_planning(self, cell_size=1):
        """
        Генерирует планировку этажа, распределяя квартиры по секциям.
        """
        self.cells = None
        self.check_and_create_cell_grid(cell_size=cell_size)
        print(len(self.sections_points))
        if len(self.sections_points) == 1:
            # Если секция одна, таблица остаётся неизменной
            section = Section(points=self.sections_points[0],
                              apartment_table=self.apartment_table,
                              building_polygon=self.building_polygon)
            section.check_and_create_cell_grid(cell_size=1)
            section.generate_section_planning(max_iterations=20)
            self.sections.append(section)
        else:
            # Распределение квартир по секциям
            section_tables = self._distribute_apartment_table_among_sections()
            for i, (points, section_table) in enumerate(zip(self.sections_points, section_tables)):
                print(f" Секция {section_table}")
                section = Section(points=points,
                                  apartment_table=section_table,
                                  building_polygon=self.building_polygon)
                section.check_and_create_cell_grid(cell_size=1)
                section.generate_section_planning(max_iterations=20)
                self.sections.append(section)

    def _distribute_apartment_table_among_sections(self):
        """
        Распределяет квартиры по секциям на основе их площадей.
        Если пропорциональное распределение дает 0, квартиры распределяются по секциям по очереди.
        """
        # Проверка на пустые секции
        if not self.sections_points:
            print("Ошибка: Список секций пуст. Невозможно распределить квартиры.")
            return None

        total_area = sum(Polygon(points).area for points in self.sections_points)
        section_areas = [Polygon(points).area for points in self.sections_points]

        # Инициализация таблиц для каждой секции
        section_tables = [{} for _ in self.sections_points]

        # Шаг 1: Первичное распределение по площадям с округлением вниз
        remaining_numbers = {apt_type: apt_info['number'] for apt_type, apt_info in self.apartment_table.items()}

        for apt_type, apt_info in self.apartment_table.items():
            total_number = apt_info['number']
            distributed_numbers = [0] * len(self.sections_points)  # Изначально все по 0

            if total_number > 0:
                for idx, area in enumerate(section_areas):
                    proportioned_number = floor(total_number * (area / total_area))
                    distributed_numbers[idx] = proportioned_number

                # Суммируем распределенные квартиры и вычисляем остаток
                total_assigned = sum(distributed_numbers)
                remaining = total_number - total_assigned

                # Шаг 2: Если остались квартиры, распределяем их по секциям по очереди
                while remaining > 0:
                    for idx in range(len(self.sections_points)):
                        if remaining == 0:
                            break
                        distributed_numbers[idx] += 1
                        remaining -= 1

                # Шаг 3: Сохраняем распределенные квартиры в таблицы секций
                for idx, number in enumerate(distributed_numbers):
                    section_tables[idx][apt_type] = {
                        'area_range': apt_info['area_range'],
                        'percent': apt_info['percent'],
                        'number': number
                    }

        return section_tables
