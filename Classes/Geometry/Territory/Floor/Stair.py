from Classes.Geometry.GeometricFigure import GeometricFigure
from typing import List, Tuple
from shapely.geometry import Polygon
# Класс для лестницы
class Stair(GeometricFigure):
    def __init__(self, points: List[Tuple[float, float]]):
        super().__init__(points)
        self.points = points
        self.polygon = Polygon(self.points)