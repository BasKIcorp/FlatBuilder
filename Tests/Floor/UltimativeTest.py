import matplotlib.pyplot as plt
from Classes.Geometry.Territory.Territory import Territory
from shapely.geometry import Polygon

# Исходные данные полигона территории и зданий
buildings_polygons = [
    [(10, 10), (35, 10), (35, 35), (75, 35), (75, 55), (10, 55)],
    [(100, 0), (100, 50), (80, 50), (80, 0)]
]
sections_polygons = [
    [(10, 10), (35, 10), (35, 55), (10, 55)], [(35, 55), (35, 35), (75, 35), (75, 55)],
    [(100, 0), (100, 25), (80, 25), (80, 0)], [(100, 25), (100, 50), (80, 50), (80, 25)]
]

# Параметры
num_floors = 6
apartment_table = {
    'studio': {'area_range': (30, 45), 'percent': 20, 'number': 24},
    '1 room': {'area_range': (40, 60), 'percent': 20, 'number': 36},
    '2 room': {'area_range': (60, 90), 'percent': 20, 'number': 24},
    '3 room': {'area_range': (80, 120), 'percent': 20, 'number': 14},
    '4 room': {'area_range': (80, 140), 'percent': 20, 'number': 24},
}
room_colors = {
    'kitchen': 'red',
    'bathroom': 'green',
    'hall': 'blue',
    'living room': 'orange',
    'bedroom': 'purple'
}

# Создание объекта территории
territory = Territory(buildings_polygons,
                      sections_polygons,
                      num_floors,
                      apartment_table)
territory.generate_building_plannings()


def plot_territory(ax):
    """Рисует территорию и здания с секциями."""
    for building_polygon in buildings_polygons:
        ax.plot(*zip(*building_polygon + [building_polygon[0]]), color='black', linewidth=3, label='Здание')
    for section_polygon in sections_polygons:
        ax.plot(*zip(*section_polygon + [section_polygon[0]]), color='gray', linewidth=1.5, linestyle='--', label='Секция')
    ax.set_title('Территория и здания с секциями')
    ax.set_aspect('equal', adjustable='box')


def plot_floor(ax, floor, title):
    """Рисует этаж со всеми квартирами и комнатами."""
    ax.plot(*floor.polygon.exterior.xy, color='black', linewidth=3, label='Этаж')
    for section in floor.sections:
        ax.plot(*section.polygon.exterior.xy, color='gray', linewidth=2)
        for apartment in section.apartments:
            ax.plot(*apartment.polygon.exterior.xy, color='blue', linewidth=1.5)
            for room in apartment.rooms:
                ax.fill(*room.polygon.exterior.xy, color=room_colors[room.type], edgecolor='black', linewidth=0.5)
    ax.set_title(title)
    ax.set_aspect('equal', adjustable='box')


# Окно 1: Территория и здания
fig1, ax1 = plt.subplots(figsize=(8, 8))
plot_territory(ax1)

# Окно 2: Первое здание - первый этаж
fig2, ax2 = plt.subplots(figsize=(8, 8))
plot_floor(ax2, territory.buildings[0].floors[0], 'Первый этаж первого здания')

# Окно 3: Первое здание - второй-последний этажи
fig3, ax3 = plt.subplots(figsize=(8, 8))
plot_floor(ax3, territory.buildings[0].floors[1], 'Второй-последний этажи первого здания')

# Окно 4: Второе здание - первый этаж
fig4, ax4 = plt.subplots(figsize=(8, 8))
plot_floor(ax4, territory.buildings[1].floors[0], 'Первый этаж второго здания')

# Окно 5: Второе здание - второй-последний этажи
fig5, ax5 = plt.subplots(figsize=(8, 8))
plot_floor(ax5, territory.buildings[1].floors[1], 'Второй-последний этажи второго здания')

# Печать выходной таблицы и ошибки
print("Выходная таблица квартир:")
print(territory.output_table)
print(f"Общая ошибка распределения: {territory.total_error:.2f}%")

plt.show()
