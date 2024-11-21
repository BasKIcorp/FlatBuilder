import matplotlib.pyplot as plt
from shapely.geometry import Polygon
from matplotlib.patches import Polygon as MplPolygon
from matplotlib.lines import Line2D
from Classes.Geometry.Territory.Apartment.Apartment import Apartment

# Определяем полигоны квартир
# Определяем полигоны квартир с более реалистичными размерами
apartment_polygons = [
    # Студия, условные размеры: 25 м²
    [
        (0, 0), (5, 0), (5, 5), (0, 5)  # Площадь 25 м²
    ],

    # Однокомнатная квартира, условные размеры: 50 м²
    [
        (0, 0), (10, 0), (10, 5), (8, 5), (8, 7), (0, 7)  # Площадь ~50 м²
    ],

    # Двухкомнатная квартира, условные размеры: 70 м²
    [
        (0, 0), (10, 0), (10, 7), (5, 7), (5, 5), (0, 5)  # Площадь ~70 м²
    ],

    # Трехкомнатная квартира, условные размеры: 90 м²
    [
        (0, 0), (12, 0), (12, 8), (8, 8), (8, 5), (4, 5), (4, 2), (0, 2)  # Площадь ~90 м²
    ],

    # Четырехкомнатная квартира, условные размеры: 100 м²
    [
        (0, 0), (12, 0), (12, 10), (8, 10), (8, 6), (4, 6), (4, 2), (0, 2)  # Площадь ~100 м²
    ]
]



figures = []

# Создаем квартиры с разными типами
apartment_types = ['studio', '1 room', '2 room', '3 room', '4 room']
for points, apt_type in zip(apartment_polygons, apartment_types):
    apartment = Apartment(points, apt_type=apt_type, cell_size=1.0)
    planning = apartment.generate_apartment_planning()
    figures.append(apartment)

fig, axs = plt.subplots(nrows=1, ncols=len(figures), figsize=(15, 8))

# Цвета для разных типов комнат
room_colors = {
    'wet_area': 'red',
    'living_room': 'orange',
    'bedroom': 'green',
    'hall': 'blue',
    'kitchen': 'purple',
    'toilet': 'pink'  # Если вам нужно добавить больше типов
}

for ax, apartment in zip(axs, figures):
    # Отображение основного полигона квартиры
    x, y = apartment.polygon.exterior.xy
    ax.plot(x, y, color='black')

    # Отображение комнат
    for room in apartment.rooms:
        x, y = room.polygon.exterior.xy
        ax.fill(x, y, alpha=0.5, facecolor=room_colors.get(room.type, 'grey'), edgecolor='black')
        # Вычисляем центр полигона для размещения метки
        centroid = room.polygon.centroid
        ax.text(centroid.x, centroid.y, room.type, horizontalalignment='center', verticalalignment='center', fontsize=8)

    # Настройка графика
    ax.set_xlim(apartment.polygon.bounds[0] - 10, apartment.polygon.bounds[2] + 10)
    ax.set_ylim(apartment.polygon.bounds[1] - 10, apartment.polygon.bounds[3] + 10)
    ax.set_aspect('equal', adjustable='box')
    ax.set_title(f'Размещение комнат в {apartment.type}')

# Легенда
legend_elements = [Line2D([0], [0], marker='s', color='w', label=room_type,
                          markerfacecolor=room_colors[room_type], markersize=10)
                   for room_type in room_colors]
fig.legend(handles=legend_elements, loc='upper right')

plt.tight_layout()
plt.show()