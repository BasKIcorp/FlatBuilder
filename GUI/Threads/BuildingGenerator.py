from PyQt5.QtCore import QObject, pyqtSignal


class BuildingGenerator(QObject):
    finished = pyqtSignal(object, object, object, object, object)

    def __init__(self, territory):
        super().__init__()
        self.floors = []
        self.territory = territory
        self.error = ""

    def run(self):
        try:
            self.territory.generate_building_plannings()
            for building in self.territory.buildings:
                floors_per_building = []
                for floor in building.floors:
                    floors_per_building.append(floor)
                self.floors.append(floors_per_building)
        except Exception:
            self.error = f"Ошибка генерации"
        self.finished.emit(self.error, self.territory.buildings, self.floors, self.territory.messages, self.territory.output_tables)