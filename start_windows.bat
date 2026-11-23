@echo off
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 (
 echo Python Launcher not found. Install Python 3.11 or 3.12 from python.org.
 pause
 exit /b 1
)
if not exist .venv py -3 -m venv .venv
call .venv\Scripts\activate.bat
python -m pip install -r requirements.txt
if errorlevel 1 (
 echo Package installation failed.
 pause
 exit /b 1
)
python -m streamlit run app.py
pause
