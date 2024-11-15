import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.animation as animation
import random
from shapely.geometry import Polygon


class Cell:
    def __init__(self, id, polygon, neighbors=None):
        self.id = id
        self.polygon = polygon
        self.assigned = False
        self.is_corner = False
        self.neighbors = neighbors if neighbors is not None else []


class TestFloor:
    def __init__(self, cell_grid):
        self.cells = cell_grid

    def _allocate_apartment_cells(self, min_cells, max_cells):
        apt_cell_count = random.randint(min_cells, max_cells)
        available_perimeter_cells = [cell for cell in self.cells if cell.is_corner]

        if not available_perimeter_cells:
            return None  # No available perimeter cells to start an apartment

        start_cell = random.choice(available_perimeter_cells)
        queue = [start_cell]
        apartment_cells = []
        visited_cells = set()

        # Determine grid size and adjust figure size dynamically
        grid_size = int(len(self.cells) ** 0.5)
        fig_size = max(5, grid_size / 10)  # Adjust figure size based on grid size

        fig, ax = plt.subplots(figsize=(fig_size, fig_size))
        anim_cells = []

        def init():
            ax.set_xlim(-1, grid_size + 1)
            ax.set_ylim(-1, grid_size + 1)
            ax.set_aspect('equal')
            for cell in self.cells:
                x, y = cell.polygon.exterior.xy
                patch = patches.Polygon(xy=list(zip(x, y)), closed=True, edgecolor='black', facecolor='white')
                anim_cells.append((cell, patch))
                ax.add_patch(patch)
            return [p[1] for p in anim_cells]

        def update(frame):
            if queue and len(apartment_cells) < apt_cell_count:
                current_cell = queue.pop(0)
                if current_cell.assigned:
                    return [p[1] for p in anim_cells]
                cell_id = current_cell.id
                if cell_id in visited_cells:
                    return [p[1] for p in anim_cells]
                visited_cells.add(cell_id)
                apartment_cells.append(current_cell)
                current_cell.assigned = True
                # Color cell as assigned
                for cell, patch in anim_cells:
                    if cell == current_cell:
                        patch.set_facecolor('red')
                # Add unassigned neighbors to the queue
                neighbors = [neighbor for neighbor in current_cell.neighbors if not neighbor.assigned]
                random.shuffle(neighbors)
                queue.extend(neighbors)
            return [p[1] for p in anim_cells]

        ani = animation.FuncAnimation(fig, update, init_func=init, frames=100, blit=True, repeat=False)
        plt.show()

        if len(apartment_cells) >= min_cells:
            return apartment_cells
        else:
            # Revert cell assignments if the apartment could not be formed
            for cell in apartment_cells:
                cell.assigned = False
            return None


# Generate a 50x50 grid of cells
cell_grid = []
for i in range(10):
    for j in range(10):
        poly = Polygon([(j, i), (j + 1, i), (j + 1, i + 1), (j, i + 1)])
        cell = Cell(id=(i, j), polygon=poly)
        cell_grid.append(cell)

# Set up neighbors (automatically for larger grid)
for cell in cell_grid:
    neighbors = []
    x, y = cell.id
    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        nx, ny = x + dx, y + dy
        neighbor = next((c for c in cell_grid if c.id == (nx, ny)), None)
        if neighbor:
            neighbors.append(neighbor)
    cell.neighbors = neighbors
    # Mark as corner if on grid edge
    cell.is_corner = x == 0 or y == 0 or x == 49 or y == 49

# Run test
floor = TestFloor(cell_grid)
floor._allocate_apartment_cells(min_cells=5, max_cells=20)