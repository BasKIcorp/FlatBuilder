from Classes.Geometry.GeometricFigure import GeometricFigure
from Classes.Geometry.Territory.Building.Floor.Floor import Floor
from Classes.Geometry.Territory.Building.Elevator import Elevator
from Classes.Geometry.Territory.Building.Stair import Stair
from typing import List, Tuple, Dict
import copy
from shapely import Polygon



class Building(GeometricFigure):
    def __init__(self, points: List[Tuple[float, float]],
                 sections: List[List[Tuple[float, float]]],
                 num_floors: int,
                 apartment_table: Dict):
        super().__init__(points)
        self.floors = []  # Список этажей в здании
        self.num_floors = num_floors  # Количество этажей
        self.sections = [section for section in sections if Polygon(points).contains(Polygon(section).exterior or
                                                                                     Polygon(points).equals(Polygon(section)))]
        self.apartment_table = apartment_table  # Таблица квартир, переданная в класс
        # Создаем лифты и лестницы

    def generate_floors(self):
        """Генерирует этажи, добавляя их в список floors."""
        total_assigned_numbers = {apt_type: 0 for apt_type in
                                  self.apartment_table.keys()}  # Инициализация счетчиков для квартир
        if self.num_floors == 1:
            self.sections = [self.points]
            floor = Floor(points=self.points, sections=self.sections,
                          apartment_table=self.apartment_table,
                          building_polygon=Polygon(self.points))
            floor.generate_floor_planning()  # Генерируем план этажа
            self.floors.append(floor)
        else:
            # Создаем общий этаж для первых num_floors - 1 этажей
            common_apartment_floor_table = {
                k: {
                    'area_range': v['area_range'],
                    'percent': v['percent'],
                    'number': v['number'] // (self.num_floors - 1)
                    # Учитываем деление на количество этажей
                } for k, v in self.apartment_table.items()
            }
            print(f"Все этажи {common_apartment_floor_table}")
            floor = Floor(points=self.points, sections=self.sections,
                          apartment_table=common_apartment_floor_table,
                          building_polygon=self.polygon)

            floor.generate_floor_planning()  # Генерируем план этажа
            for _ in range(self.num_floors - 1):
                self.floors.append(floor)

            # Генерация последнего этажа
            last_apartment_floor_table = {
                k: {
                    'area_range': v['area_range'],
                    'percent': v['percent'],
                    'number': v['number'] - (common_apartment_floor_table[k]['number'] * (self.num_floors - 1))
                    # Вычисляем количество квартир для последнего этажа
                } for k, v in self.apartment_table.items()
            }
            print(f"Первый этаж {last_apartment_floor_table}")
            # Создаем последний этаж с корректированным количеством квартир
            last_floor = Floor(points=self.points, sections=self.sections,
                               apartment_table=last_apartment_floor_table,
                               building_polygon=self.polygon)
            last_floor.generate_floor_planning()  # Генерируем план последнего этажа

            self.floors.insert(0, last_floor)  # Добавляем последний этаж в начало списка