@echo off
chcp 65001 >nul
setlocal EnableExtensions

:: Скобки в "(x86)" внутри блока if ( ) ломают разбор; путь в переменной задаём до вложенных if
set "MPI_SDK="
if exist "C:\Program Files (x86)\Microsoft SDKs\MPI\Include\mpi.h" set "MPI_SDK=C:\Program Files (x86)\Microsoft SDKs\MPI"
if not defined MPI_SDK if exist "C:\Program Files\Microsoft SDKs\MPI\Include\mpi.h" set "MPI_SDK=C:\Program Files\Microsoft SDKs\MPI"

echo ================================================
echo   Серия экспериментов: размеры 200..2000
echo   Ядра: 1, 2, 4, 8
echo ================================================
echo.

:: Создаём папку data
if not exist data mkdir data

:: Компиляция (предполагается, что mpi компилятор доступен)
echo [1] Компиляция matrix_mult.cpp ...
mpic++ -O2 -o matrix_mult.exe matrix_mult.cpp
if errorlevel 1 (

    echo ВНИМАНИЕ: Ошибка компиляции с mpic++.
    echo Пробуем стандартный g++ с флагами MS-MPI...

    if not defined MPI_SDK (
        echo ОШИБКА: Не найден MS-MPI SDK — нужен Include\mpi.h.
        echo Установите пакет MS-MPI SDK, не только redistributable, и перезапустите терминал.
        pause
        exit /b 1
    )
    
    g++ -O2 -o matrix_mult.exe matrix_mult.cpp -I"%MPI_SDK%\Include" -L"%MPI_SDK%\Lib\x64" -lmsmpi
    if errorlevel 1 (
        echo ОШИБКА компиляции! Проверьте MPI / MS-MPI, MinGW g++ и пути к библиотекам.
        pause
        exit /b 1
    )
)
echo     OK
echo.

:: Очистка файла статистики
set STATS_FILE=experiment_results.csv
echo n,cores,time_sec,gflop,gflop_s,memory_mb > %STATS_FILE%

:: Цикл по размерам
for %%N in (200 400 800 1200 1600 2000) do (
    echo ================================================
    echo   N = %%N
    echo ================================================

    python generate_matrices.py %%N

    :: Цикл по процессам
    for %%P in (1 2 4 8) do (
        echo   --- Запуск, процессов MPI: %%P ---
        mpiexec -n %%P matrix_mult.exe matrix_A.txt matrix_B.txt matrix_C.txt %STATS_FILE%
        
        python verify.py
    )

    echo   --- %%N завершено ---
    echo.
)

echo ================================================
echo   Все эксперименты завершены
echo   Данные: %STATS_FILE%
echo ================================================
echo.

:: Графики в папку data
echo Построение графиков в папку data/ ...
python plot_results.py %STATS_FILE%
echo.

:: Удаляем временные файлы матриц
del /q matrix_A.txt matrix_B.txt matrix_C.txt 2>nul

echo Готово!
pause
