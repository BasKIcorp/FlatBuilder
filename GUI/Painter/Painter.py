from collections import defaultdict

from PyQt5.QtGui import QPolygonF, QBrush, QColor, QTransform, QPen, QPainter, QCursor
from PyQt5.QtWidgets import QGraphicsView, QGraphicsPolygonItem
from PyQt5.QtCore import Qt, QPointF, pyqtSignal, QPoint
import math
from threading import Thread

from shapely import MultiPoint

from Classes.Geometry.Territory.Building.Building import Building
from Classes.Geometry.Territory.Building.Elevator import Elevator
from Classes.Geometry.Territory.Building.Floor.Floor import Floor
from Classes.Geometry.Territory.Building.Stair import Stair
from Classes.Geometry.Territory.Territory import Territory
from GUI.Painter.RotationHandle import RotationHandle
from GUI.Painter.ElevatorRect import ElevatorRect
from GUI.Painter.MovablePoint import MovablePoint
from GUI.Painter.Outline import Outline
from GUI.Painter.StairsRect import StairsRect
from GUI.Threads.BuildingGenerator import BuildingGenerator


def calculate_polygon_area(polygon):
    n = len(polygon)
    if n < 3:
        return 0

    area = 0
    for i in range(n):
        x1, y1 = polygon[i].x(), polygon[i].y()
        x2, y2 = polygon[(i + 1) % n].x(), polygon[(i + 1) % n].y()
        area += x1 * y2 - y1 * x2

    return abs(area) / 2


def divide_into_sections(points):
    # Step 1: Create a list of edges and build an adjacency list
    edges = [(points[i], points[(i + 1) % len(points)]) for i in range(len(points))]
    adjacency = defaultdict(list)
    for p1, p2 in edges:
        adjacency[p1].append(p2)
        adjacency[p2].append(p1)

    # Step 2: Helper to traverse and extract a polygon
    def extract_polygon(start, visited_edges):
        polygon = []
        current = start
        previous = None

        while True:
            polygon.append(current)
            neighbors = adjacency[current]

            # Find the next point (exclude the previous one to avoid backtracking)
            next_point = None
            for neighbor in neighbors:
                if (current, neighbor) not in visited_edges and (neighbor, current) not in visited_edges:
                    next_point = neighbor
                    break

            if next_point is None:
                break  # No further point to visit, loop ends

            # Mark edge as visited
            visited_edges.add((current, next_point))
            visited_edges.add((next_point, current))

            previous = current
            current = next_point

            # If we loop back to the start, we close the polygon
            if current == start:
                break

        return polygon

    # Step 3: Traverse all points to extract polygons
    visited_edges = set()
    polygons = []

    for edge in edges:
        p1, p2 = edge
        if edge not in visited_edges and (p2, p1) not in visited_edges:
            polygon = extract_polygon(p1, visited_edges)
            if len(polygon) > 2:  # Valid polygon has at least 3 points
                polygons.append(polygon)
    return polygons


