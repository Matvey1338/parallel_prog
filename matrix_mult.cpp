#include <mpi.h>
#include <iostream>
#include <fstream>
#include <cstdlib>
#include <cstring>
#include <iomanip>

double* readMatrix(const char* filename, int& n) {
    std::ifstream fin(filename);
    if (!fin.is_open()) {
        std::cerr << "Error: could not open file " << filename << std::endl;
        return NULL;
    }
    fin >> n;
    if (n <= 0) {
        std::cerr << "Error: invalid matrix size in file " << filename << std::endl;
        return NULL;
    }
    double* matrix = new double[n * n];
    for (int i = 0; i < n * n; i++) {
        if (!(fin >> matrix[i])) {
            std::cerr << "Error: insufficient data in file " << filename << std::endl;
            delete[] matrix;
            return NULL;
        }
    }
    fin.close();
    return matrix;
}

bool writeMatrix(const char* filename, const double* matrix, int n) {
    std::ofstream fout(filename);
    if (!fout.is_open()) {
        std::cerr << "Error: could not create file " << filename << std::endl;
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
    MPI_Init(&argc, &argv);

    int rank, size;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

    const char* fileA = "matrix_A.txt";
    const char* fileB = "matrix_B.txt";
    const char* fileC = "matrix_C.txt";
    const char* fileStats = NULL;

    if (argc >= 4) {
        fileA = argv[1];
        fileB = argv[2];
        fileC = argv[3];
    }
    if (argc >= 5) {
        fileStats = argv[4];
    }

    int n = 0;
    double *A = NULL;
    double *B = NULL;
    double *C = NULL;

    if (rank == 0) {
        std::cout << "============================================" << std::endl;
        std::cout << "  Square Matrix Multiplication (i-k-j)      " << std::endl;
        std::cout << "  MPI Implementation (processes: " << size << ") " << std::endl;
        std::cout << "============================================" << std::endl;

        int nA = 0, nB = 0;
        std::cout << "\nReading matrix A from file: " << fileA << std::endl;
        A = readMatrix(fileA, nA);
        if (A) {
            std::cout << "Reading matrix B from file: " << fileB << std::endl;
            B = readMatrix(fileB, nB);
            if (B && nA != nB) {
                std::cerr << "Error: matrix dimensions do not match (" << nA << " != " << nB << ")" << std::endl;
                delete[] A; delete[] B;
                A = NULL; B = NULL;
            } else if (B) {
                n = nA;
                std::cout << "Matrix size: " << n << " x " << n << std::endl;
            }
        }
        if (!A || !B) {
            n = -1; // Error signal to other processes
        }
    }

    // Broadcast matrix size to all processes
    MPI_Bcast(&n, 1, MPI_INT, 0, MPI_COMM_WORLD);

    if (n <= 0) {
        MPI_Finalize();
        return 1;
    }

    if (rank != 0) {
        B = new double[n * n];
    }

    // Broadcast matrix B completely
    MPI_Bcast(B, n * n, MPI_DOUBLE, 0, MPI_COMM_WORLD);

    // Preparation for Scatterv and Gatherv
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
    for (int i = 0; i < local_rows * n; i++) {
        C_local[i] = 0.0;
    }

    if (rank == 0) {
        std::cout << "\nPerforming matrix multiplication..." << std::endl;
        C = new double[n * n];
    }

    // Synchronization before starting the timer
    MPI_Barrier(MPI_COMM_WORLD);
    double start_time = MPI_Wtime();

    // Scatter matrix A across processes
    MPI_Scatterv(A, sendcounts, displs, MPI_DOUBLE, A_local, local_rows * n, MPI_DOUBLE, 0, MPI_COMM_WORLD);

    // Local computation of C_local
    for (int i = 0; i < local_rows; i++) {
        for (int k = 0; k < n; k++) {
            double a_ik = A_local[i * n + k];
            for (int j = 0; j < n; j++) {
                C_local[i * n + j] += a_ik * B[k * n + j];
            }
        }
    }

    // Gather results into matrix C on the root process
    MPI_Gatherv(C_local, local_rows * n, MPI_DOUBLE, C, sendcounts, displs, MPI_DOUBLE, 0, MPI_COMM_WORLD);

    double end_time = MPI_Wtime();

    if (rank == 0) {
        double seconds = end_time - start_time;
        long long numOperations = (long long)2 * n * n * n;
        double gflops_total = (double)numOperations / 1e9;
        double gflops_per_sec = gflops_total / seconds;
        
        long long memoryBytes = (long long)3 * n * n * sizeof(double);
        double memoryMB = (double)memoryBytes / (1024.0 * 1024.0);

        std::cout << "\n============= RESULTS ==============" << std::endl;
        std::cout << "Matrix size:          " << n << " x " << n << std::endl;
        std::cout << "Processes (cores):    " << size << std::endl;
        std::cout << "Execution time:       " << std::fixed << std::setprecision(6) << seconds << " sec" << std::endl;
        std::cout << "Task volume:          " << std::setprecision(3) << gflops_total << " GFLOP" << std::endl;
        std::cout << "Performance:          " << std::setprecision(4) << gflops_per_sec << " GFLOP/s" << std::endl;
        std::cout << "Memory (eq. 1 thread):" << std::setprecision(2) << memoryMB << " MB" << std::endl;

        std::cout << "\nWriting result to file: " << fileC << std::endl;
        if (!writeMatrix(fileC, C, n)) {
            std::cerr << "Failed to write result." << std::endl;
        }

        int printSize = (n < 5) ? n : 5;
        std::cout << "\nTop-left corner of matrix C (" << printSize << "x" << printSize << "):" << std::endl;
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
        std::cout << "\nDone!" << std::endl;

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