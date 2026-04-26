@echo off
setlocal

echo Cerrando Contable AI...

rem Cierra las ventanas CMD abiertas por iniciar_contable_ai.bat
taskkill /F /FI "WINDOWTITLE eq Contable AI API*" >nul 2>nul
taskkill /F /FI "WINDOWTITLE eq Contable AI Web*" >nul 2>nul

rem Fallback por puertos (si quedaron procesos sueltos)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":3001" ^| findstr "LISTENING"') do (
  taskkill /F /PID %%a >nul 2>nul
)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":3000" ^| findstr "LISTENING"') do (
  taskkill /F /PID %%a >nul 2>nul
)

echo Listo. Backend y frontend detenidos (si estaban activos).
