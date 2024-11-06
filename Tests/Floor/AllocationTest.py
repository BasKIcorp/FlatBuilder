import matplotlib.pyplot as plt
from shapely.geometry import Polygon
from shapely.ops import cascaded_union
from matplotlib.patches import Polygon as MplPolygon
from matplotlib.lines import Line2D
from Classes.Geometry.Territory.Floor.Floor import Floor

# Создаем объект этажа
floor_points = [(0, 0), (100, 0), (100, 80), (60, 80), (60, 100), (0, 100)]  # Пример полигона этажа
floor = Floor(floor_points)

# Таблица квартир
apartment_table = {
    'studio': {
        'area_range': (250, 300),
        'percent': 20
    },
    '1 room': {
        'area_range': (300, 400),
        'percent': 20
    },
    '2 room': {
        'area_range': (400, 500),
        'percent': 20
    },
    '3 room': {
        'area_range': (500, 600),
        'percent': 20
    },
    '4 room': {
        'area_range': (600, 700),
        'percent': 20
    },
}

# Генерация планировки
planning = floor.generatePlanning(apartment_table)

# Визуализация
fig, ax = plt.subplots(figsize=(10, 8))

# Отображение основного полигона этажа
x, y = floor.polygon.exterior.xy
ax.plot(x, y, color='black')

# Цвета для разных типов квартир
apt_colors = {
    'studio': 'red',
    '1 room': 'green',
    '2 room': 'blue',
    '3 room': 'orange',
    '4 room': 'purple'
}

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

# Легенда
legend_elements = [Line2D([0], [0], marker='s', color='w', label=apt_type,
                          markerfacecolor=apt_colors[apt_type], markersize=10) for apt_type in apt_colors]
ax.legend(handles=legend_elements, loc='upper right')

plt.title('Размещение квартир на этаже')
plt.show()
