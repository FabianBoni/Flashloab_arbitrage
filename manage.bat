@echo off
REM BSC Arbitrage Docker Management Script
REM Quick Docker operations for Windows

echo.
echo ================================
echo  BSC ARBITRAGE DOCKER MANAGER
echo ================================
echo.

:menu
echo 1. Build Docker Image
echo 2. Start Services
echo 3. Stop Services
echo 4. Show Status
echo 5. Show Logs
echo 6. Restart Services
echo 7. Python Manager (Advanced)
echo 8. Exit
echo.
set /p choice="Select option (1-8): "

if "%choice%"=="1" goto build
if "%choice%"=="2" goto start
if "%choice%"=="3" goto stop
if "%choice%"=="4" goto status
if "%choice%"=="5" goto logs
if "%choice%"=="6" goto restart
if "%choice%"=="7" goto python_manager
if "%choice%"=="8" goto exit
echo Invalid option!
goto menu

:build
echo.
echo Building Docker image...
docker build -t bsc-arbitrage .
if %errorlevel% equ 0 (
    echo ✅ Image built successfully!
) else (
    echo ❌ Build failed!
)
pause
goto menu

:start
echo.
echo Starting Docker services...
docker-compose down >nul 2>&1
docker-compose up -d
if %errorlevel% equ 0 (
    echo ✅ Services started!
    echo.
    docker-compose ps
) else (
    echo ❌ Failed to start services!
)
pause
goto menu

:stop
echo.
echo Stopping Docker services...
docker-compose down
if %errorlevel% equ 0 (
    echo ✅ Services stopped!
) else (
    echo ❌ Failed to stop services!
)
pause
goto menu

:status
echo.
echo Docker Services Status:
echo -----------------------
docker ps
echo.
echo Compose Services:
echo -----------------
docker-compose ps
pause
goto menu

:logs
echo.
echo Docker Logs (Press Ctrl+C to stop):
echo -----------------------------------
docker-compose logs -f
goto menu

:restart
echo.
echo Restarting Docker services...
docker-compose restart
if %errorlevel% equ 0 (
    echo ✅ Services restarted!
    echo.
    docker-compose ps
) else (
    echo ❌ Failed to restart services!
)
pause
goto menu

:python_manager
echo.
echo Starting Python Docker Manager...
python manage.py
goto menu

:exit
echo.
echo Goodbye!
exit /b 0
