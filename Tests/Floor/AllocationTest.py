import matplotlib.pyplot as plt
from shapely.geometry import Polygon
from matplotlib.patches import Polygon as MplPolygon
from matplotlib.lines import Line2D
from Classes.Geometry.Territory.Floor.Floor import Floor

# Полигоны этажей
floor_polygons = [
    [(0, 0), (0, 30), (35, 30), (35, 0)],
    [(0, 0), (30, 0), (30, 25), (20, 25), (20, 30), (0, 30)]
    # [(0, 0), (0, 100), (100, 100), (100, 70), (60, 70), (60, 0)],
    # [(0, 0), (0, 100), (100, 100), (100, 0), (70, 0), (70, 50), (30, 50), (30, 0)]
]



# Таблица квартир
apartment_table = {
    'studio': {
        'area_range': (30, 45),  # Уменьшение площади для студий
        'percent': 20,
        'number': 2
    },
    '1 room': {
        'area_range': (40, 60),  # Площадь для однокомнатных квартир
        'percent': 20,
        'number': 3
    },
    '2 room': {
        'area_range': (60, 90),  # Площадь для двухкомнатных квартир
        'percent': 20,
        'number': 2
    },
    '3 room': {
        'area_range': (80, 120),  # Площадь для трехкомнатных квартир
        'percent': 20,
        'number': 1
    },
    '4 room': {
        'area_range': (100, 140),  # Площадь для четырехкомнатных квартир
        'percent': 20,
        'number': 2
    },
}

# Создаем фигуры для каждого этажа и генерируем план
figures = []
for points in floor_polygons:
    floor = Floor(points)
    #floor.set_stairs([(0, 0), (0, 10), (10, 10), (10, 0)])
    floor.set_elevator([(15, 15), (15, 20), (20, 20), (20, 15)])
    #floor.set_stairs([(5, 5), (5, 10), (10, 10), (10, 5)])
    planning= floor.generatePlanning(apartment_table, max_iterations=50)
    print(len([cell for cell in floor.cells if cell['on_perimeter']]))
    figures.append(floor)

# Визуализация
fig, axs = plt.subplots(nrows=1, ncols=len(figures), figsize=(15, 8))

# Цвета для разных типов квартир
apt_colors = {
    'studio': 'red',
    '1 room': 'green',
    '2 room': 'blue',
    '3 room': 'orange',
    '4 room': 'purple',
    'elevator': 'yellow',
    'stair': 'pink',
    'free': 'gray'  # Цвет для незанятых клеток
}

for ax, floor in zip(axs, figures):
    # Отображение основного полигона этажа
    x, y = floor.polygon.exterior.xy
    ax.plot(x, y, color='black')

    for cell in floor.free_cells:  # Используем список незанятых клеток
        cell_polygon = cell['polygon']
        x, y = cell_polygon.exterior.xy
        ax.fill(x, y, alpha=0.5, facecolor=apt_colors['free'], edgecolor='black')

    # Отображение квартир
    for apt in floor.apartments:
        poly = apt.polygon
        x, y = poly.exterior.xy
        ax.fill(x, y, alpha=0.5, facecolor=apt_colors[apt.type], edgecolor='black')
        # Вычисляем центр полигона для размещения метки
        centroid = poly.centroid
        ax.text(centroid.x, centroid.y, apt.type, horizontalalignment='center', verticalalignment='center', fontsize=8)

    # Отображение лифтов
    for elevator in floor.elevators:
        x, y = elevator.polygon.exterior.xy
        ax.fill(x, y, alpha=0.5, facecolor=apt_colors['elevator'], edgecolor='black')

    for stair in floor.stairs:
        x, y = stair.polygon.exterior.xy
        ax.fill(x, y, alpha=0.5, facecolor=apt_colors['stair'], edgecolor='black')

    # Настройка графика
    ax.set_xlim(floor.polygon.bounds[0] - 10, floor.polygon.bounds[2] + 10)
    ax.set_ylim(floor.polygon.bounds[1] - 10, floor.polygon.bounds[3] + 10)
    ax.set_aspect('equal', adjustable='box')
    ax.set_title('Размещение квартир на этаже')

# Легенда
legend_elements = [Line2D([0], [0], marker='s', color='w', label=apt_type,
                          markerfacecolor=apt_colors[apt_type], markersize=10) for apt_type in apt_colors]
fig.legend(handles=legend_elements, loc='upper right')

plt.tight_layout()
plt.show()