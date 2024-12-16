import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from shapely.geometry import Polygon, LineString
from Classes.Geometry.Territory.Building.Floor.Section import Section

# Таблица квартир (как и прежде)
apartment_table = {
    'studio': {
        'area_range': (30, 45),
        'percent': 20,
        'number': 1
    },
    '1 room': {
        'area_range': (40, 60),
        'percent': 20,
        'number': 1
    },
    '2 room': {
        'area_range': (60, 90),
        'percent': 20,
        'number': 1
    },
    '3 room': {
        'area_range': (80, 120),
        'percent': 20,
        'number': 1
    },
    '4 room': {
        'area_range': (100, 140),
        'percent': 20,
        'number': 1
    },
}

# Цвета для отображения комнат
room_colors = {
    'kitchen': '#FF9999',
    'bathroom': '#99FF99',
    'hall': '#9999FF',
    'living room': '#FFCC99',
    'bedroom': '#CC99FF',
}

def plot_section(ax, apartments, room_colors, section_polygon):
    """Отображает квартиры, комнаты и клетки в секции."""
    # Контур секции
    section_boundary = Polygon(section_polygon)
    x, y = section_boundary.exterior.xy
    ax.plot(x, y, color='black', linewidth=2)

    # Отображение квартир
    for apartment in apartments:
        # Контур квартиры
        apartment_boundary = section_boundary.intersection(apartment.polygon)
        if not apartment_boundary.is_empty:
            x, y = apartment_boundary.exterior.xy
            ax.plot(x, y, color='black', linewidth=2)

        # Отображаем комнаты внутри квартиры
        for room in apartment.rooms:
            room_boundary = section_boundary.intersection(room.polygon)
            if not room_boundary.is_empty:
                rx, ry = room_boundary.exterior.xy
                color = room_colors.get(room.type, 'gray')
                ax.fill(rx, ry, color=color, edgecolor='black', alpha=0.7)

        # Отображаем окна
        for window in apartment.windows:
            wx, wy = window.line.xy
            ax.plot(wx, wy, color='blue', linewidth=3)




def add_legend(ax, room_colors):
    """Добавление легенды с цветами и типами комнат."""
    legend_elements = [Line2D([0], [0], color=color, lw=4, label=room_type)
                       for room_type, color in room_colors.items()]
    ax.legend(handles=legend_elements, loc='upper right')

# Определим секцию с несколькими квартирами
section_polygon = [(0, 0), (30, 0), (30, 20), (0, 20)]


# Генерация нескольких квартир
section = Section(points=section_polygon, apartment_table=apartment_table, building_polygon=Polygon(section_polygon))
section.generate_section_planning()


# График для отображения секции
fig, ax = plt.subplots(figsize=(12, 6))
plot_section(ax, section.apartments, room_colors, section_polygon)
add_legend(ax, room_colors)
ax.set_title('Секция с квартирами разных типов')
ax.set_aspect('equal', 'box')
ax.set_xlim(-2, 35)
ax.set_ylim(-2, 35)
plt.show()