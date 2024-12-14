import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from shapely.geometry.linestring import LineString
from Classes.Geometry.Territory.Building.Apartment.Apartment import Apartment
from Classes.Geometry.Territory.Building.Floor.Section import Section
from shapely.geometry import Polygon

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

# Изменены цвета на более мягкие
room_colors = {
    'kitchen': '#FF9999',  # Светло-красный
    'bathroom': '#99FF99',  # Светло-зеленый
    'hall': '#9999FF',      # Светло-синий
    'living room': '#FFCC99',  # Светло-оранжевый
    'bedroom': '#CC99FF',   # Светло-фиолетовый
}

def plot_section(ax, apartments, room_colors):
    """Отображает квартиры и комнаты в секции."""
    # Контур секции
    x, y = Polygon(apartment_polygon).exterior.xy
    ax.plot(x, y, color='black', linewidth=2)

    # Отображаем квартиры
    for apartment in apartments:
        # Контур квартиры
        x, y = apartment.polygon.exterior.xy
        ax.plot(x, y, color='black', linewidth=1)

        # Отображаем комнаты внутри квартиры
        for room in apartment.rooms:
            rx, ry = room.polygon.exterior.xy
            color = room_colors.get(room.type, 'gray')
            ax.fill(rx, ry, color=color, edgecolor='black', alpha=0.7)

def add_legend(ax, room_colors):
    """Добавление легенды с цветами и типами комнат."""
    legend_elements = [Line2D([0], [0], color=color, lw=4, label=room_type)
                       for room_type, color in room_colors.items()]
    ax.legend(handles=legend_elements, loc='upper right')


# Определим секцию с несколькими квартирами
apartment_polygon = [(0, 0), (9, 0), (9, 9), (0, 9)]
apartments = []
# Создаем секцию
apartment = Apartment(points=apartment_polygon, apt_type='3 room')
apartment.free_sides = [LineString([(0, 0), (9, 0)])]
apartment.building_perimeter_sides = [LineString([(9, 9), (0, 9)])]
apartment.generate_apartment_planning_method_1()
apartments.append(apartment)

# График для отображения секции
fig, ax = plt.subplots(figsize=(10, 5))
plot_section(ax, apartments, room_colors)
add_legend(ax, room_colors)  # Добавляем легенду
ax.set_title('Секция с квартирами разных типов')
ax.set_aspect('equal', 'box')
ax.set_xlim(-2, 15)
ax.set_ylim(-2, 15)
plt.show()