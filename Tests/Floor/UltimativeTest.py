import matplotlib.pyplot as plt
from shapely.geometry import Polygon

from Classes.Geometry.Territory.Territory import Territory

# buildings_polygons = [
#     [(0, 15), (5, 50), (50, 43), (110, 43), (110, 0), (50, 0)]
# ]
# sections_polygons = [
#     [(0, 15), (5, 50), (50, 43), (50, 0)],
#     [(50, 43), (110, 43), (110, 0), (50, 0)]
# ]
# buildings_polygons = [
#     [(38, 0), (45, 50), (8, 55), (0, 29)]
# ]
# sections_polygons = [
#     [(38, 0), (45, 50), (8, 55), (0, 29)]
# ]
# buildings_polygons = [
#     [(0, 0), (25, 0), (50, 35), (70, 35), (70, 45), (0, 45)]
# ]
# sections_polygons = [
#     [(0, 0), (25, 0), (50, 35), (70, 35), (70, 45), (0, 45)]
# ]
# buildings_polygons = [
#     [(0, 0), (25, 0), (26, 26), (43, 26), (43, 45), (0, 45)]
# ]
#
# sections_polygons = [
#     [(0, 0), (25, 0), (26, 26), (43, 26), (43, 45), (0, 45)]
# ]
buildings_polygons = [
    [(0, 0), (35, 0), (35, 27), (0, 27)]
]
sections_polygons = [
    [(0, 0), (35, 0), (35, 27), (0, 27)]
]

# Параметры
num_floors = 14
apartment_table = [{
    'studio': {'area_range': (25, 35), 'percent': 100, 'number': 24},
    '1 room': {'area_range': (38, 50), 'percent': 20, 'number': 36},
    '2 room': {'area_range': (55, 70), 'percent': 20, 'number': 24},
    '3 room': {'area_range': (75, 95), 'percent': 20, 'number': 14},
    '4 room': {'area_range': (95, 130), 'percent': 20, 'number': 24},
}]
# Исходные данные полигона территории и зданий


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
#
# def plot_section(ax, section, title):
#     """Рисует секцию с квартирами, закрашенными по типу, и комнатами внутри."""
#     ax.set_title(title)
#     ax.set_aspect('equal', adjustable='box')
#     apartment_number = 1  # Начальный номер квартиры
#     for apartment in section.apartments:
#         # Контур квартиры
#         polygon = Polygon(apartment.points)
#         x, y = polygon.exterior.xy
#         ax.plot(x, y, color='black', linewidth=2)  # Жирный контур квартиры
#
#         # Рисуем комнаты внутри квартиры
#         for room in apartment.rooms:
#             room_polygon = Polygon(room.points)
#             color = apartment_colors.get(apartment.type, 'gray')  # Цвет комнаты зависит от типа квартиры
#             rx, ry = room_polygon.exterior.xy
#             ax.fill(rx, ry, color=color, alpha=0.6)  # Заливка комнаты
#             ax.plot(rx, ry, color='black', linewidth=0.5)  # Тонкий контур комнаты
#
#         # Номер квартиры
#         apartment_centroid = polygon.centroid
#         ax.text(
#             apartment_centroid.x, apartment_centroid.y,
#             str(apartment_number),
#             color='black', fontsize=8, ha='center', va='center', weight='bold'
#         )
#         apartment_number += 1  # Увеличиваем номер квартиры
#
#     # Добавляем контур секции
#     cx, cy = section.polygon.exterior.xy
#     ax.plot(cx, cy, color='black', linewidth=2)  # Контур секции


# Построение графиков для каждой секции
# figure_list = []
# for building_index, building in enumerate(territory.buildings):
#     for floor_index, floor in enumerate(building.floors):
#         fig, ax = plt.subplots(figsize=(8, 8))
#         title = f"Здание {building_index + 1}, Этаж {floor_index + 1}"
#         plot_section(ax, title)
#         figure_list.append(fig)
def plot_floor(ax, floor, title):
    """Рисует весь этаж с секциями и квартирами."""
    ax.set_title(title)
    ax.set_aspect('equal', adjustable='box')
    apartment_number = 1  # Начальный номер квартиры
    for section in floor.sections:
        for apartment in section.apartments:
            # Контур квартиры
            polygon = Polygon(apartment.points)
            x, y = polygon.exterior.xy
            ax.plot(x, y, color='black', linewidth=2)  # Жирный контур квартиры

            # Рисуем комнаты внутри квартиры
            for room in apartment.rooms:
                room_polygon = Polygon(room.points)
                color = apartment_colors.get(apartment.type, 'gray')  # Цвет комнаты зависит от типа квартиры
                rx, ry = room_polygon.exterior.xy
                ax.fill(rx, ry, color=color, alpha=0.6)  # Заливка комнаты
                ax.plot(rx, ry, color='black', linewidth=0.5)  # Тонкий контур комнаты

            # Номер квартиры
            apartment_centroid = polygon.centroid
            ax.text(
                apartment_centroid.x, apartment_centroid.y,
                str(apartment_number),
                color='black', fontsize=8, ha='center', va='center', weight='bold'
            )
            apartment_number += 1  # Увеличиваем номер квартиры

        # Добавляем контур секции
        cx, cy = section.polygon.exterior.xy
        ax.plot(cx, cy, color='black', linewidth=2)  # Контур секции


# Построение графиков для каждого этажа
figure_list = []
for building_index, building in enumerate(territory.buildings):
    for floor_index, floor in enumerate(building.floors):
        fig, ax = plt.subplots(figsize=(8, 8))
        title = f"Здание {building_index + 1}, Этаж {floor_index + 1}"
        plot_floor(ax, floor, title)  # Передаём floor и title
        figure_list.append(fig)

# Показ всех графиков одновременно
plt.show()

