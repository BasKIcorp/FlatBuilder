import matplotlib.pyplot as plt
from shapely.geometry import Polygon

from Classes.Geometry.Territory.Territory import Territory

# Исходные данные полигона территории и зданий
buildings_polygons = [
    [(0, 0), (26, 0), (26, 26), (43, 26), (43, 45), (0, 45)]
]

sections_polygons = [
    [(0, 0), (26, 0), (26, 26), (43, 26), (43, 45), (0, 45)]
]

# Параметры
num_floors = 9
apartment_table = {
    'studio': {'area_range': (25, 35), 'percent': 20, 'number': 24},
    '1 room': {'area_range': (38, 50), 'percent': 20, 'number': 36},
    '2 room': {'area_range': (55, 70), 'percent': 20, 'number': 24},
    '3 room': {'area_range': (75, 95), 'percent': 20, 'number': 14},
    '4 room': {'area_range': (95, 130), 'percent': 20, 'number': 24},
}

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
print(territory.buildings[0].polygon.area)
print(territory.buildings[0].floors[0].polygon.area)
print(territory.buildings[0].floors[0].sections[0].polygon.area)
sum = 0
for cell in territory.buildings[0].floors[0].sections[0].cells:
    sum += cell['polygon'].area

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
plot_floor_with_apartments(ax, territory.buildings[0].floors[1], 'Квартиры на первом этаже')

plt.show()
print(territory.generate_output_table())