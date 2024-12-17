from shapely.geometry import Polygon, MultiPolygon
from Classes.Geometry.GeometricFigure import GeometricFigure
from Classes.Geometry.Territory.Building.Building import Building
from typing import List, Tuple, Dict


class Territory(GeometricFigure):
    def __init__(self,
                 building_points: List[List[Tuple[float, float]]],
                 sections_coords: List[List[Tuple[float, float]]],
                 num_floors: int,
                 apartment_table: Dict):

        # Очистка apartment_table от типов квартир с number = 0
        self.apartment_table = self._clean_apartment_table(apartment_table)
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
        self.messages = []  # Для хранения сообщений об ошибках
        self.sections_coords = sections_coords if sections_coords is not None else building_points
        self.total_error = None
        self.output_table = None


    def generate_building_plannings(self):
        """
        Генерирует планировки для всех зданий на территории.
        """
        total_area = sum(Polygon(points).area for points in self.building_points)  # Общая площадь всех зданий

        if len(self.building_points) == 1:
            # Если здание одно, отправляем исходную apartment_table
            building = Building(points=self.building_points[0],
                                sections=self.sections_coords,
                                num_floors=self.num_floors,
                                apartment_table=self.apartment_table)
            building.generate_floors()
            if building.message:
                self.messages.append(building.message)  # Сохраняем сообщение
                print(f"Ошибка в здании {i + 1}: {building.message}")


            self.buildings.append(building)

        total_assigned_numbers = {apt_type: 0 for apt_type in self.apartment_table.keys()}

        for i, points in enumerate(self.building_points):
            building_polygon = Polygon(points)
            building_area = building_polygon.area
            proportioned_table = self._distribute_apartment_table(i, building_area, total_area, total_assigned_numbers)
            print(f" Территория {proportioned_table}")
            # Создаем здание с распределенной таблицей
            building = Building(points=points,
                                sections=self.sections_coords,
                                num_floors=self.num_floors,
                                apartment_table=proportioned_table)
            building.generate_floors()
            if building.message:
                self.messages.append(building.message)  # Сохраняем сообщение
                print(f"Ошибка в здании {i + 1}: {building.message}")
                break  # Прерываем генерацию всех остальных зданий

            self.buildings.append(building)

        self.total_error = self.calculate_territory_error(self.buildings, self.apartment_table)
        self.output_table = self.generate_output_table()

    def _distribute_apartment_table(self, building_index, building_area, total_area, total_assigned_numbers):
        """
        Распределяет количество квартир для здания на основе его площади.

        Args:
            building_index (int): Индекс текущего здания.
            building_area (float): Площадь текущего здания.
            total_area (float): Общая площадь всех зданий.
            total_assigned_numbers (dict): Сумма квартир уже распределенных по зданиям.

        Returns:
            dict: apartment_table для текущего здания.
        """
        distributed_table = {}

        for apt_type, apt_info in self.apartment_table.items():
            if building_index == len(self.building_points) - 1:
                # Для последнего здания корректируем число квартир
                remaining_number = apt_info['number'] - total_assigned_numbers[apt_type]
                distributed_table[apt_type] = {
                    'area_range': apt_info['area_range'],
                    'percent': apt_info['percent'],
                    'number': remaining_number
                }
            else:
                # Рассчитываем пропорциональное количество квартир
                proportioned_number = round(apt_info['number'] * (building_area / total_area))
                total_assigned_numbers[apt_type] += proportioned_number

                distributed_table[apt_type] = {
                    'area_range': apt_info['area_range'],
                    'percent': apt_info['percent'],
                    'number': proportioned_number
                }

        return distributed_table

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

    def generate_output_table(self):
        """
        Генерирует выходную таблицу с фактическими данными после планирования территории.

        Возвращает:
            dict: Выходная таблица в формате словаря.
        """
        # Инициализация словаря для фактических значений
        actual_data = {apt_type: {
            'area_range': (float('inf'), float('-inf')),  # Минимальная и максимальная площадь
            'percent': 0,  # Фактический процент
            'number': 0,  # Фактическое количество
            'error': 0  # Ошибка
        } for apt_type in self.apartment_table.keys()}

        total_allocated_area = 0

        # Обход всех зданий и квартир для подсчета фактических значений
        for building in self.buildings:
            for floor in building.floors:
                for section in floor.sections:
                    for apartment in section.apartments:
                        apt_type = apartment.type
                        apt_area = apartment.area

                        # Обновляем минимальную и максимальную площадь
                        min_area, max_area = actual_data[apt_type]['area_range']
                        actual_data[apt_type]['area_range'] = (min(min_area, apt_area), max(max_area, apt_area))
                        actual_data[apt_type]['number'] += 1  # Считаем количество квартир
                        actual_data[apt_type]['percent'] += apt_area  # Суммируем площади
                        total_allocated_area += apt_area

        # Рассчитываем фактический процент и ошибки
        for apt_type, data in actual_data.items():
            # Финальные значения для процентов
            data['percent'] = (data['percent'] / total_allocated_area) * 100 if total_allocated_area > 0 else 0
            expected_percent = self.apartment_table[apt_type]['percent']
            data['error'] = abs(expected_percent - data['percent'])  # Абсолютная ошибка

            # Преобразуем range, если не было квартир
            if data['area_range'][0] == float('inf'):
                data['area_range'] = (0, 0)

        return actual_data

    def _clean_apartment_table(self, apartment_table: Dict) -> Dict:
        """
        Удаляет из apartment_table типы квартир, у которых number = 0.

        Args:
            apartment_table (dict): Исходная таблица с типами квартир.

        Returns:
            dict: Очищенная таблица.
        """
        cleaned_table = {apt_type: data for apt_type, data in apartment_table.items() if data['number'] > 0}
        return cleaned_table

    def print_messages(self):
        if self.messages:
            print("Сообщения об ошибках:")
            for msg in self.messages:
                print(f"- {msg}")
