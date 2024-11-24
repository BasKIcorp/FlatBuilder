from Classes.Geometry.GeometricFigure import GeometricFigure
from Classes.Geometry.Territory.Apartment.Room import Room
from Classes.Geometry.Territory.Apartment.WetArea import WetArea
from Classes.Geometry.Territory.Apartment.Balcony import Balcony

from typing import List, Tuple
import random
import time
from shapely.geometry import Polygon, MultiPolygon
from shapely.ops import unary_union
import math


# Класс для квартиры, содержащей комнаты, мокрые зоны и балконы
class Apartment(GeometricFigure):
    def __init__(self, points: List[Tuple[float, float]],
                 apt_type: str, rooms: List['Room'] = None,
                 wet_areas: List['WetArea'] = None,
                 balconies: List['Balcony'] = None,
                 cell_size: float = 1.0):
        super().__init__(points)
        self.starting_corner_cells = None
        self.type = apt_type  # Тип квартиры
        self.area = self.polygon.area  # Площадь квартиры, вычисленная из геометрии
        self.rooms = rooms if rooms is not None else []  # Список комнат в квартире
        self.wet_areas = wet_areas if wet_areas is not None else []  # Список мокрых зон в квартире
        self.balconies = balconies if balconies is not None else []  # Список балконов в квартире
        self.cell_size = cell_size
        room_table = self.get_room_types_by_apartment_type(self.type)
        self.total_rooms = sum(count for room_type, count in room_table)

    def generate_apartment_planning(self):
        self.cells  = None
        self.check_and_create_cell_grid(cell_size=1)
        self.rooms = []
        room_table = self.get_room_types_by_apartment_type(self.type)
        self.starting_corner_cells = [cell for cell in self.cells if cell["is_corner"]]
        remaining_cells = [cell for cell in self.cells if not cell['assigned']]  # Все доступные ячейки
        room_number = 0

        # Распределение комнат, учитывая последнее условие
        for index, (room_type, count) in enumerate(room_table):
            for _ in range(count):
                min_cells, max_cells = self._get_rooms_cell_range(room_table, cell_size=self.cell_size)

                # Выделяем ячейки для комнаты
                room_cells = self._allocate_room_cells(remaining_cells, min_cells, max_cells)
                self._update_cell_properties(room_cells)

                room_polygon = unary_union([cell['polygon'] for cell in room_cells])

                if isinstance(room_polygon, Polygon):
                    points = list(room_polygon.exterior.coords)
                elif isinstance(room_polygon, MultiPolygon):
                    points = list(room_polygon.geoms[0].exterior.coords)
                else:
                    continue

                # Создаем объект Room с соответствующим типом
                room = Room(points=points, room_type=room_type)
                room.cells = room_cells
                self.rooms.append(room)


        # Добавить не назначенные клетки к ближайшей комнате
        # self._assign_remaining_cells_to_rooms(remaining_cells)

    # def _assign_remaining_cells_to_rooms(self, remaining_cells):
    #     """Добавляет не назначенные клетки к ближайшей комнате."""
    #     for cell in remaining_cells:
    #         if not cell['assigned']:
    #             # Найдем ближайшую комнату
    #             closest_room = None
    #             closest_distance = float('inf')
    #
    #             for room in self.rooms:
    #                 distance = room.polygon.distance(cell['polygon'])  # Используем расстояние до полигона комнаты
    #                 if distance < closest_distance:
    #                     closest_distance = distance
    #                     closest_room = room
    #
    #             if closest_room:
    #                 closest_room.cells.append(cell)  # Добавляем клетку в ближайшую комнату
    #                 closest_room.polygon = unary_union(
    #                     [closest_room.polygon, cell['polygon']])  # Обновляем полигон комнаты
    #                 # Обновляем points для передачи в room
    #                 if isinstance(closest_room.polygon, Polygon):
    #                     closest_room.points = list(closest_room.polygon.exterior.coords)
    #                 elif isinstance(closest_room.polygon, MultiPolygon):
    #                     closest_room.points = list(closest_room.polygon.geoms[0].exterior.coords)
    #                 cell['assigned'] = True  # Помечаем клетку как назначенную

    def get_room_types_by_apartment_type(self, apt_type: str):
        """Возвращает таблицу комнат в зависимости от типа квартиры."""
        room_table = []

        if apt_type == 'studio':
            room_table = [('wet_area', 1), ('bedroom', 1)]

        elif apt_type == '1 room':
            room_table = [('wet_area', 1), ('bedroom', 1), ('kitchen', 1), ('hall', 1)]

        elif apt_type == '2 room':
            room_table = [('wet_area', 1), ('bedroom', 1), ('kitchen', 1), ('hall', 1), ('living room', 1)]

        elif apt_type == '3 room':
            room_table = [('wet_area', 1), ('bedroom', 2), ('kitchen', 1), ('hall', 1), ('living room', 1)]

        elif apt_type == '4 room':
            room_table = [('wet_area', 1), ('bedroom', 3), ('kitchen', 1), ('hall', 1), ('living room', 1)]

        return room_table

    def _allocate_room_cells(self, remaining_cells, min_cells, max_cells):
        """Выделяет ячейки для одной комнаты, гарантируя, что все ячейки будут заполнены."""
        room_cells = []
        visited_cells = set()
        room_cell_count = max_cells
        if self.starting_corner_cells and len(self.starting_corner_cells) >= 1:
            start_cell = self.starting_corner_cells.pop()
        else:
            start_cell = random.choice(remaining_cells)
        queue = [start_cell]

        while queue and len(room_cells) < room_cell_count:
            current_cell = queue.pop(0)
            if current_cell['assigned']:
                continue
            visited_cells.add(current_cell['id'])
            room_cells.append(current_cell)

            current_cell['assigned'] = True

            # Получаем не назначенные соседние клетки
            neighbors = [neighbor for neighbor in current_cell['neighbors'] if not neighbor['assigned']]

            # Сортируем соседей по убыванию количества их свободных соседей
            neighbors_sorted = sorted(
                neighbors,
                key=lambda cell: len([n for n in cell['neighbors'] if not n['assigned']]),
                reverse=True
            )

            # Добавляем отсортированных соседей в очередь
            queue.extend(neighbors_sorted)
        return room_cells

    def _update_cell_properties(self, room_cells):
        """Updates the properties of cells based on the allocated apartment cells."""
        for cell in room_cells:
            if cell['on_perimeter']:
                perimeter_neighbors_for_new_corner = [neighbor for neighbor in cell['neighbors'] if
                                                      neighbor['assigned'] == False and neighbor['on_perimeter']]
                if len(perimeter_neighbors_for_new_corner) > 0:
                    for cell_for_new_corner in perimeter_neighbors_for_new_corner:
                        cell_for_new_corner['is_corner'] = True  # Reset is_corner before checking
                        self.starting_corner_cells.append(cell_for_new_corner)

    def _get_rooms_cell_range(self, room_table, cell_size):
        """Определяет минимальное и максимальное количество ячеек для комнаты на основе диапазона площади."""
        cell_area = cell_size ** 2  # Площадь одной ячейки
        total_rooms = sum(count for room_type, count in room_table)
        min_cells = math.ceil((self.area / total_rooms))
        max_cells = math.ceil((self.area / total_rooms))
        return min_cells, max_cells