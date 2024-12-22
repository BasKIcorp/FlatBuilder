from collections import defaultdict

from PyQt5.QtGui import QPolygonF, QBrush, QColor, QTransform, QPen, QPainter, QCursor
from PyQt5.QtWidgets import QGraphicsView, QGraphicsPolygonItem, QGraphicsEllipseItem, QGraphicsLineItem, \
    QGraphicsTextItem, QGraphicsRectItem, QWidget, QHBoxLayout, QLabel, QFrame, QGraphicsItem, QVBoxLayout, QSpacerItem, \
    QSizePolicy
from PyQt5.QtCore import Qt, QPointF, pyqtSignal, QPoint, QLineF, QLine, QRectF
import math
from threading import Thread

from shapely import Polygon, LineString
from shapely.ops import split

from Classes.Geometry.Territory.Territory import Territory
from GUI.Painter.RotationHandle import RotationHandle
from GUI.Painter.ElevatorRect import ElevatorRect
from GUI.Painter.MovablePoint import MovablePoint
from GUI.Painter.Outline import Outline
from GUI.Painter.StairsRect import StairsRect
from GUI.Threads.BuildingGenerator import BuildingGenerator


def qpolygonf_to_shapely(qpolygonf):
    points = [(point.x(), point.y()) for point in qpolygonf]
    return Polygon(points)


def shapely_to_qpolygonf(shapely_polygon):
    return QPolygonF([QPointF(x, y) for x, y in shapely_polygon.exterior.coords])


def clip_polygon(smaller_qpolygonf, larger_qpolygonf):
    larger_polygon = qpolygonf_to_shapely(larger_qpolygonf)
    smaller_polygon = qpolygonf_to_shapely(smaller_qpolygonf)

    clipped_polygon = smaller_polygon.intersection(larger_polygon)

    if clipped_polygon.is_empty:
        return None
    return shapely_to_qpolygonf(clipped_polygon)


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


def cut_polygon(polygon, cuts):
    polygons = [polygon]  # Start with the original polygon

    for cut in cuts:
        new_polygons = []
        for poly in polygons:
            if poly.intersects(cut):
                # Split the current polygon with the cut line
                split_result = split(poly, cut)
                # Add each resulting piece to the new list
                new_polygons.extend(split_result.geoms)
            else:
                # If the polygon is unaffected by the cut, keep it as is
                new_polygons.append(poly)
        polygons = new_polygons  # Update polygons for the next cut

    # Convert polygons to lists of coordinates
    return polygons


class LegendWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: white; border: 1px solid black;")

        # Define colors and labels for the legend
        self.apt_colors = {
            'studio': '#fa6b6b',
            '1 room': '#6dd170',
            '2 room': '#6db8d1',
            '3 room': '#ed975a',
            '4 room': '#ba7ed9'
        }
        self.room_colors = {
            'kitchen': 'red',
            'bathroom': 'green',
            'hall': 'blue',
            'living room': 'orange',
            'bedroom': 'purple'
        }

        # Create a vertical layout for the legend
        self.layout = QVBoxLayout(self)

        self.apt_layout = QHBoxLayout(self)
        self.room_layout = QHBoxLayout(self)

        for label, color in self.apt_colors.items():
            legend_item_layout = QHBoxLayout(self)

            color_square = QLabel()
            color_square.setFixedSize(20, 20)  # Square size
            color_square.setStyleSheet(f"background-color: {color};")

            text_label = QLabel(label)
            text_label.setAlignment(Qt.AlignLeft)
            text_label.setStyleSheet("border: none; padding: 0px;")

            legend_item_layout.addWidget(color_square)
            legend_item_layout.addWidget(text_label)

            self.apt_layout.addLayout(legend_item_layout)

        for label, color in self.room_colors.items():
            legend_item_layout = QHBoxLayout(self)

            color_square = QLabel()
            color_square.setFixedSize(20, 20)
            color_square.setStyleSheet(f"background-color: {color};")

            text_label = QLabel(label)
            text_label.setAlignment(Qt.AlignLeft)
            text_label.setStyleSheet("border: none; padding: 0px;")

            legend_item_layout.addWidget(color_square)
            legend_item_layout.addWidget(text_label)
            legend_item_layout.addItem(QSpacerItem(30, 0))

            self.room_layout.addLayout(legend_item_layout)

        # Add both layouts to the main layout
        self.layout.addLayout(self.apt_layout)
        self.layout.addLayout(self.room_layout)

        # Set the stretch factor for the layouts
        self.layout.setStretch(0, 1)  # Give apt_layout normal space
        self.layout.setStretch(1, 2)  # Give room_layout more space

        self.setLayout(self.layout)

    def boundingRect(self):
        """Returns the bounding rectangle of the entire legend for proper positioning in the scene."""
        return QRectF(self.x_start, self.y_start, 100, len(self.legend_items) * self.spacing)

    def paint(self, painter, option, widget=None):
        """This function is not used for drawing in this case since the items are handled separately."""
        pass

    def setPos(self, x, y):
        """Override to move the entire legend together."""
        dx = x - self.x_start
        dy = y - self.y_start

        # Update position of the legend's rectangles and text items
        for idx, rect in enumerate(self.legend_rects):
            rect.setPos(self.x_start + dx, self.y_start + idx * self.spacing + dy)

        for idx, text in enumerate(self.legend_texts):
            text.setPos(self.x_start + 20 + dx, self.y_start + idx * self.spacing - 3 + dy)

        # Update the starting position for future translations
        self.x_start += dx
        self.y_start += dy


