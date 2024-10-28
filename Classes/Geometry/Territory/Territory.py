from Classes.Geometry.GeometricFigure import GeometricFigure
from typing import List, Tuple
from Classes.Geometry.Territory.Building import Building


# Класс для территории, содержащей здания
class Territory(GeometricFigure):
    def __init__(self, points: List[Tuple[float, float]], buildings: List['Building']):
        super().__init__(points)
        self.buildings = buildings  # Список зданий на территории

    def generatePlanning(self, apartment_building_table):
        ...