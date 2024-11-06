from Classes.Geometry.GeometricFigure import GeometricFigure
from Classes.Geometry.Territory.Apartment.Room import Room
from Classes.Geometry.Territory.Apartment.WetArea import WetArea
from Classes.Geometry.Territory.Apartment.Balcony import Balcony

from typing import List, Tuple

# Класс для квартиры, содержащей комнаты, мокрые зоны и балконы
class Apartment(GeometricFigure):
    def __init__(self, points: List[Tuple[float, float]], apt_type: str, rooms: List['Room'] = None, wet_areas: List['WetArea'] = None, balconies: List['Balcony'] = None):
        super().__init__(points)
        self.type = apt_type        # Тип квартиры
        self.area = self.polygon.area  # Площадь квартиры, вычисленная из геометрии
        self.rooms = rooms if rooms is not None else []            # Список комнат в квартире
        self.wet_areas = wet_areas if wet_areas is not None else []  # Список мокрых зон в квартире
        self.balconies = balconies if balconies is not None else []  # Список балконов в квартире
