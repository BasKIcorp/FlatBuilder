from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QBrush, QColor, QPen, QPainterPath, QPolygonF
from PyQt5.QtWidgets import QGraphicsPolygonItem


class Outline(QGraphicsPolygonItem):
    def __init__(self, vertices):
        super().__init__()
        self.vertices = vertices
        self.updatePolygon()
        self.elevator_squares = []
        self.stairs_squares = []
        self.selection_rect = QRectF()
        self.is_selecting = False
        self.mode = "none"

    def updatePolygon(self):
        polygon = QPolygonF([vertex.pos() for vertex in self.vertices])
        self.setPolygon(polygon)
        self.update()  # Trigger a repaint

    def startSelection(self, pos):
        self.is_selecting = True
        self.selection_rect.setTopLeft(pos)
        self.selection_rect.setBottomRight(pos)
        self.update()

    def updateSelection(self, pos):
        if self.is_selecting:
            self.selection_rect.setBottomRight(pos)
            self.update()

    def endSelection(self):
        self.is_selecting = False
        self.selectGridSquares()
        self.update()

    def selectGridSquares(self):
        if self.mode == "elevator":
            self.elevator_squares.clear()
        elif self.mode == "stairs":
            self.stairs_squares.clear()
        grid_spacing = 5
        path = QPainterPath()
        path.addPolygon(self.polygon())
        bounding_rect = self.polygon().boundingRect()

        x_start = int(bounding_rect.left())
        x_end = int(bounding_rect.right())
        y_start = int(bounding_rect.top())
        y_end = int(bounding_rect.bottom())

        for x in range(x_start, x_end, grid_spacing):
            for y in range(y_start, y_end, grid_spacing):
                square_rect = QRectF(x, y, grid_spacing, grid_spacing)
                if self.selection_rect.intersects(square_rect):
                    if self.mode == "elevator":
                        self.elevator_squares.append(square_rect)
                    elif self.mode == "stairs":
                        self.stairs_squares.append(square_rect)

    def paint(self, painter, option, widget=None, final=False):
        if len(self.polygon()) < 3:
            return  # Skip drawing if less than 3 points

        painter.setPen(QPen(Qt.black, 2))
        painter.drawPolygon(self.polygon())

        grid_spacing = 5

        path = QPainterPath()
        path.addPolygon(self.polygon())

        painter.save()
        painter.setClipPath(path)

        grid_pen = QPen(Qt.lightGray, 1, Qt.SolidLine)
        painter.setPen(grid_pen)

        bounding_rect = self.polygon().boundingRect()
        x_start = int(bounding_rect.left())
        x_end = int(bounding_rect.right())
        y_start = int(bounding_rect.top())
        y_end = int(bounding_rect.bottom())

        for x in range(x_start, x_end, grid_spacing):
            painter.drawLine(x, y_start, x, y_end)

        for y in range(y_start, y_end, grid_spacing):
            painter.drawLine(x_start, y, x_end, y)

        for square in self.elevator_squares:
            painter.fillRect(square, QBrush(QColor(0xFF, 0, 0, 0x80)))

        for square in self.stairs_squares:
            painter.fillRect(square, QBrush(QColor(245, 241, 118, 0x80)))

        if self.is_selecting:
            painter.setPen(QPen(Qt.red, 1, Qt.DashLine))
            painter.drawRect(self.selection_rect)

        painter.restore()