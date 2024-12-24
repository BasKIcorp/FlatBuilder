from shapely.geometry import Polygon, MultiPolygon
from Classes.Geometry.GeometricFigure import GeometricFigure
from Classes.Geometry.Territory.Building.Building import Building
from typing import List, Tuple, Dict


class Territory(GeometricFigure):
    def __init__(self,
                 building_points: List[List[Tuple[float, float]]],
                 sections_coords: List[List[Tuple[float, float]]],
                 num_floors: int,
                 apartment_table: list):

        # Очистка apartment_table от типов квартир с number = 0
        self.apartment_table = apartment_table
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
        self.total_error = []
        self.output_tables = None

    def generate_building_plannings(self):
        """
        Генерирует планировки для всех зданий на территории.
        """
        if not self.validate_initial_planning():
            print(self.messages)
            return None
        for i, points in enumerate(self.building_points):
            # Создаем здание с распределенной таблицей
            building = Building(points=points,
                                sections=self.sections_coords,
                                num_floors=self.num_floors,
                                apartment_table=self.apartment_table[i])
            building.generate_floors()
            self.buildings.append(building)
        self.get_messages()
        if self.messages:
            return
        self.total_error = self.calculate_territory_error(self.buildings, self.apartment_table)
        self.output_tables = self.generate_output_table()

    def calculate_territory_error(self, buildings, apartment_table):
        for i in range(len(apartment_table)):
            total_allocated_area = 0  # Общая площадь всех квартир
            type_areas = {apt_type: 0 for apt_type in apartment_table[i]}  # Площадь по типам квартир

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
            for apt_type, values in apartment_table[i].items():
                expected_percent = values['percent']
                actual_percent = (type_areas[apt_type] / total_allocated_area) * 100
                error = abs(expected_percent - actual_percent)  # Абсолютное отклонение
                errors.append(error)


        return errors

    def generate_output_table(self):
        """
        Генерирует выходную таблицу с фактическими данными после планирования территории,
        включая среднюю ошибку для каждого здания.

        Возвращает:
            List[Dict]: Список выходных таблиц для каждого здания.
        """
        output_tables = []

        # Обход всех зданий и квартир для подсчета фактических значений
        for i, building in enumerate(self.buildings):
            actual_data = {apt_type: {
                'average_area': 0,  # Средняя площадь
                'percent': 0,  # Фактический процент
                'number': 0,  # Фактическое количество
                'error': 0  # Ошибка
            } for apt_type in self.apartment_table[i].keys()}

            # Словарь для подсчета общей площади по типам квартир
            counting_area = {apt_type: 0 for apt_type in self.apartment_table[i].keys()}

            # Подсчет общей площади и количества квартир
            for floor in building.floors:
                for section in floor.sections:
                    for apartment in section.apartments:
                        apt_type = apartment.type
                        counting_area[apt_type] += apartment.area
                        actual_data[apt_type]['number'] += 1  # Считаем количество квартир

            # Общая площадь всех квартир в здании
            total_area = sum(counting_area.values())

            # Рассчитываем фактический процент, среднюю площадь и ошибки
            for apt_type, data in actual_data.items():
                if data['number'] > 0:
                    data['average_area'] = round(counting_area[apt_type] / data['number'], 1)  # Средняя площадь
                data['percent'] = round((counting_area[apt_type] / total_area) * 100, 1) if total_area > 0 else 0
                expected_percent = self.apartment_table[i][apt_type]['percent']
                data['error'] = round(abs(expected_percent - data['percent']), 1)  # Абсолютная ошибка

            # Добавляем ключ 'Средняя ошибка' для здания
            actual_data['average_error'] = round(sum(self.total_error) / len(self.total_error), 1)

            output_tables.append(actual_data)

        return output_tables

    def get_messages(self):
        for building in self.buildings:
            for floor in building.floors:
                for section in floor.sections:
                    if section.messages:
                        for message in section.messages:
                            self.messages.append(message)
                            break
                    for apartment in section.apartments:
                        if apartment.messages:
                            for message in apartment.messages:
                                self.messages.append(message)

    def validate_initial_planning(self):
        """
        Проверяет, возможно ли планирование по изначальной таблице квартир apartment_table.
        Если площадь средняя между минимальной и потенциальной площадью меньше 0.7 * allocatable_area,
        отправляет сообщение с требованием уменьшить количество квартир или площадь.
        """
        for i in range(len(self.apartment_table)):
            # Шаг 1: Расчет минимальной и максимальной потенциальной площади
            min_potential_area = sum(apt_info['area_range'][0] * apt_info['number']
                                     for apt_info in self.apartment_table[i].values())
            max_potential_area = sum(apt_info['area_range'][1] * apt_info['number']
                                     for apt_info in self.apartment_table[i].values())
            total_building_area = Polygon(self.building_points[i]).area
            avg_potential_area = (min_potential_area + max_potential_area) / 2
            if self.num_floors == 1:
                threshold_area = avg_potential_area
                print(total_building_area)
                print(threshold_area)
                if not threshold_area < total_building_area * 0.7:
                    min_area_to_reduce = threshold_area - total_building_area * 0.7
                    self.messages.append(
                        f"Пожалуйста, уменьшите количество квартир/площадь.\nМинимальная площадь для уменьшения: {min_area_to_reduce:.2f}"
                    )
                    return False  # Планирование невозможно
                else:
                    continue
            else:
                allocatable_area = total_building_area * (self.num_floors - 1)  # Площадь для аллокации
                threshold_area = 0.6 * allocatable_area
                if not avg_potential_area < threshold_area:
                    # Шаг 5: Расчет минимальной площади для уменьшения
                    min_area_to_reduce = avg_potential_area - threshold_area
                    # Формирование сообщения
                    self.messages.append(
                        f"Пожалуйста, уменьшите количество квартир/площадь.\nМинимальная площадь для уменьшения: {min_area_to_reduce:.2f}"
                    )
                    return False  # Планирование невозможно
                else:
                    continue
        return True