@echo off
REM Windows batch script for St. Louis 311+ daily sync
REM Run this script daily via Windows Task Scheduler

echo Starting St. Louis 311+ Daily Sync at %date% %time%

REM Navigate to project directory
cd /d "C:\Users\mills\geo_dev\stl311_plus"

REM Check if containers are running, start them if needed
echo Checking Docker container status...
docker-compose ps | findstr "stl311_flask" >nul
if %ERRORLEVEL% NEQ 0 (
    echo Docker containers not running. Starting them...
    docker-compose up -d
    echo Waiting for containers to be ready...
    timeout /t 30 /nobreak >nul
    echo Containers started.
) else (
    echo Docker containers are already running.
)

REM Run daily sync using Docker
echo Running daily sync...
docker exec stl311_flask python daily_sync.py yesterday

if %ERRORLEVEL% EQU 0 (
    echo Daily sync completed successfully at %date% %time%
) else (
    echo Daily sync failed at %date% %time%
)

echo Sync operation finished
pause
