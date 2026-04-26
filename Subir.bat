@echo off
echo ==============================
echo Subiendo cambios a VillaSexo
echo ==============================

:: Ir a la ruta del proyecto (opcional si ya estás ahí)
cd /d %~dp0

:: Verificar rama actual
echo Rama actual:
git branch --show-current

:: Asegurar que estás en VillaSexo
git switch VillaSexo

:: Agregar cambios
echo Agregando archivos...
git add .

:: Crear commit
set /p mensaje=Escribe el mensaje del commit: 
git commit -m "%mensaje%"

:: Subir cambios
echo Subiendo a GitHub...
git push origin VillaSexo

echo ==============================
echo Proceso terminado
pause