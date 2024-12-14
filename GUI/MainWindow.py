<<<<<<< HEAD
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIntValidator, QFont, QPainter
from PyQt5.QtPrintSupport import QPrinter
from PyQt5.QtWidgets import QGraphicsScene, QMainWindow, QPushButton, QWidget, QVBoxLayout, QFrame, \
    QSplitter, QTableWidgetItem, QTableWidget, QLineEdit, QFileDialog, QLabel, QHBoxLayout, QComboBox, QDialog, \
    QCheckBox
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
        self.table.setColumnCount(5)
        self.table.setColumnWidth(0, 100)
        self.table.setColumnWidth(1, 100)
        self.table.setColumnWidth(2, 100)
        self.table.setColumnWidth(3, 100)
        self.table.setColumnWidth(4, 100)
        self.table.setHorizontalHeaderLabels(["Тип квартир", "Площадь от", "Площадь до", "Процент", "Количество"])

        self.table.verticalHeader().setVisible(False)

        apartment_types = ["Студии", "1-комн", "2-комн", "3-комн", "4-комн"]
        for row, apartment_type in enumerate(apartment_types):
            item = QTableWidgetItem(apartment_type)
            item.setFlags(Qt.ItemIsEnabled)
            self.table.setItem(row, 0, item)

        int_validator = QIntValidator(0, 1000000, self)

        font = QFont()
        font.setPointSize(10)

        self.area_from = []
        self.area_to = []
        self.percent = []
        self.number = []
        for row in range(5):
            area_from_edit = QLineEdit()
            area_from_edit.setValidator(int_validator)
            area_from_edit.setAlignment(Qt.AlignCenter)
            area_from_edit.setFont(font)
            area_from_edit.setText("0")
            self.area_from.append(area_from_edit)
            self.table.setCellWidget(row, 1, area_from_edit)

            area_to_edit = QLineEdit()
            area_to_edit.setValidator(int_validator)
            area_to_edit.setAlignment(Qt.AlignCenter)
            area_to_edit.setFont(font)
            area_to_edit.setText("0")
            self.area_to.append(area_to_edit)
            self.table.setCellWidget(row, 2, area_to_edit)

            percent_edit = QLineEdit()
            percent_edit.setValidator(int_validator)
            percent_edit.setAlignment(Qt.AlignCenter)
            percent_edit.setFont(font)
            percent_edit.setText("0")
            self.percent.append(percent_edit)
            self.table.setCellWidget(row, 3, percent_edit)

            number_edit = QLineEdit()
            number_edit.setValidator(int_validator)
            number_edit.setAlignment(Qt.AlignCenter)
            number_edit.setFont(font)
            number_edit.setText("0")
            self.number.append(number_edit)
            self.table.setCellWidget(row, 4, number_edit)

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
        self.floor_edit.setText("1")

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

        font.setPointSize(9)
        self.checkbox = QCheckBox(text="Показать квартиры")
        self.checkbox.setVisible(False)
        self.checkbox.stateChanged.connect(self.onStateChanged)
        self.checkbox.setFont(font)
        check_layout = QVBoxLayout()
        check_layout.setAlignment(Qt.AlignTop)
        check_layout.addWidget(self.checkbox)

        right_layout.addWidget(self.generate_button)
        right_layout.addWidget(self.error_text)
        right_layout.addLayout(check_layout, Qt.AlignTop)

        bottom_buttons = QVBoxLayout()
        bottom_buttons.setAlignment(Qt.AlignBottom)
        bottom_buttons.addWidget(self.save_button)
        bottom_buttons.addWidget(self.clear_button)
        right_layout.addLayout(bottom_buttons)

        self.graphics_view.apartmentsGenerated.connect(self.after_generated)

        help_text = QLabel("ЛКМ - Добавить точку или лестницу/лифт, ПКМ - Перемещение, Delete - Удалить выбранную "
                           "точку. Красное выделение - лифт, Желтое выделение - лестница")

        self.elevator_button = QPushButton("Добавить лифт")
        self.elevator_button.clicked.connect(lambda: self.show_rectangle_dialog("elevator"))
        self.elevator_button.setFixedWidth(200)

        self.stairs_button = QPushButton("Добавить лестницу")
        self.stairs_button.clicked.connect(lambda: self.show_rectangle_dialog("stairs"))
        self.stairs_button.setFixedWidth(200)

        self.add_point_button = QPushButton("Добавить точку")
        self.add_point_button.clicked.connect(self.graphics_view.add_preview_point)
        self.add_point_button.setFixedWidth(200)

        self.add_building_button = QPushButton("Добавить здание")
        self.add_building_button.clicked.connect(self.graphics_view.add_building)
        self.add_building_button.setFixedWidth(200)

        modes_layout = QHBoxLayout()
        modes_layout.setAlignment(Qt.AlignLeft)

        modes_layout.addWidget(self.elevator_button)
        modes_layout.addWidget(self.stairs_button)
        modes_layout.addWidget(self.add_point_button)
        modes_layout.addWidget(self.add_building_button)


        left_layout.addLayout(modes_layout)

        left_layout.addWidget(help_text)

        self.combo = QComboBox(self.graphics_view)
        self.combo.setFixedWidth(200)
        self.combo.setVisible(False)
        self.combo.activated.connect(self.index_changed)

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

        self.graphics_view.add_point(-10, -10)
        self.graphics_view.add_point(-10, 10)
        self.graphics_view.add_point(10, -10)
        self.graphics_view.add_point(10, 10)
        self.graphics_view.update_shape()

    def index_changed(self, index):
        self.graphics_view.show_floor(index, self.checkbox.isChecked())
        self.combo.setCurrentIndex(index)

    def onStateChanged(self):
        self.graphics_view.show_floor(self.combo.currentIndex(), self.checkbox.isChecked())

    def after_generated(self):
        self.generate_button.setText("Сгенерировать другой вариант")
        self.generate_button.setEnabled(True)
        self.graphics_view.interactive = False
        self.checkbox.setVisible(True)
        self.save_button.setVisible(True)
        self.clear_button.setVisible(True)
        self.elevator_button.setDisabled(True)
        self.stairs_button.setDisabled(True)
        self.combo.setVisible(True)
        self.combo.clear()
        self.error_text.setText("")
        for i in range(1, int(self.floor_edit.text()) + 1):
            self.combo.addItem(f"Этаж {i}")

    def generate_clicked(self):
        if not self.graphics_view.polygon:
            self.error_text.setText("Начертите периметр здания!")
        else:
            if not self.floor_edit.text():
                self.error_text.setText("Укажите количество этажей!")
            else:
                apartment_table = {
                    'studio': {
                        'area_range': (int(self.area_from[0].text()), int(self.area_to[0].text())),
                        'percent': int(self.percent[0].text()),
                        'number': int(self.number[0].text())
                    },
                    '1 room': {
                        'area_range': (int(self.area_from[1].text()), int(self.area_to[1].text())),
                        'percent': int(self.percent[1].text()),
                        'number': int(self.number[1].text())

                    },
                    '2 room': {
                        'area_range': (int(self.area_from[2].text()), int(self.area_to[2].text())),
                        'percent': int(self.percent[2].text()),
                        'number': int(self.number[2].text())

                    },
                    '3 room': {
                        'area_range': (int(self.area_from[3].text()), int(self.area_to[3].text())),
                        'percent': int(self.percent[3].text()),
                        'number': int(self.number[3].text())

                    },
                    '4 room': {
                        'area_range': (int(self.area_from[4].text()), int(self.area_to[4].text())),
                        'percent': int(self.percent[4].text()),
                        'number': int(self.number[4].text())

                    },
                }
                all_zero = True

                for apartment, details in apartment_table.items():
                    if any(value != 0 for key, value in details.items() if isinstance(value, int)):
                        all_zero = False
                        break

                if all_zero:
                    self.error_text.setText("Введите параметры квартир!")
                elif (int(self.percent[0].text()) + int(self.percent[1].text()) + int(self.percent[2].text()) + int(self.percent[3].text()) + int(self.percent[4].text())) != 100:
                    self.error_text.setText("Сумма процентов должна быть равна 100!")
                else:
                    self.generate_button.setDisabled(True)
                    self.error_text.setText("Генерация...")
                    self.graphics_view.fillApartments(apartment_table, int(self.floor_edit.text()))

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
        self.elevator_button.setDisabled(False)
        self.stairs_button.setDisabled(False)
        self.generate_button.setText("Сгенерировать")
        self.combo.setVisible(False)
        self.graphics_view.add_point(-10, -10)
        self.graphics_view.add_point(-10, 10)
        self.graphics_view.add_point(10, -10)
        self.graphics_view.add_point(10, 10)
        self.graphics_view.update_shape()

    def show_rectangle_dialog(self, mode):
        dialog = RectangleDialog()
        if dialog.exec_():
            size = dialog.get_size()
            if size:
                self.graphics_view.set_preview_rectangle(*size, mode)
            else:
                print("Неверный размер")


class RectangleDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Выберите размер")
        self.setFixedSize(300, 200)
        self.width_input = QLineEdit()
        self.height_input = QLineEdit()

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Ширина, м:"))
        layout.addWidget(self.width_input)
        layout.addWidget(QLabel("Длина, м:"))
        layout.addWidget(self.height_input)

        button_layout = QHBoxLayout()
        ok_button = QPushButton("OK")
        cancel_button = QPushButton("Закрыть")
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)

        layout.addLayout(button_layout)
        self.setLayout(layout)

        ok_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)

    def get_size(self):
        try:
            width = int(self.width_input.text())
            height = int(self.height_input.text())
            return width, height
        except ValueError:
            return None
=======
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIntValidator, QFont, QPainter
from PyQt5.QtPrintSupport import QPrinter
from PyQt5.QtWidgets import QGraphicsScene, QMainWindow, QPushButton, QWidget, QVBoxLayout, QFrame, \
    QSplitter, QTableWidgetItem, QTableWidget, QLineEdit, QFileDialog, QLabel, QHBoxLayout, QComboBox, QDialog, \
    QCheckBox
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
            area_from_edit.setText("0")
            self.area_from.append(area_from_edit)
            self.table.setCellWidget(row, 1, area_from_edit)

            area_to_edit = QLineEdit()
            area_to_edit.setValidator(int_validator)
            area_to_edit.setAlignment(Qt.AlignCenter)
            area_to_edit.setFont(font)
            area_to_edit.setText("0")
            self.area_to.append(area_to_edit)
            self.table.setCellWidget(row, 2, area_to_edit)

            percent_edit = QLineEdit()
            percent_edit.setValidator(int_validator)
            percent_edit.setAlignment(Qt.AlignCenter)
            percent_edit.setFont(font)
            percent_edit.setText("0")
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
        self.floor_edit.setText("1")

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

        font.setPointSize(9)
        self.checkbox = QCheckBox(text="Показать квартиры")
        self.checkbox.setVisible(False)
        self.checkbox.stateChanged.connect(self.onStateChanged)
        self.checkbox.setFont(font)
        check_layout = QVBoxLayout()
        check_layout.setAlignment(Qt.AlignTop)
        check_layout.addWidget(self.checkbox)

        right_layout.addWidget(self.generate_button)
        right_layout.addWidget(self.error_text)
        right_layout.addLayout(check_layout, Qt.AlignTop)

        bottom_buttons = QVBoxLayout()
        bottom_buttons.setAlignment(Qt.AlignBottom)
        bottom_buttons.addWidget(self.save_button)
        bottom_buttons.addWidget(self.clear_button)
        right_layout.addLayout(bottom_buttons)

        self.graphics_view.apartmentsGenerated.connect(self.after_generated)

        help_text = QLabel("ЛКМ - Добавить точку или лестницу/лифт, ПКМ - Перемещение, Delete - Удалить выбранную "
                           "точку. Красное выделение - лифт, Желтое выделение - лестница")

        self.elevator_button = QPushButton("Добавить лифт")
        self.elevator_button.clicked.connect(lambda: self.show_rectangle_dialog("elevator"))
        self.elevator_button.setFixedWidth(200)

        self.stairs_button = QPushButton("Добавить лестницу")
        self.stairs_button.clicked.connect(lambda: self.show_rectangle_dialog("stairs"))
        self.stairs_button.setFixedWidth(200)

        self.add_point_button = QPushButton("Добавить точку")
        self.add_point_button.clicked.connect(self.graphics_view.add_preview_point)
        self.add_point_button.setFixedWidth(200)

        modes_layout = QHBoxLayout()
        modes_layout.setAlignment(Qt.AlignLeft)

        modes_layout.addWidget(self.elevator_button)
        modes_layout.addWidget(self.stairs_button)
        modes_layout.addWidget(self.add_point_button)

        left_layout.addLayout(modes_layout)

        left_layout.addWidget(help_text)

        self.combo = QComboBox(self.graphics_view)
        self.combo.setFixedWidth(200)
        self.combo.setVisible(False)
        self.combo.activated.connect(self.index_changed)

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

        self.graphics_view.add_point(-100, -100)
        self.graphics_view.add_point(-100, 100)
        self.graphics_view.add_point(100, -100)
        self.graphics_view.add_point(100, 100)
        self.graphics_view.update_shape()

    def index_changed(self, index):
        self.graphics_view.show_floor(index, self.checkbox.isChecked())
        self.combo.setCurrentIndex(index)

    def onStateChanged(self):
        self.graphics_view.show_floor(self.combo.currentIndex(), self.checkbox.isChecked())

    def after_generated(self):
        self.generate_button.setText("Сгенерировать другой вариант")
        self.generate_button.setEnabled(True)
        self.graphics_view.interactive = False
        self.checkbox.setVisible(True)
        self.save_button.setVisible(True)
        self.clear_button.setVisible(True)
        self.combo.setVisible(True)
        self.combo.clear()
        self.error_text.setText("")
        for i in range(1, int(self.floor_edit.text()) + 1):
            self.combo.addItem(f"Этаж {i}")

    def generate_clicked(self):
        if not self.graphics_view.polygon:
            self.error_text.setText("Начертите периметр здания!")
        else:
            if not self.floor_edit.text():
                self.error_text.setText("Укажите количество этажей!")
            else:
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
                all_zero = True

                for apartment, details in apartment_table.items():
                    if any(value != 0 for key, value in details.items() if isinstance(value, int)):
                        all_zero = False
                        break

                if all_zero:
                    self.error_text.setText("Введите параметры квартир!")
                else:
                    self.generate_button.setDisabled(True)
                    self.error_text.setText("Генерация...")
                    self.graphics_view.fillApartments(apartment_table, int(self.floor_edit.text()))

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

    def show_rectangle_dialog(self, mode):
        dialog = RectangleDialog()
        if dialog.exec_():
            size = dialog.get_size()
            if size:
                self.graphics_view.set_preview_rectangle(*size, mode)
            else:
                print("Неверный размер")


class RectangleDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Выберите размер")
        self.setFixedSize(300, 200)
        self.width_input = QLineEdit()
        self.height_input = QLineEdit()

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Ширина, м:"))
        layout.addWidget(self.width_input)
        layout.addWidget(QLabel("Длина, м:"))
        layout.addWidget(self.height_input)

        button_layout = QHBoxLayout()
        ok_button = QPushButton("OK")
        cancel_button = QPushButton("Закрыть")
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)

        layout.addLayout(button_layout)
        self.setLayout(layout)

        ok_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)

    def get_size(self):
        try:
            width = int(self.width_input.text())
            height = int(self.height_input.text())
            return width, height
        except ValueError:
            return None
>>>>>>> 03dfb9510b1b841f741c0c76a6d6795ed7416cdb
