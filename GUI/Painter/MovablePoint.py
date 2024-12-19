from PyQt5.QtCore import QRectF, Qt, QPointF, QLineF
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
        self.cuts = []

    def __del__(self):
        for line_item, other_point in self.cuts:
            other_point.remove_cut(line_item)
            self.scene().removeItem(line_item)

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
            # Округление до ближайшего значения, кратного snap_threshold
            x = round(value.x() / self.snap_threshold) * self.snap_threshold
            y = round(value.y() / self.snap_threshold) * self.snap_threshold
            new_pos = QPointF(x, y)

            for line_item, other_point in self.cuts:
                line_item.setLine(QLineF(new_pos, other_point.scenePos()))

            # Обновляем полигон, связанный с точкой
            polygon_item = self.parent_polygon
            polygon_item.updatePolygon()

            return new_pos
        return super().itemChange(change, value)

    def add_cut(self, line_item, other_point):
        self.cuts.append((line_item, other_point))

    def remove_cut(self, line_item):
        self.cuts = [(line, point) for line, point in self.cuts if line != line_item]

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