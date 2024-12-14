<<<<<<< HEAD
import math
from PyQt5.QtCore import Qt, QPointF, QRectF, QRect
from PyQt5.QtGui import QPen, QPainterPath, QPolygonF, QColor
from PyQt5.QtWidgets import QGraphicsItemGroup, QGraphicsRectItem, QGraphicsPathItem


class RotationHandle(QGraphicsItemGroup):
    def __init__(self, parent_rect, radius=3):
        super().__init__()
        self.user_interaction = False

        self.parent_rect = parent_rect

        self.radius = radius
        self.setFlags(QGraphicsItemGroup.ItemIsMovable | QGraphicsItemGroup.ItemSendsScenePositionChanges)

        # Create the custom rotation icon (arch with arrow)
        self.rotation_icon = self.create_rotation_icon()
        self.addToGroup(self.rotation_icon)

        # Update initial position
        self.update_position()

    def create_rotation_icon(self):
        """Create the arc with a horizontal arrow to represent the rotation handle."""
        path = QPainterPath()
        arc_start_angle = 20  # In degrees
        arc_span_angle = 270  # In degrees

        # Define the arc
        rect = QRectF(-self.radius, -self.radius, self.radius * 2, self.radius * 2)
        rect.moveTopLeft(QPointF(-self.radius, -self.radius))
        path.arcMoveTo(rect, arc_start_angle)
        path.arcTo(rect, arc_start_angle, arc_span_angle)

        # Arrowhead (horizontal, pointing left)
        arrow_tip = path.currentPosition()  # Get the endpoint of the arc
        arrow_size = 2
        arrow_left = QPointF(arrow_tip.x() - arrow_size, arrow_tip.y() - arrow_size / 2)
        arrow_right = QPointF(arrow_tip.x() - arrow_size, arrow_tip.y() + arrow_size / 2)

        path.moveTo(arrow_tip)
        path.lineTo(arrow_left)
        path.moveTo(arrow_tip)
        path.lineTo(arrow_right)

        icon = QGraphicsPathItem(path)
        icon.setPen(QPen(QColor("black"), 0.5))  # Customize pen color and width
        return icon

    def update_position(self):
        """Update the position of the rotation handle relative to the parent rectangle."""
        center = self.parent_rect.getPosition()
        rect_radius = max(self.parent_rect.boundingRect().width(), self.parent_rect.boundingRect().height()) / 2
        total_radius = rect_radius + 10
        # Position the handle at the top of the circular path
        self.setPos(center.x(), center.y() - total_radius)

    def itemChange(self, change, value):
        """Handle the change in item position."""
        if self.user_interaction:
            if change == QGraphicsItemGroup.ItemPositionChange:
                center = self.parent_rect.getPosition()
                constrained_position = self.constrain_to_circle(center, value)
                self.rotate_parent(constrained_position)  # Only rotate the parent (ElevatorRect)
                self.setPos(constrained_position)  # Move only the handle, not the rect
                return constrained_position  # Return the new position of the handle

        return super().itemChange(change, value)

    def constrain_to_circle(self, center, position):
        """Constrain the position of the handle to a circular path."""
        dx = position.x() - center.x()
        dy = position.y() - center.y()
        angle = math.atan2(dy, dx)

        # Adjust radius to include the 10-pixel offset
        rect_radius = max(self.parent_rect.boundingRect().width(), self.parent_rect.boundingRect().height()) / 2
        total_radius = rect_radius + 10

        x = center.x() + total_radius * math.cos(angle)
        y = center.y() + total_radius * math.sin(angle)
        return QPointF(x, y)

    def rotate_parent(self, handle_position):
        """Rotate the parent rectangle based on the handle's position."""
        center = self.parent_rect.mapToScene(self.parent_rect.transformOriginPoint())
        dx = handle_position.x() - center.x()
        dy = handle_position.y() - center.y()
        angle = math.degrees(math.atan2(dy, dx))
        self.parent_rect.setRotation(angle)

    def mousePressEvent(self, event):
        """Track user interaction when the item is clicked."""
        self.user_interaction = True
        if self.parent_rect.isSelected():
            self.parent_rect.setFlag(QGraphicsItemGroup.ItemIsMovable, False)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        """Reset user interaction when the mouse is released."""
        self.user_interaction = False
        if self.parent_rect.isSelected():
            self.parent_rect.setFlag(QGraphicsItemGroup.ItemIsMovable, True)
        super().mouseReleaseEvent(event)


