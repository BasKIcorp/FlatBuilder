from Classes.Geometry.GeometricFigure import GeometricFigure
from typing import List, Tuple, Dict
from shapely.geometry import Polygon
# Класс для лифта
class Elevator(GeometricFigure):
    def __init__(self, points: List[Tuple[float, float]]):
        super().__init__(points)
        self.points = points
        self.polygon = Polygon(self.points)


