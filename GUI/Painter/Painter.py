from PyQt5.QtGui import QPolygonF, QBrush, QColor, QTransform, QPen, QPainter
from PyQt5.QtWidgets import QGraphicsView, QGraphicsLineItem, QGraphicsPolygonItem, \
    QGraphicsRectItem
from PyQt5.QtCore import Qt, QPointF, pyqtSignal, QRectF, QPoint
import math
from threading import Thread

from Classes.Geometry.Territory.Floor.Floor import Floor
from GUI.Painter.MovablePoint import MovablePoint
from GUI.Painter.Outline import Outline
from GUI.Threads.FloorGenerator import FloorGenerator


class Painter(QGraphicsView):
    apartmentsGenerated = pyqtSignal()

    def __init__(self, scene):
        super().__init__()
        self.scene = scene
        self.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        self.setScene(self.scene)
        self.points = []
        self.radius = 2
        self.point_id_counter = 1
        self.zoom_factor = 1.15
        self.default_zoom = 2.0
        self.polygon = None
        self.interactive = True
        self.setSceneRect(-1000, -1000, 2000, 2000)
        self.setDragMode(QGraphicsView.NoDrag)
        self.setMouseTracking(True)
        self._is_panning = False
        self._start_pos = QPoint()
        self.setTransform(QTransform().scale(self.default_zoom, self.default_zoom))

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            self._is_panning = True
            self._start_pos = event.pos()
            self.setCursor(Qt.ClosedHandCursor)
            event.accept()
        if self.interactive:
            if event.button() == Qt.LeftButton:
                clicked_item = self.itemAt(event.pos())
                if clicked_item is None:
                    scene_pos = self.mapToScene(event.pos())
                    self.add_point(scene_pos.x(), scene_pos.y())
                    self.update_shape()
                else:
                    if self.polygon and (self.polygon.mode == "elevator" or self.polygon.mode == "stairs"):
                        scene_pos = self.mapToScene(event.pos())
                        self.polygon.startSelection(scene_pos)
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
            if self.polygon and self.polygon.is_selecting:
                self.polygon.updateSelection(self.mapToScene(event.pos()))

            super().mouseMoveEvent(event)
        else:
            pass

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.RightButton:
            self._is_panning = False
            self.setCursor(Qt.ArrowCursor)
            event.accept()
        if self.interactive:
            if self.polygon and (self.polygon.mode == "elevator" or self.polygon.mode == "stairs"):
                self.polygon.endSelection()

            super().mouseReleaseEvent(event)
        else:
            pass

    def wheelEvent(self, event):
        if event.angleDelta().y() > 0:
            self.scale(self.zoom_factor, self.zoom_factor)
        else:
            self.scale(1 / self.zoom_factor, 1 / self.zoom_factor)

    def add_point(self, x, y):
        point = MovablePoint(x, y, self.radius, self.point_id_counter, self.polygon, self)
        self.point_id_counter += 1
        self.scene.addItem(point)
        self.points.append(point)

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
        if len(self.points) == 3:
            self.polygon = Outline(self.points)
            self.scene.addItem(self.polygon)
        elif len(self.points) > 3:
            self.polygon.updatePolygon()
        for handle in self.points:
            handle.parent_polygon = self.polygon

    def keyPressEvent(self, event):
        if self.interactive:
            if event.key() == Qt.Key_Delete and self.scene.selectedItems():
                for item in self.scene.selectedItems():
                    if isinstance(item, MovablePoint):
                        self.points.remove(item)
                        self.scene.removeItem(item)

                self.update_shape()
        else:
            pass

    def fillApartments(self, apartment_table):
        floor_points = []
        for point in self.points:
            floor_points.append((int(point.get_position()[0]), int(point.get_position()[1])))
            self.scene.removeItem(point)
        floor = Floor(floor_points)

        # Создаем поток и передаем его в отдельный класс Worker для выполнения в фоне
        self.worker = FloorGenerator(floor, apartment_table)
        self.worker_thread = Thread(target=self.worker.run)

        # Соединяем сигнал завершения работы с функцией для обработки результата
        self.worker.finished.connect(self.onApartmentsGenerated)
        self.worker_thread.start()

    def paint_outline(self):
        def frange(start, stop, step=1.0):
            while start < stop:
                yield start
                start += step

        polygon = QPolygonF([vertex.pos() for vertex in self.polygon.vertices])
        outline = QGraphicsPolygonItem(polygon)
        outline.setPen(QPen(Qt.black, 2))
        self.scene.addItem(outline)

        # Черчение лифтов
        min_x = float('inf')
        min_y = float('inf')
        max_x = float('-inf')
        max_y = float('-inf')

        for square in self.polygon.elevator_squares:
            (x1, y1, x2, y2) = square.getCoords()
            min_x = min(min_x, int(x1))
            min_y = min(min_y, int(y1))
            max_x = max(max_x, int(x2))
            max_y = max(max_y, int(y2))

        elevator_rect = QRectF(QPointF(min_x, min_y), QPointF(max_x, max_y))
        elevator_rect = QGraphicsRectItem(elevator_rect)
        elevator_rect.setPen(QPen(Qt.black, 0.5))
        self.scene.addItem(elevator_rect)

        line = QGraphicsLineItem(min_x, min_y, max_x, max_y)
        line.setPen(QPen(Qt.black, 0.3))
        self.scene.addItem(line)

        line = QGraphicsLineItem(min_x, max_y, max_x, min_y)
        line.setPen(QPen(Qt.black, 0.3))
        self.scene.addItem(line)

        # Черчение лестниц
        min_x = float('inf')
        min_y = float('inf')
        max_x = float('-inf')
        max_y = float('-inf')

        for square in self.polygon.stairs_squares:
            (x1, y1, x2, y2) = square.getCoords()
            min_x = min(min_x, int(x1))
            min_y = min(min_y, int(y1))
            max_x = max(max_x, int(x2))
            max_y = max(max_y, int(y2))

        stair_rect = QRectF(QPointF(min_x, min_y), QPointF(max_x, max_y))
        width = stair_rect.width()
        height = stair_rect.height()
        stair_rect = QGraphicsRectItem(stair_rect)
        stair_rect.setPen(QPen(Qt.black, 0.5))
        self.scene.addItem(stair_rect)

        if height > width:
            stop_y = min_y + width // 5
            stop_line = QGraphicsLineItem(min_x, stop_y, max_x, stop_y)
            stop_line.setPen(QPen(Qt.black, 0.5))
            self.scene.addItem(stop_line)

            line = QGraphicsLineItem(min_x + width // 2, stop_y, min_x + width // 2, max_y)
            line.setPen(QPen(Qt.black, 0.5))
            self.scene.addItem(line)

            for inc in frange(stop_y, max_y, 2.0):
                line = QGraphicsLineItem(min_x, inc, max_x, inc)
                line.setPen(QPen(Qt.black, 0.3))
                self.scene.addItem(line)
        else:
            stop_x = min_x + width // 5
            stop_line = QGraphicsLineItem(stop_x, min_y, stop_x, max_y)
            stop_line.setPen(QPen(Qt.black, 0.5))
            self.scene.addItem(stop_line)

            line = QGraphicsLineItem(stop_x, min_y + height // 2, max_x, min_y + height // 2)
            line.setPen(QPen(Qt.black, 0.5))
            self.scene.addItem(line)

            for inc in frange(stop_x, max_x, 2.0):
                line = QGraphicsLineItem(inc, min_y, inc, max_y)
                line.setPen(QPen(Qt.black, 0.3))
                self.scene.addItem(line)

    def onApartmentsGenerated(self, floor):
        # Цвета для разных типов квартир
        apt_colors = {
            'studio': '#fa6b6b',
            '1 room': '#6dd170',
            '2 room': '#6db8d1',
            '3 room': '#ed975a',
            '4 room': '#ba7ed9'
        }
        self.scene.clear()
        self.paint_outline()
        # Добавляем квартиры на сцену
        for apt in floor.apartments:
            poly = apt.polygon
            x, y = poly.exterior.xy
            poly_points = [QPointF(x[i], y[i]) for i in range(len(x))]
            polygon = QPolygonF(poly_points)

            filled_shape = QGraphicsPolygonItem(polygon)
            filled_shape.setBrush(QBrush(QColor(apt_colors[apt.type])))
            self.scene.addItem(filled_shape)

        self.apartmentsGenerated.emit()