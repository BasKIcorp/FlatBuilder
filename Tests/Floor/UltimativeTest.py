import matplotlib.pyplot as plt
from shapely.geometry import Polygon

from Classes.Geometry.Territory.Territory import Territory

# Исходные данные полигона территории и зданий
buildings_polygons = [
    [(-10, -10), (10, -10), (10, 10), (-10, 10)], [(27, -34), (37, -34), (37, -25), (26, -26)]
]

sections_polygons = [
    [(-10, -10), (10, -10), (10, 10), (-10, 10)], [(27, -34), (37, -34), (37, -25), (26, -26)]
]

# Параметры
num_floors = 3
apartment_table = [{
    'studio': {'area_range': (25, 35), 'percent': 100, 'number': 5},
    '1 room': {'area_range': (38, 50), 'percent': 0, 'number': 0},
    '2 room': {'area_range': (55, 70), 'percent': 0, 'number': 0},
    '3 room': {'area_range': (75, 95), 'percent': 0, 'number': 0},
    '4 room': {'area_range': (95, 130), 'percent': 0, 'number': 0},
},
    {'studio': {'area_range': (20, 30), 'percent': 100, 'number': 1},
     '1 room': {'area_range': (38, 50), 'percent': 0, 'number': 0},
     '2 room': {'area_range': (55, 70), 'percent': 0, 'number': 0},
     '3 room': {'area_range': (75, 95), 'percent': 0, 'number': 0},
     '4 room': {'area_range': (95, 130), 'percent': 0, 'number': 0},
     }]

# Определяем цвета для каждого типа квартиры
apartment_colors = {
    'studio': 'lightblue',
    '1 room': 'lightgreen',
    '2 room': 'orange',
    '3 room': 'pink',
    '4 room': 'purple'
}

# Создание объекта территории
territory = Territory(buildings_polygons, sections_polygons, num_floors, apartment_table)
territory.generate_building_plannings()

def plot_floor_with_apartments(ax, floor, title):
    """Рисует этаж с квартирами, закрашенными по типу, без комнат."""
    ax.set_title(title)
    ax.set_aspect('equal', adjustable='box')
    ax.fill()

    apartment_number = 1  # Начальный номер квартиры
    for section in floor.sections:
        for apartment in section.apartments:
            color = apartment_colors.get(apartment.type, 'gray')  # Используем цвет по типу или серый по умолчанию
            polygon = Polygon(apartment.points)
            x, y = polygon.exterior.xy
            ax.fill(x, y, color=color, alpha=0.6)
            ax.plot(x, y, color='black', linewidth=0.5)

            # Находим центр полигона, чтобы разместить номер
            apartment_centroid = polygon.centroid
            ax.text(
                apartment_centroid.x, apartment_centroid.y,
                str(apartment_number),
                color='black', fontsize=8, ha='center', va='center', weight='bold'
            )
            apartment_number += 1  # Увеличиваем номер квартиры

    # Добавляем контур этажа
    cx, cy = floor.polygon.exterior.xy
    ax.plot(cx, cy, color='black', linewidth=2)

# Построение графика для первого этажа
fig, ax = plt.subplots(figsize=(8, 8))
plot_floor_with_apartments(ax, territory.buildings[1].floors[1], 'Квартиры на первом этаже')
plt.show()