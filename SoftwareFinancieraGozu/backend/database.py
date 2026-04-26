import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATABASE_FILE = BASE_DIR.parent / 'database' / 'financiera.db'

def create_database(db_path: str = None):
    """Crea la base de datos con schema v2.0 - ContableAI"""
    db_path = db_path or DATABASE_FILE
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # ============================================================
    #  CONTABLE AI  —  Schema v2.0
    #  Motor: SQLite (compatible con PostgreSQL con ajustes mínimos)
    #  Convenciones: snake_case, timestamps UTC, soft-delete universal
    # ============================================================

    cursor.execute("PRAGMA foreign_keys = ON")
    cursor.execute("PRAGMA journal_mode = WAL")

    # ────────────────────────────────────────────────
    # 1. PLAN CONTABLE  (catálogo de cuentas)
    # ────────────────────────────────────────────────
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS plan_contable (
            codigo          TEXT    PRIMARY KEY,
            descripcion     TEXT    NOT NULL,
            tipo_cuenta     TEXT    NOT NULL
                            CHECK(tipo_cuenta IN ('ACTIVO','PASIVO','PATRIMONIO','INGRESO','GASTO')),
            naturaleza      TEXT    NOT NULL DEFAULT 'DEBE'
                            CHECK(naturaleza IN ('DEBE','HABER')),
            nivel           INTEGER NOT NULL DEFAULT 1,
            cuenta_padre    TEXT    REFERENCES plan_contable(codigo),
            activo          INTEGER NOT NULL DEFAULT 1
        )
    ''')

    cursor.executemany('''
        INSERT OR IGNORE INTO plan_contable 
        (codigo, descripcion, tipo_cuenta, naturaleza, nivel) VALUES (?, ?, ?, ?, ?)
    ''', [
        ('10', 'EFECTIVO',               'ACTIVO',    'DEBE',  1),
        ('12', 'BANCOS',                 'ACTIVO',    'DEBE',  1),
        ('20', 'CUENTAS POR COBRAR',     'ACTIVO',    'DEBE',  1),
        ('33', 'INVENTARIO',             'ACTIVO',    'DEBE',  1),
        ('36', 'ACTIVOS FIJOS',          'ACTIVO',    'DEBE',  1),
        ('40', 'VENTAS',                 'INGRESO',   'HABER', 1),
        ('42', 'OTROS INGRESOS',         'INGRESO',   'HABER', 1),
        ('50', 'GASTOS ADMINISTRATIVOS', 'GASTO',     'DEBE',  1),
        ('60', 'GASTOS DE VENTA',        'GASTO',     'DEBE',  1),
        ('70', 'GASTOS FINANCIEROS',     'GASTO',     'DEBE',  1),
        ('80', 'CUENTAS POR PAGAR',      'PASIVO',    'HABER', 1),
        ('90', 'PATRIMONIO',             'PATRIMONIO','HABER', 1),
    ])

    # ────────────────────────────────────────────────
    # 2. DICCIONARIO DE SINÓNIMOS
    # ────────────────────────────────────────────────
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS diccionario_sinonimos (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            palabra_usuario     TEXT    NOT NULL,
            concepto_estandar   TEXT    NOT NULL,
            idioma              TEXT    NOT NULL DEFAULT 'es',
            activo              INTEGER NOT NULL DEFAULT 1
        )
    ''')

    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_ds_palabra ON diccionario_sinonimos(palabra_usuario)
    ''')

    cursor.executemany('''
        INSERT OR IGNORE INTO diccionario_sinonimos (palabra_usuario, concepto_estandar) VALUES (?, ?)
    ''', [
        ('cash','EFECTIVO'),('yape','EFECTIVO'),('efectivo','EFECTIVO'),
        ('plin','EFECTIVO'),('billete','EFECTIVO'),
        ('banco','BANCOS'),('transferencia','BANCOS'),('deposito','BANCOS'),
        ('venta','VENTA'),('cobro','COBRO'),('ingreso','VENTA'),
        ('factura','VENTA'),('boleta','VENTA'),('servicio','VENTA'),
        ('compra','COMPRA'),('gasto','GASTO'),('pago','PAGO'),
        ('luz','LUZ'),('agua','AGUA'),('internet','INTERNET'),
        ('alquiler','ALQUILER'),('sueldo','PLANILLA'),('planilla','PLANILLA'),
        ('credito','CREDITO'),('tarjeta','CREDITO'),('prestamo','CREDITO'),
        ('laptop','ACTIVO_FIJO'),('activo','ACTIVO_FIJO'),('maquina','ACTIVO_FIJO'),
        ('mueble','ACTIVO_FIJO'),('vehiculo','ACTIVO_FIJO'),
        ('mercaderia','INVENTARIO'),('stock','INVENTARIO'),('producto','INVENTARIO'),
    ])

    # ────────────────────────────────────────────────
    # 3. MATRIZ DE COMPORTAMIENTO
    # ────────────────────────────────────────────────
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS matriz_comportamiento (
            id                    INTEGER PRIMARY KEY AUTOINCREMENT,
            concepto_estandar     TEXT    NOT NULL,
            cuenta_debe           TEXT    REFERENCES plan_contable(codigo),
            cuenta_haber          TEXT    REFERENCES plan_contable(codigo),
            descripcion_plantilla TEXT,
            prioridad             INTEGER NOT NULL DEFAULT 5,
            activo                INTEGER NOT NULL DEFAULT 1
        )
    ''')

    cursor.executemany('''
        INSERT OR IGNORE INTO matriz_comportamiento
        (concepto_estandar, cuenta_debe, cuenta_haber, descripcion_plantilla, prioridad) VALUES
        (?, ?, ?, ?, ?)
    ''', [
        ('VENTA',       '20','40','Venta de {detalle} por S/ {monto}',9),
        ('COBRO',       '10','20','Cobro de cliente por S/ {monto}',9),
        ('COMPRA',      '33','80','Compra de {detalle} por S/ {monto}',9),
        ('INVENTARIO',  '33','80','Ingreso de inventario {detalle}',8),
        ('PAGO',        '80','10','Pago a proveedor por S/ {monto}',8),
        ('GASTO',       '50','10','Gasto: {detalle} por S/ {monto}',7),
        ('LUZ',         '50','10','Pago servicio de luz S/ {monto}',9),
        ('AGUA',        '50','10','Pago servicio de agua S/ {monto}',9),
        ('INTERNET',    '50','10','Pago servicio internet S/ {monto}',9),
        ('ALQUILER',    '50','10','Pago alquiler S/ {monto}',9),
        ('PLANILLA',    '60','10','Pago planilla / sueldos S/ {monto}',9),
        ('ACTIVO_FIJO', '36','10','Adquisición activo fijo: {detalle}',6),
        ('CREDITO',     '10','80','Préstamo / crédito recibido S/ {monto}',7),
        ('BANCOS',      '12','10','Depósito bancario S/ {monto}',6),
    ])

    # ────────────────────────────────────────────────
    # 4. REGISTRO DE RECEPCIÓN
    # ────────────────────────────────────────────────
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS registro_recepcion (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            enunciado_raw   TEXT    NOT NULL,
            enunciado_norm  TEXT,
            tipo            TEXT    NOT NULL CHECK(tipo IN ('texto','audio','imagen')),
            archivo_url     TEXT,
            estado_proceso  TEXT    NOT NULL DEFAULT 'pendiente'
                            CHECK(estado_proceso IN ('pendiente','procesado','error')),
            error_msg       TEXT,
            usuario_id      INTEGER DEFAULT 1,
            ip_origen       TEXT,
            fecha           TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # ────────────────────────────────────────────────
    # 5. LIBRO DIARIO
    # ────────────────────────────────────────────────
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS libro_diario (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha            DATE    NOT NULL DEFAULT (date('now')),
            cuenta_debe      TEXT    NOT NULL REFERENCES plan_contable(codigo),
            cuenta_haber     TEXT    NOT NULL REFERENCES plan_contable(codigo),
            monto            REAL    NOT NULL CHECK(monto > 0),
            descripcion      TEXT    NOT NULL,
            concepto_std     TEXT,
            moneda           TEXT    NOT NULL DEFAULT 'PEN',
            tipo_cambio      REAL    NOT NULL DEFAULT 1.0,
            monto_base       REAL,
            id_recepcion     INTEGER REFERENCES registro_recepcion(id),
            eliminado        INTEGER NOT NULL DEFAULT 0,
            fecha_eliminado  TIMESTAMP,
            motivo_eliminado TEXT,
            creado_en        TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            modificado_en    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('CREATE INDEX IF NOT EXISTS idx_ld_fecha     ON libro_diario(fecha)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_ld_eliminado ON libro_diario(eliminado)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_ld_debe      ON libro_diario(cuenta_debe)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_ld_haber     ON libro_diario(cuenta_haber)')

    # ────────────────────────────────────────────────
    # 6. VISTAS CONTABLES
    # ────────────────────────────────────────────────

    # Solo asientos activos
    cursor.execute('''
        CREATE VIEW IF NOT EXISTS v_diario_activo AS
        SELECT * FROM libro_diario WHERE eliminado = 0
    ''')

    # Libro Mayor
    cursor.execute('''
        CREATE VIEW IF NOT EXISTS v_libro_mayor AS
        SELECT
            pc.codigo,
            pc.descripcion,
            pc.tipo_cuenta,
            pc.naturaleza,
            COALESCE(SUM(CASE WHEN ld.cuenta_debe  = pc.codigo THEN ld.monto ELSE 0 END), 0) AS total_debe,
            COALESCE(SUM(CASE WHEN ld.cuenta_haber = pc.codigo THEN ld.monto ELSE 0 END), 0) AS total_haber,
            CASE pc.naturaleza
                WHEN 'DEBE'  THEN
                    COALESCE(SUM(CASE WHEN ld.cuenta_debe  = pc.codigo THEN ld.monto ELSE 0 END), 0) -
                    COALESCE(SUM(CASE WHEN ld.cuenta_haber = pc.codigo THEN ld.monto ELSE 0 END), 0)
                WHEN 'HABER' THEN
                    COALESCE(SUM(CASE WHEN ld.cuenta_haber = pc.codigo THEN ld.monto ELSE 0 END), 0) -
                    COALESCE(SUM(CASE WHEN ld.cuenta_debe  = pc.codigo THEN ld.monto ELSE 0 END), 0)
            END AS saldo
        FROM plan_contable pc
        LEFT JOIN libro_diario ld
            ON (ld.cuenta_debe = pc.codigo OR ld.cuenta_haber = pc.codigo)
            AND ld.eliminado = 0
        GROUP BY pc.codigo
    ''')

    # Balance General
    cursor.execute('''
        CREATE VIEW IF NOT EXISTS v_balance_general AS
        SELECT tipo_cuenta, SUM(saldo) AS total
        FROM v_libro_mayor
        GROUP BY tipo_cuenta
    ''')

    # Estado de Resultados
    cursor.execute('''
        CREATE VIEW IF NOT EXISTS v_estado_resultados AS
        SELECT 'INGRESOS'     AS categoria, SUM(saldo) AS total FROM v_libro_mayor WHERE tipo_cuenta = 'INGRESO'
        UNION ALL
        SELECT 'GASTOS',                                          SUM(saldo)         FROM v_libro_mayor WHERE tipo_cuenta = 'GASTO'
        UNION ALL
        SELECT 'UTILIDAD NETA',
            (SELECT SUM(saldo) FROM v_libro_mayor WHERE tipo_cuenta = 'INGRESO') -
            (SELECT SUM(saldo) FROM v_libro_mayor WHERE tipo_cuenta = 'GASTO')
    ''')

    # ────────────────────────────────────────────────
    # 7. KPIs
    # ────────────────────────────────────────────────
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS kpi_config (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre        TEXT    NOT NULL UNIQUE,
            formula_sql   TEXT    NOT NULL,
            descripcion   TEXT,
            icono         TEXT,
            unidad        TEXT    DEFAULT '%',
            activo        INTEGER NOT NULL DEFAULT 1
        )
    ''')

    cursor.executemany('''
        INSERT OR IGNORE INTO kpi_config (nombre, formula_sql, descripcion, icono, unidad) VALUES (?, ?, ?, ?, ?)
    ''', [
        ('Utilidad Neta',
         'SELECT ROUND((SELECT COALESCE(SUM(saldo),0) FROM v_libro_mayor WHERE tipo_cuenta=\'INGRESO\')-(SELECT COALESCE(SUM(saldo),0) FROM v_libro_mayor WHERE tipo_cuenta=\'GASTO\'),2)',
         'Ganancia real después de restar todos los gastos',
         '💰','S/'),
        ('Margen de Ganancia',
         'SELECT ROUND(((SELECT COALESCE(SUM(saldo),0) FROM v_libro_mayor WHERE tipo_cuenta=\'INGRESO\')-(SELECT COALESCE(SUM(saldo),0) FROM v_libro_mayor WHERE tipo_cuenta=\'GASTO\'))*100.0/NULLIF((SELECT SUM(saldo) FROM v_libro_mayor WHERE tipo_cuenta=\'INGRESO\'),0),2)',
         'Porcentaje de ganancia sobre ingresos',
         '📈','%'),
        ('Total Ingresos',
         'SELECT ROUND(COALESCE(SUM(saldo),0),2) FROM v_libro_mayor WHERE tipo_cuenta=\'INGRESO\'',
         'Suma de todo el dinero que ha entrado',
         '⬆️','S/'),
        ('Total Gastos',
         'SELECT ROUND(COALESCE(SUM(saldo),0),2) FROM v_libro_mayor WHERE tipo_cuenta=\'GASTO\'',
         'Suma de todo el dinero que ha salido',
         '⬇️','S/'),
        ('Efectivo Disponible',
         'SELECT ROUND(COALESCE(saldo,0),2) FROM v_libro_mayor WHERE codigo=\'10\'',
         'Dinero en efectivo disponible',
         '💵','S/'),
        ('Cuentas por Cobrar',
         'SELECT ROUND(COALESCE(saldo,0),2) FROM v_libro_mayor WHERE codigo=\'20\'',
         'Dinero que clientes aún deben',
         '🕐','S/'),
    ])

    # ────────────────────────────────────────────────
    # 8. CURSOR / TUTORIAL
    # ────────────────────────────────────────────────
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cursor_sesiones (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id  INTEGER NOT NULL DEFAULT 1,
            elemento    TEXT    NOT NULL,
            visto_en    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE UNIQUE INDEX IF NOT EXISTS idx_cs_usuario_elemento
        ON cursor_sesiones(usuario_id, elemento)
    ''')

    # ────────────────────────────────────────────────
    # 9. CONFIGURACIÓN DE SISTEMA
    # ────────────────────────────────────────────────
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS config_sistema (
            clave       TEXT PRIMARY KEY,
            valor       TEXT NOT NULL,
            descripcion TEXT
        )
    ''')

    cursor.executemany('''
        INSERT OR IGNORE INTO config_sistema (clave, valor, descripcion) VALUES (?, ?, ?)
    ''', [
        ('nombre_empresa',  'Mi Empresa',   'Nombre del negocio'),
        ('moneda_base',     'PEN',          'Moneda principal'),
        ('simbolo_moneda',  'S/',           'Símbolo de la moneda'),
        ('ollama_model',    'llama3.2',     'Modelo Ollama para NLP'),
        ('whisper_model',   'whisper-1',    'Modelo para transcripción de audio'),
        ('cursor_activo',   '1',            'Mostrar guía para nuevos usuarios (1/0)'),
        ('voz_activa',      '1',            'Narración por voz activada (1/0)'),
        ('primer_uso',      '1',            'Primera vez de uso (1/0)'),
    ])

    conn.commit()
    conn.close()
    print(f"✅ Base de datos creada/actualizada: {db_path}")
    print("   Schema: ContableAI v2.0")
    print("   Tablas: 9 + 3 vistas")
    print("   Motor: SQLite WAL mode")

if __name__ == '__main__':
    create_database()