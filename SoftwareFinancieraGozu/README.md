# Sistema Financiera Gozu

Arquitectura:
- Backend Python + FastAPI en `backend/`
- Base de datos SQLite en `database/financiera.db`
- Interfaz de escritorio WPF C# en `frontend/` usando WebView2
- Frontend HTML/JS servido por FastAPI desde `backend/static/index.html`

Tablas clave en SQLite:
- `plan_contable`
- `diccionario_sinonimos`
- `matriz_comportamiento`
- `registro_recepcion`
- `libro_diario`

## Cómo iniciar

1. Instalar dependencias Python:
   ```bash
   cd backend
   C:/Users/ACER/AppData/Local/Programs/Python/Python312/python.exe -m pip install -r requirements.txt
   ```

2. Crear la base de datos (ya creada automáticamente si ejecutas):
   ```bash
   C:/Users/ACER/AppData/Local/Programs/Python/Python312/python.exe database.py
   ```

3. Correr el backend FastAPI:
   ```bash
   C:/Users/ACER/AppData/Local/Programs/Python/Python312/python.exe main.py
   ```

4. Abrir el frontend WPF en Visual Studio o compilar con .NET SDK. Si no dispone de .NET SDK, use el navegador para abrir `http://127.0.0.1:8000/static/index.html`.

## Funcionalidades implementadas

- Editor de diccionario de sinónimos.
- Editor de reglas de comportamiento para conceptos contables.
- Procesamiento de texto para extraer conceptos y proponer asientos.
- Validación de asientos antes de guardarlos en `libro_diario`.
- Balance de comprobación.
- Generación básica de PDF de estados financieros.

## Notas

- El soporte de Whisper está preparado como opción en `backend/main.py`, pero requiere instalar `openai-whisper`.
- Si no dispone de `.NET SDK`, puede usar solo el backend y la carpeta `backend/static` para probar la UI desde un navegador.
