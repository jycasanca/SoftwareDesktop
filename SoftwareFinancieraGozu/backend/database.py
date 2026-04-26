import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATABASE_FILE = BASE_DIR.parent / 'database' / 'financiera.db'

def create_database(db_path: str = None):
    db_path = db_path or DATABASE_FILE
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Tabla plan_contable: códigos de 2 dígitos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS plan_contable (
            codigo TEXT PRIMARY KEY,
            descripcion TEXT
        )
    ''')

    # Tabla diccionario_sinonimos: (palabra_usuario, concepto_estandar)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS diccionario_sinonimos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            palabra_usuario TEXT,
            concepto_estandar TEXT
        )
    ''')

    # Tabla matriz_comportamiento: (concepto_estandar, cuenta_asociada, naturaleza_default, prioridad)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS matriz_comportamiento (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            concepto_estandar TEXT,
            cuenta_asociada TEXT,
            naturaleza_default TEXT,  -- 'DEBE' o 'HABER'
            prioridad INTEGER
        )
    ''')

    # Tabla registro_recepcion: enunciados originales
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS registro_recepcion (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            enunciado TEXT,
            tipo TEXT,  -- 'texto' o 'audio'
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Tabla libro_diario: asientos finales
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS libro_diario (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha DATE,
            cuenta_debe TEXT,
            cuenta_haber TEXT,
            monto REAL,
            descripcion TEXT,
            id_recepcion INTEGER,
            FOREIGN KEY (id_recepcion) REFERENCES registro_recepcion(id)
        )
    ''')

    # Insertar datos iniciales en plan_contable
    initial_accounts = [
        ('10', 'EFECTIVO'),
        ('12', 'BANCOS'),
        ('20', 'CUENTAS POR COBRAR'),
        ('33', 'INVENTARIO'),
        ('40', 'VENTAS'),
        ('42', 'OTROS INGRESOS'),
        ('50', 'GASTOS ADMINISTRATIVOS'),
        ('60', 'GASTOS DE VENTA'),
        ('70', 'GASTOS FINANCIEROS')
    ]
    cursor.executemany('INSERT OR IGNORE INTO plan_contable (codigo, descripcion) VALUES (?, ?)', initial_accounts)

    # Insertar datos iniciales de sinónimos
    initial_synonyms = [
        ('cash', 'EFECTIVO'),
        ('yape', 'EFECTIVO'),
        ('efectivo', 'EFECTIVO'),
        ('luz', 'LUZ'),
        ('pago', 'PAGO'),
        ('venta', 'VENTA'),
        ('cobro', 'COBRO'),
        ('credito', 'CREDITO'),
        ('tarjeta', 'CREDITO'),
        ('laptop', 'ACTIVO'),
        ('activo', 'ACTIVO')
    ]
    cursor.executemany('INSERT OR IGNORE INTO diccionario_sinonimos (palabra_usuario, concepto_estandar) VALUES (?, ?)', initial_synonyms)

    # Insertar configuración inicial de matriz de comportamiento
    initial_matrix = [
        ('LUZ', '50', 'DEBE', 9),
        ('PAGO', '50', 'DEBE', 8),
        ('VENTA', '40', 'HABER', 9),
        ('COBRO', '40', 'HABER', 9),
        ('ACTIVO', '10', 'DEBE', 5),
        ('GASTO', '50', 'DEBE', 7)
    ]
    cursor.executemany('INSERT OR IGNORE INTO matriz_comportamiento (concepto_estandar, cuenta_asociada, naturaleza_default, prioridad) VALUES (?, ?, ?, ?)', initial_matrix)

    conn.commit()
    conn.close()

if __name__ == '__main__':
    create_database()