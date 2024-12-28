from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPen
from PyQt5.QtWidgets import QGraphicsItemGroup, QGraphicsRectItem, QGraphicsLineItem

from GUI.Painter.RotationHandle import RotationHandle


class StairsRect(QGraphicsItemGroup):
    def __init__(self, x, y, width, height, parent=None):
        super().__init__(parent)

        def frange(start, stop, step=0.2):
            while start < stop:
                yield start
                start += step

        # Create the rectangle
        self.setFlag(QGraphicsItemGroup.ItemIsMovable)
        self.setFlag(QGraphicsItemGroup.ItemSendsScenePositionChanges)
        self.handle = None
        self.setFlag(QGraphicsItemGroup.ItemIsSelectable)
        self.rect = QGraphicsRectItem(x, y, width, height)
        self.rect.setPen(QPen(Qt.black))
        self.setTransformOriginPoint(self.rect.rect().center())
        self.rect.setPen(QPen(Qt.black, 0.1))

        self.addToGroup(self.rect)

        if height > width:
            stop_y = self.rect.rect().topLeft().y() + width / 5
            stop_line = QGraphicsLineItem(self.rect.rect().topLeft().x(), stop_y, self.rect.rect().bottomRight().x(), stop_y)
            stop_line.setPen(QPen(Qt.black, 0.05))
            self.addToGroup(stop_line)

            line = QGraphicsLineItem(self.rect.rect().topLeft().x() + width / 2, stop_y, self.rect.rect().topLeft().x() + width / 2,
                                     self.rect.rect().bottomRight().y())
            line.setPen(QPen(Qt.black, 0.05))
            self.addToGroup(line)

            for inc in frange(stop_y, self.rect.rect().bottomRight().y(), 0.2):
                line = QGraphicsLineItem(self.rect.rect().topLeft().x(), inc, self.rect.rect().bottomRight().x(), inc)
                line.setPen(QPen(Qt.black, 0.03))
                self.addToGroup(line)

        else:
            stop_x = self.rect.rect().topLeft().x() + width / 5
            stop_line = QGraphicsLineItem(stop_x, self.rect.rect().topLeft().y(), stop_x, self.rect.rect().bottomRight().y())
            stop_line.setPen(QPen(Qt.black, 0.05))
            self.addToGroup(stop_line)

            line = QGraphicsLineItem(stop_x, self.rect.rect().topLeft().y() + height / 2, self.rect.rect().bottomRight().x(),
                                     self.rect.rect().topLeft().y() + height / 2)
            line.setPen(QPen(Qt.black, 0.05))
            self.addToGroup(line)

            for inc in frange(stop_x, self.rect.rect().bottomRight().x(), 0.2):
                line = QGraphicsLineItem(inc, self.rect.rect().topLeft().y(), inc, self.rect.rect().bottomRight().y())
                line.setPen(QPen(Qt.black, 0.03))
                self.addToGroup(line)

    def setPosition(self, pos):
        self.setPos(pos)

    def getPosition(self):
        return self.sceneBoundingRect().center()

    def rotateObject(self, angle):
        self.setRotation(angle)

    def itemChange(self, change, value):
        if change == QGraphicsItemGroup.ItemPositionChange:
            if self.handle:
                self.handle.update_position()  # Обновляем позицию маленького прямоугольника
        return super().itemChange(change, value)