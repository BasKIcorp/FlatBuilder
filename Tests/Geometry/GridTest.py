from Classes.Geometry.GeometricFigure import GeometricFigure
from shapely.geometry import Polygon, box

# Include the Cell class and updated functions here
# (Cell class definition and functions as provided above)

# Define the floor polygon (Example: a simple L-shaped polygon)
points = [
    (0, 0), (10, 0), (10, 5), (15, 5),
    (15, 15), (0, 15), (0, 0)
]

# Create a GeometricFigure object
geom_fig = GeometricFigure(points)

# Create the cell grid with a specified cell size
cell_size = 1  # Cell size in meters
geom_fig.create_cell_grid(cell_size)

# Access the cells
cells = geom_fig.cells


# Optional: Visualize the grid
def plot_cell_grid(polygon, cells):
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon as MplPolygon
    from matplotlib.collections import PatchCollection

    fig, ax = plt.subplots(figsize=(8, 8))

    # Plot the polygon
    x, y = polygon.exterior.xy
    ax.plot(x, y, color='black', linewidth=2)

    # Create patches for the cells
    patches = []
    for cell in cells:
        cell_poly = cell['polygon']
        x, y = cell_poly.exterior.xy
        coords = list(zip(x, y))
        polygon_patch = MplPolygon(coords, True)
        patches.append(polygon_patch)

    # Create a PatchCollection
    p = PatchCollection(patches, facecolor='lightblue', edgecolor='gray', alpha=0.5)
    ax.add_collection(p)

    # Set plot limits
    minx, miny, maxx, maxy = polygon.bounds
    ax.set_xlim(minx - 1, maxx + 1)
    ax.set_ylim(miny - 1, maxy + 1)
    ax.set_aspect('equal', 'box')
    ax.set_title('Cell Grid Overlay on Polygon')
    plt.xlabel('X-coordinate')
    plt.ylabel('Y-coordinate')
    plt.grid(True)
    plt.show()


# Plot the grid
plot_cell_grid(geom_fig.polygon, geom_fig.cells)