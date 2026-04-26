from pathlib import Path
from typing import List

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import FileResponse
from starlette.staticfiles import StaticFiles
import sqlite3
import os
from pydantic import BaseModel
from processing import process_text
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

BASE_DIR = Path(__file__).resolve().parent
DATABASE_FILE = BASE_DIR.parent / 'database' / 'financiera.db'
STATIC_DIR = BASE_DIR / 'static'
REPORTS_DIR = BASE_DIR.parent / 'reports'

app = FastAPI()
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

try:
    import whisper
    model = whisper.load_model("base")
except ImportError:
    model = None


def get_db_connection():
    return sqlite3.connect(DATABASE_FILE)


@app.post("/process_text")
def process_text_endpoint(text: str = Form(...), amount: float = Form(...)):
    entries = process_text(text, amount)
    return {"entries": entries}

@app.post("/process_audio")
def process_audio(file: UploadFile = File(...), amount: float = Form(...)):
    if model is None:
        raise HTTPException(status_code=501, detail="Whisper no está instalado. Instale openai-whisper para habilitar transcripción.")
    temp_path = BASE_DIR / 'temp_audio.wav'
    with open(temp_path, "wb") as f:
        f.write(file.file.read())
    result = model.transcribe(str(temp_path))
    text = result.get("text", "")
    temp_path.unlink(missing_ok=True)
    entries = process_text(text, amount)
    return {"text": text, "entries": entries}

@app.get("/diccionario")
def get_diccionario():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM diccionario_sinonimos')
    rows = cursor.fetchall()
    conn.close()
    return {"diccionario": rows}

@app.post("/add_sinonimo")
def add_sinonimo(palabra: str = Form(...), concepto: str = Form(...)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO diccionario_sinonimos (palabra_usuario, concepto_estandar) VALUES (?, ?)', (palabra, concepto))
    conn.commit()
    conn.close()
    return {"message": "Agregado"}

@app.get("/matriz_comportamiento")
def get_matriz():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM matriz_comportamiento')
    rows = cursor.fetchall()
    conn.close()
    return {"matriz": rows}

@app.post("/add_regla")
def add_regla(concepto: str = Form(...), cuenta: str = Form(...), naturaleza: str = Form(...), prioridad: int = Form(...)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO matriz_comportamiento (concepto_estandar, cuenta_asociada, naturaleza_default, prioridad) VALUES (?, ?, ?, ?)', (concepto, cuenta, naturaleza, prioridad))
    conn.commit()
    conn.close()
    return {"message": "Agregado"}

class AsientoEntry(BaseModel):
    cuenta: str
    naturaleza: str
    monto: float

class SaveAsientoRequest(BaseModel):
    entries: List[AsientoEntry]
    descripcion: str

@app.post("/save_asiento")
def save_asiento(request: SaveAsientoRequest):
    conn = get_db_connection()
    cursor = conn.cursor()
    # Insertar en registro_recepcion
    cursor.execute('INSERT INTO registro_recepcion (enunciado, tipo) VALUES (?, ?)', (request.descripcion, 'manual'))
    id_recepcion = cursor.lastrowid
    # Insertar en libro_diario
    for entry in request.entries:
        cursor.execute('INSERT INTO libro_diario (fecha, cuenta_debe, cuenta_haber, monto, descripcion, id_recepcion) VALUES (date("now"), ?, ?, ?, ?, ?)',
                       (entry.cuenta if entry.naturaleza.upper() == 'DEBE' else None,
                        entry.cuenta if entry.naturaleza.upper() == 'HABER' else None,
                        entry.monto, request.descripcion, id_recepcion))
    conn.commit()
    conn.close()
    return {"message": "Guardado"}

@app.get("/plan_contable")
def get_plan_contable():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT codigo, descripcion FROM plan_contable ORDER BY codigo')
    rows = cursor.fetchall()
    conn.close()
    return {"plan_contable": rows}

@app.get("/balance_comprobacion")
def balance_comprobacion():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT cuenta_debe, SUM(monto) as debe FROM libro_diario WHERE cuenta_debe IS NOT NULL GROUP BY cuenta_debe
        UNION ALL
        SELECT cuenta_haber, -SUM(monto) as haber FROM libro_diario WHERE cuenta_haber IS NOT NULL GROUP BY cuenta_haber
    ''')
    rows = cursor.fetchall()
    conn.close()
    # Procesar para balance
    balance = {}
    for row in rows:
        cuenta, monto = row
        if cuenta not in balance:
            balance[cuenta] = 0
        balance[cuenta] += monto
    return {"balance": balance}

@app.get("/generate_pdf")
def generate_pdf():
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    output_file = REPORTS_DIR / 'estados_financieros.pdf'
    c = canvas.Canvas(str(output_file), pagesize=letter)
    c.drawString(100, 750, "Balance General")
    c.drawString(100, 730, "Balance de Comprobación")
    c.drawString(100, 710, "(reporte generado automáticamente)")
    c.save()
    return FileResponse(str(output_file), media_type='application/pdf', filename="estados_financieros.pdf")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)