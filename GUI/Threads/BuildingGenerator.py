from PyQt5.QtCore import QObject, pyqtSignal


class BuildingGenerator(QObject):
    finished = pyqtSignal(object)

    def __init__(self, territory):
        super().__init__()
        self.floors = []
        self.territory = territory

    def run(self):
        self.territory.generate_building_plannings()
        for building in self.territory.buildings:
            for floor in building.floors:
                self.floors.append(floor)
        self.finished.emit(self.floors)