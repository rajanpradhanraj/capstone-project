@echo off
echo Starting E-Commerce Platform Services...

REM Kill any existing services on those ports
echo Killing existing services...
for /f "tokens=5" %%a in ('netstat -aon ^| find ":5000" ^| find "LISTENING"') do taskkill /F /PID %%a 2>nul
for /f "tokens=5" %%a in ('netstat -aon ^| find ":5001" ^| find "LISTENING"') do taskkill /F /PID %%a 2>nul
for /f "tokens=5" %%a in ('netstat -aon ^| find ":5002" ^| find "LISTENING"') do taskkill /F /PID %%a 2>nul
for /f "tokens=5" %%a in ('netstat -aon ^| find ":4200" ^| find "LISTENING"') do taskkill /F /PID %%a 2>nul

echo Starting API Gateway (Port 5000)...
cd api-gateway
start "API Gateway" cmd /c "python app.py"
cd ..

timeout /t 3

echo Starting Product Catalog Service (Port 5001)...
cd product-catalog-service
start "Product Service" cmd /c "python app.py"
cd ..

timeout /t 3

echo Starting Order Service (Port 5002)...
cd order-service
start "Order Service" cmd /c "python app.py"
cd ..

timeout /t 3

echo Starting Angular Frontend (Port 4200)...
cd frontend
start "Frontend" cmd /c "ng serve --open"
cd ..

echo All services started!
echo API Gateway: http://localhost:5000
echo Product Service: http://localhost:5001
echo Order Service: http://localhost:5002
echo Frontend: http://localhost:4200

pause
