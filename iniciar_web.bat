@echo off
setlocal

REM Script para iniciar la aplicacion web - Backend FastAPI + Frontend HTML/JS
REM Acceso: http://127.0.0.1:8000

set "ROOT_DIR=%~dp0"
set "APP_DIR=%ROOT_DIR%SoftwareFinancieraGozu"
set "BACKEND_DIR=%APP_DIR%\backend"

if not exist "%BACKEND_DIR%\main.py" (
  echo [ERROR] No se encontro el backend en: %BACKEND_DIR%
  pause
  exit /b 1
)

echo.
echo ========================================
echo   Sistema Financiera Gozu - WEB
echo ========================================
echo.

set "PYTHON_CMD="
where py >nul 2>nul
if %errorlevel%==0 (
  for %%V in (3.12 3.11 3.10) do (
    py -%%V -c "import sys" >nul 2>nul
    if not errorlevel 1 (
      set "PYTHON_CMD=py -%%V"
      goto :python_ok
    )
  )
)

where python >nul 2>nul
if %errorlevel%==0 (
  set "PYTHON_CMD=python"
  goto :python_ok
)

echo [ERROR] No se encontro Python compatible en PATH.
pause
exit /b 1

:python_ok
echo [1/3] Usando interprete: %PYTHON_CMD%

echo [2/3] Instalando dependencias de backend...
pushd "%BACKEND_DIR%"
call %PYTHON_CMD% -m pip install -q -r requirements.txt
if not %errorlevel%==0 (
  echo [ERROR] Fallo al instalar dependencias.
  popd
  pause
  exit /b 1
)

echo [3/3] Preparando base de datos...
call %PYTHON_CMD% database.py >nul 2>nul

echo.
echo ========================================
echo   BACKEND INICIADO
echo ========================================
echo.
echo URL: http://127.0.0.1:8000
echo.
echo Presiona Ctrl+C para detener el servidor
echo.

call %PYTHON_CMD% "%BACKEND_DIR%\main.py"
