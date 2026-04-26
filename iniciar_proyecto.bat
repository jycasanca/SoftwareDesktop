@echo off
setlocal

REM Script para iniciar backend (FastAPI) y frontend (WPF) del proyecto.

set "ROOT_DIR=%~dp0"
set "APP_DIR=%ROOT_DIR%SoftwareFinancieraGozu"
set "BACKEND_DIR=%APP_DIR%\backend"
set "FRONTEND_PROJ=%APP_DIR%\frontend\SoftwareFinancieraGozu.csproj"

if not exist "%BACKEND_DIR%\main.py" (
  echo [ERROR] No se encontro el backend en: %BACKEND_DIR%
  pause
  exit /b 1
)

if not exist "%FRONTEND_PROJ%" (
  echo [ERROR] No se encontro el proyecto frontend en: %FRONTEND_PROJ%
  pause
  exit /b 1
)

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
  for /f "tokens=1,2 delims=." %%A in ('python -c "import sys; print(str(sys.version_info[0]) + '.' + str(sys.version_info[1]))"') do (
    if %%A==3 if %%B LEQ 12 (
      set "PYTHON_CMD=python"
      goto :python_ok
    )
  )
)

echo [ERROR] No se encontro Python compatible (3.10 a 3.12) en PATH.
echo [ERROR] Dependencias fijadas del backend fallan con Python 3.13/3.14.
pause
exit /b 1

:python_ok
echo Usando interprete: %PYTHON_CMD%

where dotnet >nul 2>nul
if not %errorlevel%==0 (
  echo [ERROR] .NET SDK no esta disponible en PATH.
  pause
  exit /b 1
)

echo.
echo [1/4] Instalando dependencias de backend...
pushd "%BACKEND_DIR%"
call %PYTHON_CMD% -m pip install -r requirements.txt
if not %errorlevel%==0 (
  echo [ERROR] Fallo al instalar dependencias de Python.
  popd
  pause
  exit /b 1
)

echo [2/4] Preparando base de datos...
call %PYTHON_CMD% database.py
if not %errorlevel%==0 (
  echo [ERROR] Fallo al preparar la base de datos.
  popd
  pause
  exit /b 1
)

echo [3/4] Iniciando backend en una nueva ventana...
start "Backend FastAPI" cmd /k "cd /d "%BACKEND_DIR%" && %PYTHON_CMD% main.py"
popd

echo [4/4] Iniciando frontend WPF...
dotnet nuget list source | findstr /i "nuget.org" >nul
if not %errorlevel%==0 (
  echo Configurando origen NuGet nuget.org...
  dotnet nuget add source "https://api.nuget.org/v3/index.json" --name "nuget.org" >nul
)

echo Restaurando paquetes de frontend...
dotnet restore "%FRONTEND_PROJ%"
if not %errorlevel%==0 (
  echo [ERROR] Fallo al restaurar paquetes NuGet del frontend.
  pause
  exit /b 1
)

dotnet run --project "%FRONTEND_PROJ%"

echo.
echo Frontend finalizado.
endlocal