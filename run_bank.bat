@echo off
echo Activating virtual environment...
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
) else (
    echo [ERROR] Virtual environment not found! Please ensure 'venv' or '.venv' exists.
    pause
    exit /b 1
)

echo Starting the Banking System...
python run.py
pause
