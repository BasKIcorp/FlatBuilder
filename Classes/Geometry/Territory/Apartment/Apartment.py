from Classes.Geometry.GeometricFigure import GeometricFigure
from Classes.Geometry.Territory.Apartment.Room import Room
from Classes.Geometry.Territory.Apartment.WetArea import WetArea
from Classes.Geometry.Territory.Apartment.Balcony import Balcony

from typing import List, Tuple


# Класс для квартиры, содержащей комнаты, мокрые зоны и балконы
class Apartment(GeometricFigure):
    def __init__(self, points: List[Tuple[float, float]], rooms: List['Room'], wet_areas: List['WetArea'], balconies: List['Balcony']):
        super().__init__(points)
        self.rooms = rooms  # Список комнат в квартире
        self.wet_areas = wet_areas  # Список мокрых зон в квартире
        self.balconies = balconies  # Список балконов в квартире