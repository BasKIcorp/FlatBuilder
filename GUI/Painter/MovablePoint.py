from PyQt5.QtCore import QRectF, Qt, QPointF
from PyQt5.QtWidgets import QGraphicsEllipseItem, QGraphicsItem


class MovablePoint(QGraphicsEllipseItem):
    def __init__(self, x, y, radius, point_id, parent_polygon, editor, preview=False):
        super().__init__(-radius, -radius, 2 * radius, 2 * radius)
        self.setPos(x, y)
        if not preview:
            self.setFlags(QGraphicsEllipseItem.ItemIsMovable | QGraphicsEllipseItem.ItemIsSelectable | QGraphicsEllipseItem.ItemSendsGeometryChanges)
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
        self.snap_threshold = 1

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

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange and self.scene():
            polygon_item = self.parent_polygon
            new_pos = self.snap_to_axes(value, polygon_item.polygon())
            polygon_item.updatePolygon()
            return new_pos
        return super().itemChange(change, value)

    def snap_to_axes(self, pos, polygon):
        # Snap to horizontal or vertical alignment for all points in the polygon
        for point in polygon:
            if abs(pos.x() - point.x()) < self.snap_threshold:
                pos.setX(point.x())
            if abs(pos.y() - point.y()) < self.snap_threshold:
                pos.setY(point.y())
        return pos

    def mouseMoveEvent(self, event):
        """ Update connected lines in real-time as the point moves. """
        super().mouseMoveEvent(event)
        if not self.preview:
            self.parent_polygon.updatePolygon()