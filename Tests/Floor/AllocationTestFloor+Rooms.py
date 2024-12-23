import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from Classes.Geometry.Territory.Building.Floor.Floor import Floor

# Полигоны этажей
floor_polygons = [[(0, 0), (0, 30), (35, 30), (35, 0)]
    #[(0, 0), (0, 100), (100, 100), (100, 0), (70, 0), (70, 50), (30, 50), (30, 0)]
    # [(0, 0), (100, 0), (100, 80), (60, 80), (60, 100), (0, 100)],
    # [(0, 0), (0, 100), (100, 100), (100, 70), (60, 70), (60, 0)],
    # [(0, 0), (0, 100), (100, 100), (100, 0), (70, 0), (70, 50), (30, 50), (30, 0)]
]

# Таблица квартир
apartment_table = {
    'studio': {
        'area_range': (30, 45),  # Уменьшение площади для студий
        'percent': 20,
        'number': 2
    },
    '1 room': {
        'area_range': (40, 60),  # Площадь для однокомнатных квартир
        'percent': 20,
        'number': 3
    },
    '2 room': {
        'area_range': (60, 90),  # Площадь для двухкомнатных квартир
        'percent': 20,
        'number': 2
    },
    '3 room': {
        'area_range': (80, 120),  # Площадь для трехкомнатных квартир
        'percent': 20,
        'number': 1
    },
    '4 room': {
        'area_range': (100, 140),  # Площадь для четырехкомнатных квартир
        'percent': 20,
        'number': 2
    },
}

# Создаем фигуры для каждого этажа и генерируем план
floors = []
fig, axs = plt.subplots(nrows=1, ncols=len(floor_polygons) * 2, figsize=(15, 8))

# Цвета для разных типов комнат
room_colors = {
    'kitchen': 'red',
    'wet_area': 'green',
    'hall': 'blue',
    'living room': 'orange',
    'bedroom': 'purple'
}

# Генерация планов этажей и сохранение квартир
for i, points in enumerate(floor_polygons):
    floor = Floor(points)
    floor.set_elevator([(15, 15), (15, 20), (20, 20), (20, 15)])
    planning = floor.generatePlanning(apartment_table, max_iterations=15)
    floors.append(floor)


    # Отображение основного полигона этажа для комнат
    ax = axs[i]
    x, y = floor.polygon.exterior.xy
    ax.plot(x, y, color='black')

    # Отображение квартир с жирными контурами
    for apt in floor.apartments:
        poly = apt.polygon
        ax.plot(poly.exterior.xy[0], poly.exterior.xy[1], color='black', linewidth=2)  # Жирный контур квартиры
        for room in apt.rooms:
            x, y = room.polygon.exterior.xy
            ax.fill(x, y, alpha=0.5, facecolor=room_colors[room.type], edgecolor='black')
            room_centroid = room.polygon.centroid
            ax.text(room_centroid.x, room_centroid.y, room.type,
                    horizontalalignment='center', verticalalignment='center', fontsize=8)

    for elevator in floor.elevators:
        x, y = elevator.polygon.exterior.xy
        ax.fill(x, y, alpha=0.5, facecolor='yellow', edgecolor='black')  # Цвет для лифтов

    # Настройка графика для комнат
    ax.set_xlim(floor.polygon.bounds[0] - 10, floor.polygon.bounds[2] + 10)
    ax.set_ylim(floor.polygon.bounds[1] - 10, floor.polygon.bounds[3] + 10)
    ax.set_aspect('equal', adjustable='box')
    ax.set_title('Размещение комнат на этаже')

# Отображение квартир
for i, floor in enumerate(floors):
    ax = axs[len(floor_polygons) + i]
    x, y = floor.polygon.exterior.xy
    ax.plot(x, y, color='black')

    # Отображение квартир без комнат
    for apt in floor.apartments:
        poly = apt.polygon
        ax.fill(poly.exterior.xy[0], poly.exterior.xy[1], alpha=0.25, facecolor='grey', edgecolor='black')
        centroid = poly.centroid
        ax.text(centroid.x, centroid.y, apt.type, horizontalalignment='center', verticalalignment='center', fontsize=8)

    for elevator in floor.elevators:
        x, y = elevator.polygon.exterior.xy
        ax.fill(x, y, alpha=0.5, facecolor='yellow', edgecolor='black')  # Цвет для лифтов

    # Настройка графика для квартир
    ax.set_xlim(floor.polygon.bounds[0] - 10, floor.polygon.bounds[2] + 10)
    ax.set_ylim(floor.polygon.bounds[1] - 10, floor.polygon.bounds[3] + 10)
    ax.set_aspect('equal', adjustable='box')
    ax.set_title('Размещение квартир на этаже (без комнат)')

# Легенда
legend_elements = [
    Line2D([0], [0], marker='s', color='w', label=room_type,
           markerfacecolor=room_colors[room_type], markersize=10)
    for room_type in room_colors  # Правильная итерация
]

fig.legend(handles=legend_elements, loc='upper right')

plt.tight_layout()
plt.show()