#include <iostream>
#include <fstream>
#include <cstdlib>
#include <cstring>
#include <iomanip>
#include <windows.h>
#include <cuda_runtime.h>

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

__global__ void multiplyMatrices_kernel(const double* A, const double* B, double* C, int n) {
    int row = blockIdx.y * blockDim.y + threadIdx.y;
    int col = blockIdx.x * blockDim.x + threadIdx.x;

    if (row < n && col < n) {
        double sum = 0.0;
        for (int k = 0; k < n; k++) {
            sum += A[row * n + k] * B[k * n + col];
        }
        C[row * n + col] = sum;
    }
}

int main(int argc, char* argv[]) {
    SetConsoleOutputCP(65001);

    const char* fileA = "matrix_A.txt";
    const char* fileB = "matrix_B.txt";
    const char* fileC = "matrix_C.txt";
    const char* fileStats = nullptr;
    int blockSize = 16;

    if (argc >= 4) {
        fileA = argv[1];
        fileB = argv[2];
        fileC = argv[3];
    }
    if (argc >= 5) {
        fileStats = argv[4];
    }
    if (argc >= 6) {
        blockSize = std::atoi(argv[5]);
        if (blockSize <= 0) blockSize = 16;
    }

    std::cout << "============================================" << std::endl;
    std::cout << "  Перемножение квадратных матриц (CUDA)     " << std::endl;
    std::cout << "  Размер блока: " << blockSize << "x" << blockSize << std::endl;
    std::cout << "============================================" << std::endl;

    int nA = 0, nB = 0;

    std::cout << "\nЧтение матрицы A из файла: " << fileA << std::endl;
    double* h_A = readMatrix(fileA, nA);
    if (!h_A) return 1;

    std::cout << "Чтение матрицы B из файла: " << fileB << std::endl;
    double* h_B = readMatrix(fileB, nB);
    if (!h_B) { delete[] h_A; return 1; }

    if (nA != nB) {
        std::cerr << "Ошибка: размеры матриц не совпадают ("
                  << nA << " != " << nB << ")" << std::endl;
        delete[] h_A; delete[] h_B;
        return 1;
    }

    int n = nA;
    std::cout << "Размер матриц: " << n << " x " << n << std::endl;

    // Объём задачи
    long long numOperations = 2LL * n * n * n;
    double gflops_total = (double)numOperations / 1e9;
    std::cout << "Объём задачи: " << numOperations << " операций ("
              << std::fixed << std::setprecision(3) << gflops_total << " GFLOP)" << std::endl;

    long long memoryBytes = 3LL * n * n * sizeof(double);
    double memoryMB = (double)memoryBytes / (1024.0 * 1024.0);
    std::cout << "Требуемая память: " << std::fixed << std::setprecision(2)
              << memoryMB << " МБ (" << memoryBytes << " байт)" << std::endl;

    double* h_C = new double[n * n];

    // Выделение памяти на устройстве
    double *d_A = nullptr, *d_B = nullptr, *d_C = nullptr;
    cudaMalloc((void**)&d_A, n * n * sizeof(double));
    cudaMalloc((void**)&d_B, n * n * sizeof(double));
    cudaMalloc((void**)&d_C, n * n * sizeof(double));

    std::cout << "\nКопирование данных на GPU..." << std::endl;
    cudaMemcpy(d_A, h_A, n * n * sizeof(double), cudaMemcpyHostToDevice);
    cudaMemcpy(d_B, h_B, n * n * sizeof(double), cudaMemcpyHostToDevice);

    dim3 threadsPerBlock(blockSize, blockSize);
    dim3 numBlocks((n + blockSize - 1) / blockSize, (n + blockSize - 1) / blockSize);

    std::cout << "Выполняется умножение матриц..." << std::endl;

    cudaEvent_t start, stop;
    cudaEventCreate(&start);
    cudaEventCreate(&stop);

    cudaEventRecord(start);
    multiplyMatrices_kernel<<<numBlocks, threadsPerBlock>>>(d_A, d_B, d_C, n);
    cudaEventRecord(stop);
    
    cudaEventSynchronize(stop);

    float milliseconds = 0;
    cudaEventElapsedTime(&milliseconds, start, stop);
    double seconds = milliseconds / 1000.0;
    
    cudaEventDestroy(start);
    cudaEventDestroy(stop);

    cudaError_t err = cudaGetLastError();
    if (err != cudaSuccess) {
        std::cerr << "CUDA Error: " << cudaGetErrorString(err) << std::endl;
    }

    std::cout << "Копирование результатов с GPU..." << std::endl;
    cudaMemcpy(h_C, d_C, n * n * sizeof(double), cudaMemcpyDeviceToHost);

    double gflops_per_sec = gflops_total / seconds;

    std::cout << "\n============ РЕЗУЛЬТАТЫ ============" << std::endl;
    std::cout << "Размер матрицы:       " << n << " x " << n << std::endl;
    std::cout << "Размер блока:         " << blockSize << "x" << blockSize << std::endl;
    std::cout << "Время выполнения:     " << std::fixed << std::setprecision(6)
              << seconds << " сек" << std::endl;
    std::cout << "Производительность:   " << std::setprecision(4)
              << gflops_per_sec << " GFLOP/s" << std::endl;

    std::cout << "\nЗапись результата в файл: " << fileC << std::endl;
    if (!writeMatrix(fileC, h_C, n)) {
        delete[] h_A; delete[] h_B; delete[] h_C;
        cudaFree(d_A); cudaFree(d_B); cudaFree(d_C);
        return 1;
    }

    int printSize = (n < 5) ? n : 5;
    std::cout << "\nЛевый верхний угол матрицы C (" << printSize << "x" << printSize << "):" << std::endl;
    for (int i = 0; i < printSize; i++) {
        for (int j = 0; j < printSize; j++) {
            std::cout << std::setw(12) << std::setprecision(4) << h_C[i * n + j];
        }
        std::cout << std::endl;
    }

    if (fileStats) {
        std::ofstream fstat(fileStats, std::ios::app);
        if (fstat.is_open()) {
            fstat << n << ","
                  << blockSize << ","
                  << std::fixed << std::setprecision(6) << seconds << ","
                  << std::setprecision(3) << gflops_total << ","
                  << std::setprecision(4) << gflops_per_sec << ","
                  << std::setprecision(2) << memoryMB << std::endl;
            fstat.close();
        }
    }

    std::cout << "\nГотово!" << std::endl;

    delete[] h_A;
    delete[] h_B;
    delete[] h_C;
    cudaFree(d_A);
    cudaFree(d_B);
    cudaFree(d_C);
    
    return 0;
}
