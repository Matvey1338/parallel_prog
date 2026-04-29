#include <mpi.h>
#include <iostream>
#include <fstream>
#include <cstdlib>
#include <cstring>
#include <chrono>
#include <iomanip>
#include <windows.h>

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

int main(int argc, char* argv[]) {
    SetConsoleOutputCP(65001);
    MPI_Init(&argc, &argv);

    int rank, size;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

    if (rank == 0) {
        SetConsoleOutputCP(65001);
    }

    const char* fileA = "matrix_A.txt";
    const char* fileB = "matrix_B.txt";
    const char* fileC = "matrix_C.txt";
    const char* fileStats = nullptr;

    if (argc >= 4) {
        fileA = argv[1];
        fileB = argv[2];
        fileC = argv[3];
    }
    if (argc >= 5) {
        fileStats = argv[4];
    }

    int n = 0;
    double *A = nullptr;
    double *B = nullptr;
    double *C = nullptr;

    if (rank == 0) {
        std::cout << "============================================" << std::endl;
        std::cout << "  Перемножение квадратных матриц (i-k-j)    " << std::endl;
        std::cout << "  MPI реализация (процессов: " << size << ")     " << std::endl;
        std::cout << "============================================" << std::endl;

        int nA = 0, nB = 0;
        std::cout << "\nЧтение матрицы A из файла: " << fileA << std::endl;
        A = readMatrix(fileA, nA);
        if (A) {
            std::cout << "Чтение матрицы B из файла: " << fileB << std::endl;
            B = readMatrix(fileB, nB);
            if (B && nA != nB) {
                std::cerr << "Ошибка: размеры матриц не совпадают (" << nA << " != " << nB << ")" << std::endl;
                delete[] A; delete[] B;
                A = nullptr; B = nullptr;
            } else if (B) {
                n = nA;
                std::cout << "Размер матриц: " << n << " x " << n << std::endl;
            }
        }
        if (!A || !B) {
            n = -1; // Сигнал ошибки другим процессам
        }
    }

    // Рассылаем размер матрицы всем процессам
    MPI_Bcast(&n, 1, MPI_INT, 0, MPI_COMM_WORLD);

    if (n <= 0) {
        MPI_Finalize();
        return 1;
    }

    if (rank != 0) {
        B = new double[n * n];
    }

    // Рассылаем матрицу B целиком
    MPI_Bcast(B, n * n, MPI_DOUBLE, 0, MPI_COMM_WORLD);

    // Подготовка Scatterv и Gatherv
    int* sendcounts = new int[size];
    int* displs = new int[size];
    int offset = 0;
    for (int i = 0; i < size; i++) {
        int rows = n / size + (i < n % size ? 1 : 0);
        sendcounts[i] = rows * n;
        displs[i] = offset;
        offset += sendcounts[i];
    }

    int local_rows = n / size + (rank < n % size ? 1 : 0);
    double* A_local = new double[local_rows * n];
    double* C_local = new double[local_rows * n];
    std::fill(C_local, C_local + local_rows * n, 0.0);

    if (rank == 0) {
        std::cout << "\nВыполняется умножение матриц..." << std::endl;
        C = new double[n * n];
    }

    // Синхронизация перед началом отсчёта времени
    MPI_Barrier(MPI_COMM_WORLD);
    double start_time = MPI_Wtime();

    // Разделяем матрицу A по процессам
    MPI_Scatterv(A, sendcounts, displs, MPI_DOUBLE, A_local, local_rows * n, MPI_DOUBLE, 0, MPI_COMM_WORLD);

    // Локальное вычисление C_local
    for (int i = 0; i < local_rows; i++) {
        for (int k = 0; k < n; k++) {
            double a_ik = A_local[i * n + k];
            for (int j = 0; j < n; j++) {
                C_local[i * n + j] += a_ik * B[k * n + j];
            }
        }
    }

    // Собираем результаты в матрицу C на нулевом процессе
    MPI_Gatherv(C_local, local_rows * n, MPI_DOUBLE, C, sendcounts, displs, MPI_DOUBLE, 0, MPI_COMM_WORLD);

    double end_time = MPI_Wtime();

    if (rank == 0) {
        double seconds = end_time - start_time;
        long long numOperations = 2LL * n * n * n;
        double gflops_total = (double)numOperations / 1e9;
        double gflops_per_sec = gflops_total / seconds;
        
        long long memoryBytes = 3LL * n * n * sizeof(double);
        double memoryMB = (double)memoryBytes / (1024.0 * 1024.0);

        std::cout << "\n============ РЕЗУЛЬТАТЫ ============" << std::endl;
        std::cout << "Размер матрицы:       " << n << " x " << n << std::endl;
        std::cout << "Процессов (ядер):     " << size << std::endl;
        std::cout << "Время выполнения:     " << std::fixed << std::setprecision(6) << seconds << " сек" << std::endl;
        std::cout << "Объём задачи:         " << std::setprecision(3) << gflops_total << " GFLOP" << std::endl;
        std::cout << "Производительность:   " << std::setprecision(4) << gflops_per_sec << " GFLOP/s" << std::endl;
        std::cout << "Память (эквив. 1 пот.): " << std::setprecision(2) << memoryMB << " МБ" << std::endl;

        std::cout << "\nЗапись результата в файл: " << fileC << std::endl;
        if (!writeMatrix(fileC, C, n)) {
            std::cerr << "Не удалось записать результат." << std::endl;
        }

        int printSize = (n < 5) ? n : 5;
        std::cout << "\nЛевый верхний угол матрицы C (" << printSize << "x" << printSize << "):" << std::endl;
        for (int i = 0; i < printSize; i++) {
            for (int j = 0; j < printSize; j++) {
                std::cout << std::setw(12) << std::setprecision(4) << C[i * n + j];
            }
            std::cout << std::endl;
        }

        if (fileStats) {
            std::ofstream fstat(fileStats, std::ios::app);
            if (fstat.is_open()) {
                fstat << n << "," << size << ","
                      << std::fixed << std::setprecision(6) << seconds << ","
                      << std::setprecision(3) << gflops_total << ","
                      << std::setprecision(4) << gflops_per_sec << ","
                      << std::setprecision(2) << memoryMB << std::endl;
                fstat.close();
            }
        }
        std::cout << "\nГотово!" << std::endl;

        delete[] A;
        delete[] C;
    }

    delete[] B;
    delete[] A_local;
    delete[] C_local;
    delete[] sendcounts;
    delete[] displs;

    MPI_Finalize();
    return 0;
}