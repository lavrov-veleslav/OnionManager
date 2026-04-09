@echo off
title Build OnionManager
echo =======================================
echo Building OnionManager.exe with PyInstaller
echo =======================================

set "CUR_DIR=%~dp0"
cd /d "%CUR_DIR%"

:: Проверка наличия PyInstaller
where pyinstaller >nul 2>nul
if errorlevel 1 (
    echo PyInstaller not found! Please install: pip install pyinstaller
    pause
    exit /b 1
)

:: Сборка
pyinstaller --onefile --windowed --icon="icon.ico" --name "OnionManager" --add-data "icon.ico;." "Onion.pyw"

if errorlevel 1 (
    echo Build failed!
    pause
    exit /b 1
)

:: Перемещение exe
if exist "dist\OnionManager.exe" (
    move /y "dist\OnionManager.exe" "%CUR_DIR%" >nul
    echo OK: OnionManager.exe moved to %CUR_DIR%
) else (
    echo ERROR: dist\OnionManager.exe not found!
    pause
    exit /b 1
)

:: Удаление мусора
rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul
del /q "OnionManager.spec" 2>nul

echo =======================================
echo Build complete! File: OnionManager.exe
echo =======================================
pause