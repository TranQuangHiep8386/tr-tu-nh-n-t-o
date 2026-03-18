@echo off
chcp 65001 > nul
title FireSentinel AI - He Thong Canh Bao Chay
echo ======================================================
echo    STARTING FIRE DETECTION SYSTEM...
echo    DANG KHOI DONG HE THONG CANH BAO CHAY...
echo ======================================================

cd /d "%~dp0"

:: Kiem tra moi truong ao
if exist ".venv\Scripts\activate.bat" (
    echo [INFO] Activating virtual environment...
    call .venv\Scripts\activate.bat
) else (
    echo [WARNING] Virtual environment not found. Using system Python.
)

:: Chay ung dung
echo [INFO] Launching Streamlit App...
streamlit run app.py

pause
