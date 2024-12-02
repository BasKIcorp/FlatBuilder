import matplotlib.pyplot as plt
from Classes.Geometry.Territory.Building.Floor.Floor import Floor
import time
import numpy as np

def generate_test_floors(num_floors):
    """Генерирует список тестовых этажей с возрастающей площадью."""
    test_floors = []
    base_size = 50  # Начальный размер
    size_increment = 20  # Прирост размера на каждом шаге

    for i in range(num_floors):
        size = base_size + i * size_increment
        # Создаем простые прямоугольные этажи для простоты
        floor_points = [
            (0, 0),
            (size, 0),
            (size, size * 0.8),
            (size * 0.6, size * 0.8),
            (size * 0.6, size),
            (0, size)
        ]
        test_floors.append((size, floor_points))
    return test_floors

def test_algorithm_speed(test_floors, apartment_table, max_iterations=10):
    """Тестирует скорость работы алгоритма на заданных этажах."""
    areas = []
    execution_times = []

    for size, floor_points in test_floors:
        # Создаем объект Floor
        floor = Floor(floor_points)
        # Вычисляем площадь этажа
        area = floor.polygon.area
        areas.append(area)

        # Запускаем генерацию планировки и измеряем время
        start_time = time.time()
        apartments = floor.generatePlanning(apartment_table, max_iterations=max_iterations)
        end_time = time.time()

        execution_time = end_time - start_time
        execution_times.append(execution_time)

        print(f"Этаж размером {size}x{size}: Площадь = {area:.2f}, Время выполнения = {execution_time:.2f} сек")

    return areas, execution_times

def plot_execution_time(areas, execution_times):
    """Строит график зависимости времени выполнения от площади и рисует регрессионную прямую."""
    # Преобразуем списки в numpy массивы для удобства
    areas = np.array(areas)
    execution_times = np.array(execution_times)

    # Вычисление линии регрессии
    coeffs = np.polyfit(areas, execution_times, deg=1)
    regression_line = np.poly1d(coeffs)

    # Создание значений для линии регрессии
    area_range = np.linspace(min(areas), max(areas), 100)
    predicted_times = regression_line(area_range)

    # Построение графика
    plt.figure(figsize=(10, 6))
    plt.scatter(areas, execution_times, color='blue', label='Измеренные данные')
    plt.plot(area_range, predicted_times, color='red', linestyle='--', label='Линия регрессии')

    plt.title('Зависимость времени выполнения от площади этажа')
    plt.xlabel('Площадь этажа (кв. единиц)')
    plt.ylabel('Время выполнения (сек)')
    plt.legend()
    plt.grid(True)
    plt.show()

    # Вывод уравнения регрессии и коэффициента детерминации R^2
    from sklearn.metrics import r2_score
    r_squared = r2_score(execution_times, regression_line(areas))
    print(f"Уравнение регрессии: Время = {coeffs[0]:.5f} * Площадь + {coeffs[1]:.5f}")
    print(f"Коэффициент детерминации R² = {r_squared:.4f}")

if __name__ == '__main__':
    # Параметры тестирования
    num_test_floors = 10
    max_iterations = 20  # Количество итераций для генерации планировки

    # Таблица квартир (можно использовать ту же, что и ранее)
    apartment_table = {
        'studio': {'area_range': (250, 300), 'percent': 20},
        '1 room': {'area_range': (300, 400), 'percent': 20},
        '2 room': {'area_range': (400, 500), 'percent': 20},
        '3 room': {'area_range': (500, 600), 'percent': 20},
        '4 room': {'area_range': (600, 700), 'percent': 20},
    }

    # Генерация тестовых этажей
    test_floors = generate_test_floors(num_test_floors)

    # Тестирование алгоритма
    areas, execution_times = test_algorithm_speed(test_floors, apartment_table, max_iterations=max_iterations)

    # Построение графика
    plot_execution_time(areas, execution_times)