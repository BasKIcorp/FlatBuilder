from Classes.Geometry.GeometricFigure import GeometricFigure
from typing import List, Tuple
from shapely.geometry import Polygon, MultiPolygon

# Класс для комнаты
class Room(GeometricFigure):
    def __init__(self, points: List[Tuple[float, float]],
                 room_type: str):
        super().__init__(points)
        self.type = room_type
        self.area = self.polygon.area
        self.points = points
        self.polygon = Polygon(self.points)
