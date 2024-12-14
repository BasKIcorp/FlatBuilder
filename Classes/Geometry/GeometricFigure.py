import math
from typing import List, Tuple
import numpy as np
from shapely.geometry import Polygon, box, LineString
from shapely.prepared import prep
from shapely.vectorized import contains

class GeometricFigure:
    def __init__(self, points: List[Tuple[float, float]]):
        self.points = points  # List of points defining the geometry
        self.polygon = Polygon(self.points)
        self.cells = None        # Will store the list of cells after grid creation
        self.cell_dict = None    # Optional dictionary for quick cell lookup

    def area(self) -> float:
        """Calculates the area of the polygon using the Shoelace formula."""
        n = len(self.points)
        area = 0.0
        for i in range(n):
            x1, y1 = self.points[i]
            x2, y2 = self.points[(i + 1) % n]  # Next point (with cyclic wrap-around)
            area += x1 * y2 - x2 * y1
        return abs(area) / 2.0

    def _reset_cell_assignments(self):
        """Resets the 'assigned' status of all cells in the grid."""
        for cell in self.cells:
            cell['assigned'] = False
        #self._process_cells()

    def perimeter(self) -> float:
        """Calculates the perimeter of the polygon as the sum of distances between adjacent points."""
        n = len(self.points)
        perimeter = 0.0
        for i in range(n):
            x1, y1 = self.points[i]
            x2, y2 = self.points[(i + 1) % n]  # Next point (with cyclic wrap-around)
            perimeter += math.hypot(x2 - x1, y2 - y1)
        return perimeter

    def set_cells(self, cells):
        self.cells = cells

    def check_and_create_cell_grid(self, cell_size: float):
        """Creates a grid of cells covering the polygon and stores it in the object.

        Args:
            cell_size (float): The size of each cell in meters.
        """
        if self.cells is None:
            minx, miny, maxx, maxy = self.polygon.bounds

            # Create arrays of x and y coordinates
            x_coords = np.arange(minx, maxx, cell_size)
            y_coords = np.arange(miny, maxy, cell_size)
            x_grid, y_grid = np.meshgrid(x_coords, y_coords)

            # Flatten the grid arrays
            x_flat = x_grid.ravel()
            y_flat = y_grid.ravel()

            # Create cell center points
            x_centers = x_flat + cell_size / 2
            y_centers = y_flat + cell_size / 2

            # Use shapely.vectorized.contains to check which cell centers are inside the polygon
            points_inside = contains(self.polygon, x_centers, y_centers)

            # Filter the grid cells to only include those inside the polygon
            cells = []
            cell_dict = {}
            indices = np.where(points_inside)[0]
            for idx in indices:
                i = int((x_flat[idx] - minx) / cell_size)
                j = int((y_flat[idx] - miny) / cell_size)
                x1 = x_flat[idx]
                y1 = y_flat[idx]
                x2 = x1 + cell_size
                y2 = y1 + cell_size
                cell_polygon = box(x1, y1, x2, y2)

                cell = {
                    'polygon': cell_polygon,
                    'assigned': False,
                    'neighbors': [],
                    'id': (i, j),
                    'on_perimeter': False,
                    'is_corner': False,
                    'assigned_for_elevators_stairs': False
                }
                cells.append(cell)
                cell_dict[(i, j)] = cell

            # Store the cells and cell_dict in the object
            self.cells = cells
            self.cell_dict = cell_dict

            # Optionally, process cells to find neighbors and perimeter cells
            self._process_cells()

    def _process_cells(self):
        """Determines neighbors of cells and marks cells on the perimeter."""
        # Prepare the polygon for faster operations
        polygon_prepared = prep(self.polygon)
        exterior = self.polygon.exterior

        for cell in self.cells:
            i, j = cell['id']
            cell_polygon = cell['polygon']

            # Check if the cell touches the exterior boundary
            if cell_polygon.exterior.intersects(exterior):
                cell['on_perimeter'] = True
                # Проверяем угловые клетки
                edges = list(exterior.coords)
                intersection_count = 0

                for k in range(len(edges) - 1):
                    # Получаем координаты рёбер
                    x1, y1 = edges[k]
                    x2, y2 = edges[k + 1]

                    # Проверяем пересечение с ребром
                    if cell_polygon.intersects(LineString([(x1, y1), (x2, y2)])):
                        intersection_count += 1

                # Если пересекает два или более рёбер, помечаем как угловую
                cell['is_corner'] = intersection_count >= 2
            else:
                cell['is_corner'] = False



            # Find neighbors, including diagonal neighbors
            neighbors = []
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1), (1, 1), (-1, -1), (-1, 1), (1, -1)]:
                ni, nj = i + dx, j + dy
                if (ni, nj) in self.cell_dict:
                    neighbor = self.cell_dict[(ni, nj)]
                    neighbors.append(neighbor)
            cell['neighbors'] = neighbors

        # corner_cells = [cell for cell in self.cells if cell['is_corner']]
        # corners_to_delete = []
        # for neighbor in corner_cells:
        #     if neighbor['is_corner']:
        #         corners_to_delete.append(neighbor)
        # if len(corners_to_delete) > 0:
        #     for corner in corners_to_delete:
        #         corner['is_corner'] = False


