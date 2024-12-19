import matplotlib.pyplot as plt
from shapely.geometry import Polygon

from Classes.Geometry.Territory.Territory import Territory

# Исходные данные полигона территории и зданий
buildings_polygons = [
    [(0, 0), (42, 0), (42, 38), (0, 38)]
]

sections_polygons = [
    [(0, 0), (42, 0), (42, 38), (0, 38)]
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


def plot_floor_with_apartments(ax, floor, title):
    """Рисует этаж с квартирами, закрашенными по типу, без комнат."""
    ax.set_title(title)
    ax.set_aspect('equal', adjustable='box')
    for section in floor.sections:
        for apartment in section.apartments:
            color = apartment_colors.get(apartment.type, 'gray')  # Используем цвет по типу или серый по умолчанию
            polygon = Polygon(apartment.points)
            x, y = polygon.exterior.xy
            ax.fill(x, y, color=color, alpha=0.6)
            ax.plot(x, y, color='black', linewidth=0.5)


# Построение графика для первого этажа
fig, ax = plt.subplots(figsize=(8, 8))
plot_floor_with_apartments(ax, territory.buildings[0].floors[1], 'Квартиры на первом этаже')

plt.show()
