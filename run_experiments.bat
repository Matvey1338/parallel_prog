@echo off
chcp 65001 >nul

echo ================================================
echo   Серия экспериментов: размеры 200..2000
echo ================================================
echo.

:: Создаём папку data
if not exist data mkdir data

:: Компиляция
echo [1] Компиляция matrix_mult.cpp ...
g++ -O2 -o matrix_mult.exe matrix_mult.cpp
if %ERRORLEVEL% neq 0 (
    echo ОШИБКА компиляции!
    pause
    exit /b 1
)
echo     OK
echo.

:: Очистка файла статистики
set STATS_FILE=experiment_results.csv
echo n,time_sec,gflop,gflop_s,memory_mb > %STATS_FILE%

:: Цикл по размерам
for %%N in (200 400 800 1200 1600 2000) do (
    echo ================================================
    echo   N = %%N
    echo ================================================

    python generate_matrices.py %%N

    matrix_mult.exe matrix_A.txt matrix_B.txt matrix_C.txt %STATS_FILE%

    python verify.py

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