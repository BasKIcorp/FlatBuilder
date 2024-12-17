from Classes.Geometry.GeometricFigure import GeometricFigure
from Classes.Geometry.Territory.Building.Floor.Floor import Floor
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
        self.sections = [section for section in sections if Polygon(points).contains(Polygon(section) or
                                                                                     Polygon(points).equals(Polygon(section)))]
        self.apartment_table = self._clean_apartment_table(apartment_table)
        self.message = None  # Для сообщений об ошибках

    def generate_floors(self):
        """Генерирует этажи, добавляя их в список floors."""
        print(f"Количество этажей {self.num_floors}")
        if self.num_floors == 1:
            floor = Floor(points=self.points,
                          sections_list=self.sections,
                          apartment_table=self.apartment_table,
                          building_polygon=self.polygon)
            floor.generate_floor_planning()
            self.floors.append(floor)
        else:
            # Распределяем таблицу квартир между этажами
            floor_tables = self._distribute_apartment_table_among_floors()

            if not floor_tables:  # Если floor_tables вернул None из-за ошибки
                return  # Прерываем генерацию этажей

            # Генерация этажей при успешном распределении
            first_floor = Floor(points=self.points,
                                sections_list=self.sections,
                                apartment_table=floor_tables[0],
                                building_polygon=self.polygon)
            first_floor.generate_floor_planning()
            self.floors.append(first_floor)

            # Второй этаж как эталон
            second_floor = Floor(points=self.points,
                                 sections_list=self.sections,
                                 apartment_table=floor_tables[1],
                                 building_polygon=self.polygon)
            second_floor.generate_floor_planning()

            # Добавляем второй и все последующие этажи
            for _ in range(1, self.num_floors):
                self.floors.append(second_floor)

    def _distribute_apartment_table_among_floors(self):
        num_floors = self.num_floors
        if num_floors == 1:
            return [self.apartment_table]

        floor_tables = [{} for _ in range(num_floors)]
        for apt_type, apt_info in self.apartment_table.items():
            total_number = apt_info['number']
            base_number = floor(total_number / (num_floors - 1))

            # Если base_number = 0, но total_number > 0, генерируем сообщение
            if base_number == 0 and total_number > 0:
                self.message = f"Ошибка: невозможно распределить {apt_type} (всего {total_number}) на {num_floors} этажей."
                return None  # Прерываем выполнение

            remaining = total_number
            for i in range(1, num_floors):  # Со 2-го этажа
                assigned_number = min(base_number, remaining)
                if assigned_number > 0:
                    floor_tables[i][apt_type] = {
                        'area_range': apt_info['area_range'],
                        'percent': apt_info['percent'],
                        'number': assigned_number
                    }
                    remaining -= assigned_number

            # Оставшиеся квартиры на первый этаж
            floor_tables[0][apt_type] = {
                'area_range': apt_info['area_range'],
                'percent': apt_info['percent'],
                'number': remaining
            }
        return floor_tables

    def _clean_apartment_table(self, apartment_table: Dict) -> Dict:
        """
        Удаляет из apartment_table типы квартир, у которых number = 0.
        """
        return {apt_type: data for apt_type, data in apartment_table.items() if data['number'] > 0}

