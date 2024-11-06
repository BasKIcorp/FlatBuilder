from Classes.Geometry.GeometricFigure import GeometricFigure
from Classes.Geometry.Territory.Apartment.Apartment import Apartment
from Classes.Geometry.Territory.Apartment.Room import Room
from Classes.Geometry.Territory.Apartment.WetArea import WetArea
from Classes.Geometry.Territory.Apartment.Balcony import Balcony
from Classes.Geometry.Territory.Floor.Elevator import Elevator
from Classes.Geometry.Territory.Floor.Stair import Stair
from shapely.geometry import Polygon, LineString
from shapely.ops import unary_union
import random
from typing import List, Tuple
import math
import time

class Floor(GeometricFigure):
    def __init__(self, points: List[Tuple[float, float]], apartments: List['Apartment'] = None, elevators: List['Elevator'] = None, stairs: List['Stair'] = None):
        super().__init__(points)
        self.apartments = apartments if apartments is not None else []  # List of Apartment objects
        self.elevators = elevators if elevators is not None else []
        self.stairs = stairs if stairs is not None else []

    def generatePlanning(self, apartment_table, max_iterations=50, cell_size = 2):
        """Generates a floor plan by allocating apartments according to the given apartment table."""
        self.apartments = []  # Initialize as empty list
        best_plan = None
        best_score = float('inf')  # The lower, the better
        start_time = time.time()

        # Create the cell grid once
        self.create_cell_grid(cell_size=cell_size)

        for iteration in range(max_iterations):
            # Reset the cell assignments between iterations
            self._reset_cell_assignments()

            # Allocate apartments using the cell grid
            apartments = self._allocate_apartments(self.cells, apartment_table)

            # **Validation**: Validate apartments for free sides
            if not apartments:
                continue  # No apartments allocated in this iteration

            if not self._validate_apartments_free_sides(apartments):
                # Allocation is invalid, skip to next iteration
                # print(f"Iteration {iteration + 1}: Allocation rejected due to lack of free sides.")
                continue

            # Calculate distribution error
            total_error = self._calculate_total_error(apartments, apartment_table)

            # Update the best plan if current is better
            if total_error < best_score:
                best_score = total_error
                best_plan = apartments
                print(f"Iteration {iteration + 1}: Found a better plan with error {best_score:.2f}%")

            # Early exit if perfect plan is found
            if best_score == 0:
                break

        self.apartments = best_plan if best_plan is not None else []  # Save the best generated plan
        total_time = time.time() - start_time
        print(f"Floor planning completed in {total_time:.2f} seconds.")

        return self.apartments

    def _reset_cell_assignments(self):
        """Resets the 'assigned' status of all cells in the grid."""
        for cell in self.cells:
            cell['assigned'] = False

    def _allocate_apartments(self, cells, apartment_table):
        """Allocates cells to apartments according to the specified parameters."""
        random.shuffle(cells)
        apartments = []
        remaining_cells = [cell for cell in cells if not cell['assigned']]

        # Calculate the number of cells for each apartment type
        cell_counts, remaining_cell_counts = self._calculate_cell_counts(apartment_table, cells)

        for apt_type, apt_info in apartment_table.items():
            min_cells, max_cells = self._get_apartment_cell_range(apt_info['area_range'], cell_size=2)
            allocated_cell_count = remaining_cell_counts[apt_type]

            while allocated_cell_count >= min_cells:
                apartment_cells = self._allocate_apartment_cells(remaining_cells, min_cells, max_cells)

                if not apartment_cells:
                    break  # No more apartments of this type can be allocated

                # Create the apartment polygon
                apartment_polygon = unary_union([cell['polygon'] for cell in apartment_cells])

                # First Validation: Check if apartment has at least one side adjacent to the external perimeter
                if not self._validate_apartment_perimeter_adjacency(apartment_polygon):
                    # If the apartment does not touch the perimeter, unassign the cells and try again
                    for cell in apartment_cells:
                        cell['assigned'] = False
                    continue

                # Create an Apartment object
                points = list(apartment_polygon.exterior.coords)
                rooms = []       # Placeholder for rooms
                wet_areas = []   # Placeholder for wet areas
                balconies = []   # Placeholder for balconies

                apartment = Apartment(points=points, apt_type=apt_type, rooms=rooms, wet_areas=wet_areas, balconies=balconies)

                apartments.append(apartment)
                allocated_cell_count -= len(apartment_cells)
                remaining_cell_counts[apt_type] = allocated_cell_count

                # Update the list of remaining cells
                remaining_cells = [cell for cell in remaining_cells if not cell['assigned']]

        return apartments

    def _validate_apartment_perimeter_adjacency(self, apartment_polygon):
        """First validation: Checks if the apartment has at least one side adjacent to the external perimeter."""
        return apartment_polygon.exterior.intersects(self.polygon.exterior)

    def _validate_apartments_free_sides(self, apartments):
        """Second validation: Checks that each apartment has at least one free side.

        A free side is a side not adjacent to the external perimeter or any other apartment.
        Returns True if all apartments have at least one free side, False otherwise.
        """
        for i, apt in enumerate(apartments):
            apartment_polygon = apt.polygon
            has_free_side = False
            # Get the exterior coordinates as pairs of points
            coords = list(apartment_polygon.exterior.coords)
            # Create LineStrings for each side
            sides = [LineString([coords[j], coords[j+1]]) for j in range(len(coords)-1)]  # last point is same as first

            for side in sides:
                # Check if side intersects with external perimeter
                if self.polygon.exterior.intersects(side):
                    continue
                # Check if side intersects with any other apartment
                for k, other_apt in enumerate(apartments):
                    if k == i:
                        continue
                    if other_apt.polygon.exterior.intersects(side):
                        break  # Side touches another apartment
                else:
                    # Side does not touch external perimeter or any other apartment
                    has_free_side = True
                    break

            if not has_free_side:
                # Apartment does not have any free sides
                return False
        return True

    def _calculate_cell_counts(self, apartment_table, cells):
        """Calculates the number of cells to allocate for each apartment type."""
        total_area = self.polygon.area
        cell_area = cells[0]['polygon'].area if cells else 0
        cell_counts = {}
        for apt_type, apt_info in apartment_table.items():
            percent = apt_info['percent']
            allocated_area = total_area * (percent / 100)
            allocated_cell_count = int(allocated_area / cell_area)
            cell_counts[apt_type] = allocated_cell_count
        remaining_cell_counts = cell_counts.copy()
        return cell_counts, remaining_cell_counts

    def _get_apartment_cell_range(self, area_range, cell_size):
        """Determines the minimum and maximum number of cells for an apartment based on the area range."""
        cell_area = cell_size ** 2  # Area of a single cell
        min_cells = max(1, int(area_range[0] / cell_area))
        max_cells = int(area_range[1] / cell_area)
        return min_cells, max_cells

    def _allocate_apartment_cells(self, remaining_cells, min_cells, max_cells):
        """Allocates cells for a single apartment using BFS to ensure contiguity."""
        apt_cell_count = random.randint(min_cells, max_cells)
        available_perimeter_cells = [cell for cell in remaining_cells if cell['on_perimeter']]
        if not available_perimeter_cells:
            return None  # No available perimeter cells to start an apartment

        start_cell = random.choice(available_perimeter_cells)
        queue = [start_cell]
        apartment_cells = []
        visited_cells = set()

        while queue and len(apartment_cells) < apt_cell_count:
            current_cell = queue.pop(0)
            if current_cell['assigned']:
                continue
            cell_id = current_cell['id']
            if cell_id in visited_cells:
                continue
            visited_cells.add(cell_id)
            apartment_cells.append(current_cell)
            current_cell['assigned'] = True

            # Add unassigned neighbors to the queue
            neighbors = [neighbor for neighbor in current_cell['neighbors'] if not neighbor['assigned']]
            random.shuffle(neighbors)
            queue.extend(neighbors)

        if len(apartment_cells) >= min_cells:
            return apartment_cells
        else:
            # Revert cell assignments if the apartment could not be formed
            for cell in apartment_cells:
                cell['assigned'] = False
            return None

    def _calculate_total_error(self, apartments, apartment_table):
        """Calculates the total error in apartment type distribution among allocated area."""
        # Calculate the total allocated area
        total_allocated_area = sum(apt.area for apt in apartments)

        # Calculate actual percentages among allocated area
        actual_percentages = {}
        for apt_type in apartment_table.keys():
            total_type_area = sum(apt.area for apt in apartments if apt.type == apt_type)
            actual_percent = (total_type_area / total_allocated_area) * 100 if total_allocated_area > 0 else 0
            actual_percentages[apt_type] = actual_percent

        # Calculate total desired percentage
        total_desired_percent = sum(apt_info['percent'] for apt_info in apartment_table.values())

        # Normalize desired percentages to sum up to 100%
        normalized_desired_percentages = {}
        for apt_type, apt_info in apartment_table.items():
            normalized_percent = (apt_info['percent'] / total_desired_percent) * 100 if total_desired_percent > 0 else 0
            normalized_desired_percentages[apt_type] = normalized_percent

        # Calculate total error based on normalized desired percentages
        total_error = sum(
            abs(normalized_desired_percentages[apt_type] - actual_percentages.get(apt_type, 0))
            for apt_type in apartment_table.keys()
        )
        return total_error
