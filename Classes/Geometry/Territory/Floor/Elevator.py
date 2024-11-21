from Classes.Geometry.GeometricFigure import GeometricFigure
from typing import List, Tuple
from shapely.geometry import Polygon
# Класс для лифта
class Elevator(GeometricFigure):
    def __init__(self, points: List[Tuple[float, float]]):
        super().__init__(points)
        self.points = points
        self.polygon = Polygon(self.points)


    def generatePlanning(self, apartment_table, max_iterations=150, cell_size=2):

        self.cell_size = cell_size
        """Generates a floor plan by allocating apartments according to the given apartment table."""
        self.apartments = []  # Initialize as empty list
        best_plan = None
        best_score = float('inf')  # The lower, the better
        start_time = time.time()

        # Create the cell grid once