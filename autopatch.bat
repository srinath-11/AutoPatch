@echo off
chcp 65001 > nul
echo Starting AutoPatch...

cd /d "C:\Users\moham\Projects\Linux project\AutoPatch"

:: Check if Podman is available
podman --version > nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Podman is not installed or not in PATH
    pause
    exit /b 1
)

:: Run AutoPatch
python src\main.py

if %errorlevel% equ 0 (
    echo AutoPatch completed successfully
) else (
    echo AutoPatch encountered errors
)

pause