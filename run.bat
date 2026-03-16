@echo off
chcp 65001 >nul

set MATRIX_SIZE=1000

echo ================================================
echo   Автоматический запуск: генерация, умножение,
echo   верификация матриц %MATRIX_SIZE%x%MATRIX_SIZE%
echo ================================================
echo.

:: --- Компиляция ---
echo [1/4] Компиляция matrix_mult.cpp ...
g++ -O2 -o matrix_mult.exe matrix_mult.cpp
if %ERRORLEVEL% neq 0 (
    echo ОШИБКА компиляции!
    pause
    exit /b 1
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
echo [3/4] Запуск умножения матриц ...
echo.
matrix_mult.exe
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