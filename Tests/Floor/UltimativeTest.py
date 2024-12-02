import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from Classes.Geometry.Territory.Territory import Territory
from Classes.Geometry.Territory.Building.Building import Building
from Classes.Geometry.Territory.Building.Floor.Floor import Floor
from Classes.Geometry.Territory.Building.Floor.Section import Section
from shapely.geometry import Polygon

# Исходные данные полигона территории и зданий
territory_polygon = [(0, 0), (100, 0), (100, 100), (0, 100)]
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
elevators_coords = [[(15, 15), (18, 15), (18, 17), (15, 17)]]
stairs_coords = [[(90, 10), (88, 10), (88, 12), (90, 12)]]
apartment_table = {
    'studio': {'area_range': (30, 45), 'percent': 20, 'number': 24},
    '1 room': {'area_range': (40, 60), 'percent': 20, 'number': 36},
    '2 room': {'area_range': (60, 90), 'percent': 20, 'number': 24},
    '3 room': {'area_range': (80, 120), 'percent': 20, 'number': 12},
    '4 room': {'area_range': (80, 140), 'percent': 20, 'number': 24},
}
room_colors = {
    'kitchen': 'red',
    'wet_area': 'green',
    'hall': 'blue',
    'living room': 'orange',
    'bedroom': 'purple'
}

# Создание объекта территории
territory = Territory(territory_polygon,
                      buildings_polygons,
                      sections_polygons,
                      num_floors,
                      apartment_table,
                      elevators_coords,
                      stairs_coords)
territory.generate_building_plannings()

# Создание графиков
fig, axs = plt.subplots(3, 2, figsize=(15, 12))

# Первый график: территория и здания
ax = axs[0, 0]
x, y = territory_polygon[0]  # Обводим контур территории
ax.plot([p[0] for p in territory_polygon + [territory_polygon[0]]],
        [p[1] for p in territory_polygon + [territory_polygon[0]]],
        color='black', linewidth=5)  # Граница территории

for building_polygon in buildings_polygons:
    ax.plot([p[0] for p in building_polygon + [building_polygon[0]]],
            [p[1] for p in building_polygon + [building_polygon[0]]],
            color='black', linewidth=5)  # Контуры зданий

for building in territory.buildings:
    for floor in building.floors:
        for section in floor.sections:
            x, y = section.polygon.exterior.xy  # Укажите правильный способ получения секций
            ax.plot(x, y, color='black', linewidth=2.5)  # Контуры секций на здании

    # Отображение лифтов и лестниц из зданий
    for elevator in building.elevators:
        x, y = elevator.polygon.exterior.xy
        ax.fill(x, y, color='yellow', edgecolor='black', alpha=0.5)  # Лифты
    for stair in building.stairs:
        x, y = stair.polygon.exterior.xy
        ax.fill(x, y, color='pink', edgecolor='black', alpha=0.5)  # Лестницы

ax.set_title('Территория со зданиями')
ax.set_xlim(-10, 110)
ax.set_ylim(-10, 110)
ax.set_aspect('equal', adjustable='box')

# График для первого этажа первого здания
first_floor = territory.buildings[0].floors[0]
ax = axs[0, 1]
x, y = first_floor.polygon.exterior.xy
ax.plot(x, y, color='black', linewidth=5)  # Этаж
for section in first_floor.sections:
    x, y = section.polygon.exterior.xy
    ax.plot(x, y, color='black', linewidth=3)  # Секции на этаже
    if section.elevators:
        for elevator in section.elevators:
            x, y = elevator.polygon.exterior.xy
            ax.fill(x, y, color='yellow', edgecolor='black', alpha=0.5)  # Лифты
    if section.stairs:
        for stair in section.stairs:
            x, y = stair.polygon.exterior.xy
            ax.fill(x, y, color='pink', edgecolor='black', alpha=0.5)  # Лестницы
    for apartment in section.apartments:
        x, y = apartment.polygon.exterior.xy
        ax.plot(x, y, color='blue', linewidth=1.5)  # Квартиры
        for room in apartment.rooms:
            x, y = room.polygon.exterior.xy
            ax.fill(x, y, color=room_colors[room.type], edgecolor='black')  # Комнаты

ax.set_title('Первый этаж первого здания')
ax.set_xlim(first_floor.polygon.bounds[0] - 10, first_floor.polygon.bounds[2] + 10)
ax.set_ylim(first_floor.polygon.bounds[1] - 10, first_floor.polygon.bounds[3] + 10)
ax.set_aspect('equal', adjustable='box')

