from Classes.Geometry.GeometricFigure import GeometricFigure
from typing import List, Tuple


# Класс для балкона
class Balcony(GeometricFigure):
    def __init__(self, points: List[Tuple[float, float]]):
        super().__init__(points)