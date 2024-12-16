from shapely.geometry import Polygon, MultiPolygon
from Classes.Geometry.GeometricFigure import GeometricFigure
from Classes.Geometry.Territory.Building.Building import Building
from typing import List, Tuple, Dict


class Territory(GeometricFigure):
    def __init__(self,
                 building_points: List[List[Tuple[float, float]]],
                 sections_coords: List[List[Tuple[float, float]]],
                 num_floors: int,
                 apartment_table: Dict,
                 elevators_coords: List[List[Tuple[float, float]]] = None,
                 stairs_coords: List[List[Tuple[float, float]]] = None):

        # Автоматически создаём envelope для территории на основе building_points
        combined_polygons = MultiPolygon([Polygon(points) for points in building_points])
        envelope = combined_polygons.envelope

        # Преобразуем envelope в список координат
        territory_points = list(envelope.exterior.coords)

        # Инициализируем GeometricFigure с построенными точками
        super().__init__(territory_points)

        self.building_points = building_points
        self.num_floors = num_floors
        self.apartment_table = apartment_table
        self.buildings = []
        self.elevators_coords = elevators_coords if elevators_coords is not None else []
        self.stairs_coords = stairs_coords if stairs_coords is not None else []
        self.sections_coords = sections_coords if sections_coords is not None else building_points

    def generate_building_plannings(self):
        """
        Генерирует планировки для всех зданий на территории.
        """
        total_area = sum(Polygon(points).area for points in self.building_points)  # Общая площадь всех зданий
        total_assigned_numbers = {apt_type: 0 for apt_type in self.apartment_table.keys()}

        for i, points in enumerate(self.building_points):
            building_polygon = Polygon(points)
            proportioned_area = building_polygon.area / total_area

            # Создаем таблицу квартир для этого здания
            building_apartment_table = {
                apt_type: {
                    'area_range': apt['area_range'],
                    'percent': apt['percent'],
                    'number': int(proportioned_area * apt['number'])
                } for apt_type, apt in self.apartment_table.items()
            }

            building = Building(points=points,
                                sections=self.sections_coords,
                                num_floors=self.num_floors,
                                apartment_table=building_apartment_table)
            building.generate_floors()
            self.buildings.append(building)

        self.total_error = self.calculate_territory_error(self.buildings, self.apartment_table)
        print(self.total_error)

    def calculate_territory_error(self, buildings, apartment_table):
        """
        Подсчитывает общую ошибку отклонения площади квартир на уровне всей территории.

        Args:
            buildings (list): Список зданий, каждое из которых содержит квартиры и их площади.
            apartment_table (dict): Таблица с ожидаемыми процентами площадей для типов квартир.

        Returns:
            float: Общая ошибка, равная сумме абсолютных отклонений фактических процентов от заданных.
        """
        total_allocated_area = 0  # Общая площадь всех квартир
        type_areas = {apt_type: 0 for apt_type in apartment_table}  # Площадь по типам квартир

        # Суммируем площади всех квартир во всех зданиях
        for building in buildings:
            for floor in building.floors:
                for section in floor.sections:
                    for apartment in section.apartments:
                        type_areas[apartment.type] += apartment.area
                        total_allocated_area += apartment.area

        # Проверка: если площадь квартир равна 0, возвращаем максимальную ошибку
        if total_allocated_area == 0:
            return float('inf')  # Ошибка максимальна, если квартиры не распределены

        # Вычисляем фактический процент площадей и общую ошибку
        errors = []
        for apt_type, values in apartment_table.items():
            expected_percent = values['percent']
            actual_percent = (type_areas[apt_type] / total_allocated_area) * 100
            error = abs(expected_percent - actual_percent)  # Абсолютное отклонение
            errors.append(error)

            # Отладочная информация
            print(
                f"Тип: {apt_type}, Ожидаемый %: {expected_percent:.2f}, Фактический %: {actual_percent:.2f}, Ошибка: {error:.2f}")
        average_error = sum(errors) / len(errors)
        return average_error