class Painter(QGraphicsView):
    apartmentsGenerated = pyqtSignal()

    def __init__(self, scene):
        super().__init__()
        self.scene = scene
        self.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        self.setScene(self.scene)
        self.all_points = []
        self.points = []
        self.radius = 0.5
        self.point_id_counter = 1
        self.zoom_factor = 1.15
        self.default_zoom = 8.0
        self.polygon = None
        self.polygons = {}
        self.interactive = True
        self.setSceneRect(-1000, -1000, 2000, 2000)
        self.setDragMode(QGraphicsView.NoDrag)
        self.setMouseTracking(True)
        self._is_panning = False
        self.sections = []
        self.rooms = []
        self.internal_edges = []
        self.internal_edge = None
        self.floor_figures = []

        self.preview_rect = None
        self.rect_width = 0
        self.rect_height = 0

        self._start_pos = QPoint()
        self.stairs = []
        self.elevators = []
        self.mode = None
        self.setTransform(QTransform().scale(self.default_zoom, self.default_zoom))

        self.scene.selectionChanged.connect(self.on_selection_changed)

        self.preview_point = None

    def set_preview_rectangle(self, width, height, mode):
        cursor_pos = QCursor.pos()  # Получаем позицию курсора в глобальных координатах
        scene_pos = self.mapToScene(self.mapFromGlobal(cursor_pos))  # Преобразуем в координаты сцены

        if self.preview_point:
            self.scene.removeItem(self.preview_point)
        if self.preview_rect:
            self.scene.removeItem(self.preview_rect)

        self.rect_width = width
        self.rect_height = height

        self.preview_rect = self.scene.addRect(0, 0, width, height)
        self.preview_rect.setPos(scene_pos - QPointF(self.rect_width / 2, self.rect_height / 2))
        self.mode = mode
        self.preview_rect.setPen(QPen(Qt.DashLine))  # Dashed line for preview

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            self._is_panning = True
            self._start_pos = event.pos()
            self.setCursor(Qt.ClosedHandCursor)
            event.accept()
        if self.interactive:
            if event.button() == Qt.LeftButton:
                item = self.itemAt(event.pos())
                if self.preview_point:
                    self.scene.removeItem(self.preview_point)
                    scene_pos = self.mapToScene(event.pos())
                    self.add_point(scene_pos.x(), scene_pos.y())
                    self.update_shape()
                    self.preview_point = None
                elif self.preview_rect:
                    rect_pos = self.preview_rect.pos()
                    if self.mode == "elevator":
                        rect = ElevatorRect(rect_pos.x(), rect_pos.y(), self.rect_width, self.rect_height)
                        self.elevators.append(rect)
                    elif self.mode == "stairs":
                        rect = StairsRect(rect_pos.x(), rect_pos.y(), self.rect_width, self.rect_height)
                        self.stairs.append(rect)
                    self.scene.addItem(rect)
                    self.scene.removeItem(self.preview_rect)
                    self.preview_rect = None

                elif isinstance(item, MovablePoint):
                    self.polygon = item.parent_polygon
                    self.points = self.polygons.get(self.polygon)
                    super().mousePressEvent(event)
                elif isinstance(item, Outline):
                    self.polygon = item
                    self.points = self.polygons.get(self.polygon)
                    super().mousePressEvent(event)
                else:
                    super().mousePressEvent(event)
        else:
            pass

    def mouseMoveEvent(self, event):
        if self._is_panning:
            delta = event.pos() - self._start_pos
            self._start_pos = event.pos()
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
            event.accept()
        if self.interactive:
            if self.preview_rect:
                mouse_pos = self.mapToScene(event.pos())
                self.preview_rect.setPos(mouse_pos - QPointF(self.rect_width / 2, self.rect_height / 2))
            elif self.preview_point:
                mouse_pos = self.mapToScene(event.pos())
                self.preview_point.setPos(mouse_pos)
            super().mouseMoveEvent(event)
        else:
            pass

    def on_selection_changed(self):
        selected_items = self.scene.selectedItems()  # Get all selected items
        for child in self.scene.items():
            if isinstance(child, RotationHandle):
                self.scene.removeItem(child)
        for item in selected_items:
            if isinstance(item, ElevatorRect) or isinstance(item, StairsRect):
                handle = RotationHandle(item)  # Handle the rotation of the selected item
                item.handle = handle
                self.scene.addItem(handle)
                handle.update_position()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.RightButton:
            self._is_panning = False
            self.setCursor(Qt.ArrowCursor)
            event.accept()
        if self.interactive:
            super().mouseReleaseEvent(event)
        else:
            pass

    def wheelEvent(self, event):
        if event.angleDelta().y() > 0:
            self.scale(self.zoom_factor, self.zoom_factor)
        else:
            self.scale(1 / self.zoom_factor, 1 / self.zoom_factor)

    def add_preview_point(self):
        cursor_pos = QCursor.pos()  # Получаем позицию курсора в глобальных координатах
        scene_pos = self.mapToScene(self.mapFromGlobal(cursor_pos))  # Преобразуем в координаты сцены

        x, y = scene_pos.x(), scene_pos.y()
        self.preview_point = MovablePoint(x, y, self.radius, self.point_id_counter, self.polygon, self, preview=True)
        self.scene.addItem(self.preview_point)

    def add_point(self, x, y):
        point = MovablePoint(x, y, self.radius, self.point_id_counter, self.polygon, self)
        self.point_id_counter += 1
        self.scene.addItem(point)
        self.points.append(point)

    def add_building(self):
        self.all_points.append(self.points)
        self.polygons.update({self.polygon: self.points})
        self.points = []
        self.polygon = None
        self.add_preview_point()

    def update_shape(self):
        center = {'x': 0, 'y': 0}

        for point in self.points:
            center['x'] += point.get_position()[0] / len(self.points)
            center['y'] += point.get_position()[1] / len(self.points)

        def clockwise_angle(point):
            angle = math.atan2(point.get_position()[1] - center["y"], point.get_position()[0] - center["x"])
            distance = math.sqrt(
                (point.get_position()[0] - center["x"]) ** 2 + (point.get_position()[1] - center["y"]) ** 2)
            return angle, distance

        self.points.sort(key=clockwise_angle)
        if self.polygon is None:
            self.polygon = Outline(self.points)
            self.scene.addItem(self.polygon)
            self.polygons.update({self.polygon: self.points})
        else:
            self.polygon.updatePolygon()
            self.polygon.update_all_edge_lengths()
        for handle in self.points:
            handle.parent_polygon = self.polygon

    def keyPressEvent(self, event):
        if self.interactive:
            if event.key() == Qt.Key_Delete and self.scene.selectedItems():
                for item in self.scene.selectedItems():
                    if isinstance(item, MovablePoint):
                        self.points.remove(item)
                        self.scene.removeItem(item)
                    if isinstance(item, ElevatorRect):
                        self.elevators.remove(item)
                        self.scene.removeItem(item)
                    if isinstance(item, StairsRect):
                        self.stairs.remove(item)
                        self.scene.removeItem(item)

                self.update_shape()
        else:
            pass

    def fillApartments(self, apartment_table, num_floors):
        self.floors = []
        self.all_points.append(self.points)
        self.polygons.update({self.polygon: self.points})
        territory_points = []
        points_for_sections = []
        building = []
        buildings = []
        for points in self.all_points:
            for point in points:
                territory_points.append((int(point.get_position()[0]), int(point.get_position()[1])))
                building.append((int(point.get_position()[0]), int(point.get_position()[1])))
                self.scene.removeItem(point)
                points_for_sections.append((int(point.get_position()[0]), int(point.get_position()[1])))
            buildings.append(building)
        sections = divide_into_sections(points_for_sections)

        for polygon in self.polygons.keys():
            polygon.delete_edge_lengths()
        elevators = []
        stairs = []
        for stair in self.stairs:
            stair_object = [(stair.rect.sceneBoundingRect().topLeft().x(), stair.rect.sceneBoundingRect().topLeft().y()),
                 (stair.rect.sceneBoundingRect().bottomRight().x(), stair.rect.sceneBoundingRect().topLeft().y()),
                 (stair.rect.sceneBoundingRect().topLeft().x(), stair.rect.sceneBoundingRect().bottomRight().y()),
                 (stair.rect.sceneBoundingRect().bottomRight().x(), stair.rect.sceneBoundingRect().bottomRight().x())]
            stairs.append(stair_object)

        for elevator in self.elevators:
            elevator_object = [(elevator.rect.sceneBoundingRect().topLeft().x(), elevator.rect.sceneBoundingRect().topLeft().y()),
                 (elevator.rect.sceneBoundingRect().bottomRight().x(), elevator.rect.sceneBoundingRect().topLeft().y()),
                 (elevator.rect.sceneBoundingRect().topLeft().x(), elevator.rect.sceneBoundingRect().bottomRight().y()),
                 (elevator.rect.sceneBoundingRect().bottomRight().x(), elevator.rect.sceneBoundingRect().bottomRight().x())]
            elevators.append(elevator_object)

        if not stairs:
            stairs = [[]]
        if not elevators:
            elevators = [[]]

        territory = Territory(points=[(-100, -100), (100, -100), (100, 100), (-100, 100)], building_points=buildings, sections_coords=sections,
                              num_floors=num_floors, apartment_table=apartment_table,
                              elevators_coords=elevators, stairs_coords=stairs)

        self.worker = BuildingGenerator(territory)
        self.worker_thread = Thread(target=self.worker.run)
        self.worker.finished.connect(self.onApartmentsGenerated)
        self.worker_thread.start()

        for i in range(1, num_floors + 1):
            for building in territory.buildings:
                for floor in building.floors:
                    self.floors.append(floor)



    def onApartmentsGenerated(self, floor):
        # Цвета для разных типов квартир
        room_colors = {
            'wet_area': 'red',
            'living_room': 'orange',
            'bedroom': 'green',
            'hall': 'blue',
            'kitchen': 'purple',
            'toilet': 'pink'  # Если вам нужно добавить больше типов
        }
        apt_colors = {
            'studio': '#fa6b6b',
            '1 room': '#6dd170',
            '2 room': '#6db8d1',
            '3 room': '#ed975a',
            '4 room': '#ba7ed9'
        }
        # Добавляем квартиры на сцену
        for section in floor.sections:
            for apt in section.apartments:
                poly = apt.polygon
                x, y = poly.exterior.xy
                poly_points = [QPointF(x[i], y[i]) for i in range(len(x))]
                polygon = QPolygonF(poly_points)
                area = calculate_polygon_area(polygon)
                filled_shape = QGraphicsPolygonItem(polygon)
                filled_shape.setPen(QPen(Qt.black, 0.1))
                filled_shape.setBrush(QBrush(QColor(apt_colors[apt.type])))
                filled_shape.setToolTip(f"Площадь: {area}м^2")
                self.scene.addItem(filled_shape)
                self.floor_figures.append(filled_shape)
                for room in apt.rooms:
                    x, y = room.polygon.exterior.xy
                    poly_points = [QPointF(x[i], y[i]) for i in range(len(x))]
                    polygon = QPolygonF(poly_points)
                    area = calculate_polygon_area(polygon)
                    filled_shape = QGraphicsPolygonItem(polygon)
                    filled_shape.setBrush(QBrush(QColor(room_colors.get(room.type, 'grey'))))
                    filled_shape.setToolTip(f"Площадь: {area}м^2")
                    filled_shape.setPen(QPen(Qt.black, 0.05))
                    self.rooms.append(filled_shape)

        self.apartmentsGenerated.emit()

    def show_floor(self, floor_num, show_rooms):
        room_colors = {
            'wet_area': 'red',
            'living_room': 'orange',
            'bedroom': 'green',
            'hall': 'blue',
            'kitchen': 'purple',
            'toilet': 'pink'  # Если вам нужно добавить больше типов
        }
        apt_colors = {
            'studio': '#fa6b6b',
            '1 room': '#6dd170',
            '2 room': '#6db8d1',
            '3 room': '#ed975a',
            '4 room': '#ba7ed9'
        }
        if self.floor_figures:
            for floor in self.floor_figures:
                self.scene.removeItem(floor)
        if self.rooms:
            for room in self.rooms:
                self.scene.removeItem(room)
        # Добавляем квартиры на сцену
        for section in self.floors[floor_num].sections:
            for apt in section.apartments:
                poly = apt.polygon
                x, y = poly.exterior.xy
                poly_points = [QPointF(x[i], y[i]) for i in range(len(x))]
                polygon = QPolygonF(poly_points)
                area = calculate_polygon_area(polygon)
                filled_shape = QGraphicsPolygonItem(polygon)
                filled_shape.setPen(QPen(Qt.black, 0.1))
                filled_shape.setBrush(QBrush(QColor(apt_colors[apt.type])))
                filled_shape.setToolTip(f"Площадь: {area}м^2")
                self.floor_figures.append(filled_shape)
                self.scene.addItem(filled_shape)
                for room in apt.rooms:
                    x, y = room.polygon.exterior.xy
                    poly_points = [QPointF(x[i], y[i]) for i in range(len(x))]
                    polygon = QPolygonF(poly_points)
                    area = calculate_polygon_area(polygon)
                    filled_shape = QGraphicsPolygonItem(polygon)
                    filled_shape.setToolTip(f"Площадь: {area}м^2")
                    filled_shape.setBrush(QBrush(QColor(room_colors.get(room.type, 'grey'))))
                    filled_shape.setPen(QPen(Qt.black, 0.05))
                    self.rooms.append(filled_shape)
                    if show_rooms:
                        self.scene.addItem(filled_shape)

        self.apartmentsGenerated.emit()
