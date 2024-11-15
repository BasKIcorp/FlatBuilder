import sys

from PyQt5.QtGui import QPolygonF, QBrush, QColor, QTransform, QPen, QPainterPath
from PyQt5.QtWidgets import QGraphicsView, QGraphicsEllipseItem, QGraphicsLineItem, QGraphicsPolygonItem, \
    QGraphicsPathItem
from PyQt5.QtCore import Qt, QPointF, QObject, pyqtSignal
import math
from threading import Thread

from Classes.Geometry.Territory.Floor.Floor import Floor


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


class Worker(QObject):
    finished = pyqtSignal(object)

    def __init__(self, floor, apartment_table):
        super().__init__()
        self.floor = floor
        self.apartment_table = apartment_table

    def run(self):
        self.floor.generatePlanning(self.apartment_table, max_iterations=15)
        self.finished.emit(self.floor)  # Сигнал с результатом


class MovablePoint(QGraphicsEllipseItem):
    def __init__(self, x, y, radius, point_id, editor):
        super().__init__(-radius, -radius, 2 * radius, 2 * radius)
        self.setPos(x, y)
        self.setFlags(QGraphicsEllipseItem.ItemIsMovable | QGraphicsEllipseItem.ItemIsSelectable)
        self.setBrush(Qt.blue)
        self.point_id = point_id
        self.editor = editor
        self.connected_lines = []

    def get_position(self):
        pos = self.scenePos()
        return pos.x(), pos.y()

    def add_line(self, line):
        """ Add a reference to a line connected to this point. """
        self.connected_lines.append(line)

    def remove_line(self, line):
        """ Remove a line from this point's connected lines. """
        if line in self.connected_lines:
            self.connected_lines.remove(line)

    def mouseMoveEvent(self, event):
        """ Update connected lines in real-time as the point moves. """
        super().mouseMoveEvent(event)
        for line in self.connected_lines:
            line.update_line()


class ConnectionLine(QGraphicsLineItem):
    def __init__(self, start_point, end_point):
        super().__init__()
        self.start_point = start_point
        self.end_point = end_point
        start_point.add_line(self)
        end_point.add_line(self)
        self.update_line()

    def update_line(self):
        """ Update the line's position based on connected points. """
        start_x, start_y = self.start_point.get_position()
        end_x, end_y = self.end_point.get_position()
        self.setLine(start_x, start_y, end_x, end_y)


class Painter(QGraphicsView):
    def __init__(self, scene):
        super().__init__()
        self.scene = scene
        self.setScene(self.scene)
        self.points = []
        self.lines = []
        self.radius = 2
        self.point_id_counter = 1
        self.zoom_factor = 1.15
        self.default_zoom = 2.0
        self.hatched_polygon = None

        self.setSceneRect(-300, -300, 300, 300)

        self.setTransform(QTransform().scale(self.default_zoom, self.default_zoom))

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            clicked_item = self.itemAt(event.pos())
            if clicked_item is None:
                scene_pos = self.mapToScene(event.pos())
                self.add_point(scene_pos.x(), scene_pos.y())
                self.update_shape()
            else:
                super().mousePressEvent(event)

    def wheelEvent(self, event):
        if event.angleDelta().y() > 0:
            self.scale(self.zoom_factor, self.zoom_factor)
        else:
            self.scale(1 / self.zoom_factor, 1 / self.zoom_factor)

    def add_point(self, x, y):
        point = MovablePoint(x, y, self.radius, self.point_id_counter, self)
        self.point_id_counter += 1
        self.scene.addItem(point)
        self.points.append(point)

    def update_shape(self):
        # Calculate center and reorder points to form a polygon in clockwise order
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

        # Update lines connecting the points
        for line in self.lines:
            self.scene.removeItem(line)
        self.lines.clear()

        for i in range(len(self.points)):
            start_point = self.points[i]
            end_point = self.points[(i + 1) % len(self.points)]
            line = ConnectionLine(start_point, end_point)
            self.lines.append(line)
            self.scene.addItem(line)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Delete and self.scene.selectedItems():
            for item in self.scene.selectedItems():
                if isinstance(item, MovablePoint):
                    for line in item.connected_lines[:]:
                        self.scene.removeItem(line)
                        line.start_point.remove_line(line)
                        line.end_point.remove_line(line)

                        try:
                            self.lines.remove(line)
                        except ValueError:
                            pass

                    index = self.points.index(item)
                    prev_point = self.points[index - 1] if index > 0 else self.points[-1]
                    next_point = self.points[(index + 1) % len(self.points)]

                    self.points.remove(item)
                    self.scene.removeItem(item)

                    if len(self.points) > 1:
                        new_line = ConnectionLine(prev_point, next_point)
                        self.lines.append(new_line)
                        self.scene.addItem(new_line)

            self.update_shape()

    def fillApartments(self, apartment_table):
        floor_points = []
        for point in self.points:
            floor_points.append((int(point.get_position()[0]), int(point.get_position()[1])))
            self.scene.removeItem(point)
        floor = Floor(floor_points)

        # Создаем поток и передаем его в отдельный класс Worker для выполнения в фоне
        self.worker = Worker(floor, apartment_table)
        self.worker_thread = Thread(target=self.worker.run)

        # Соединяем сигнал завершения работы с функцией для обработки результата
        self.worker.finished.connect(self.onApartmentsGenerated)
        self.worker_thread.start()

    def onApartmentsGenerated(self, floor):
        # Цвета для разных типов квартир
        apt_colors = {
            'studio': '#fa6b6b',
            '1 room': '#6dd170',
            '2 room': '#6db8d1',
            '3 room': '#ed975a',
            '4 room': '#ba7ed9'
        }

        # Добавляем квартиры на сцену
        for apt in floor.apartments:
            poly = apt.polygon
            x, y = poly.exterior.xy
            poly_points = [QPointF(x[i], y[i]) for i in range(len(x))]
            polygon = QPolygonF(poly_points)

            filled_shape = QGraphicsPolygonItem(polygon)
            filled_shape.setBrush(QBrush(QColor(apt_colors[apt.type])))
            self.scene.addItem(filled_shape)
