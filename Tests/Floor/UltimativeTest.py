import matplotlib.pyplot as plt
from shapely.geometry import Polygon

from Classes.Geometry.Territory.Territory import Territory

# Исходные данные полигона территории и зданий
# Исходные данные полигона территории и зданий
buildings_polygons = [
    [(-10, -10), (10, -10), (10, 10), (-10, 10)]
]

sections_polygons = [
    [(-10, -10), (10, -10), (10, 10), (-10, 10)]
]

# Параметры
num_floors = 2
apartment_table = [{
    'studio': {'area_range': (25, 35), 'percent': 100, 'number': 5},
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

def plot_section(ax, section, title):
    """Рисует секцию с квартирами, закрашенными по типу."""
    ax.set_title(title)
    ax.set_aspect('equal', adjustable='box')

    apartment_number = 1  # Начальный номер квартиры
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

    # Добавляем контур секции
    cx, cy = section.polygon.exterior.xy
    ax.plot(cx, cy, color='black', linewidth=2)

# Построение графиков для каждой секции
figure_list = []
for building_index, building in enumerate(territory.buildings):
    for floor_index, floor in enumerate(building.floors):
        for section_index, section in enumerate(floor.sections):
            fig, ax = plt.subplots(figsize=(8, 8))
            title = f"Здание {building_index + 1}, Этаж {floor_index + 1}, Секция {section_index + 1}"
            plot_section(ax, section, title)
            figure_list.append(fig)

# Показ всех графиков одновременно
plt.show()
