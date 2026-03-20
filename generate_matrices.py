import numpy as np
import sys
import os

def generate_matrix(filename, n, low=-10.0, high=10.0, use_int=False):
    """Генерация случайной матрицы и запись в файл."""
    if use_int:
        matrix = np.random.randint(int(low), int(high) + 1, size=(n, n)).astype(float)
    else:
        matrix = np.random.uniform(low, high, size=(n, n))

    with open(filename, 'w') as f:
        f.write(f"{n}\n")
        for i in range(n):
            row = " ".join(f"{matrix[i, j]:.6f}" for j in range(n))
            f.write(row + "\n")

    print(f"  Матрица {n}x{n} записана в {filename}")
    return matrix

def main():
    n = 1000  # размер по умолчанию

    if len(sys.argv) >= 2:
        n = int(sys.argv[1])

    use_int = False
    if len(sys.argv) >= 3 and sys.argv[2] == "int":
        use_int = True

    print(f"Генерация матриц размером {n}x{n}...")

    np.random.seed()

    generate_matrix("matrix_A.txt", n, use_int=use_int)
    generate_matrix("matrix_B.txt", n, use_int=use_int)

    print("Генерация завершена.")

if __name__ == "__main__":
    main()