from collections import defaultdict

from PyQt5.QtGui import QPolygonF, QBrush, QColor, QTransform, QPen, QPainter, QCursor, QFont
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

apt_colors = {
    'studio': '#fa6b6b',
    '1 room': '#6dd170',
    '2 room': '#6db8d1',
    '3 room': '#ed975a',
    '4 room': '#ba7ed9'
}
room_colors = {
    'kitchen': '#FF9999',
    'bathroom': '#99FF99',
    'hall': '#9999FF',
    'living room': '#FFCC99',
    'bedroom': '#CC99FF',
}


def qpolygonf_to_shapely(qpolygonf):
    points = [(point.x(), point.y()) for point in qpolygonf]
    return Polygon(points)


def shapely_to_qpolygonf(shapely_polygon):
    return QPolygonF([QPointF(x, y) for x, y in shapely_polygon.exterior.coords])


def clip_polygon(smaller_qpolygonf, larger_polygon):
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


class AptLegendWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: white; border: 1px solid black;")

        self.apt_layout = QHBoxLayout(self)  # Stack apartment items vertically

        # Populate apartment colors
        for label, color in apt_colors.items():
            legend_item_layout = QHBoxLayout()

            color_square = QLabel()
            color_square.setFixedSize(20, 20)
            color_square.setStyleSheet(f"background-color: {color};")

            text_label = QLabel(label)
            text_label.setAlignment(Qt.AlignLeft)
            text_label.setStyleSheet("border: none; padding: 0px;")

            legend_item_layout.addWidget(color_square)
            legend_item_layout.addWidget(text_label)

            self.apt_layout.addLayout(legend_item_layout)

        # Set the main layout
        self.setLayout(self.apt_layout)


class RoomLegendWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: white; border: 1px solid black;")
        self.room_layout = QHBoxLayout(self)  # Stack room items vertically

        for label, color in room_colors.items():
            legend_item_layout = QHBoxLayout()

            color_square = QLabel()
            color_square.setFixedSize(20, 20)
            color_square.setStyleSheet(f"background-color: {color};")

            text_label = QLabel(label)
            text_label.setAlignment(Qt.AlignLeft)
            text_label.setStyleSheet("border: none; padding: 0px;")

            legend_item_layout.addWidget(color_square)
            legend_item_layout.addWidget(text_label)

            self.room_layout.addLayout(legend_item_layout)

        # Set the main layout
        self.setLayout(self.room_layout)


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
        self.generator_error = None
        self.window_items = []
        self.apt_areas = []
        self.room_areas = []
        self.preview_point_1 = None
        self.preview_point_2 = None
        self.preview_point_3 = None
        self.preview_point_4 = None

        self.setTransform(QTransform().scale(self.default_zoom, self.default_zoom))
        self.scene.selectionChanged.connect(self.on_selection_changed)

        self.apt_legend_widget = AptLegendWidget()

        self.apt_legend_widget.setParent(self)  # Make the legend part of the view
        self.apt_legend_widget.move(0, 25)
        self.apt_legend_widget.setVisible(False)

        self.room_legend_widget = RoomLegendWidget()

        self.room_legend_widget.setParent(self)  # Make the legend part of the view
        self.room_legend_widget.move(0, 55)
        self.room_legend_widget.setVisible(False)

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
        self.preview_rect.setPen(QPen(Qt.DashLine))

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
        self.generator_error = None
        self.window_items = []
        self.apt_areas = []
        self.room_areas = []
        self.preview_point_1 = None
        self.preview_point_2 = None
        self.preview_point_3 = None
        self.preview_point_4 = None

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
                elif self.preview_point_1:
                    self.scene.removeItem(self.preview_point_1)
                    self.scene.removeItem(self.preview_point_2)
                    self.scene.removeItem(self.preview_point_3)
                    self.scene.removeItem(self.preview_point_4)
                    scene_pos = self.mapToScene(event.pos())
                    self.add_point(scene_pos.x(), scene_pos.y())
                    self.add_point(scene_pos.x() + 20, scene_pos.y())
                    self.add_point(scene_pos.x() + 20, scene_pos.y() + 20)
                    self.add_point(scene_pos.x(), scene_pos.y() + 20)
                    self.update_shape()
                    self.preview_point_1 = None
                    self.preview_point_2 = None
                    self.preview_point_3 = None
                    self.preview_point_4 = None
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
            elif self.preview_point_1:
                mouse_pos = self.mapToScene(event.pos())
                self.preview_point_1.setPos(mouse_pos)
                self.preview_point_2.setPos(mouse_pos.x() + 20, mouse_pos.y())
                self.preview_point_3.setPos(mouse_pos.x() + 20, mouse_pos.y() + 20)
                self.preview_point_4.setPos(mouse_pos.x(), mouse_pos.y() + 20)

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

    def add_preview_building(self):
        cursor_pos = QCursor.pos()  # Получаем позицию курсора в глобальных координатах
        scene_pos = self.mapToScene(self.mapFromGlobal(cursor_pos))  # Преобразуем в координаты сцены

        x, y = scene_pos.x(), scene_pos.y()
        self.preview_point_1 = MovablePoint(x, y, self.radius, self.point_id_counter, self.polygon, self, preview=True)
        self.preview_point_2 = MovablePoint(x + 20, y, self.radius, self.point_id_counter, self.polygon, self, preview=True)
        self.preview_point_3 = MovablePoint(x + 20, y + 20, self.radius, self.point_id_counter, self.polygon, self, preview=True)
        self.preview_point_4 = MovablePoint(x, y + 20, self.radius, self.point_id_counter, self.polygon, self, preview=True)
        self.scene.addItem(self.preview_point_1)
        self.scene.addItem(self.preview_point_2)
        self.scene.addItem(self.preview_point_3)
        self.scene.addItem(self.preview_point_4)

    def add_building(self):
        self.all_points.append(self.points)
        self.polygons.update({self.polygon: self.points})
        self.points = []
        self.polygon = None
        self.add_preview_building()

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
        self.sections = sections
        print(buildings)
        for section in sections:
            print("Секция: ", section)
        print(sections)
        territory = Territory(building_points=buildings, sections_coords=sections,
                              num_floors=num_floors, apartment_table=apartment_table)
        worker = BuildingGenerator(territory)
        worker_thread = Thread(target=worker.run)
        worker.finished.connect(self.onApartmentsGenerated)
        worker_thread.start()
        self.points = []

    def onApartmentsGenerated(self, error, floors, messages, output_tables):
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
            self.show_floor(0, False)
            self.apt_legend_widget.setVisible(True)
        self.apartmentsGenerated.emit()

    def show_floor(self, floor_num, show_rooms):
        if self.apt_areas:
            for area in self.apt_areas:
                self.scene.removeItem(area)
        if self.room_areas:
            for area in self.room_areas:
                self.scene.removeItem(area)
        if self.floor_figures:
            for floor in self.floor_figures:
                self.scene.removeItem(floor)
        if self.rooms:
            for room in self.rooms:
                self.scene.removeItem(room)
        # Добавляем квартиры на сцену
        if show_rooms:
            self.room_legend_widget.setVisible(True)
        else:
            self.room_legend_widget.setVisible(False)

        for i in range(len(self.floors)):
            building = self.floors[i]
            floor = building[floor_num]
            # print(floor.polygon.exterior)
            for section in floor.sections:
                print(section.polygon.exterior)
                for apt in section.apartments:
                    poly = apt.polygon
                    x, y = poly.exterior.xy
                    poly_points = [QPointF(x[i], y[i]) for i in range(len(x))]
                    polygon = QPolygonF(poly_points)
                    # outer_polygon = list(self.polygons.keys())[i].polygon()
                    polygon = clip_polygon(polygon, section.polygon)
                    area = calculate_polygon_area(polygon)
                    filled_shape = QGraphicsPolygonItem(polygon)
                    filled_shape.setToolTip(f"Площадь: {area}м^2")
                    filled_shape.setPen(QPen(Qt.black, 0.3))
                    filled_shape.setBrush(QBrush(QColor(apt_colors[apt.type])))
                    #
                    # shape = qpolygonf_to_shapely(QPolygonF(poly_points))
                    # centroid = shape.centroid
                    # centroid_x, centroid_y = centroid.x, centroid.y
                    # area = shape.area

                    self.floor_figures.append(filled_shape)
                    self.scene.addItem(filled_shape)
                    #
                    # area_text = QGraphicsTextItem(f"{area:.1f}")
                    # area_text.setScale(0.05)
                    # bounding_rect = area_text.boundingRect()
                    # scaled_width = bounding_rect.width() * area_text.scale()
                    # scaled_height = bounding_rect.height() * area_text.scale()
                    #
                    # centered_x = centroid_x - scaled_width / 2
                    # centered_y = centroid_y - scaled_height / 2
                    #
                    # area_text.setPos(centered_x, centered_y)
                    # area_text.setZValue(1)
                    # self.scene.addItem(area_text)
                    # self.apt_areas.append(area_text)

                    for item in self.window_items:
                        self.scene.removeItem(item)
                    self.window_items.clear()
                    for window in apt.windows:
                        window_linestring = window.line
                        x1, y1 = window_linestring.coords[0]
                        x2, y2 = window_linestring.coords[1]

                        gray_line = QGraphicsLineItem(QLineF(QPointF(x1, y1), QPointF(x2, y2)))
                        gray_line.setPen(QPen(Qt.lightGray, 0.3))
                        self.scene.addItem(gray_line)

                        self.window_items.append(gray_line)
                    for room in apt.rooms:
                        x, y = room.polygon.exterior.xy
                        poly_points = [QPointF(x[i], y[i]) for i in range(len(x))]
                        polygon = QPolygonF(poly_points)
                        # outer_polygon = list(self.polygons.keys())[i].polygon()
                        polygon = clip_polygon(polygon, section.polygon)
                        area = calculate_polygon_area(polygon)
                        filled_shape = QGraphicsPolygonItem(polygon)
                        filled_shape.setToolTip(f"Площадь: {area}м^2")
                        filled_shape.setBrush(QBrush(QColor(room_colors.get(room.type, 'grey'))))
                        filled_shape.setPen(QPen(Qt.black, 0.05))
                        self.rooms.append(filled_shape)

                        # shape = qpolygonf_to_shapely(QPolygonF(poly_points))
                        # centroid = shape.centroid
                        # centroid_x, centroid_y = centroid.x, centroid.y
                        # area = shape.area
                        #
                        # area_text = QGraphicsTextItem(f"{area:.1f}")
                        # area_text.setScale(0.05)
                        #
                        # bounding_rect = area_text.boundingRect()
                        # scaled_width = bounding_rect.width() * area_text.scale()
                        # scaled_height = bounding_rect.height() * area_text.scale()
                        #
                        # centered_x = centroid_x - scaled_width / 2
                        # centered_y = centroid_y - scaled_height / 2
                        #
                        # area_text.setPos(centered_x, centered_y)
                        # area_text.setZValue(1)
                        # self.room_areas.append(area_text)
                        if show_rooms:
                            self.scene.addItem(filled_shape)
                            if self.apt_areas:
                                for area in self.apt_areas:
                                    self.scene.removeItem(area)
                            # self.scene.addItem(area_text)

