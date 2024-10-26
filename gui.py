from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIntValidator, QFont
from PyQt5.QtWidgets import QGraphicsScene, QMainWindow, QPushButton, QWidget, QVBoxLayout, QFrame, \
    QSplitter, QTableWidgetItem, QTableWidget, QLineEdit, QSpacerItem
from painter import Painter


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        splitter = QSplitter(Qt.Horizontal)
        self.setCentralWidget(splitter)

        self.scene = QGraphicsScene()

        self.graphics_view = Painter(self.scene)
        self.graphics_view.setFrameShape(QFrame.StyledPanel)

        right_widget = QWidget()
        right_layout = QVBoxLayout()

        right_layout.setAlignment(Qt.AlignTop)

        self.table = QTableWidget()
        self.table.setRowCount(5)
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Тип квартир", "Площадь от", "Площадь до", "Процент"])

        self.table.verticalHeader().setVisible(False)

        apartment_types = ["Студии", "1-комн", "2-комн", "3-комн", "4-комн"]
        for row, apartment_type in enumerate(apartment_types):
            item = QTableWidgetItem(apartment_type)
            item.setFlags(Qt.ItemIsEnabled)
            self.table.setItem(row, 0, item)

        int_validator = QIntValidator(0, 1000000, self)

        for row in range(5):
            area_from_edit = QLineEdit()
            area_from_edit.setValidator(int_validator)
            area_from_edit.setAlignment(Qt.AlignCenter)
            self.table.setCellWidget(row, 1, area_from_edit)

            area_to_edit = QLineEdit()
            area_to_edit.setValidator(int_validator)
            area_to_edit.setAlignment(Qt.AlignCenter)
            self.table.setCellWidget(row, 2, area_to_edit)

            percent_edit = QLineEdit()
            percent_edit.setValidator(int_validator)
            percent_edit.setAlignment(Qt.AlignCenter)
            self.table.setCellWidget(row, 3, percent_edit)

        right_layout.addWidget(self.table)

        spacer = QSpacerItem(0, 10)
        right_layout.addSpacerItem(spacer)

        button_font = QFont()
        button_font.setPointSize(9)
        button_font.setBold(False)

        generate_button = QPushButton("Сгенерировать")
        generate_button.setFixedHeight(50)
        generate_button.setFont(button_font)
        right_layout.addWidget(generate_button)

        spacer2 = QSpacerItem(0, 494)
        right_layout.addSpacerItem(spacer2)

        right_widget.setLayout(right_layout)

        splitter.addWidget(self.graphics_view)
        splitter.addWidget(right_widget)

        splitter.setSizes([500, 270])

        self.setWindowTitle("Квартирограф")

        self.setGeometry(0, 0, 1500, 800)