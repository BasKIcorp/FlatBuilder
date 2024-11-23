from Classes.Geometry.GeometricFigure import GeometricFigure
from Classes.Geometry.Territory.Floor.Floor import Floor
from typing import List, Tuple, Dict

class Building(GeometricFigure):
    def __init__(self, points: List[Tuple[float, float]], num_floors: int, apartment_table: Dict):
        super().__init__(points)
        self.floors = []  # Список этажей в здании
        self.num_floors = num_floors  # Количество этажей
        self.apartment_table = apartment_table  # Таблица квартир, переданная в класс

        # Генерируем этажи
        self.generate_floors()

    def generate_floors(self):
        """Генерирует этажи, добавляя их в список floors."""
        # Генерируем первый этаж
        first_floor = Floor(points=self.points)
        first_floor.generatePlanning(self.apartment_table, max_iterations=20)  # Планирование первого этажа
        self.floors.append(first_floor)  # Добавляем первый этаж в список

        # Копируем первый этаж для остальных этажей
        for _ in range(1, self.num_floors):
            copied_floor = Floor(points=self.points)  # Создаем новый объект Floor с теми же points
            copied_floor.apartments = first_floor.apartments.copy()  # Копируем список квартир
            self.floors.append(copied_floor)  # Добавляем копию этажа в список