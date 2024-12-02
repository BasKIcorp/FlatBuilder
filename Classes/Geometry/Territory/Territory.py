from Classes.Geometry.GeometricFigure import GeometricFigure
from typing import List, Tuple, Dict
from Classes.Geometry.Territory.Building.Building import Building
from shapely.geometry import Polygon

# Класс для территории, содержащей здания
class Territory(GeometricFigure):
    def __init__(self, points: List[Tuple[float, float]],
                 building_points: List[List[Tuple[float, float]]],
                 sections_coords: List[List[Tuple[float, float]]],
                 num_floors: int,
                 apartment_table: Dict,
                 elevators_coords: List[List[Tuple[float, float]]] = None,
                 stairs_coords: List[List[Tuple[float, float]]] = None):

        super().__init__(points)
        self.building_points = building_points
        self.num_floors = num_floors
        self.apartment_table = apartment_table
        self.buildings = []
        self.elevators_coords = elevators_coords if elevators_coords is not None else []
        self.stairs_coords = stairs_coords if stairs_coords is not None else []
        self.sections_coords = sections_coords if sections_coords is not None else building_points

    def generate_building_plannings(self):
        # Проверяем и создаем сетку ячеек
        self.check_and_create_cell_grid(cell_size=1)
        total_area = 0.0  # Общая площадь территории

        # Вычисляем общую площадь всех зданий
        for points in self.building_points:
            building_polygon = Polygon(points)
            total_area += building_polygon.area

        # Переменные для суммирования количества квартир
        total_assigned_numbers = {apt_type: 0 for apt_type in self.apartment_table.keys()}

        # Перебираем здания и рассчитываем количество квартир
        for i, points in enumerate(self.building_points):
            building_polygon = Polygon(points)
            proportioned_building_area = building_polygon.area / total_area  # Пропорция площади текущего здания

            # Создаем отдельный apartment_table для каждого здания на основе пропорции
            apartment_building_table = {
                k: {
                    'area_range': v['area_range'],
                    'percent': v['percent'],
                    'number': int(proportioned_building_area * v['number'])
                } for k, v in self.apartment_table.items()
            }

            # Обновляем общее распределенное количество квартир для каждого типа
            for apt_type in apartment_building_table.keys():
                total_assigned_numbers[apt_type] += apartment_building_table[apt_type]['number']

            # Убедитесь, что в последнем здании все квартиры распределены
            if i == len(self.building_points) - 1:
                for apt_type, info in apartment_building_table.items():
                    apartment_building_table[apt_type]['number'] = self.apartment_table[apt_type]['number'] - \
                                                                   total_assigned_numbers[apt_type]

            # Создаем здания
            building = Building(points=points,
                                sections=self.sections_coords,
                                num_floors=self.num_floors,
                                apartment_table=apartment_building_table,
                                elevators_coords=self.elevators_coords,
                                stairs_coords=self.stairs_coords)
            building.generate_floors()
            self.buildings.append(building)

