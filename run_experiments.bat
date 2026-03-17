@echo off
chcp 65001 >nul

echo ================================================
echo   Серия экспериментов: размеры 200..2000
echo ================================================
echo.

:: --- Компиляция ---
echo [1] Компиляция...
g++ -O2 -o matrix_mult.exe matrix_mult.cpp
if %ERRORLEVEL% neq 0 (
    echo ОШИБКА компиляции!
    pause
    exit /b 1
)
echo     Компиляция успешна.
echo.

:: --- Очистка файла статистики ---
set STATS_FILE=experiment_results.csv
echo n,time_sec,gflop,gflop_s,memory_mb > %STATS_FILE%

:: --- Цикл по размерам ---
for %%N in (200 400 800 1200 1600 2000) do (
    echo ================================================
    echo   Размер матрицы: %%N x %%N
    echo ================================================

    echo   Генерация матриц...
    python generate_matrices.py %%N
    echo.

    echo   Умножение матриц...
    matrix_mult.exe matrix_A.txt matrix_B.txt matrix_C.txt %STATS_FILE%
    echo.

    echo   Верификация...
    python verify.py
    echo.

    echo   --- %%N x %%N завершено ---
    echo.
)

echo ================================================
echo   Все эксперименты завершены!
echo   Результаты в файле: %STATS_FILE%
echo ================================================
echo.

:: --- Построение графиков ---
echo Построение графиков...
python plot_results.py %STATS_FILE%
echo.

pause