# График для второго-до-последнего этажа первого здания
second_to_last_floor = territory.buildings[0].floors[1]  # Пример для второго этажа
ax = axs[1, 0]
x, y = second_to_last_floor.polygon.exterior.xy
ax.plot(x, y, color='black', linewidth=5)  # Этаж
for section in second_to_last_floor.sections:
    x, y = section.polygon.exterior.xy
    ax.plot(x, y, color='black', linewidth=3)  # Секции на этаже
    if section.elevators:
        for elevator in section.elevators:
            x, y = elevator.polygon.exterior.xy
            ax.fill(x, y, color='yellow', edgecolor='black', alpha=0.5)  # Лифты
    if section.stairs:
        for stair in section.stairs:
            x, y = stair.polygon.exterior.xy
            ax.fill(x, y, color='pink', edgecolor='black', alpha=0.5)  # Лестницы
    for apartment in section.apartments:
        x, y = apartment.polygon.exterior.xy
        ax.plot(x, y, color='blue', linewidth=1.5)  # Квартиры
        for room in apartment.rooms:
            x, y = room.polygon.exterior.xy
            ax.fill(x, y, color=room_colors[room.type], edgecolor='black')  # Комнаты

ax.set_title('Второй-до-последнего этаж первого здания')
ax.set_xlim(second_to_last_floor.polygon.bounds[0] - 10, second_to_last_floor.polygon.bounds[2] + 10)
ax.set_ylim(second_to_last_floor.polygon.bounds[1] - 10, second_to_last_floor.polygon.bounds[3] + 10)
ax.set_aspect('equal', adjustable='box')

# График для первого этажа второго здания
first_floor_bldg_2 = territory.buildings[1].floors[0]
ax = axs[1, 1]
x, y = first_floor_bldg_2.polygon.exterior.xy
ax.plot(x, y, color='black', linewidth=5)  # Этаж
for section in first_floor_bldg_2.sections:
    x, y = section.polygon.exterior.xy
    ax.plot(x, y, color='black', linewidth=3)  # Секции на этаже
    if section.elevators:
        for elevator in section.elevators:
            x, y = elevator.polygon.exterior.xy
            ax.fill(x, y, color='yellow', edgecolor='black', alpha=0.5)  # Лифты
    if section.stairs:
        for stair in section.stairs:
            x, y = stair.polygon.exterior.xy
            ax.fill(x, y, color='pink', edgecolor='black', alpha=0.5)  # Лестницы
    for apartment in section.apartments:
        x, y = apartment.polygon.exterior.xy
        ax.plot(x, y, color='blue', linewidth=1.5)  # Квартиры
        for room in apartment.rooms:
            x, y = room.polygon.exterior.xy
            ax.fill(x, y, color=room_colors[room.type], edgecolor='black')  # Комнаты

ax.set_title('Первый этаж второго здания')
ax.set_xlim(first_floor_bldg_2.polygon.bounds[0] - 10, first_floor_bldg_2.polygon.bounds[2] + 10)
ax.set_ylim(first_floor_bldg_2.polygon.bounds[1] - 10, first_floor_bldg_2.polygon.bounds[3] + 10)
ax.set_aspect('equal', adjustable='box')

# График для второго-до-последнего этажа второго здания
second_to_last_floor_bldg_2 = territory.buildings[1].floors[1]  # Пример для второго этажа
ax = axs[2, 0]
x, y = second_to_last_floor_bldg_2.polygon.exterior.xy
ax.plot(x, y, color='black', linewidth=5)  # Этаж
for section in second_to_last_floor_bldg_2.sections:
    x, y = section.polygon.exterior.xy
    ax.plot(x, y, color='black', linewidth=3)  # Секции на этаже
    if section.elevators:
        for elevator in section.elevators:
            x, y = elevator.polygon.exterior.xy
            ax.fill(x, y, color='yellow', edgecolor='black', alpha=0.5)  # Лифты
    if section.stairs:
        for stair in section.stairs:
            x, y = stair.polygon.exterior.xy
            ax.fill(x, y, color='pink', edgecolor='black', alpha=0.5)  # Лестницы
    for apartment in section.apartments:
        x, y = apartment.polygon.exterior.xy
        ax.plot(x, y, color='blue', linewidth=1.5)  # Квартиры
        for room in apartment.rooms:
            x, y = room.polygon.exterior.xy
            ax.fill(x, y, color=room_colors[room.type], edgecolor='black')  # Комнаты

ax.set_title('Второй-до-последнего этаж второго здания')
ax.set_xlim(second_to_last_floor_bldg_2.polygon.bounds[0] - 10, second_to_last_floor_bldg_2.polygon.bounds[2] + 10)
ax.set_ylim(second_to_last_floor_bldg_2.polygon.bounds[1] - 10, second_to_last_floor_bldg_2.polygon.bounds[3] + 10)
ax.set_aspect('equal', adjustable='box')

plt.tight_layout()
plt.show()