<<<<<<< HEAD
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPen
from PyQt5.QtWidgets import QGraphicsItemGroup, QGraphicsRectItem, QGraphicsLineItem

from GUI.Painter.RotationHandle import RotationHandle


class ElevatorRect(QGraphicsItemGroup):
    def __init__(self, x, y, width, height, parent=None):
        super().__init__(parent)
        self.setFlag(QGraphicsItemGroup.ItemIsMovable)
        self.setFlag(QGraphicsItemGroup.ItemSendsScenePositionChanges)
        self.handle = None
        self.setFlag(QGraphicsItemGroup.ItemIsSelectable)

        self.rect = QGraphicsRectItem(x, y, width, height)
        self.setTransformOriginPoint(self.rect.rect().center())

        self.rect.setPen(QPen(Qt.black, 0.2))
        self.addToGroup(self.rect)

        line = QGraphicsLineItem(self.rect.rect().topLeft().x(), self.rect.rect().topLeft().y(),
                                 self.rect.rect().bottomRight().x(),
                                 self.rect.rect().bottomRight().y())
        line.setPen(QPen(Qt.black, 0.05))
        self.addToGroup(line)

        line = QGraphicsLineItem(self.rect.rect().topLeft().x(), self.rect.rect().bottomRight().y(),
                                 self.rect.rect().bottomRight().x(),
                                 self.rect.rect().topLeft().y())
        line.setPen(QPen(Qt.black, 0.05))
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
=======
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPen
from PyQt5.QtWidgets import QGraphicsItemGroup, QGraphicsRectItem, QGraphicsLineItem

from GUI.Painter.RotationHandle import RotationHandle


class ElevatorRect(QGraphicsItemGroup):
    def __init__(self, x, y, width, height, parent=None):
        super().__init__(parent)
        self.setFlag(QGraphicsItemGroup.ItemIsMovable)
        self.setFlag(QGraphicsItemGroup.ItemSendsScenePositionChanges)
        self.handle = None
        self.setFlag(QGraphicsItemGroup.ItemIsSelectable)

        self.rect = QGraphicsRectItem(x, y, width, height)
        self.setTransformOriginPoint(self.rect.rect().center())

        self.rect.setPen(QPen(Qt.black, 0.5))
        self.addToGroup(self.rect)

        line = QGraphicsLineItem(self.rect.rect().topLeft().x(), self.rect.rect().topLeft().y(),
                                 self.rect.rect().bottomRight().x(),
                                 self.rect.rect().bottomRight().y())
        line.setPen(QPen(Qt.black, 0.3))
        self.addToGroup(line)

        line = QGraphicsLineItem(self.rect.rect().topLeft().x(), self.rect.rect().bottomRight().y(),
                                 self.rect.rect().bottomRight().x(),
                                 self.rect.rect().topLeft().y())
        line.setPen(QPen(Qt.black, 0.3))
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
>>>>>>> 03dfb9510b1b841f741c0c76a6d6795ed7416cdb
