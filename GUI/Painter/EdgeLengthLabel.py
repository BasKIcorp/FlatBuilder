import math

from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QGraphicsTextItem


class EdgeLengthLabel(QGraphicsTextItem):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDefaultTextColor(Qt.black)
        font = QFont()
        font.setPointSize(1)
        self.setFont(font)

    def update_position_and_value(self, start, end):
        length = self.calculate_length(start, end)
        if length == 0:
            if self.scene():
                self.setVisible(False)
        else:
            self.setVisible(True)
            self.setPlainText(f"{length:.2f} м")
            midpoint = QPointF((start.x() + end.x()) / 2 - 3, (start.y() + end.y()) / 2 - 3)
            self.setPos(midpoint)

    @staticmethod
    def calculate_length(start, end):
        return math.sqrt((end.x() - start.x()) ** 2 + (end.y() - start.y()) ** 2)