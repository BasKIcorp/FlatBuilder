import matplotlib.pyplot as plt
from shapely.geometry import Polygon
from matplotlib.patches import Polygon as MplPolygon
from matplotlib.lines import Line2D
from Classes.Geometry.Territory.Building import Building  # Не забудьте изменить путь на актуальный
from Classes.Geometry.Territory.Floor.Floor import Floor

# Исходный полигон здания
building_polygon = [(0, 0), (100, 0), (100, 80), (0, 80)]

# Количество этажей
num_floors = 2

# Таблица квартир
apartment_table = {
    'studio': {
        'area_range': (300, 400),
        'percent': 20
    },
    '1 room': {
        'area_range': (500, 600),
        'percent': 20
    },
    '2 room': {
        'area_range': (800, 900),
        'percent': 20
    },
    '3 room': {
        'area_range': (1000, 1100),
        'percent': 20
    },
    '4 room': {
        'area_range': (1200, 1300),
        'percent': 20
    },
}

# Создаем здание
building = Building(points=building_polygon, num_floors=num_floors, apartment_table=apartment_table)

# Визуализация
fig, axs = plt.subplots(nrows=1, ncols=building.num_floors, figsize=(15, 8))

# Цвета для разных типов квартир
apt_colors = {
    'studio': 'red',
    '1 room': 'green',
    '2 room': 'blue',
    '3 room': 'orange',
    '4 room': 'purple'
}

# Отображение каждого этажа
for ax, floor in zip(axs, building.floors):
    # Отображение основного полигона этажа
    x, y = floor.polygon.exterior.xy
    ax.plot(x, y, color='black')

    # Отображение квартир
    for apt in floor.apartments:
        poly = apt.polygon
        x, y = poly.exterior.xy
        ax.fill(x, y, alpha=0.5, facecolor=apt_colors[apt.type], edgecolor='black')
        # Вычисляем центр полигона для размещения метки
        centroid = poly.centroid
        ax.text(centroid.x, centroid.y, apt.type, horizontalalignment='center', verticalalignment='center', fontsize=8)

    # Настройка графика
    ax.set_xlim(floor.polygon.bounds[0] - 10, floor.polygon.bounds[2] + 10)
    ax.set_ylim(floor.polygon.bounds[1] - 10, floor.polygon.bounds[3] + 10)
    ax.set_aspect('equal', adjustable='box')
    ax.set_title(f'Этаж {building.floors.index(floor) + 1}')

# Легенда
legend_elements = [Line2D([0], [0], marker='s', color='w', label=apt_type,
                          markerfacecolor=apt_colors[apt_type], markersize=10) for apt_type in apt_colors]
fig.legend(handles=legend_elements, loc='upper right')

plt.tight_layout()
plt.show()