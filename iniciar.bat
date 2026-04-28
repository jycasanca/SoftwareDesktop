@echo off
chcp 65001 >nul
title GOZU - Sistema Contable - Iniciador
color 0A

echo ==============================================================
echo                 GOZU - Sistema Contable
echo                   Verificando Sistema
echo ==============================================================
echo.

:: 1. VERIFICAR PYTHON
echo [*] Verificando Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    color 0C
    echo [ERROR] Python no esta instalado o no esta configurado en el PATH del sistema.
    echo Por favor descarga e instala Python 3.10 o superior desde https://www.python.org/
    echo Asegurate de marcar la casilla "Add Python to PATH" durante la instalacion.
    pause
    exit /b
)
echo [OK] Python detectado correctamente.
echo.

:: 2. VERIFICAR TESSERACT OCR
echo [*] Verificando Tesseract OCR (Para lectura de comprobantes)...
set TESS_FOUND=0
tesseract --version >nul 2>&1
if %errorlevel% equ 0 set TESS_FOUND=1
if exist "C:\Program Files\Tesseract-OCR\tesseract.exe" set TESS_FOUND=1
if exist "C:\Program Files (x86)\Tesseract-OCR\tesseract.exe" set TESS_FOUND=1
if exist "%LOCALAPPDATA%\Programs\Tesseract-OCR\tesseract.exe" set TESS_FOUND=1

if %TESS_FOUND% equ 1 (
    echo [OK] Tesseract OCR detectado.
) else (
    color 0E
    echo [ADVERTENCIA] Tesseract OCR no parece estar instalado.
    echo La funcion de escaneo y lectura de imagenes/PDFs podria no funcionar.
    echo Puedes descargarlo desde: https://github.com/UB-Mannheim/tesseract/wiki
)
echo.

:: 3. VERIFICAR OLLAMA
echo [*] Verificando Ollama (Para IA de clasificacion automatica)...
ollama --version >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Ollama detectado.
) else (
    color 0E
    echo [ADVERTENCIA] Ollama no esta instalado o no esta ejecutandose.
    echo La clasificacion inteligente de transacciones con IA no estara disponible.
    echo Puedes descargarlo desde: https://ollama.com/
)
echo.

:: 4. ENTORNO VIRTUAL
echo [*] Configurando Entorno Virtual de Python...
if not exist ".venv\Scripts\activate.bat" (
    echo Creando entorno virtual por primera vez ^(esto puede tardar un momento^)...
    python -m venv .venv
    if %errorlevel% neq 0 (
        color 0C
        echo [ERROR] No se pudo crear el entorno virtual. Verifica tu instalacion de Python.
        pause
        exit /b
    )
)
call .venv\Scripts\activate.bat
echo [OK] Entorno virtual activado.
echo.

:: 5. DEPENDENCIAS
echo [*] Verificando e instalando dependencias (requirements.txt)...
python -m pip install --upgrade pip --quiet
if exist "gozu_contable\requirements.txt" (
    pip install -r gozu_contable\requirements.txt --quiet
    if %errorlevel% neq 0 (
        color 0C
        echo [ERROR] Ocurrio un problema al instalar las dependencias.
        echo Revisa la conexion a internet e intenta nuevamente.
        pause
        exit /b
    )
    echo [OK] Dependencias instaladas y al dia.
) else (
    color 0C
    echo [ERROR] No se encontro el archivo gozu_contable\requirements.txt.
    echo Asegurate de que la carpeta gozu_contable exista y contenga el archivo.
    pause
    exit /b
)
echo.

:: 6. INICIAR APLICACION
echo ==============================================================
echo                 Sistema verificado con exito
echo                    Iniciando aplicacion...
echo ==============================================================
echo.

color 0F
cd gozu_contable
if exist "main.py" (
    python main.py
) else (
    color 0C
    echo [ERROR] No se encontro main.py en la carpeta gozu_contable.
    pause
    exit /b
)

:: Salir de gozu_contable para dejar la consola en el directorio original si se cierra
cd ..
pause
