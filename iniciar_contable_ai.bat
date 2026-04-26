@echo off
setlocal

cd /d %~dp0
set "APP_DIR=%~dp0SoftwareFinancieraGozu"
set "WEB_URL=http://localhost:3000"
set "API_URL=http://localhost:3001/api/health"

if not exist "%APP_DIR%\package.json" (
  echo No se encontro SoftwareFinancieraGozu en "%APP_DIR%".
  pause
  exit /b 1
)

cd /d "%APP_DIR%"

where npm >nul 2>nul
if errorlevel 1 (
  echo npm no esta disponible en PATH.
  echo Instala Node.js y vuelve a intentarlo.
  pause
  exit /b 1
)

if not exist node_modules (
  echo Instalando dependencias del monorepo...
  call npm install
  if errorlevel 1 (
    echo Fallo la instalacion de dependencias.
    pause
    exit /b 1
  )
)

start "Contable AI API" /D "%APP_DIR%" cmd /k "npm run dev --workspace backend"
start "Contable AI Web" /D "%APP_DIR%" cmd /k "npm run dev --workspace frontend"

timeout /t 4 /nobreak >nul
start "" "%WEB_URL%"

echo.
echo API: %API_URL%
echo WEB: %WEB_URL%
echo.