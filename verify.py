import numpy as np
import sys
import time

def read_matrix(filename):
    """Чтение матрицы из файла."""
    with open(filename, 'r') as f:
        n = int(f.readline().strip())
        matrix = np.zeros((n, n), dtype=np.float64)
        for i in range(n):
            values = list(map(float, f.readline().strip().split()))
            for j in range(n):
                matrix[i, j] = values[j]
    return matrix, n

def main():
    file_a = "matrix_A.txt"
    file_b = "matrix_B.txt"
    file_c = "matrix_C.txt"

    if len(sys.argv) >= 4:
        file_a = sys.argv[1]
        file_b = sys.argv[2]
        file_c = sys.argv[3]

    print("=" * 50)
    print("  ВЕРИФИКАЦИЯ РЕЗУЛЬТАТОВ (NumPy)")
    print("=" * 50)

    # Чтение матриц
    print(f"\nЧтение матрицы A из {file_a}...")
    A, nA = read_matrix(file_a)

    print(f"Чтение матрицы B из {file_b}...")
    B, nB = read_matrix(file_b)

    print(f"Чтение матрицы C (результат C++) из {file_c}...")
    C_cpp, nC = read_matrix(file_c)

    print(f"\nРазмеры: A={nA}x{nA}, B={nB}x{nB}, C={nC}x{nC}")

    # Эталонное умножение через NumPy (использует BLAS)
    print("\nВычисление эталонного произведения через NumPy...")
    start = time.time()
    C_ref = A @ B
    elapsed = time.time() - start
    print(f"Время NumPy: {elapsed:.6f} сек")

    # Сравнение
    diff = np.abs(C_cpp - C_ref)
    max_abs_error = np.max(diff)
    mean_abs_error = np.mean(diff)

    # Относительная ошибка
    norm_ref = np.linalg.norm(C_ref, 'fro')
    norm_diff = np.linalg.norm(C_cpp - C_ref, 'fro')
    relative_error = norm_diff / norm_ref if norm_ref > 0 else 0.0

    print("\n" + "=" * 50)
    print("  РЕЗУЛЬТАТЫ ВЕРИФИКАЦИИ")
    print("=" * 50)
    print(f"  Макс. абсолютная ошибка:    {max_abs_error:.2e}")
    print(f"  Средняя абсолютная ошибка:  {mean_abs_error:.2e}")
    print(f"  Относительная ошибка (Фр.): {relative_error:.2e}")

    # Порог для double
    tolerance = 1e-6
    if relative_error < tolerance:
        print(f"\n  ✅ ВЕРИФИКАЦИЯ ПРОЙДЕНА (отн. ошибка < {tolerance})")
        result = 0
    else:
        print(f"\n  ❌ ВЕРИФИКАЦИЯ НЕ ПРОЙДЕНА (отн. ошибка >= {tolerance})")
        result = 1

    # Вывод углов для наглядности
    ps = min(4, nC)
    print(f"\nУгол C++ результата ({ps}x{ps}):")
    for i in range(ps):
        print("  ", "  ".join(f"{C_cpp[i,j]:12.4f}" for j in range(ps)))

    print(f"\nУгол NumPy эталона ({ps}x{ps}):")
    for i in range(ps):
        print("  ", "  ".join(f"{C_ref[i,j]:12.4f}" for j in range(ps)))

    print()
    return result

if __name__ == "__main__":
    sys.exit(main())