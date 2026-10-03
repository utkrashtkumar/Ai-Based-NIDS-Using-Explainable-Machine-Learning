@echo off
setlocal enabledelayedexpansion
title AI-Based Network Intrusion Detection System (XAI-NIDS)
color 0A

:: 1. Self-Elevation to Administrator Privileges (Required for Scapy raw sockets and Firewall netsh rules)
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [*] Requesting Administrator Privileges for Network Packet Sniffing...
    powershell -Command "Start-Process cmd -ArgumentList '/c call \"%~f0\"' -Verb RunAs"
    exit /b
)

cd /d "%~dp0"

echo ======================================================================
echo    AI-Based Network Intrusion Detection System (XAI-NIDS)
echo    Powered by XGBoost, TreeSHAP, Scapy & FastAPI
echo ======================================================================
echo.

:: 2. Verify Virtual Environment
if not exist ".venv\Scripts\activate.bat" (
    color 0C
    echo [ERROR] Virtual environment not found.
    echo Please run install_prereqs.bat first to set up the environment.
    echo.
    pause
    exit /b 1
)

echo [*] Activating environment (.venv)...
call .venv\Scripts\activate.bat

:: 3. Launch the NIDS Server
echo [*] Starting AI-NIDS Core Engine on http://127.0.0.1:8000...
echo [*] Opening your web browser in 3 seconds...

:: Launch browser in background after 3 seconds
start /b cmd /c "timeout /t 3 /nobreak >nul && start http://127.0.0.1:8000"

:: Start Uvicorn Server
python -m uvicorn backend.app:app --host 127.0.0.1 --port 8000 --log-level info

pause
