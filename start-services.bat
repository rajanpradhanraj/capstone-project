@echo off
REM E-Commerce Microservices Startup Script for Windows

echo 🚀 Starting E-Commerce Microservices Application...

REM Function to check if a service is running
:check_service
setlocal
set service_name=%1
set port=%2
set max_attempts=30
set attempt=1

echo ⏳ Waiting for %service_name% to start on port %port%...

:loop
if %attempt% leq %max_attempts% (
    curl -s -f http://localhost:%port%/health >nul 2>&1
    if %errorlevel% equ 0 (
        echo ✅ %service_name% is running!
        goto :end_check
    )
    
    echo    Attempt %attempt%/%max_attempts% - %service_name% not ready yet...
    timeout /t 2 /nobreak >nul
    set /a attempt+=1
    goto loop
)

echo ❌ %service_name% failed to start within expected time
:end_check
endlocal
goto :eof

REM Stop any existing containers
echo 🧹 Cleaning up existing containers...
docker-compose down

REM Build and start services
echo 🔨 Building and starting services...
docker-compose up -d --build

REM Check services
echo 🔍 Checking service health...

REM Wait a bit for containers to initialize
timeout /t 5 /nobreak >nul

REM Check Product Catalog Service
call :check_service "Product Catalog Service" 5001

REM Check Order Service  
call :check_service "Order Service" 5002

REM Check API Gateway
call :check_service "API Gateway" 5000

REM Check Frontend
curl -s -f http://localhost:4200/health >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Frontend is running!
) else (
    echo ⚠️  Frontend may still be starting up...
)

echo.
echo 🎉 E-Commerce Application is ready!
echo.
echo 📱 Frontend (Angular):     http://localhost:4200
echo 🔧 API Gateway:           http://localhost:5000
echo 📦 Product Service:       http://localhost:5001
echo 🛒 Order Service:         http://localhost:5002
echo.
echo 👨‍💼 Demo Admin Login:      username: admin, password: password
echo 👤 Demo User Login:       username: user1, password: password
echo.
echo To stop the application: docker-compose down
echo To view logs: docker-compose logs -f [service-name]

pause



