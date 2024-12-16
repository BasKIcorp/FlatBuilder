from PyQt5.QtCore import QObject, pyqtSignal


class BuildingGenerator(QObject):
    finished = pyqtSignal(object)

    def __init__(self, territory):
        super().__init__()
        self.territory = territory

    def run(self):
        self.territory.generate_building_plannings()
        self.finished.emit(self.territory)