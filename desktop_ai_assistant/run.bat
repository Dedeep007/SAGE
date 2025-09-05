@echo off
echo Starting SAGE Desktop AI Assistant...
echo.

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

REM Run the application
python main.py

REM If we get here, the application has closed
echo.
echo SAGE Desktop AI Assistant has closed.
pause
