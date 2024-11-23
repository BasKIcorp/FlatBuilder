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