@echo off
echo Starting all services NOW...

taskkill /F /IM python.exe 2>nul
taskkill /F /IM node.exe 2>nul

cd api-gateway
start "API" python app.py
cd ..\product-catalog-service
start "Products" python app.py  
cd ..\order-service
start "Orders" python app.py
cd ..\frontend
start "Frontend" ng serve --open
cd ..

echo All services started! Wait 30 seconds then visit http://localhost:4200
timeout /t 30
echo Your project is ready at http://localhost:4200
