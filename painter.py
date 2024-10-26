from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsEllipseItem, QApplication, QGraphicsLineItem
from PyQt5.QtCore import Qt, QLineF
from PyQt5.QtGui import QBrush, QPen


class MovablePoint(QGraphicsEllipseItem):
    def __init__(self, x, y, radius, graph, point_id):
        super().__init__(-radius, -radius, 2 * radius, 2 * radius)
        self.setBrush(QBrush(Qt.black))
        self.setFlags(QGraphicsEllipseItem.ItemIsMovable | QGraphicsEllipseItem.ItemIsSelectable)
        self.setPos(x, y)
        self.graph = graph
        self.point_id = point_id

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        for line, is_start in self.graph[self.point_id]:
            line_item = line.line()
            if is_start:
                line_item.setP1(self.scenePos())
            else:
                line_item.setP2(self.scenePos())
            line.setLine(line_item)


class Painter(QGraphicsView):
    def __init__(self, scene):
        super().__init__(scene)
        self.graphs = []
        self.pen = QPen(Qt.black, 2)

        self.graph = {}
        self.first_point = None
        self.last_placed_point = None
        self.point_counter = 0
        self.closing_line = None

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            item = self.itemAt(event.pos())
            if item is None:
                scene_pos = self.mapToScene(event.pos())
                new_point = MovablePoint(scene_pos.x(), scene_pos.y(), 5, self.graph, self.point_counter)
                self.scene().addItem(new_point)

                self.graph[self.point_counter] = []

                if self.last_placed_point is not None:
                    line_item = QGraphicsLineItem(QLineF(self.last_placed_point.scenePos(), scene_pos))
                    self.scene().addItem(line_item)

                    self.graph[self.point_counter].append((line_item, False))
                    self.graph[self.last_placed_point.point_id].append((line_item, True))

                if self.point_counter == 0:
                    self.first_point = new_point

                if self.first_point and self.point_counter > 1:
                    if self.closing_line:
                        print(self.closing_line.x())
                        self.scene().removeItem(self.closing_line)
                        self.graph[self.first_point.point_id].remove((self.closing_line, False))
                        self.graph[self.last_placed_point.point_id].remove((self.closing_line, True))
                        print("clsoing line removed")
                        print(self.point_counter)
                        print(self.first_point.point_id)

                    self.closing_line = QGraphicsLineItem(QLineF(scene_pos, self.first_point.scenePos()))
                    self.scene().addItem(self.closing_line)

                    self.graph[self.point_counter].append((self.closing_line, True))
                    self.graph[self.first_point.point_id].append((self.closing_line, False))

                self.last_placed_point = new_point

                self.point_counter += 1

                print(f"added new point at {scene_pos} with ID {self.point_counter - 1}")
            event.accept()
        else:
            super().mousePressEvent(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.graphs.append(self.graph)
            self.graph = {}
            self.first_point = None
            self.last_placed_point = None
            self.point_counter = 0
            self.closing_line = None
        if event.key() == Qt.Key_Delete:
            selected_items = self.scene().selectedItems()
            if selected_items:
                for item in selected_items:
                    if isinstance(item, MovablePoint):
                        self.delete_point(item)
            event.accept()
        else:
            super().keyPressEvent(event)

    def delete_point(self, point):
        point_id = point.point_id
        if point_id not in self.graph:
            return

        connected_lines = self.graph[point_id]

        neighbors = []
        for line, is_start in connected_lines:
            if is_start:
                other_point_id = [pid for pid, lst in self.graph.items() if (line, False) in lst]
            else:
                other_point_id = [pid for pid, lst in self.graph.items() if (line, True) in lst]

            if other_point_id:
                neighbors.append(other_point_id[0])

            self.scene().removeItem(line)

        self.scene().removeItem(point)
        del self.graph[point_id]

        if point == self.last_placed_point:
            remaining_point_ids = list(self.graph.keys())
            if remaining_point_ids:
                self.last_placed_point = next(
                    (p for p in self.scene().items() if
                     isinstance(p, MovablePoint) and p.point_id == remaining_point_ids[-1]),
                    None
                )
            else:
                self.last_placed_point = None

        if len(neighbors) == 2:
            start_point_id = neighbors[0]
            end_point_id = neighbors[1]

            start_point = next(
                (item for item in self.scene().items() if
                 isinstance(item, MovablePoint) and item.point_id == start_point_id),
                None
            )
            end_point = next(
                (item for item in self.scene().items() if
                 isinstance(item, MovablePoint) and item.point_id == end_point_id),
                None
            )

            if start_point and end_point:
                new_line = QGraphicsLineItem(QLineF(start_point.scenePos(), end_point.scenePos()))
                self.scene().addItem(new_line)

                self.graph[start_point_id].append((new_line, True))
                self.graph[end_point_id].append((new_line, False))

        if len(self.graph) < 3 and self.closing_line:
            self.scene().removeItem(self.closing_line)
            self.closing_line = None

        if self.first_point == point:
            if len(self.graph) > 0:
                new_first_point_id = list(self.graph.keys())[0]
                self.first_point = next(
                    (item for item in self.scene().items() if
                     isinstance(item, MovablePoint) and item.point_id == new_first_point_id),
                    None
                )
                self.scene().removeItem(self.closing_line)
                print("first point remove closing line")
                print(self.first_point.point_id)
            else:
                self.first_point = None

        if self.last_placed_point and self.first_point and len(self.graph) > 2:
            if self.closing_line:
                self.scene().removeItem(self.closing_line)
            self.closing_line = QGraphicsLineItem(
                QLineF(self.last_placed_point.scenePos(), self.first_point.scenePos()))
            self.scene().addItem(self.closing_line)
            self.graph[self.last_placed_point.point_id].append((self.closing_line, True))
            self.graph[self.first_point.point_id].append((self.closing_line, False))

        print(f"deleted point with ID {point_id}")