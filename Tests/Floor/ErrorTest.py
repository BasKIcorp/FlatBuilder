import matplotlib.pyplot as plt
from shapely.geometry import Polygon
from Classes.Geometry.Territory.Floor.Floor import Floor
import time
import multiprocessing
import numpy as np  # Импортируем numpy для вычисления регрессии


def run_test_iteration(args):
    max_iterations, floor_points, apartment_table = args
    floor = Floor(floor_points)
    apartments = floor.generatePlanning(apartment_table, max_iterations=max_iterations)
    if floor.apartments:
        total_error = floor._calculate_total_error(floor.apartments, apartment_table)
    else:
        total_error = None
    return (max_iterations, total_error)


if __name__ == '__main__':
    # Определение точек полигона этажа
    floor_points = [(0, 0), (100, 0), (100, 80), (60, 80), (60, 100), (0, 100)]  # Пример полигона этажа

    # Таблица квартир
    apartment_table = {
        'studio': {
            'area_range': (250, 300),
            'percent': 20
        },
        '1 room': {
            'area_range': (300, 400),
            'percent': 20
        },
        '2 room': {
            'area_range': (400, 500),
            'percent': 20
        },
        '3 room': {
            'area_range': (500, 600),
            'percent': 20
        },
        '4 room': {
            'area_range': (600, 700),
            'percent': 20
        },
    }

    # Параметры тестирования
    max_iterations_limit = 100  # Максимальное количество итераций
    num_processes = multiprocessing.cpu_count()  # Используем все доступные ядра

    # Подготовка аргументов для каждого процесса
    test_args = [(i, floor_points, apartment_table) for i in range(1, max_iterations_limit + 1, 10)]

    # Запуск пула процессов
    with multiprocessing.Pool(processes=num_processes) as pool:
        results = pool.map(run_test_iteration, test_args)

    # Обработка результатов
    allocation_found = False
    error_below_10_percent = False
    iterations_for_first_allocation = None
    iterations_for_error_below_10_percent = None
    errors = []

    for max_iterations, total_error in results:
        if not allocation_found and total_error is not None:
            allocation_found = True
            iterations_for_first_allocation = max_iterations
            print(f"Распределение найдено при max_iterations = {max_iterations}")

        if total_error is not None:
            errors.append((max_iterations, total_error))
            if not error_below_10_percent and total_error < 10:
                error_below_10_percent = True
                iterations_for_error_below_10_percent = max_iterations
                print(
                    f"Ошибка ниже 10% достигнута при max_iterations = {max_iterations}, Общая ошибка: {total_error:.2f}%")
        else:
            errors.append((max_iterations, None))

    if not allocation_found:
        print(f"Распределение не найдено в пределах max_iterations = {max_iterations_limit}")

    # Подготовка данных для построения графика
    iterations = [it for it, err in errors if err is not None]
    total_errors = [err for it, err in errors if err is not None]

    # Вычисление линии регрессии
    coeffs = np.polyfit(iterations, total_errors, deg=1)  # Коэффициенты линейной регрессии
    regression_line = np.poly1d(coeffs)  # Создаем функцию на основе коэффициентов

    # Создание значений для линии регрессии
    regression_iterations = np.linspace(min(iterations), max(iterations), 100)
    regression_errors = regression_line(regression_iterations)

    # Построение графика зависимости общей ошибки от количества итераций
    plt.figure(figsize=(10, 6))
    plt.plot(iterations, total_errors, marker='o', label='Данные')
    plt.plot(regression_iterations, regression_errors, color='blue', linestyle='--', label='Линия регрессии')
    plt.axhline(10, color='red', linestyle='--', label='Порог ошибки 10%')
    if iterations_for_first_allocation:
        plt.axvline(iterations_for_first_allocation, color='green', linestyle='--',
                    label='Первое распределение найдено')
    if iterations_for_error_below_10_percent:
        plt.axvline(iterations_for_error_below_10_percent, color='orange', linestyle='--', label='Ошибка < 10%')
    plt.title('Общая ошибка в зависимости от количества итераций')
    plt.xlabel('Максимальное количество итераций')
    plt.ylabel('Общая ошибка (%)')
    plt.legend()
    plt.grid(True)
    plt.show()
