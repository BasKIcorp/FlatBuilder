<<<<<<< HEAD
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QBrush, QColor, QPen, QPainterPath, QPolygonF
from PyQt5.QtWidgets import QGraphicsPolygonItem

from GUI.Painter.EdgeLengthLabel import EdgeLengthLabel


class Outline(QGraphicsPolygonItem):
    def __init__(self, vertices):
        super().__init__()
        self.vertices = vertices
        self.updatePolygon()
        self.edge_labels = []

    def paint(self, painter, option, widget=None, final=False):
        if len(self.polygon()) < 3:
            return  # Skip drawing if less than 3 points

        painter.setPen(QPen(Qt.black, 0.3))
        painter.drawPolygon(self.polygon())

        path = QPainterPath()
        path.addPolygon(self.polygon())

        painter.save()
        painter.setClipPath(path)

        painter.restore()
        for i in range(len(self.vertices)):
            label = EdgeLengthLabel()
            self.scene().addItem(label)
            self.edge_labels.append(label)

            # Initial update of labels
        self.update_all_edge_lengths()

    def update_all_edge_lengths(self):
        polygon = self.polygon()
        for i in range(len(polygon)):
            start = polygon[i]
            end = polygon[(i + 1) % len(polygon)]  # Next vertex (wrap around for the last edge)
            self.edge_labels[i].update_position_and_value(start, end)

    def delete_edge_lengths(self):
        for edge in self.edge_labels:
            self.scene().removeItem(edge)

    def updatePolygon(self):
        polygon = QPolygonF([vertex.pos() for vertex in self.vertices])
        self.setPolygon(polygon)
        self.update()  # Trigger a repaint
=======
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QBrush, QColor, QPen, QPainterPath, QPolygonF
from PyQt5.QtWidgets import QGraphicsPolygonItem


class Outline(QGraphicsPolygonItem):
    def __init__(self, vertices):
        super().__init__()
        self.vertices = vertices
        self.updatePolygon()

    def paint(self, painter, option, widget=None, final=False):
        if len(self.polygon()) < 3:
            return  # Skip drawing if less than 3 points

        painter.setPen(QPen(Qt.black, 1))
        painter.drawPolygon(self.polygon())


        path = QPainterPath()
        path.addPolygon(self.polygon())

        painter.save()
        painter.setClipPath(path)

        painter.restore()

    def updatePolygon(self):
        polygon = QPolygonF([vertex.pos() for vertex in self.vertices])
        self.setPolygon(polygon)
        self.update()  # Trigger a repaint
>>>>>>> 03dfb9510b1b841f741c0c76a6d6795ed7416cdb
