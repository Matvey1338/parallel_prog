@echo off
chcp 65001 >nul
setlocal EnableExtensions

if exist "C:\Program Files\Microsoft MPI\Bin" set "PATH=%PATH%;C:\Program Files\Microsoft MPI\Bin"
if exist "C:\Program Files (x86)\Microsoft SDKs\MPI\Bin" set "PATH=%PATH%;C:\Program Files (x86)\Microsoft SDKs\MPI\Bin"

set "MPI_SDK="
if exist "C:\Program Files (x86)\Microsoft SDKs\MPI\Include\mpi.h" set "MPI_SDK=C:\Program Files (x86)\Microsoft SDKs\MPI"
if not defined MPI_SDK if exist "C:\Program Files\Microsoft SDKs\MPI\Include\mpi.h" set "MPI_SDK=C:\Program Files\Microsoft SDKs\MPI"

set MATRIX_SIZE=1000

echo ================================================
echo   Автоматический запуск: генерация, умножение,
echo   верификация матриц %MATRIX_SIZE%x%MATRIX_SIZE% (MPI)
echo ================================================
echo.

:: --- Компиляция ---
echo [1/4] Компиляция matrix_mult.cpp ...
mpic++ -O2 -o matrix_mult.exe matrix_mult.cpp
if errorlevel 1 (
    echo ВНИМАНИЕ: Ошибка компиляции с mpic++.
    echo Пробуем стандартный g++ с флагами MS-MPI...
    if not defined MPI_SDK (
        echo ОШИБКА: Не найден MS-MPI SDK. Установите пакет SDK, не только redistributable.
        pause
        exit /b 1
    )
    g++ -O2 -o matrix_mult.exe matrix_mult.cpp -I"%MPI_SDK%\Include" -L"%MPI_SDK%\Lib\x64" -lmsmpi
    if errorlevel 1 (
        echo ОШИБКА компиляции! Убедитесь, что установлен MPI.
        pause
        exit /b 1
    )
)
echo       Компиляция успешна.
echo.

:: --- Генерация матриц ---
echo [2/4] Генерация тестовых матриц ...
python generate_matrices.py %MATRIX_SIZE%
if %ERRORLEVEL% neq 0 (
    echo ОШИБКА генерации матриц!
    pause
    exit /b 1
)
echo.

:: --- Умножение ---
echo [3/4] Запуск умножения матриц (4 процесса) ...
echo.
mpiexec -n 4 matrix_mult.exe
if %ERRORLEVEL% neq 0 (
    echo ОШИБКА при умножении матриц!
    pause
    exit /b 1
)
echo.

:: --- Верификация ---
echo [4/4] Верификация результатов (Python + NumPy) ...
echo.
python verify.py
if %ERRORLEVEL% neq 0 (
    echo ВЕРИФИКАЦИЯ НЕ ПРОЙДЕНА!
    pause
    exit /b 1
)

echo.
echo ================================================
echo   Все этапы завершены успешно
echo ================================================
pause
