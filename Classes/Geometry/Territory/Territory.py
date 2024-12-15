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
        self.check_and_create_cell_grid_for_building(cell_size=1)
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


            if len(self.building_points) == 1:
                for apt_type in apartment_building_table.keys():
                    apartment_building_table[apt_type].pop('number')
                    apartment_building_table[apt_type]['number'] = self.apartment_table[apt_type]['number']
                building = Building(points=points,
                                    sections=self.sections_coords,
                                    num_floors=self.num_floors,
                                    apartment_table=apartment_building_table,
                                    elevators_coords=self.elevators_coords,
                                    stairs_coords=self.stairs_coords)
                building.generate_floors()
                self.buildings.append(building)
                return self.buildings
            # Убедитесь, что в последнем здании все квартиры распределены
            if i == len(self.building_points) - 1:
                for apt_type in apartment_building_table.keys():
                    apartment_building_table[apt_type].pop('number')
                    apartment_building_table[apt_type]['number'] = (self.apartment_table[apt_type]['number'] -
                                                                   total_assigned_numbers[apt_type])
            else:
                # Обновляем общее распределенное количество квартир для каждого типа
                for apt_type in apartment_building_table.keys():
                    total_assigned_numbers[apt_type] += apartment_building_table[apt_type]['number']
                    print(total_assigned_numbers)

            print(f"Здание {i}: {apartment_building_table}")
            # Создаем здания
            building = Building(points=points,
                                sections=self.sections_coords,
                                num_floors=self.num_floors,
                                apartment_table=apartment_building_table,
                                elevators_coords=self.elevators_coords,
                                stairs_coords=self.stairs_coords)
            building.generate_floors()
            self.buildings.append(building)

    def _calculate_total_error(self):
        """Calculates the total error in apartment type distribution across all buildings and their floors."""
        total_allocated_area = 0
        actual_percentages = {}
        total_apartment_table = {}

        # Суммируем площади каждой квартиры во всех зданиях, этажах и секциях
        for building in self.buildings:
            for floor in building.floors:
                for section in floor.sections:
                    for apt in section.apartments:
                        total_allocated_area += apt.area
                        apt_type = apt.type
                        if apt_type in actual_percentages:
                            actual_percentages[apt_type] += apt.area
                        else:
                            actual_percentages[apt_type] = apt.area

                        # Собираем общую информацию по квартире
                        if apt_type in total_apartment_table:
                            total_apartment_table[apt_type]['number'] += 1
                        else:
                            total_apartment_table[apt_type] = {
                                'number': 1,
                                'area_range': apt.area_range,  # Предполагается, что area_range есть в каждом apt
                                'percent': apt.percent  # Предполагается, что percent есть в каждом apt
                            }

        # Рассчитываем процент для каждой квартиры
        for apt_type in total_apartment_table.keys():
            actual_percent = (actual_percentages.get(apt_type,
                                                     0) / total_allocated_area) * 100 if total_allocated_area > 0 else 0
            total_apartment_table[apt_type]['actual_percent'] = actual_percent

        # Вычисляем общую ошибку
        total_error = 0
        for apt_type, info in total_apartment_table.items():
            desired_percent = info['percent']
            actual_percent = info.get('actual_percent', 0)
            total_error += abs(desired_percent - actual_percent)

        return total_error