=======
import math
from PyQt5.QtCore import Qt, QPointF, QRectF, QRect
from PyQt5.QtGui import QPen, QPainterPath, QPolygonF, QColor
from PyQt5.QtWidgets import QGraphicsItemGroup, QGraphicsRectItem, QGraphicsPathItem


class RotationHandle(QGraphicsItemGroup):
    def __init__(self, parent_rect, radius=3):
        super().__init__()
        self.user_interaction = False

        self.parent_rect = parent_rect

        self.radius = radius
        self.setFlags(QGraphicsItemGroup.ItemIsMovable | QGraphicsItemGroup.ItemSendsScenePositionChanges)

        # Create the custom rotation icon (arch with arrow)
        self.rotation_icon = self.create_rotation_icon()
        self.addToGroup(self.rotation_icon)

        # Update initial position
        self.update_position()

    def create_rotation_icon(self):
        """Create the arc with a horizontal arrow to represent the rotation handle."""
        path = QPainterPath()
        arc_start_angle = 20  # In degrees
        arc_span_angle = 270  # In degrees

        # Define the arc
        rect = QRectF(-self.radius, -self.radius, self.radius * 2, self.radius * 2)
        rect.moveTopLeft(QPointF(-self.radius, -self.radius))
        path.arcMoveTo(rect, arc_start_angle)
        path.arcTo(rect, arc_start_angle, arc_span_angle)

        # Arrowhead (horizontal, pointing left)
        arrow_tip = path.currentPosition()  # Get the endpoint of the arc
        arrow_size = 2
        arrow_left = QPointF(arrow_tip.x() - arrow_size, arrow_tip.y() - arrow_size / 2)
        arrow_right = QPointF(arrow_tip.x() - arrow_size, arrow_tip.y() + arrow_size / 2)

        path.moveTo(arrow_tip)
        path.lineTo(arrow_left)
        path.moveTo(arrow_tip)
        path.lineTo(arrow_right)

        icon = QGraphicsPathItem(path)
        icon.setPen(QPen(QColor("black"), 0.5))  # Customize pen color and width
        return icon

    def update_position(self):
        """Update the position of the rotation handle relative to the parent rectangle."""
        center = self.parent_rect.getPosition()
        rect_radius = max(self.parent_rect.boundingRect().width(), self.parent_rect.boundingRect().height()) / 2
        total_radius = rect_radius + 10
        # Position the handle at the top of the circular path
        self.setPos(center.x(), center.y() - total_radius)

    def itemChange(self, change, value):
        """Handle the change in item position."""
        if self.user_interaction:
            if change == QGraphicsItemGroup.ItemPositionChange:
                center = self.parent_rect.getPosition()
                constrained_position = self.constrain_to_circle(center, value)
                self.rotate_parent(constrained_position)  # Only rotate the parent (ElevatorRect)
                self.setPos(constrained_position)  # Move only the handle, not the rect
                return constrained_position  # Return the new position of the handle

        return super().itemChange(change, value)

    def constrain_to_circle(self, center, position):
        """Constrain the position of the handle to a circular path."""
        dx = position.x() - center.x()
        dy = position.y() - center.y()
        angle = math.atan2(dy, dx)

        # Adjust radius to include the 10-pixel offset
        rect_radius = max(self.parent_rect.boundingRect().width(), self.parent_rect.boundingRect().height()) / 2
        total_radius = rect_radius + 10

        x = center.x() + total_radius * math.cos(angle)
        y = center.y() + total_radius * math.sin(angle)
        return QPointF(x, y)

    def rotate_parent(self, handle_position):
        """Rotate the parent rectangle based on the handle's position."""
        center = self.parent_rect.mapToScene(self.parent_rect.transformOriginPoint())
        dx = handle_position.x() - center.x()
        dy = handle_position.y() - center.y()
        angle = math.degrees(math.atan2(dy, dx))
        self.parent_rect.setRotation(angle)

    def mousePressEvent(self, event):
        """Track user interaction when the item is clicked."""
        self.user_interaction = True
        if self.parent_rect.isSelected():
            self.parent_rect.setFlag(QGraphicsItemGroup.ItemIsMovable, False)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        """Reset user interaction when the mouse is released."""
        self.user_interaction = False
        if self.parent_rect.isSelected():
            self.parent_rect.setFlag(QGraphicsItemGroup.ItemIsMovable, True)
        super().mouseReleaseEvent(event)


>>>>>>> 03dfb9510b1b841f741c0c76a6d6795ed7416cdb
