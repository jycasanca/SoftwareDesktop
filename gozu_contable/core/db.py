import sqlite3
import os
import config

class DB:
    @staticmethod
    def get_conexion():
        conn = sqlite3.connect(config.DB_PATH)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        return conn
    
    @staticmethod
    def fetchone(sql, params=()):
        conn = DB.get_conexion()
        try:
            cursor = conn.execute(sql, params)
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()
    
    @staticmethod
    def fetchall(sql, params=()):
        conn = DB.get_conexion()
        try:
            cursor = conn.execute(sql, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()
    
    @staticmethod
    def execute(sql, params=()):
        conn = DB.get_conexion()
        try:
            cursor = conn.execute(sql, params)
            conn.commit()
            return cursor
        finally:
            conn.close()
    
    @staticmethod
    def transaction(operaciones):
        conn = DB.get_conexion()
        try:
            cursor = conn.cursor()
            for sql, params in operaciones:
                cursor.execute(sql, params)
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    @staticmethod
    def inicializar():
        os.makedirs(os.path.dirname(config.DB_PATH), exist_ok=True)
        conn = DB.get_conexion()
        try:
            DB._ejecutar_schema(conn)
            DB._ejecutar_seed(conn)
        finally:
            conn.close()
    
    @staticmethod
    def _ejecutar_schema(conn):
        SCHEMA_SQL = """
        CREATE TABLE IF NOT EXISTS plan_contable (
            codigo      INTEGER PRIMARY KEY,
            descripcion TEXT NOT NULL,
            tipo_cuenta TEXT NOT NULL,
            naturaleza  TEXT NOT NULL,
            activa      INTEGER DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS libro_diario (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            numero_asiento   INTEGER NOT NULL,
            fecha            TEXT NOT NULL,
            cuenta_codigo    INTEGER NOT NULL,
            descripcion      TEXT,
            debe             REAL DEFAULT 0,
            haber            REAL DEFAULT 0,
            eliminado        INTEGER DEFAULT 0,
            fecha_eliminado  TEXT,
            motivo_eliminado TEXT,
            creado_en        TEXT DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (cuenta_codigo) REFERENCES plan_contable(codigo)
        );

        CREATE TABLE IF NOT EXISTS diccionario_sinonimos (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            palabra_clave   TEXT NOT NULL,
            termino_estandar TEXT NOT NULL,
            codigo_cuenta   INTEGER,
            FOREIGN KEY (codigo_cuenta) REFERENCES plan_contable(codigo)
        );

        CREATE TABLE IF NOT EXISTS matriz_comportamiento (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            palabras_clave TEXT NOT NULL,
            cuentas_debe   TEXT NOT NULL,
            cuentas_haber  TEXT NOT NULL,
            prioridad      INTEGER DEFAULT 0,
            activa         INTEGER DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS config_sistema (
            clave TEXT PRIMARY KEY,
            valor TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS registro_recepcion (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            texto_original  TEXT,
            fuente          TEXT,
            resultado_json  TEXT,
            estado          TEXT DEFAULT 'preview',
            creado_en       TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE VIEW IF NOT EXISTS v_diario_activo AS
        SELECT * FROM libro_diario WHERE eliminado = 0;

        CREATE VIEW IF NOT EXISTS v_libro_mayor AS
        SELECT
            ld.cuenta_codigo,
            p.descripcion,
            p.tipo_cuenta,
            p.naturaleza,
            SUM(ld.debe)            AS total_debe,
            SUM(ld.haber)           AS total_haber,
            SUM(ld.debe)-SUM(ld.haber) AS saldo
        FROM libro_diario ld
        JOIN plan_contable p ON p.codigo = ld.cuenta_codigo
        WHERE ld.eliminado = 0
        GROUP BY ld.cuenta_codigo;

        CREATE VIEW IF NOT EXISTS v_balance_comprobacion AS
        SELECT
            ld.cuenta_codigo AS codigo,
            p.descripcion,
            p.tipo_cuenta,
            SUM(ld.debe)   AS sumas_debe,
            SUM(ld.haber)  AS sumas_haber,
            CASE WHEN SUM(ld.debe)>=SUM(ld.haber)
                 THEN SUM(ld.debe)-SUM(ld.haber) ELSE 0 END AS saldo_deudor,
            CASE WHEN SUM(ld.haber)>SUM(ld.debe)
                 THEN SUM(ld.haber)-SUM(ld.debe) ELSE 0 END AS saldo_acreedor
        FROM libro_diario ld
        JOIN plan_contable p ON p.codigo = ld.cuenta_codigo
        WHERE ld.eliminado = 0
        GROUP BY ld.cuenta_codigo;

        CREATE VIEW IF NOT EXISTS v_balance_general AS
        SELECT
            p.tipo_cuenta,
            SUM(ld.debe)  AS total_debe,
            SUM(ld.haber) AS total_haber
        FROM libro_diario ld
        JOIN plan_contable p ON p.codigo = ld.cuenta_codigo
        WHERE ld.eliminado = 0
        GROUP BY p.tipo_cuenta;

        CREATE VIEW IF NOT EXISTS v_estado_resultados AS
        SELECT
            p.tipo_cuenta,
            p.codigo,
            p.descripcion,
            SUM(ld.haber)-SUM(ld.debe) AS saldo
        FROM libro_diario ld
        JOIN plan_contable p ON p.codigo = ld.cuenta_codigo
        WHERE ld.eliminado = 0
          AND p.tipo_cuenta IN ('ingreso','gasto','costo')
        GROUP BY p.codigo;
        """
        conn.executescript(SCHEMA_SQL)
        conn.commit()
    
    @staticmethod
    def _ejecutar_seed(conn):
        cursor = conn.cursor()
        
        # Verificar si ya hay datos
        cursor.execute("SELECT COUNT(*) FROM plan_contable")
        if cursor.fetchone()[0] > 0:
            return
        
        # Seed plan_contable
        PLAN_CONTABLE_SEED = [
            (10,'Efectivo y Equivalentes de Efectivo','activo_corriente','deudora'),
            (11,'Inversiones Financieras','activo_corriente','deudora'),
            (12,'Cuentas por Cobrar Comerciales - Terceros','activo_corriente','deudora'),
            (13,'Cuentas por Cobrar Comerciales - Relacionadas','activo_corriente','deudora'),
            (14,'Cuentas por Cobrar al Personal y Accionistas','activo_corriente','deudora'),
            (16,'Cuentas por Cobrar Diversas - Terceros','activo_corriente','deudora'),
            (17,'Cuentas por Cobrar Diversas - Relacionadas','activo_corriente','deudora'),
            (18,'Servicios Contratados por Anticipado','activo_corriente','deudora'),
            (20,'Mercaderías','activo_corriente','deudora'),
            (21,'Productos Terminados','activo_corriente','deudora'),
            (22,'Subproductos, Desechos y Desperdicios','activo_corriente','deudora'),
            (23,'Productos en Proceso','activo_corriente','deudora'),
            (24,'Materias Primas','activo_corriente','deudora'),
            (25,'Materiales Auxiliares, Suministros y Repuestos','activo_corriente','deudora'),
            (26,'Envases y Embalajes','activo_corriente','deudora'),
            (28,'Existencias por Recibir','activo_corriente','deudora'),
            (29,'Desvalorización de Existencias','activo_corriente','acreedora'),
            (30,'Inversiones Mobiliarias','activo_no_corriente','deudora'),
            (31,'Inversiones Inmobiliarias','activo_no_corriente','deudora'),
            (32,'Activos en Arrendamiento Financiero','activo_no_corriente','deudora'),
            (33,'Inmuebles, Maquinaria y Equipo','activo_no_corriente','deudora'),
            (34,'Intangibles','activo_no_corriente','deudora'),
            (35,'Activos Biológicos','activo_no_corriente','deudora'),
            (37,'Activo Diferido','activo_no_corriente','deudora'),
            (39,'Depreciación y Amortización Acumulada','activo_no_corriente','acreedora'),
            (40,'Tributos y Aportes al Sistema de Pensiones y Salud','pasivo_corriente','acreedora'),
            (41,'Remuneraciones y Participaciones por Pagar','pasivo_corriente','acreedora'),
            (42,'Cuentas por Pagar Comerciales - Terceros','pasivo_corriente','acreedora'),
            (43,'Cuentas por Pagar Comerciales - Relacionadas','pasivo_corriente','acreedora'),
            (44,'Cuentas por Pagar a Accionistas y Directores','pasivo_corriente','acreedora'),
            (45,'Obligaciones Financieras','pasivo_no_corriente','acreedora'),
            (46,'Cuentas por Pagar Diversas - Terceros','pasivo_corriente','acreedora'),
            (47,'Cuentas por Pagar Diversas - Relacionadas','pasivo_corriente','acreedora'),
            (48,'Provisiones','pasivo_corriente','acreedora'),
            (49,'Pasivo Diferido','pasivo_no_corriente','acreedora'),
            (50,'Capital','patrimonio','acreedora'),
            (51,'Acciones de Inversión','patrimonio','acreedora'),
            (52,'Capital Adicional','patrimonio','acreedora'),
            (56,'Resultados No Realizados','patrimonio','acreedora'),
            (57,'Excedente de Revaluación','patrimonio','acreedora'),
            (58,'Reservas','patrimonio','acreedora'),
            (59,'Resultados Acumulados','patrimonio','acreedora'),
            (60,'Compras','gasto','deudora'),
            (61,'Variación de Existencias','gasto','deudora'),
            (62,'Gastos de Personal, Directores y Gerentes','gasto','deudora'),
            (63,'Gastos de Servicios Prestados por Terceros','gasto','deudora'),
            (64,'Gastos por Tributos','gasto','deudora'),
            (65,'Otros Gastos de Gestión','gasto','deudora'),
            (67,'Gastos Financieros','gasto','deudora'),
            (68,'Valuación y Deterioro de Activos','gasto','deudora'),
            (69,'Costo de Ventas','costo','deudora'),
            (70,'Ventas','ingreso','acreedora'),
            (71,'Variación de la Producción Almacenada','ingreso','acreedora'),
            (72,'Producción de Activo Inmovilizado','ingreso','acreedora'),
            (73,'Descuentos, Rebajas y Bonificaciones Obtenidos','ingreso','acreedora'),
            (75,'Otros Ingresos de Gestión','ingreso','acreedora'),
            (77,'Ingresos Financieros','ingreso','acreedora'),
            (88,'Impuesto a la Renta','gasto','deudora'),
            (89,'Resultado del Ejercicio','patrimonio','acreedora'),
        ]
        
        cursor.executemany(
            "INSERT OR IGNORE INTO plan_contable (codigo, descripcion, tipo_cuenta, naturaleza) VALUES (?,?,?,?)",
            PLAN_CONTABLE_SEED
        )
        
        # Seed diccionario_sinonimos
        DICCIONARIO_SEED = [
            ('caja','efectivo',10),
            ('banco','efectivo_banco',10),
            ('efectivo','efectivo',10),
            ('clientes','cuentas_cobrar',12),
            ('deudores','cuentas_cobrar',12),
            ('proveedores','cuentas_pagar',42),
            ('mercaderia','mercaderias',20),
            ('mercadería','mercaderias',20),
            ('inventario','mercaderias',20),
            ('maquinaria','inmuebles_maq',33),
            ('terreno','inmuebles_maq',33),
            ('equipo','inmuebles_maq',33),
            ('planilla','gasto_personal',62),
            ('sueldos','gasto_personal',62),
            ('salarios','gasto_personal',62),
            ('igv','tributo_igv',40),
            ('renta','tributo_renta',40),
            ('prestamo','obligacion_financiera',45),
            ('préstamo','obligacion_financiera',45),
            ('capital','capital_social',50),
            ('ventas','ventas',70),
            ('ingresos','ventas',70),
            ('compras','compras',60),
            ('servicios','servicios_terceros',63),
            ('alquiler','servicios_terceros',63),
        ]
        
        cursor.executemany(
            "INSERT OR IGNORE INTO diccionario_sinonimos (palabra_clave, termino_estandar, codigo_cuenta) VALUES (?,?,?)",
            DICCIONARIO_SEED
        )
        
        # Seed matriz_comportamiento
        MATRIZ_SEED = [
            ('["compra","mercaderia","inventario"]','[60]','[42]',10,1),
            ('["venta","ingreso","cobro"]','[12]','[70]',10,1),
            ('["planilla","sueldo","salario","remuneracion"]','[62]','[41]',10,1),
            ('["pago","proveedor","factura"]','[42]','[10]',9,1),
            ('["prestamo","banco","credito"]','[10]','[45]',9,1),
            ('["alquiler","servicio","tercero"]','[63]','[10]',8,1),
            ('["igv","impuesto","tributo"]','[64]','[40]',8,1),
            ('["depreciacion"]','[68]','[39]',7,1),
        ]
        
        cursor.executemany(
            "INSERT OR IGNORE INTO matriz_comportamiento (palabras_clave, cuentas_debe, cuentas_haber, prioridad, activa) VALUES (?,?,?,?,?)",
            MATRIZ_SEED
        )
        
        # Seed config_sistema
        CONFIG_SEED = [
            ('empresa_nombre','Mi Empresa S.A.C.'),
            ('empresa_ruc','20000000000'),
            ('empresa_direccion','Lima, Perú'),
            ('empresa_moneda','S/'),
            ('tasa_ir','29.5'),
        ]
        
        cursor.executemany(
            "INSERT OR IGNORE INTO config_sistema (clave, valor) VALUES (?,?)",
            CONFIG_SEED
        )
        
        conn.commit()
