import matplotlib.pyplot as plt
from Classes.Geometry.Territory.Building.Building import Building
from shapely.geometry import Polygon

# Исходные данные для полигона зданий
buildings_polygons = [
    [(0, 0), (0, 30), (35, 30), (35, 0)],
    [(0, 0), (30, 0), (30, 25), (20, 25), (20, 30), (0, 30)]
]
sections_polygons = [
    [[(0, 0), (0, 30), (35, 30), (35, 0)]],
    [[(0, 0), (30, 0), (30, 25), (20, 25), (20, 30), (0, 30)]]
]

# Параметры
num_floors = 1
elevators_coords = [[(15, 15), (15, 20), (20, 20), (20, 15)]]
apartment_table = {
    'studio': {'area_range': (30, 45), 'percent': 20, 'number': 1},
    '1 room': {'area_range': (40, 60), 'percent': 20, 'number': 3},
    '2 room': {'area_range': (60, 90), 'percent': 20, 'number': 2},
    '3 room': {'area_range': (80, 120), 'percent': 20, 'number': 1},
    '4 room': {'area_range': (100, 140), 'percent': 20, 'number': 2},
}

# Создание объектов зданий и генерация планов этажей
buildings = []
building = Building(
    points=buildings_polygons[0],
    sections=[buildings_polygons[0]],
    apartment_table=apartment_table,
    elevators_coords=elevators_coords,
    num_floors=num_floors
)
building.generate_floors()
buildings.append(building)
building = Building(
    points=buildings_polygons[1],
    sections=sections_polygons[1],
    apartment_table=apartment_table,
    elevators_coords=elevators_coords,
    num_floors=num_floors
)
building.generate_floors()
buildings.append(building)

# Цвета для разных типов комнат и квартир
apt_colors = {
    'studio': 'red',
    '1 room': 'green',
    '2 room': 'blue',
    '3 room': 'orange',
    '4 room': 'purple',
}

room_colors = {
    'wet_area': 'cyan',
    'bedroom': 'lightblue',
    'kitchen': 'lightgreen',
    'hall': 'lightyellow',
    'living room': 'lightpink',
}

# Визуализация: Этаж здания с лифтами, лестницами и комнатами
fig, axs = plt.subplots(2, 2, figsize=(15, 10))

# Верхний левый график: с комнатами
for ax, building in zip(axs[0], buildings):
    floor = building.floors[0]  # Поскольку у нас только один этаж

    # Отображение основного полигона этажа
    x, y = floor.polygon.exterior.xy
    ax.plot(x, y, color='black')

    # Отображение комнат в квартирах и добавление подписей
    for section in floor.sections:
        for apt in section.apartments:
            for room in apt.rooms:
                room_poly = room.polygon
                x, y = room_poly.exterior.xy
                ax.fill(x, y, alpha=0.5, facecolor=room_colors[room.type], edgecolor='black',
                        label=room.type.capitalize())
                # Отображаем название комнаты
                ax.text(room_poly.centroid.x, room_poly.centroid.y, room.type.capitalize(), fontsize=8, ha='center')

    # Настройка графика
    ax.set_xlim(floor.polygon.bounds[0] - 10, floor.polygon.bounds[2] + 10)
    ax.set_ylim(floor.polygon.bounds[1] - 10, floor.polygon.bounds[3] + 10)
    ax.set_aspect('equal', adjustable='box')
    ax.set_title('Этаж здания с комнатами')

    # Создание легенды
    handles = [plt.Line2D([0], [0], marker='o', color='w', label=room_type.capitalize(),
                          markerfacecolor=color, markersize=10) for room_type, color in room_colors.items()]
    ax.legend(handles=handles)

# Нижний левый график: квартиры без комнат
for ax, building in zip(axs[1], buildings):
    floor = building.floors[0]  # Поскольку у нас только один этаж

    # Отображение основного полигона этажа
    x, y = floor.polygon.exterior.xy
    ax.plot(x, y, color='black')

    # Отображение квартир (цвета для разных типов) и добавление подписей
    for section in floor.sections:
        for apt in section.apartments:
            poly = apt.polygon
            x, y = poly.exterior.xy
            ax.fill(x, y, alpha=0.5, facecolor=apt_colors[apt.type], edgecolor='black', label=apt.type.capitalize())
            # Отображаем название квартиры
            ax.text(poly.centroid.x, poly.centroid.y, apt.type.capitalize(), fontsize=8, ha='center')

    # Настройка графика
    ax.set_xlim(floor.polygon.bounds[0] - 10, floor.polygon.bounds[2] + 10)
    ax.set_ylim(floor.polygon.bounds[1] - 10, floor.polygon.bounds[3] + 10)
    ax.set_aspect('equal', adjustable='box')
    ax.set_title('Этаж здания: квартиры без комнат')

    # Создание легенды
    handles = [plt.Line2D([0], [0], marker='o', color='w', label=apt_type.capitalize(),
                          markerfacecolor=color, markersize=10) for apt_type, color in apt_colors.items()]
    ax.legend(handles=handles)

plt.tight_layout()
plt.show()