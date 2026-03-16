#include <iostream>
#include <fstream>
#include <cstdlib>
#include <cstring>
#include <chrono>
#include <iomanip>
#include <windows.h>

// Чтение квадратной матрицы из файла
// Формат файла: первая строка — размер N, далее N строк по N чисел
double* readMatrix(const char* filename, int& n) {
    std::ifstream fin(filename);
    if (!fin.is_open()) {
        std::cerr << "Ошибка: не удалось открыть файл " << filename << std::endl;
        return nullptr;
    }

    fin >> n;
    if (n <= 0) {
        std::cerr << "Ошибка: некорректный размер матрицы в файле " << filename << std::endl;
        return nullptr;
    }

    double* matrix = new double[n * n];

    for (int i = 0; i < n * n; i++) {
        if (!(fin >> matrix[i])) {
            std::cerr << "Ошибка: недостаточно данных в файле " << filename << std::endl;
            delete[] matrix;
            return nullptr;
        }
    }

    fin.close();
    return matrix;
}

// Запись матрицы в файл
bool writeMatrix(const char* filename, const double* matrix, int n) {
    std::ofstream fout(filename);
    if (!fout.is_open()) {
        std::cerr << "Ошибка: не удалось создать файл " << filename << std::endl;
        return false;
    }

    fout << n << std::endl;
    fout << std::fixed << std::setprecision(6);

    for (int i = 0; i < n; i++) {
        for (int j = 0; j < n; j++) {
            if (j > 0) fout << " ";
            fout << matrix[i * n + j];
        }
        fout << std::endl;
    }

    fout.close();
    return true;
}

// Перемножение матриц порядком i-k-j (однопоточное)
void multiplyMatrices_ikj(const double* A, const double* B, double* C, int n) {
    // Обнуление результирующей матрицы
    memset(C, 0, sizeof(double) * n * n);

    for (int i = 0; i < n; i++) {
        for (int k = 0; k < n; k++) {
            double a_ik = A[i * n + k];
            for (int j = 0; j < n; j++) {
                C[i * n + j] += a_ik * B[k * n + j];
            }
        }
    }
}

int main(int argc, char* argv[]) {
    SetConsoleOutputCP(65001);

    // Имена файлов по умолчанию
    const char* fileA = "matrix_A.txt";
    const char* fileB = "matrix_B.txt";
    const char* fileC = "matrix_C.txt";

    // Можно передать имена файлов через аргументы командной строки
    if (argc >= 4) {
        fileA = argv[1];
        fileB = argv[2];
        fileC = argv[3];
    }

    std::cout << "============================================" << std::endl;
    std::cout << "  Перемножение квадратных матриц (i-k-j)  " << std::endl;
    std::cout << "  Однопоточная реализация                  " << std::endl;
    std::cout << "============================================" << std::endl;

    // Чтение матриц
    int nA = 0, nB = 0;

    std::cout << "\nЧтение матрицы A из файла: " << fileA << std::endl;
    double* A = readMatrix(fileA, nA);
    if (!A) return 1;

    std::cout << "Чтение матрицы B из файла: " << fileB << std::endl;
    double* B = readMatrix(fileB, nB);
    if (!B) {
        delete[] A;
        return 1;
    }

    // Проверка совместимости размеров
    if (nA != nB) {
        std::cerr << "Ошибка: размеры матриц не совпадают ("
                  << nA << " != " << nB << ")" << std::endl;
        delete[] A;
        delete[] B;
        return 1;
    }

    int n = nA;
    std::cout << "Размер матриц: " << n << " x " << n << std::endl;

    // Объём задачи: количество операций умножения и сложения
    long long numOperations = 2LL * n * n * n;
    double gflops_total = (double)numOperations / 1e9;
    std::cout << "Объём задачи: " << numOperations << " операций с плавающей точкой ("
              << std::fixed << std::setprecision(3) << gflops_total << " GFLOP)" << std::endl;

    // Выделение памяти под результат
    double* C = new double[n * n];

    // Перемножение с замером времени
    std::cout << "\nВыполняется умножение матриц..." << std::endl;

    auto start = std::chrono::high_resolution_clock::now();
    multiplyMatrices_ikj(A, B, C, n);
    auto end = std::chrono::high_resolution_clock::now();

    std::chrono::duration<double> elapsed = end - start;
    double seconds = elapsed.count();

    double gflops_per_sec = gflops_total / seconds;

    std::cout << "\n============ РЕЗУЛЬТАТЫ ============" << std::endl;
    std::cout << "Размер матрицы:       " << n << " x " << n << std::endl;
    std::cout << "Время выполнения:     " << std::fixed << std::setprecision(6)
              << seconds << " сек" << std::endl;
    std::cout << "Объём задачи:         " << std::setprecision(3)
              << gflops_total << " GFLOP" << std::endl;
    std::cout << "Производительность:   " << std::setprecision(4)
              << gflops_per_sec << " GFLOP/s" << std::endl;

    // Запись результата
    std::cout << "\nЗапись результата в файл: " << fileC << std::endl;
    if (!writeMatrix(fileC, C, n)) {
        delete[] A;
        delete[] B;
        delete[] C;
        return 1;
    }

    // Вывод угла результирующей матрицы (для визуальной проверки)
    int printSize = (n < 5) ? n : 5;
    std::cout << "\nЛевый верхний угол матрицы C (" << printSize << "x" << printSize << "):" << std::endl;
    for (int i = 0; i < printSize; i++) {
        for (int j = 0; j < printSize; j++) {
            std::cout << std::setw(12) << std::setprecision(4) << C[i * n + j];
        }
        std::cout << std::endl;
    }

    std::cout << "\nГотово!" << std::endl;

    // Освобождение памяти
    delete[] A;
    delete[] B;
    delete[] C;

    return 0;
}