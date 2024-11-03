from Classes.Geometry.GeometricFigure import GeometricFigure
from Classes.Geometry.Territory.Floor.Floor import Floor
from typing import List, Tuple


# Класс для здания, содержащего этажи
class Building(GeometricFigure):
    def __init__(self, points: List[Tuple[float, float]], floors: List['Floor']):
        super().__init__(points)
        self.floors = floors  # Список этажей в здании

    def generatePlanning(self, apartment_building_table):
        ...