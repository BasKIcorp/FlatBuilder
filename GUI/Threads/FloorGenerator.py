from PyQt5.QtCore import QObject, pyqtSignal


class FloorGenerator(QObject):
    finished = pyqtSignal(object)

    def __init__(self, floor, apartment_table):
        super().__init__()
        self.floor = floor
        self.apartment_table = apartment_table

    def run(self):
        self.floor.generatePlanning(self.apartment_table, max_iterations=15)
        self.finished.emit(self.floor)