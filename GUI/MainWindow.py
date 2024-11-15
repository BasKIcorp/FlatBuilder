from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIntValidator, QFont, QPainter
from PyQt5.QtPrintSupport import QPrinter
from PyQt5.QtWidgets import QGraphicsScene, QMainWindow, QPushButton, QWidget, QVBoxLayout, QFrame, \
    QSplitter, QTableWidgetItem, QTableWidget, QLineEdit, QFileDialog, QLabel, QHBoxLayout, QComboBox
from GUI.Painter.Painter import Painter


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.generating = False

        splitter = QSplitter(Qt.Horizontal)
        self.setCentralWidget(splitter)

        self.scene = QGraphicsScene()

        self.graphics_view = Painter(self.scene)
        self.graphics_view.setFrameShape(QFrame.StyledPanel)
        right_widget = QWidget()
        right_layout = QVBoxLayout()

        right_layout.setAlignment(Qt.AlignTop)

        left_widget = QWidget()
        left_layout = QVBoxLayout()

        left_layout.setAlignment(Qt.AlignTop)

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

        font = QFont()
        font.setPointSize(12)

        self.area_from = []
        self.area_to = []
        self.percent = []
        for row in range(5):
            area_from_edit = QLineEdit()
            area_from_edit.setValidator(int_validator)
            area_from_edit.setAlignment(Qt.AlignCenter)
            area_from_edit.setFont(font)
            self.area_from.append(area_from_edit)
            self.table.setCellWidget(row, 1, area_from_edit)

            area_to_edit = QLineEdit()
            area_to_edit.setValidator(int_validator)
            area_to_edit.setAlignment(Qt.AlignCenter)
            area_to_edit.setFont(font)
            self.area_to.append(area_to_edit)
            self.table.setCellWidget(row, 2, area_to_edit)

            percent_edit = QLineEdit()
            percent_edit.setValidator(int_validator)
            percent_edit.setAlignment(Qt.AlignCenter)
            percent_edit.setFont(font)
            self.percent.append(percent_edit)
            self.table.setCellWidget(row, 3, percent_edit)

        right_layout.addWidget(self.table)

        self.table.setFixedSize(505, 220)

        floor_layout = QHBoxLayout()
        font.setPointSize(9)
        self.floor_label = QLabel("Количество этажей")
        self.floor_label.setFixedWidth(150)
        self.floor_label.setFont(font)

        int_validator = QIntValidator(1, 100, self)
        font.setPointSize(12)
        self.floor_edit = QLineEdit()
        self.floor_edit.setValidator(int_validator)
        self.floor_edit.setFixedWidth(40)
        self.floor_edit.setFont(font)

        self.floor_label.setVisible(True)
        self.floor_edit.setVisible(True)
        floor_layout.addWidget(self.floor_label)
        floor_layout.addWidget(self.floor_edit, alignment=Qt.AlignLeft)

        right_layout.addLayout(floor_layout)

        button_font = QFont()
        button_font.setPointSize(9)
        button_font.setBold(False)

        self.generate_button = QPushButton("Сгенерировать")
        self.generate_button.setFixedHeight(50)
        self.generate_button.setFont(button_font)
        self.generate_button.clicked.connect(self.generate_clicked)

        self.save_button = QPushButton("Сохранить как PDF")
        self.save_button.setFixedHeight(50)
        self.save_button.setFont(button_font)
        self.save_button.setVisible(False)
        self.save_button.clicked.connect(self.save_as_pdf)

        self.clear_button = QPushButton("Очистить")
        self.clear_button.setFixedHeight(50)
        self.clear_button.setFont(button_font)
        self.clear_button.setVisible(False)
        self.clear_button.clicked.connect(self.clear_painter)

        font.setPointSize(12)
        self.error_text = QLabel("")
        self.error_text.setAlignment(Qt.AlignCenter)
        self.error_text.setFont(font)
        self.error_text.setFixedHeight(40)

        right_layout.addWidget(self.generate_button)
        right_layout.addWidget(self.error_text, alignment=Qt.AlignTop)

        bottom_buttons = QVBoxLayout()
        bottom_buttons.setAlignment(Qt.AlignBottom)
        bottom_buttons.addWidget(self.save_button)
        bottom_buttons.addWidget(self.clear_button)
        right_layout.addLayout(bottom_buttons)

        self.graphics_view.apartmentsGenerated.connect(self.after_generated)

        help_text = QLabel("ЛКМ - Добавить точку или лестницу/лифт, ПКМ - Перемещение, Delete - Удалить выбранную "
                           "точку. Красное выделение - лифт, Желтое выделение - лестница")

        self.elevator_button = QPushButton("Добавить лифт")
        self.elevator_button.clicked.connect(self.elevator_mode)
        self.elevator_button.setFixedWidth(200)
        self.elevator_button.setCheckable(True)

        self.stairs_button = QPushButton("Добавить лестницу")
        self.stairs_button.clicked.connect(self.stairs_mode)
        self.stairs_button.setFixedWidth(200)
        self.stairs_button.setCheckable(True)

        modes_layout = QHBoxLayout()
        modes_layout.setAlignment(Qt.AlignLeft)

        modes_layout.addWidget(self.elevator_button)
        modes_layout.addWidget(self.stairs_button)

        left_layout.addLayout(modes_layout)

        left_layout.addWidget(help_text)

        self.combo = QComboBox(self.graphics_view)
        self.combo.setFixedWidth(200)
        self.combo.setVisible(False)
        left_layout.addWidget(self.graphics_view)
        right_widget.setLayout(right_layout)
        left_widget.setLayout(left_layout)

        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)

        splitter.setSizes([1500, 1])

        self.setWindowTitle("Квартирограф")

        self.setGeometry(0, 0, 1500, 800)
        self.combo.move(self.graphics_view.width() // 2 + 50, 0)

        self.setFocus()

    def after_generated(self):
        self.generate_button.setText("Сгенерировать другой вариант")
        self.generate_button.setEnabled(True)
        self.graphics_view.interactive = False
        self.save_button.setVisible(True)
        self.clear_button.setVisible(True)
        self.combo.setVisible(True)
        for i in range(1, int(self.floor_edit.text()) + 1):
            self.combo.addItem(f"Этаж {i}")

    def generate_clicked(self):
        if not self.graphics_view.polygon:
            self.error_text.setText("Начертите периметр здания!")
        else:
            if not self.floor_edit.text():
                self.error_text.setText("Укажите количество этажей!")
            else:
                try:
                    apartment_table = {
                        'studio': {
                            'area_range': (int(self.area_from[0].text()), int(self.area_to[0].text())),
                            'percent': int(self.percent[0].text())
                        },
                        '1 room': {
                            'area_range': (int(self.area_from[1].text()), int(self.area_to[1].text())),
                            'percent': int(self.percent[1].text())
                        },
                        '2 room': {
                            'area_range': (int(self.area_from[2].text()), int(self.area_to[2].text())),
                            'percent': int(self.percent[2].text())
                        },
                        '3 room': {
                            'area_range': (int(self.area_from[3].text()), int(self.area_to[3].text())),
                            'percent': int(self.percent[3].text())
                        },
                        '4 room': {
                            'area_range': (int(self.area_from[4].text()), int(self.area_to[4].text())),
                            'percent': int(self.percent[4].text())
                        },
                    }
                    self.generate_button.setDisabled(True)
                    self.error_text.setText("")
                    self.graphics_view.fillApartments(apartment_table)
                except ValueError:
                    self.error_text.setText("Введите параметры квартир!")

    def save_as_pdf(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save as PDF", "", "PDF Files (*.pdf);;All Files (*)")

        if file_path:
            printer = QPrinter(QPrinter.HighResolution)
            printer.setOutputFormat(QPrinter.PdfFormat)
            printer.setOutputFileName(file_path)

            painter = QPainter(printer)
            self.graphics_view.scene.render(painter)
            painter.end()
            print(f"Saved as {file_path}")

    def clear_painter(self):
        self.graphics_view.scene.clear()
        self.graphics_view.polygon = None
        self.graphics_view.interactive = True
        self.graphics_view.points = []
        self.clear_button.setVisible(False)
        self.save_button.setVisible(False)
        self.generate_button.setText("Сгенерировать")
        self.combo.setVisible(False)

    def elevator_mode(self):
        if self.elevator_button.isChecked():
            self.stairs_button.setChecked(False)
            self.graphics_view.polygon.mode = "elevator"
        else:
            self.stairs_button.setChecked(False)
            self.elevator_button.setChecked(False)
            self.graphics_view.polygon.mode = "none"

    def stairs_mode(self):
        if self.stairs_button.isChecked():
            self.elevator_button.setChecked(False)
            self.graphics_view.polygon.mode = "stairs"
        else:
            self.elevator_button.setChecked(False)
            self.stairs_button.setChecked(False)
            self.graphics_view.polygon.mode = "none"
