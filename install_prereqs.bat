@echo off
setlocal enabledelayedexpansion
title AI-NIDS - System Setup and Prerequisites Installer
color 0B

echo ======================================================================
echo    AI-Based Network Intrusion Detection System (XAI-NIDS)
echo    Phase 1: Automated Environment & Prerequisites Setup
echo ======================================================================
echo.

:: 1. Check Python Installation
echo [*] Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    color 0C
    echo [ERROR] Python is not installed or not added to your system PATH!
    echo Please install Python 3.10 or higher from https://www.python.org/
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VER=%%i
echo [OK] Python %PYTHON_VER% detected.
echo.

:: 2. Setup Virtual Environment
if not exist ".venv" (
    echo [*] Creating Python virtual environment in .venv...
    python -m venv .venv
    if %errorlevel% neq 0 (
        color 0C
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created successfully.
) else (
    echo [OK] Existing virtual environment found (.venv).
)
echo.

:: 3. Activate Virtual Environment & Install Dependencies
echo [*] Activating virtual environment and upgrading pip...
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip

echo.
echo [*] Installing required Python dependencies from requirements.txt...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    color 0C
    echo [ERROR] Failed to install one or more dependencies.
    echo Please check your internet connection and try again.
    pause
    exit /b 1
)
echo [OK] Python dependencies installed successfully.
echo.

:: 4. Detect Npcap Driver for Windows Packet Sniffing
echo [*] Checking for Npcap packet capture driver (Required for live sniffing)...
set NPCAP_FOUND=0

reg query "HKLM\SOFTWARE\Npcap" >nul 2>&1
if %errorlevel% equ 0 set NPCAP_FOUND=1

reg query "HKLM\SOFTWARE\WOW6432Node\Npcap" >nul 2>&1
if %errorlevel% equ 0 set NPCAP_FOUND=1

if exist "%SystemRoot%\System32\drivers\npcap.sys" set NPCAP_FOUND=1

if %NPCAP_FOUND% equ 1 (
    echo [OK] Npcap packet capture driver is installed and ready.
) else (
    color 0E
    echo [!] WARNING: Npcap is NOT detected on this computer.
    echo.
    echo Live network packet sniffing on Windows requires Npcap.
    echo (Note: Offline CSV Studio and Simulator mode will still work without it).
    echo.
    echo Would you like to open the official Npcap download page now? (Y/N)
    set /p NPCAP_CHOICE="Enter Y or N: "
    if /i "!NPCAP_CHOICE!"=="Y" (
        start https://npcap.com/#download
        echo.
        echo Please download and run the installer. Recommended settings:
        echo   - "Install Npcap in WinPcap API-compatible Mode" (Checked)
        echo   - "Support raw 802.11 traffic (and monitor mode)" (Optional)
        echo.
        pause
    )
)

echo.
echo ======================================================================
echo [SUCCESS] Environment setup is complete!
echo You can now launch the application anytime using: Start_NIDS.bat
echo ======================================================================
echo.
pause
