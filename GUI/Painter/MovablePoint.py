from PyQt5.QtCore import QRectF, Qt
from PyQt5.QtWidgets import QGraphicsEllipseItem


class MovablePoint(QGraphicsEllipseItem):
    def __init__(self, x, y, radius, point_id, parent_polygon, editor, preview=False):
        super().__init__(-radius, -radius, 2 * radius, 2 * radius)
        self.setPos(x, y)
        if not preview:
            self.setFlags(QGraphicsEllipseItem.ItemIsMovable | QGraphicsEllipseItem.ItemIsSelectable)
        else:
            self.setFlag(QGraphicsEllipseItem.ItemIsSelectable, False)
        self.default_brush = Qt.blue
        self.setBrush(self.default_brush)
        self.selected_brush = Qt.lightGray
        self.radius = radius
        self.point_id = point_id
        self.editor = editor
        self.preview = preview
        self.parent_polygon = parent_polygon

    def paint(self, painter, option, widget=None):
        if self.isSelected():
            self.setBrush(self.selected_brush)
            scale_factor = 1.5
            rect = QRectF(-self.radius * scale_factor, -self.radius * scale_factor,
                          2 * self.radius * scale_factor, 2 * self.radius * scale_factor)
        else:
            self.setBrush(self.default_brush)
            rect = QRectF(-self.radius, -self.radius, 2 * self.radius, 2 * self.radius)

        painter.setBrush(self.brush())
        painter.drawEllipse(rect)

    def get_position(self):
        pos = self.scenePos()
        return pos.x(), pos.y()

    def mouseMoveEvent(self, event):
        """ Update connected lines in real-time as the point moves. """
        super().mouseMoveEvent(event)
        if not self.preview:
            self.parent_polygon.updatePolygon()