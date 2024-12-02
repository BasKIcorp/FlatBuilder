from Classes.Geometry.GeometricFigure import GeometricFigure
from Classes.Geometry.Territory.Building.Floor.Floor import Floor
from Classes.Geometry.Territory.Building.Elevator import Elevator
from Classes.Geometry.Territory.Building.Stair import Stair
from typing import List, Tuple, Dict
import copy


class Building(GeometricFigure):
    def __init__(self, points: List[Tuple[float, float]],
                 sections: List[List[Tuple[float, float]]],
                 num_floors: int,
                 apartment_table: Dict,
                 elevators_coords: List[List[Tuple[float, float]]] = None,
                 stairs_coords: List[List[Tuple[float, float]]] = None):
        super().__init__(points)
        self.floors = []  # Список этажей в здании
        self.num_floors = num_floors  # Количество этажей
        self.sections = sections  # Секции этажей
        self.apartment_table = apartment_table  # Таблица квартир, переданная в класс
        # Создаем лифты и лестницы
        self.elevators = [Elevator(coords) for coords in elevators_coords] if elevators_coords is not None else []
        self.stairs = [Stair(coords) for coords in stairs_coords] if stairs_coords is not None else []

    def generate_floors(self):
        """Генерирует этажи, добавляя их в список floors."""
        total_assigned_numbers = {apt_type: 0 for apt_type in
                                  self.apartment_table.keys()}  # Инициализация счетчиков для квартир

        # Создаем общий этаж для первых num_floors - 1 этажей
        common_apartment_floor_table = {
            k: {
                'area_range': v['area_range'],
                'percent': v['percent'],
                'number': v['number'] // (self.num_floors - 1) if self.num_floors > 1 else v['number']
                # Учитываем деление на количество этажей
            } for k, v in self.apartment_table.items()
        }
        floor = Floor(points=self.points, sections=self.sections,
                      apartment_table=common_apartment_floor_table,
                      elevators=self.elevators, stairs=self.stairs)
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

        # Создаем последний этаж с корректированным количеством квартир
        last_floor = Floor(points=self.points, sections=self.sections,
                           apartment_table=last_apartment_floor_table,
                           elevators=self.elevators, stairs=self.stairs)
        last_floor.generate_floor_planning()  # Генерируем план последнего этажа

        self.floors.insert(0, last_floor)  # Добавляем последний этаж в начало списка