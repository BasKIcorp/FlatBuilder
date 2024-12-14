from Classes.Geometry.GeometricFigure import GeometricFigure
from Classes.Geometry.Territory.Building.Floor.Section import Section
from Classes.Geometry.Territory.Building.Elevator import Elevator
from Classes.Geometry.Territory.Building.Stair import Stair
from shapely.geometry import Polygon
from shapely.ops import unary_union
from typing import List, Tuple, Dict


class Floor(GeometricFigure):
    def __init__(self, points: List[Tuple[float, float]], sections: List[List[Tuple[float, float]]],
                 apartment_table: Dict,
                 elevators: List['Elevator'] = None,
                 stairs: List['Stair'] = None,
                 building_polygon: Polygon = None):
        super().__init__(points)  # Передаем points в конструктор родительского класса
        self.apartment_table = apartment_table  # Таблица квартир, переданная в класс

        # Создание секций
        self.sections_points = sections
        self.elevators = elevators if elevators is not None else []
        self.stairs = stairs if stairs is not None else []
        self.sections = []
        self.building_polygon = building_polygon

    def generate_floor_planning(self, cell_size=1):
        self.cells = None
        self.check_and_create_cell_grid(cell_size=cell_size)

        # Создаем apartment_section_table
        total_assigned_numbers = {apt_type: 0 for apt_type in self.apartment_table.keys()}  # Инициализация счетчиков
        apartment_section_table = {
            k: {
                'area_range': v['area_range'],
                'percent': v['percent'],
                'number': 0
            } for k, v in self.apartment_table.items()
        }

        # Перебираем секции и рассчитываем количество квартир
        total_section_area = sum(Polygon(points).area for points in self.sections_points)  # Общая площадь секций
        if len(self.sections_points) == 1:
            section = Section(points=self.sections_points[0], apartment_table=self.apartment_table)
            section.check_and_create_cell_grid(cell_size=1)
            if len(self.elevators) > 0:
                for elevator in self.elevators:
                    if section.polygon.contains(elevator.polygon):
                        section.elevators.append(elevator)
                section.set_elevators()
            if len(self.stairs) > 0:
                for stair in self.stairs:
                    if section.polygon.contains(stair.polygon):
                        section.stairs.append(stair)
                section.set_stairs()

            section.generate_section_planning(max_iterations=20)
            self.sections.append(section)
        else:
            for i, points in enumerate(self.sections_points):
                section_polygon = Polygon(points)
                proportioned_section_area = section_polygon.area / total_section_area if total_section_area > 0 else 0  # Пропорции площади секции

                if i == len(self.sections_points) - 1:
                    for apt_type in apartment_section_table.keys():
                        apartment_section_table[apt_type].pop('number')
                        apartment_section_table[apt_type]['number'] = (self.apartment_table[apt_type]['number'] -
                                                                      total_assigned_numbers[apt_type])
                else:
                    for apt_type in apartment_section_table.keys():
                        assigned_number = int(proportioned_section_area * self.apartment_table[apt_type]['number'])
                        apartment_section_table[apt_type].pop('number')
                        apartment_section_table[apt_type]['number'] = assigned_number
                        total_assigned_numbers[apt_type] += assigned_number
                print(f"Секция {i}: {apartment_section_table}")

                # Создаем секцию
                section = Section(points=points, apartment_table=apartment_section_table,
                                  building_polygon=self.building_polygon)
                section.check_and_create_cell_grid(cell_size=1)
                if len(self.elevators) > 0:
                    for elevator in self.elevators:
                        if section.polygon.contains(elevator.polygon):
                            section.elevators.append(elevator)
                    section.set_elevators()
                if len(self.stairs) > 0:
                    for stair in self.stairs:
                        if section.polygon.contains(stair.polygon):
                            section.stairs.append(stair)
                    section.set_stairs()

                section.generate_section_planning(max_iterations=20)
                self.sections.append(section)