class Painter(QGraphicsView):
    apartmentsGenerated = pyqtSignal()

    def __init__(self, scene):
        super().__init__()
        self.scene = scene
        self.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        self.setScene(self.scene)
        self.setSceneRect(-1000, -1000, 2000, 2000)
        self.preview_rect = None
        self.rect_width = 0
        self.rect_height = 0
        self.setDragMode(QGraphicsView.NoDrag)
        self.setMouseTracking(True)

        self.all_points = []
        self.points = []
        self.radius = 0.5
        self.point_id_counter = 1
        self.zoom_factor = 1.15
        self.default_zoom = 8.0
        self.polygon = None
        self.polygons = {}
        self.interactive = True
        self._is_panning = False
        self.sections = []
        self.rooms = []
        self.internal_edges = []
        self.floors = []
        self.floor_figures = []
        self.cuts = []
        self._start_pos = QPoint()
        self.stairs = []
        self.elevators = []
        self.preview_point = None
        self.cutting_mode = False
        self.cut_first_point = None
        self.cut_second_point = None
        self.output_tables = None

        self.setTransform(QTransform().scale(self.default_zoom, self.default_zoom))
        self.scene.selectionChanged.connect(self.on_selection_changed)

        self.legend_widget = LegendWidget()

        self.legend_widget.setParent(self)  # Make the legend part of the view
        self.legend_widget.move(0, 25)
        self.legend_widget.setVisible(False)

    def reset(self):
        self.all_points = []
        self.points = []
        self.radius = 0.5
        self.point_id_counter = 1
        self.zoom_factor = 1.15
        self.default_zoom = 8.0
        self.polygon = None
        self.polygons = {}
        self.interactive = True
        self._is_panning = False
        self.sections = []
        self.rooms = []
        self.internal_edges = []
        self.floors = []
        self.floor_figures = []
        self.cuts = []
        self._start_pos = QPoint()
        self.stairs = []
        self.elevators = []
        self.preview_point = None
        self.cutting_mode = False
        self.cut_first_point = None
        self.cut_second_point = None

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
        selected_items = self.scene.selectedItems()
        if selected_items:
            item = selected_items[0]
            if isinstance(item, MovablePoint):
                if self.cutting_mode:
                    item.setFlag(QGraphicsEllipseItem.ItemIsMovable, False)
                    if self.cut_first_point:
                        self.cut_second_point = item
                        # Create the cut (line) between the two points
                        cut = QGraphicsLineItem(
                            QLineF(self.cut_first_point.scenePos(), self.cut_second_point.scenePos()))
                        cut.setPen(QPen(Qt.black, 0.3))
                        self.scene.addItem(cut)
                        self.cuts.append([(cut.line().x1(), cut.line().y1()), (cut.line().x2(), cut.line().y2())])

                        # Register the cut with both points
                        self.cut_first_point.add_cut(cut, self.cut_second_point)
                        self.cut_second_point.add_cut(cut, self.cut_first_point)

                        # Reset for the next cut
                        self.cut_first_point = None
                        self.cut_second_point = None
                        self.cutting_mode = False
                    else:
                        self.cut_first_point = item
                    item.setFlag(QGraphicsEllipseItem.ItemIsMovable, True)
            for child in self.scene.items():
                if isinstance(child, RotationHandle):
                    self.scene.removeItem(child)
            if isinstance(item, ElevatorRect) or isinstance(item, StairsRect):
                handle = RotationHandle(item)
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

    def add_section(self):
        self.cutting_mode = True

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
            print(self.polygon.polygon())

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
        if self.points:
            self.all_points.append(self.points)
            self.polygons.update({self.polygon: self.points})
        points_for_sections = []
        buildings = []
        sections = []
        for points in self.all_points:
            building = []
            for point in points:
                points_for_sections.append((int(point.get_position()[0]), int(point.get_position()[1])))
                building.append((int(point.get_position()[0]), int(point.get_position()[1])))
            buildings.append(building)
            if self.cuts:
                polygon = Polygon(building)
                cuts = []
                for cut in self.cuts:
                    cuts.append(LineString(cut))
                section_polygons = cut_polygon(polygon, cuts)
                for section_polygon in section_polygons:
                    section = []
                    x, y = section_polygon.exterior.xy
                    for i in range(len(x)):
                        section.append((x[i], y[i]))
                    sections.append(section)
        if not self.cuts:
            sections = buildings
        territory = Territory(building_points=buildings, sections_coords=sections,
                              num_floors=num_floors, apartment_table=apartment_table)

        self.worker = BuildingGenerator(territory)
        self.worker_thread = Thread(target=self.worker.run)
        self.worker.finished.connect(self.onApartmentsGenerated)
        self.worker_thread.start()
        self.points = []

    def onApartmentsGenerated(self, error, floors, messages, output_tables):
        # Цвета для разных типов квартир
        self.generator_error = error
        self.output_tables = output_tables
        if self.generator_error == "":
            if messages:
                self.generator_error = messages[0]
        if self.generator_error == "":
            for points in self.all_points:
                for point in points:
                    self.scene.removeItem(point)
            for polygon in self.polygons.keys():
                print(self.polygon)
                polygon.delete_edge_lengths()
            self.floors = floors
            room_colors = {
                'kitchen': 'red',
                'bathroom': 'green',
                'hall': 'blue',
                'living room': 'orange',
                'bedroom': 'purple'
            }
            apt_colors = {
                'studio': '#fa6b6b',
                '1 room': '#6dd170',
                '2 room': '#6db8d1',
                '3 room': '#ed975a',
                '4 room': '#ba7ed9'
            }
            # Добавляем квартиры на сцену
            for i in range(len(floors)):
                building = floors[i]
                floor = building[0]
                for section in floor.sections:
                    for apt in section.apartments:
                        poly = apt.polygon
                        x, y = poly.exterior.xy
                        poly_points = [QPointF(x[i], y[i]) for i in range(len(x))]
                        polygon = QPolygonF(poly_points)
                        outer_polygon = list(self.polygons.keys())[i].polygon()
                        polygon = clip_polygon(polygon, outer_polygon)
                        area = calculate_polygon_area(polygon)
                        filled_shape = QGraphicsPolygonItem(polygon)
                        filled_shape.setPen(QPen(Qt.black, 0.3))
                        filled_shape.setBrush(QBrush(QColor(apt_colors[apt.type])))
                        filled_shape.setToolTip(f"Площадь: {area}м^2")
                        self.scene.addItem(filled_shape)
                        self.floor_figures.append(filled_shape)
                        for room in apt.rooms:
                            x, y = room.polygon.exterior.xy
                            poly_points = [QPointF(x[i], y[i]) for i in range(len(x))]
                            polygon = QPolygonF(poly_points)
                            outer_polygon = list(self.polygons.keys())[i].polygon()
                            polygon = clip_polygon(polygon, outer_polygon)
                            area = calculate_polygon_area(polygon)
                            filled_shape = QGraphicsPolygonItem(polygon)
                            filled_shape.setBrush(QBrush(QColor(room_colors.get(room.type, 'grey'))))
                            filled_shape.setToolTip(f"Площадь: {area}м^2")
                            filled_shape.setPen(QPen(Qt.black, 0.05))
                            self.rooms.append(filled_shape)
            self.apartmentsGenerated.emit()
            self.legend_widget.setVisible(True)

    def show_floor(self, floor_num, show_rooms):
        room_colors = {
            'kitchen': 'red',
            'bathroom': 'green',
            'hall': 'blue',
            'living room': 'orange',
            'bedroom': 'purple'
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
        for i in range(len(self.floors)):
            building = self.floors[i]
            floor = building[floor_num]
            for section in floor.sections:
                for apt in section.apartments:
                    poly = apt.polygon
                    x, y = poly.exterior.xy
                    poly_points = [QPointF(x[i], y[i]) for i in range(len(x))]
                    polygon = QPolygonF(poly_points)
                    outer_polygon = list(self.polygons.keys())[i].polygon()
                    polygon = clip_polygon(polygon, outer_polygon)
                    area = calculate_polygon_area(polygon)
                    filled_shape = QGraphicsPolygonItem(polygon)
                    filled_shape.setPen(QPen(Qt.black, 0.3))
                    filled_shape.setBrush(QBrush(QColor(apt_colors[apt.type])))
                    filled_shape.setToolTip(f"Площадь: {area}м^2")
                    self.floor_figures.append(filled_shape)
                    self.scene.addItem(filled_shape)
                    for room in apt.rooms:
                        x, y = room.polygon.exterior.xy
                        poly_points = [QPointF(x[i], y[i]) for i in range(len(x))]
                        polygon = QPolygonF(poly_points)
                        outer_polygon = list(self.polygons.keys())[i].polygon()
                        polygon = clip_polygon(polygon, outer_polygon)
                        area = calculate_polygon_area(polygon)
                        filled_shape = QGraphicsPolygonItem(polygon)
                        filled_shape.setToolTip(f"Площадь: {area}м^2")
                        filled_shape.setBrush(QBrush(QColor(room_colors.get(room.type, 'grey'))))
                        filled_shape.setPen(QPen(Qt.black, 0.05))
                        self.rooms.append(filled_shape)
                        if show_rooms:
                            self.scene.addItem(filled_shape)
