from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QIntValidator, QFont, QPainter, QPen, QColor, QPageLayout
from PyQt5.QtPrintSupport import QPrinter
from PyQt5.QtWidgets import QGraphicsScene, QMainWindow, QPushButton, QWidget, QVBoxLayout, QFrame, \
    QSplitter, QTableWidgetItem, QTableWidget, QLineEdit, QFileDialog, QLabel, QHBoxLayout, QComboBox, QDialog, \
    QCheckBox, QGraphicsPolygonItem, QGraphicsRectItem, QGraphicsTextItem
from GUI.Painter.Painter import Painter
from GUI.Painter.RotationHandle import RotationHandle

apt_colors = {
    'studio': '#fa6b6b',
    '1 room': '#6dd170',
    '2 room': '#6db8d1',
    '3 room': '#ed975a',
    '4 room': '#ba7ed9'
}
room_colors = {
    'kitchen': '#FF9999',
    'bathroom': '#99FF99',
    'hall': '#9999FF',
    'living room': '#FFCC99',
    'bedroom': '#CC99FF',
}


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.generating = False
        splitter = QSplitter(Qt.Horizontal)
        self.setCentralWidget(splitter)
        self.scene = QGraphicsScene()
        self.done = False
        self.output_tables = None

        self.graphics_view = Painter(self.scene)
        self.graphics_view.setFrameShape(QFrame.StyledPanel)
        right_widget = QWidget()
        self.right_layout = QVBoxLayout()

        self.right_layout.setAlignment(Qt.AlignTop)

        left_widget = QWidget()
        left_layout = QVBoxLayout()

        left_layout.setAlignment(Qt.AlignTop)

        font = QFont()
        font.setPointSize(9)

        self.table = QTableWidget()
        self.table.setFont(font)
        self.table.setRowCount(5)
        self.table.setColumnCount(5)
        self.table.setColumnWidth(0, 100)
        self.table.setColumnWidth(1, 100)
        self.table.setColumnWidth(2, 100)
        self.table.setColumnWidth(3, 100)
        self.table.setColumnWidth(4, 100)
        self.table.setHorizontalHeaderLabels(["Тип квартир", "Площадь от", "Площадь до", "Процент", "Количество"])

        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setFont(font)

        apartment_types = ["Студии", "1-комн", "2-комн", "3-комн", "4-комн"]
        for row, apartment_type in enumerate(apartment_types):
            item = QTableWidgetItem(apartment_type)
            item.setFlags(Qt.ItemIsEnabled)
            self.table.setItem(row, 0, item)

        int_validator = QIntValidator(0, 1000000, self)

        font = QFont()
        font.setPointSize(10)

        self.building_combo = QComboBox(self.graphics_view)
        self.building_combo.setFixedWidth(200)
        self.building_combo.activated.connect(self.building_changed)
        self.building_combo.addItem("Здание 1")
        self.previous_index = self.building_combo.currentIndex()

        self.area_from = []
        self.area_to = []
        self.percent = []
        self.number = []

        self.building_tables = []

        area_from = ["25", "40", "58", "78", "100"]
        area_to = ["35", "55", "75", "98", "135"]
        percent = ["0", "0", "0", "0", "0"]
        number = ["0", "0", "0", "0", "0"]
        for row in range(5):
            area_from_edit = QLineEdit()
            area_from_edit.setValidator(int_validator)
            area_from_edit.setAlignment(Qt.AlignCenter)
            area_from_edit.setFont(font)
            area_from_edit.setText(area_from[row])
            self.area_from.append(area_from_edit)
            self.table.setCellWidget(row, 1, area_from_edit)

            area_to_edit = QLineEdit()
            area_to_edit.setValidator(int_validator)
            area_to_edit.setAlignment(Qt.AlignCenter)
            area_to_edit.setFont(font)
            area_to_edit.setText(area_to[row])
            self.area_to.append(area_to_edit)
            self.table.setCellWidget(row, 2, area_to_edit)

            percent_edit = QLineEdit()
            percent_edit.setValidator(int_validator)
            percent_edit.setAlignment(Qt.AlignCenter)
            percent_edit.setFont(font)
            percent_edit.setText(percent[row])
            self.percent.append(percent_edit)
            self.table.setCellWidget(row, 3, percent_edit)

            number_edit = QLineEdit()
            number_edit.setValidator(int_validator)
            number_edit.setAlignment(Qt.AlignCenter)
            number_edit.setFont(font)
            number_edit.setText(number[row])
            self.number.append(number_edit)
            self.table.setCellWidget(row, 4, number_edit)

        self.building_tables.append([area_from, area_to, percent, number])

        self.right_layout.addWidget(self.building_combo)
        self.right_layout.addWidget(self.table)
        self.table.setFixedSize(505, 220)

        floor_layout = QHBoxLayout()
        font.setPointSize(9)
        self.floor_label = QLabel("Количество этажей")
        self.floor_label.setFixedWidth(140)
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

        font.setPointSize(9)
        self.checkbox = QCheckBox(text="Показать квартиры")
        self.checkbox.setVisible(False)
        self.checkbox.stateChanged.connect(self.toggle_floors)
        self.checkbox.setFont(font)
        self.checkbox.setFixedHeight(40)
        self.checkbox.setFixedWidth(250)
        self.checkbox.setStyleSheet("QCheckBox { border: none; }")

        floor_layout.addWidget(self.floor_label)
        floor_layout.addWidget(self.floor_edit, alignment=Qt.AlignLeft)
        floor_layout.addWidget(self.checkbox, alignment=Qt.AlignLeft)

        self.right_layout.addLayout(floor_layout)

        self.auto_check = QCheckBox(text="Автокоррекция количества квартир")
        self.auto_check.setFont(font)
        self.auto_check.setFixedHeight(40)
        self.auto_check.setFixedWidth(400)
        self.auto_check.setStyleSheet("QCheckBox { border: none; }")

        self.right_layout.addWidget(self.auto_check)

        button_font = QFont()
        button_font.setPointSize(10)
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

        font.setPointSize(10)
        self.error_text = QLabel("")
        self.error_text.setAlignment(Qt.AlignCenter)
        self.error_text.setFont(font)
        self.error_text.setFixedHeight(60)

        self.right_layout.addWidget(self.generate_button)
        self.right_layout.addWidget(self.error_text)

        self.output_label = QLabel("Результирующая таблица")
        font.setPointSize(9)
        self.output_label.setFont(font)
        self.output_label.setVisible(False)
        self.right_layout.addWidget(self.output_label, alignment=Qt.AlignCenter)

        # таблица вывода
        font.setPointSize(10)
        self.output_table = QTableWidget()
        self.output_table.setVisible(False)
        self.output_table.setRowCount(6)
        self.output_table.setColumnCount(5)
        self.output_table.setColumnWidth(0, 100)
        self.output_table.setColumnWidth(1, 100)
        self.output_table.setColumnWidth(2, 100)
        self.output_table.setColumnWidth(3, 100)
        self.output_table.setColumnWidth(4, 100)
        self.output_table.setFont(font)
        self.output_table.setHorizontalHeaderLabels(["Тип квартир", "Ср. площадь", "Процент", "Количество", "Ошибка"])
        self.output_table.horizontalHeader().setFont(font)

        self.output_table.verticalHeader().setVisible(False)

        apartment_types = ["Студии", "1-комн", "2-комн", "3-комн", "4-комн", "Ср. ошибка"]
        for row, apartment_type in enumerate(apartment_types):
            item = QTableWidgetItem(apartment_type)
            item.setFlags(Qt.ItemIsEnabled)
            self.output_table.setItem(row, 0, item)

        self.output_av_area = []
        self.output_percent = []
        self.output_number = []
        self.output_error = []
        for row in range(5):
            av_area_cell = QLineEdit()
            av_area_cell.setAlignment(Qt.AlignCenter)
            av_area_cell.setFont(font)
            av_area_cell.setText("0")
            av_area_cell.setReadOnly(True)
            self.output_av_area.append(av_area_cell)
            self.output_table.setCellWidget(row, 1, av_area_cell)

            percent_cell = QLineEdit()
            percent_cell.setAlignment(Qt.AlignCenter)
            percent_cell.setFont(font)
            percent_cell.setText("0")
            percent_cell.setReadOnly(True)
            self.output_percent.append(percent_cell)
            self.output_table.setCellWidget(row, 2, percent_cell)

            number_cell = QLineEdit()
            number_cell.setAlignment(Qt.AlignCenter)
            number_cell.setFont(font)
            number_cell.setText("0")
            number_cell.setReadOnly(True)
            self.output_number.append(number_cell)
            self.output_table.setCellWidget(row, 3, number_cell)

            error_cell = QLineEdit()
            error_cell.setAlignment(Qt.AlignCenter)
            error_cell.setFont(font)
            error_cell.setText("0")
            error_cell.setReadOnly(True)
            self.output_error.append(error_cell)
            self.output_table.setCellWidget(row, 4, error_cell)

        av_error_cell = QLineEdit()
        av_error_cell.setAlignment(Qt.AlignCenter)
        av_error_cell.setFont(font)
        av_error_cell.setText("0")
        av_error_cell.setReadOnly(True)
        self.output_av_error = av_error_cell
        self.output_table.setCellWidget(5, 1, av_error_cell)
        self.output_table.setSpan(5, 1, 1, 4)
        self.output_table.setFixedSize(505, 255)

        self.right_layout.addWidget(self.output_table)

        bottom_buttons = QVBoxLayout()
        bottom_buttons.setAlignment(Qt.AlignBottom)
        bottom_buttons.addWidget(self.save_button)
        bottom_buttons.addWidget(self.clear_button)
        self.right_layout.addLayout(bottom_buttons, Qt.AlignTop)

        self.graphics_view.apartmentsGenerated.connect(self.after_generated)

        help_text = QLabel(
            "ПКМ - Перемещение, Delete - Удалить выбранную точку. Для добавления деформационного шва выберите две точки")

        self.elevator_button = QPushButton("Добавить лифт")
        self.elevator_button.clicked.connect(lambda: self.show_rectangle_dialog("elevator"))
        self.elevator_button.setFixedWidth(180)
        self.elevator_button.setDisabled(True)

        self.stairs_button = QPushButton("Добавить лестницу")
        self.stairs_button.clicked.connect(lambda: self.show_rectangle_dialog("stairs"))
        self.stairs_button.setFixedWidth(180)
        self.stairs_button.setDisabled(True)

        self.add_point_button = QPushButton("Добавить точку")
        self.add_point_button.clicked.connect(self.add_point)
        self.add_point_button.setFixedWidth(180)

        self.add_building_button = QPushButton("Добавить здание")
        self.add_building_button.clicked.connect(self.add_building)
        self.add_building_button.setFixedWidth(180)

        self.add_section_button = QPushButton("Добавить ДШ")
        self.add_section_button.clicked.connect(self.add_section)
        self.add_section_button.setFixedWidth(180)

        modes_layout = QHBoxLayout()
        modes_layout.setAlignment(Qt.AlignLeft)

        modes_layout.addWidget(self.elevator_button)
        modes_layout.addWidget(self.stairs_button)
        modes_layout.addWidget(self.add_point_button)
        modes_layout.addWidget(self.add_building_button)
        modes_layout.addWidget(self.add_section_button)

        left_layout.addLayout(modes_layout)

        left_layout.addWidget(help_text)

        self.combo = QComboBox(self.graphics_view)
        self.combo.setFixedWidth(200)
        self.combo.setVisible(False)
        self.combo.activated.connect(self.index_changed)

        left_layout.addWidget(self.graphics_view)
        right_widget.setLayout(self.right_layout)
        left_widget.setLayout(left_layout)

        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)

        splitter.setSizes([1500, 1])

        self.setWindowTitle("Квартирограф")

        self.setGeometry(0, 0, 1500, 900)
        self.combo.move(self.graphics_view.width() // 2 + 50, 0)

        self.setFocus()

        self.graphics_view.add_point(-10, -10)
        self.graphics_view.add_point(-10, 10)
        self.graphics_view.add_point(10, -10)
        self.graphics_view.add_point(10, 10)
        self.graphics_view.update_shape()

        self.graphics_view.point_added.connect(self.unlock_buttons)
        self.graphics_view.building_added.connect(self.unlock_buttons)
        self.graphics_view.section_added.connect(self.unlock_buttons)

    def building_changed(self, index):
        if hasattr(self, 'previous_index') and self.previous_index is not None:
            if self.previous_index < len(self.building_tables):
                area_from = [area.text() for area in self.area_from]
                area_to = [area.text() for area in self.area_to]
                percent = [perc.text() for perc in self.percent]
                number = [num.text() for num in self.number]

                self.building_tables[self.previous_index] = [area_from, area_to, percent, number]

        building = self.building_tables[index]
        area_from = building[0]
        area_to = building[1]
        percent = building[2]
        number = building[3]

        for row in range(5):
            self.area_from[row].setText(area_from[row])
            self.area_to[row].setText(area_to[row])
            self.percent[row].setText(percent[row])
            self.number[row].setText(number[row])

        self.previous_index = index
        self.graphics_view.polygon = list(self.graphics_view.polygons.keys())[index]
        self.graphics_view.points = list(self.graphics_view.polygons.values())[index]
        if self.done:
            building_output = self.output_tables[self.building_combo.currentIndex()]
            av_area = [building_output['studio']['average_area'], building_output['1 room']['average_area'],
                       building_output['2 room']['average_area'], building_output['3 room']['average_area'],
                       building_output['4 room']['average_area']]
            percent = [building_output['studio']['percent'], building_output['1 room']['percent'],
                       building_output['2 room']['percent'], building_output['3 room']['percent'],
                       building_output['4 room']['percent']]
            number = [building_output['studio']['number'], building_output['1 room']['number'],
                      building_output['2 room']['number'], building_output['3 room']['number'],
                      building_output['4 room']['number']]
            error = [building_output['studio']['error'], building_output['1 room']['error'],
                     building_output['2 room']['error'], building_output['3 room']['error'],
                     building_output['4 room']['error']]
            average_error = building_output['average_error']

            for row in range(5):
                self.output_av_area[row].setText(str(av_area[row]))
                self.output_percent[row].setText(str(percent[row]))
                self.output_number[row].setText(str(number[row]))
                self.output_error[row].setText(str(error[row]))

            self.output_av_error.setText(str(average_error))

    def add_building(self):
        if hasattr(self, 'previous_index') and self.previous_index is not None:
            if self.previous_index < len(self.building_tables):
                area_from = [area.text() for area in self.area_from]
                area_to = [area.text() for area in self.area_to]
                percent = [perc.text() for perc in self.percent]
                number = [num.text() for num in self.number]
                self.building_tables[self.previous_index] = [area_from, area_to, percent, number]

        area_from = ["25", "40", "58", "78", "100"]
        area_to = ["35", "55", "75", "98", "135"]
        number = ["0", "0", "0", "0", "0"]
        percent = ["0", "0", "0", "0", "0"]

        new_building = [area_from, area_to, percent, number]
        self.building_tables.append(new_building)

        self.building_combo.addItem(f"Здание {len(self.building_tables)}")
        self.building_combo.setCurrentIndex(len(self.building_tables) - 1)

        for row in range(5):
            self.area_from[row].setText(area_from[row])
            self.area_to[row].setText(area_to[row])
            self.percent[row].setText(percent[row])
            self.number[row].setText(number[row])

        self.previous_index = len(self.building_tables) - 1

        self.graphics_view.add_building()
        self.lock_buttons()

    def add_section(self):
        self.graphics_view.add_section()
        self.lock_buttons()

    def add_point(self):
        self.graphics_view.add_preview_point()
        self.lock_buttons()

    def lock_buttons(self):
        self.add_point_button.setDisabled(True)
        self.add_building_button.setDisabled(True)
        self.add_section_button.setDisabled(True)

    def unlock_buttons(self):
        self.add_point_button.setDisabled(False)
        self.add_building_button.setDisabled(False)
        self.add_section_button.setDisabled(False)

    def index_changed(self, index):
        self.graphics_view.show_floor(index, self.checkbox.isChecked())
        self.combo.setCurrentIndex(index)

    def toggle_floors(self):
        self.graphics_view.show_floor(self.combo.currentIndex(), self.checkbox.isChecked())

    def after_generated(self):
        if self.graphics_view.generator_error != "":
            self.generate_button.setDisabled(False)
            self.graphics_view.interactive = True
            self.error_text.setText(self.graphics_view.generator_error)
        else:
            self.done = True
            self.generate_button.setText("Сгенерировать другой вариант")
            self.add_point_button.setEnabled(False)
            self.add_building_button.setEnabled(False)
            self.generate_button.setEnabled(True)
            self.graphics_view.interactive = True
            self.checkbox.setVisible(True)
            self.save_button.setVisible(True)
            self.clear_button.setVisible(True)
            self.elevator_button.setDisabled(False)
            self.stairs_button.setDisabled(False)
            self.combo.setVisible(True)
            self.add_section_button.setDisabled(True)
            self.combo.clear()
            self.error_text.setText("")

            self.checkbox.setChecked(False)
            self.clear_button.setDisabled(False)
            self.save_button.setDisabled(False)
            for i in range(1, int(self.floor_edit.text()) + 1):
                self.combo.addItem(f"Этаж {i}")

            self.output_table.setVisible(True)
            self.output_label.setVisible(True)
            self.output_tables = self.graphics_view.output_tables
            building_output = self.output_tables[self.building_combo.currentIndex()]
            av_area = [building_output['studio']['average_area'], building_output['1 room']['average_area'],
                       building_output['2 room']['average_area'], building_output['3 room']['average_area'],
                       building_output['4 room']['average_area']]
            percent = [building_output['studio']['percent'], building_output['1 room']['percent'],
                       building_output['2 room']['percent'], building_output['3 room']['percent'],
                       building_output['4 room']['percent']]
            number = [building_output['studio']['number'], building_output['1 room']['number'],
                      building_output['2 room']['number'], building_output['3 room']['number'],
                      building_output['4 room']['number']]
            error = [building_output['studio']['error'], building_output['1 room']['error'],
                     building_output['2 room']['error'], building_output['3 room']['error'],
                     building_output['4 room']['error']]
            average_error = building_output['average_error']
            for row in range(5):
                self.output_av_area[row].setText(str(av_area[row]))
                self.output_percent[row].setText(str(percent[row]))
                self.output_number[row].setText(str(number[row]))
                self.output_error[row].setText(str(error[row]))

            self.output_av_error.setText(str(average_error))
            if int(self.floor_edit.text()) > 1:
                self.combo.setCurrentIndex(1)
                self.graphics_view.show_floor(1, self.checkbox.isChecked())

    def generate_clicked(self):
        apartment_tables = []
        area_from = [area.text() for area in self.area_from]
        area_to = [area.text() for area in self.area_to]
        percent = [perc.text() for perc in self.percent]
        number = [num.text() for num in self.number]

        self.building_tables[self.building_combo.currentIndex()] = [area_from, area_to, percent, number]
        if not self.graphics_view.polygon:
            self.error_text.setText("Начертите периметр здания!")
        else:
            if not self.floor_edit.text():
                self.error_text.setText("Укажите количество этажей!")
            else:
                for building in self.building_tables:
                    apartment_table = {
                        'studio': {
                            'area_range': (int(building[0][0]), int(building[1][0])),
                            'percent': int(building[2][0]),
                            'number': int(building[3][0])
                        },
                        '1 room': {
                            'area_range': (int(building[0][1]), int(building[1][1])),
                            'percent': int(building[2][1]),
                            'number': int(building[3][1])
                        },
                        '2 room': {
                            'area_range': (int(building[0][2]), int(building[1][2])),
                            'percent': int(building[2][2]),
                            'number': int(building[3][2])
                        },
                        '3 room': {
                            'area_range': (int(building[0][3]), int(building[1][3])),
                            'percent': int(building[2][3]),
                            'number': int(building[3][3])
                        },
                        '4 room': {
                            'area_range': (int(building[0][4]), int(building[1][4])),
                            'percent': int(building[2][4]),
                            'number': int(building[3][4])
                        },
                    }
                    apartment_tables.append(apartment_table)
                first_check_index = -1
                second_check_index = -1
                third_check_index = -1
                for i in range(len(apartment_tables)):
                    for apartment, details in apartment_tables[i].items():
                        if (details["area_range"][0] == 0) or (details["area_range"][1] == 0):
                            first_check_index = i
                        if details["percent"] != 0 and details["number"] == 0:
                            third_check_index = i
                    sum_percent = 0
                    for apartment, details in apartment_tables[i].items():
                        sum_percent += details["percent"]
                    if sum_percent != 100:
                        second_check_index = i
                if first_check_index != -1:
                    self.error_text.setText(f"Введите параметры квартир для здания №{first_check_index+1}!")
                elif second_check_index != -1:
                    self.error_text.setText(f"Сумма процентов должна быть равна 100 для здания №{second_check_index+1}!")
                elif third_check_index != -1:
                    self.error_text.setText(f"Введите количество квартир для здания №{third_check_index+1}!")
                else:
                    if self.generate_button.text() == "Сгенерировать другой вариант":
                        self.generate_button.setDisabled(True)
                        self.graphics_view.interactive = False
                        self.generate_button.setDisabled(True)
                        self.clear_button.setDisabled(True)
                        self.save_button.setDisabled(True)
                        self.elevator_button.setDisabled(True)
                        self.stairs_button.setDisabled(True)
                        for room in self.graphics_view.rooms:
                            self.scene.removeItem(room)
                        for filled_shape in self.graphics_view.floor_figures:
                            self.scene.removeItem(filled_shape)
                        for apt_area in self.graphics_view.apt_areas:
                            self.scene.removeItem(apt_area)
                        for room_area in self.graphics_view.room_areas:
                            self.scene.removeItem(room_area)
                        for window in self.graphics_view.window_items:
                            self.scene.removeItem(window)
                    self.error_text.setText("Генерация...")
                    self.graphics_view.fillApartments(apartment_tables, int(self.floor_edit.text()),
                                                      self.auto_check.isChecked())

    def save_as_pdf(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save as PDF", "", "PDF Files (*.pdf);;All Files (*)")

        if file_path:
            previous_floor = self.combo.currentIndex()
            self.error_text.setText("Сохранение...")
            self.generate_button.setDisabled(True)
            self.clear_button.setDisabled(True)
            self.save_button.setDisabled(True)
            self.elevator_button.setDisabled(True)
            self.stairs_button.setDisabled(True)
            for child in self.graphics_view.scene.items():
                if isinstance(child, RotationHandle):
                    self.graphics_view.scene.removeItem(child)
            printer = QPrinter(QPrinter.HighResolution)
            printer.setOutputFormat(QPrinter.PdfFormat)
            printer.setOutputFileName(file_path)
            printer.setPageOrientation(QPageLayout.Portrait)

            painter = QPainter(printer)

            total_floors = int(self.floor_edit.text())
            margin = 600
            spacing_between_parts = 1
            size = 5000

            for i in range(total_floors):
                if i > 0:
                    printer.newPage()

                font = QFont("Arial", 15)
                painter.setFont(font)
                painter.drawText(4300, 100, f"Этаж {i+1}")
                y_offset = 200
                font = QFont("Arial", 8)
                painter.setFont(font)

                x_start = 0
                y_start = y_offset + 50
                box_size = 60
                spacing = 100

                painter.drawText(x_start, y_start, "Типы квартир")
                y_start += spacing
                for label, color in apt_colors.items():
                    painter.setBrush(QColor(color))
                    painter.setPen(Qt.NoPen)
                    painter.drawRect(x_start, y_start, box_size, box_size)
                    painter.setPen(Qt.black)
                    painter.setBrush(Qt.NoBrush)
                    painter.drawText(x_start + box_size + spacing, y_start + box_size - 5, label)
                    y_start += box_size + spacing

                scene_rect = self.graphics_view.scene.itemsBoundingRect()
                x_offset = 2500
                self.graphics_view.show_floor(i, False)
                painter.save()
                painter.translate(x_offset, 2 * margin)
                self.graphics_view.scene.render(painter, QRectF(0, 0, size, size), scene_rect)
                painter.restore()

                x_start = 0
                y_start = 2 * margin + size + spacing_between_parts + y_offset + 50

                painter.drawText(x_start, y_start, "Типы комнат")
                y_start += spacing
                for label, color in room_colors.items():
                    painter.setBrush(QColor(color))
                    painter.setPen(Qt.NoPen)
                    painter.drawRect(x_start, y_start, box_size, box_size)
                    painter.setPen(Qt.black)
                    painter.setBrush(Qt.NoBrush)
                    painter.drawText(x_start + box_size + spacing, y_start + box_size - 5, label)
                    y_start += box_size + spacing

                self.graphics_view.show_floor(i, True)
                painter.save()
                painter.translate(x_offset, y_start)
                self.graphics_view.scene.render(painter, QRectF(0, 0, size, size),
                                                scene_rect)
                painter.restore()

            painter.end()
            print(f"Saved as {file_path}")
            self.generate_button.setDisabled(False)
            self.clear_button.setDisabled(False)
            self.save_button.setDisabled(False)
            self.elevator_button.setDisabled(False)
            self.stairs_button.setDisabled(False)
            self.error_text.setText("")
            self.graphics_view.show_floor(previous_floor, self.checkbox.isChecked())

    def clear_painter(self):
        self.graphics_view.scene.clear()
        self.graphics_view.reset()
        self.graphics_view.add_point(-10, -10)
        self.graphics_view.add_point(-10, 10)
        self.graphics_view.add_point(10, -10)
        self.graphics_view.add_point(10, 10)
        self.graphics_view.update_shape()
        self.clear_button.setVisible(False)
        self.save_button.setVisible(False)
        self.elevator_button.setDisabled(True)
        self.stairs_button.setDisabled(True)
        self.add_point_button.setEnabled(True)
        self.add_building_button.setEnabled(True)
        self.add_section_button.setDisabled(False)
        self.checkbox.setVisible(False)
        self.generate_button.setText("Сгенерировать")
        self.combo.setVisible(False)
        self.output_table.setVisible(False)
        self.output_label.setVisible(False)
        self.graphics_view.room_legend_widget.setVisible(False)
        self.graphics_view.apt_legend_widget.setVisible(False)
        self.output_table.setVisible(False)
        self.previous_index = 0
        self.building_combo.setCurrentIndex(0)
        for i in range(1, self.building_combo.count()):
            self.building_combo.removeItem(i)
        self.previous_index = 0
        area_from = ["25", "40", "58", "78", "100"]
        area_to = ["35", "55", "75", "98", "135"]
        number = ["0", "0", "0", "0", "0"]
        percent = ["0", "0", "0", "0", "0"]

        for row in range(5):
            self.area_from[row].setText(area_from[row])
            self.area_to[row].setText(area_to[row])
            self.percent[row].setText(percent[row])
            self.number[row].setText(number[row])

        self.building_tables.clear()
        self.building_tables.append([area_from, area_to, percent, number])
        self.done = False

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
