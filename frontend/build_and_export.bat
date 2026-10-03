@echo off
setlocal enabledelayedexpansion
title Next.js Frontend Export to FastAPI Static
color 0B

echo [*] Building Next.js Static Export...
cd /d "%~dp0"

call npm run build
if %errorlevel% neq 0 (
    color 0C
    echo [ERROR] Next.js build failed.
    pause
    exit /b 1
)

echo.
echo [*] Copying static export from out/ to backend/static/...
if exist "out" (
    xcopy /E /I /Y "out\*" "..\backend\static\"
    echo [SUCCESS] Copied out/ to backend/static/ successfully!
) else (
    color 0C
    echo [ERROR] 'out' directory was not generated. Check next.config.ts for output: 'export'.
    pause
    exit /b 1
)

echo.
echo [DONE] Frontend built and deployed to FastAPI backend static folder!
