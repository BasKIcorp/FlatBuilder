from typing import List, Tuple

# Абстрактный класс для геометрических фигур
import math
from typing import List, Tuple
from shapely.geometry import Polygon, box

class GeometricFigure:
    def __init__(self, points: List[Tuple[float, float]]):
        self.points = points  # Список точек, определяющих геометрию
        self.polygon = Polygon(self.points)

    def area(self) -> float:
        """Вычисляет площадь многоугольника по формуле Шоеля."""
        n = len(self.points)
        area = 0.0
        for i in range(n):
            x1, y1 = self.points[i]
            x2, y2 = self.points[(i + 1) % n]  # Следующая точка (с циклическим переходом)
            area += x1 * y2 - x2 * y1
        return abs(area) / 2.0

    def perimeter(self) -> float:
        """Вычисляет периметр многоугольника как сумму расстояний между соседними точками."""
        n = len(self.points)
        perimeter = 0.0
        for i in range(n):
            x1, y1 = self.points[i]
            x2, y2 = self.points[(i + 1) % n]  # Следующая точка (с циклическим переходом)
            perimeter += math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
        return perimeter








