PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;

CREATE TABLE IF NOT EXISTS plan_contable (
  codigo TEXT PRIMARY KEY,
  descripcion TEXT NOT NULL,
  tipo_cuenta TEXT NOT NULL CHECK (tipo_cuenta IN ('ACTIVO', 'PASIVO', 'PATRIMONIO', 'INGRESO', 'GASTO')),
  naturaleza TEXT NOT NULL CHECK (naturaleza IN ('DEBE', 'HABER')),
  nivel INTEGER NOT NULL DEFAULT 1,
  cuenta_padre TEXT REFERENCES plan_contable(codigo),
  activo INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS diccionario_sinonimos (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  palabra_usuario TEXT NOT NULL,
  concepto_estandar TEXT NOT NULL,
  idioma TEXT NOT NULL DEFAULT 'es',
  activo INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS matriz_comportamiento (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  concepto_estandar TEXT NOT NULL,
  cuenta_debe TEXT REFERENCES plan_contable(codigo),
  cuenta_haber TEXT REFERENCES plan_contable(codigo),
  descripcion_plantilla TEXT,
  prioridad INTEGER NOT NULL DEFAULT 5,
  activo INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS registro_recepcion (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  enunciado_raw TEXT NOT NULL,
  enunciado_norm TEXT,
  tipo TEXT NOT NULL CHECK (tipo IN ('texto', 'audio', 'imagen')),
  archivo_url TEXT,
  estado_proceso TEXT NOT NULL DEFAULT 'pendiente' CHECK (estado_proceso IN ('pendiente', 'procesado', 'error')),
  error_msg TEXT,
  usuario_id INTEGER DEFAULT 1,
  ip_origen TEXT,
  fecha TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS libro_diario (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  fecha DATE NOT NULL DEFAULT (date('now')),
  cuenta_debe TEXT NOT NULL REFERENCES plan_contable(codigo),
  cuenta_haber TEXT NOT NULL REFERENCES plan_contable(codigo),
  monto REAL NOT NULL CHECK (monto > 0),
  descripcion TEXT NOT NULL,
  concepto_std TEXT,
  moneda TEXT NOT NULL DEFAULT 'PEN',
  tipo_cambio REAL NOT NULL DEFAULT 1.0,
  monto_base REAL,
  id_recepcion INTEGER REFERENCES registro_recepcion(id),
  eliminado INTEGER NOT NULL DEFAULT 0,
  fecha_eliminado TIMESTAMP,
  motivo_eliminado TEXT,
  creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  modificado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS kpi_config (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  nombre TEXT NOT NULL UNIQUE,
  formula_sql TEXT NOT NULL,
  descripcion TEXT,
  icono TEXT,
  unidad TEXT NOT NULL DEFAULT 'S/',
  activo INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS cursor_sesiones (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  usuario_id INTEGER NOT NULL DEFAULT 1,
  elemento TEXT NOT NULL,
  visto_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS config_sistema (
  clave TEXT PRIMARY KEY,
  valor TEXT NOT NULL,
  descripcion TEXT
);

INSERT OR IGNORE INTO plan_contable (codigo, descripcion, tipo_cuenta, naturaleza, nivel) VALUES
('10', 'EFECTIVO', 'ACTIVO', 'DEBE', 1),
('12', 'BANCOS', 'ACTIVO', 'DEBE', 1),
('20', 'CUENTAS POR COBRAR', 'ACTIVO', 'DEBE', 1),
('33', 'INVENTARIO', 'ACTIVO', 'DEBE', 1),
('36', 'ACTIVOS FIJOS', 'ACTIVO', 'DEBE', 1),
('40', 'VENTAS', 'INGRESO', 'HABER', 1),
('42', 'OTROS INGRESOS', 'INGRESO', 'HABER', 1),
('50', 'GASTOS ADMINISTRATIVOS', 'GASTO', 'DEBE', 1),
('60', 'GASTOS DE VENTA', 'GASTO', 'DEBE', 1),
('70', 'GASTOS FINANCIEROS', 'GASTO', 'DEBE', 1),
('80', 'CUENTAS POR PAGAR', 'PASIVO', 'HABER', 1),
('90', 'PATRIMONIO', 'PATRIMONIO', 'HABER', 1);

INSERT OR IGNORE INTO diccionario_sinonimos (palabra_usuario, concepto_estandar) VALUES
('cash', 'EFECTIVO'),
('yape', 'EFECTIVO'),
('efectivo', 'EFECTIVO'),
('plin', 'EFECTIVO'),
('banco', 'BANCOS'),
('transferencia', 'BANCOS'),
('deposito', 'BANCOS'),
('venta', 'VENTA'),
('cobro', 'COBRO'),
('compra', 'COMPRA'),
('gasto', 'GASTO'),
('pago', 'PAGO'),
('factura', 'VENTA'),
('boleta', 'VENTA'),
('alquiler', 'ALQUILER'),
('sueldo', 'PLANILLA');

INSERT OR IGNORE INTO matriz_comportamiento (concepto_estandar, cuenta_debe, cuenta_haber, descripcion_plantilla, prioridad) VALUES
('VENTA', '20', '40', 'Venta de {detalle} por S/ {monto}', 9),
('COBRO', '10', '20', 'Cobro de cliente por S/ {monto}', 9),
('COMPRA', '33', '80', 'Compra de {detalle} por S/ {monto}', 9),
('PAGO', '80', '10', 'Pago a proveedor por S/ {monto}', 8),
('GASTO', '50', '10', 'Gasto: {detalle} por S/ {monto}', 7),
('ALQUILER', '50', '10', 'Pago alquiler S/ {monto}', 9),
('PLANILLA', '60', '10', 'Pago planilla S/ {monto}', 9),
('BANCOS', '12', '10', 'Deposito bancario S/ {monto}', 6);

INSERT OR IGNORE INTO kpi_config (nombre, formula_sql, descripcion, icono, unidad) VALUES
('Utilidad Neta', 'SELECT ROUND((SELECT COALESCE(SUM(CASE WHEN tipo_cuenta = ''INGRESO'' THEN saldo ELSE 0 END),0) FROM v_libro_mayor)-(SELECT COALESCE(SUM(CASE WHEN tipo_cuenta = ''GASTO'' THEN saldo ELSE 0 END),0) FROM v_libro_mayor),2)', 'Ganancia real despues de restar los gastos', '💰', 'S/'),
('Margen de Ganancia', 'SELECT ROUND((((SELECT COALESCE(SUM(CASE WHEN tipo_cuenta = ''INGRESO'' THEN saldo ELSE 0 END),0) FROM v_libro_mayor)-(SELECT COALESCE(SUM(CASE WHEN tipo_cuenta = ''GASTO'' THEN saldo ELSE 0 END),0) FROM v_libro_mayor))*100.0)/NULLIF((SELECT COALESCE(SUM(CASE WHEN tipo_cuenta = ''INGRESO'' THEN saldo ELSE 0 END),0) FROM v_libro_mayor),0),2)', 'Porcentaje de ganancia sobre ingresos', '📈', '%'),
('Total Ingresos', 'SELECT ROUND(COALESCE(SUM(saldo),0),2) FROM v_libro_mayor WHERE tipo_cuenta = ''INGRESO''', 'Suma de ingresos', '⬆️', 'S/'),
('Total Gastos', 'SELECT ROUND(COALESCE(SUM(saldo),0),2) FROM v_libro_mayor WHERE tipo_cuenta = ''GASTO''', 'Suma de gastos', '⬇️', 'S/'),
('Efectivo Disponible', 'SELECT ROUND(COALESCE(SUM(saldo),0),2) FROM v_libro_mayor WHERE codigo = ''10''', 'Saldo de caja', '💵', 'S/'),
('Cuentas por Cobrar', 'SELECT ROUND(COALESCE(SUM(saldo),0),2) FROM v_libro_mayor WHERE codigo = ''20''', 'Saldo por cobrar', '📒', 'S/');

INSERT OR IGNORE INTO config_sistema (clave, valor, descripcion) VALUES
('empresa_nombre', 'Contable AI', 'Nombre de la empresa'),
('moneda', 'PEN', 'Moneda base'),
('ollama_url', 'http://localhost:11434', 'URL de Ollama'),
('ollama_model', 'llama3.2', 'Modelo por defecto'),
('cursor_activo', '1', 'Tutorial activo'),
('voz_activa', '1', 'Narracion activa'),
('primer_uso', '1', 'Indicador de primera ejecucion');

CREATE VIEW IF NOT EXISTS v_diario_activo AS
SELECT * FROM libro_diario WHERE eliminado = 0;

CREATE VIEW IF NOT EXISTS v_libro_mayor AS
SELECT
  pc.codigo,
  pc.descripcion,
  pc.tipo_cuenta,
  pc.naturaleza,
  COALESCE(SUM(CASE WHEN ld.cuenta_debe = pc.codigo THEN ld.monto ELSE 0 END), 0) AS total_debe,
  COALESCE(SUM(CASE WHEN ld.cuenta_haber = pc.codigo THEN ld.monto ELSE 0 END), 0) AS total_haber,
  CASE pc.naturaleza
    WHEN 'DEBE' THEN
      COALESCE(SUM(CASE WHEN ld.cuenta_debe = pc.codigo THEN ld.monto ELSE 0 END), 0) -
      COALESCE(SUM(CASE WHEN ld.cuenta_haber = pc.codigo THEN ld.monto ELSE 0 END), 0)
    WHEN 'HABER' THEN
      COALESCE(SUM(CASE WHEN ld.cuenta_haber = pc.codigo THEN ld.monto ELSE 0 END), 0) -
      COALESCE(SUM(CASE WHEN ld.cuenta_debe = pc.codigo THEN ld.monto ELSE 0 END), 0)
  END AS saldo
FROM plan_contable pc
LEFT JOIN libro_diario ld ON (ld.cuenta_debe = pc.codigo OR ld.cuenta_haber = pc.codigo) AND ld.eliminado = 0
GROUP BY pc.codigo;

CREATE VIEW IF NOT EXISTS v_balance_general AS
SELECT tipo_cuenta, SUM(saldo) AS total
FROM v_libro_mayor
GROUP BY tipo_cuenta;

CREATE VIEW IF NOT EXISTS v_estado_resultados AS
SELECT 'INGRESOS' AS categoria, COALESCE(SUM(saldo), 0) AS total
FROM v_libro_mayor
WHERE tipo_cuenta = 'INGRESO'
UNION ALL
SELECT 'GASTOS' AS categoria, COALESCE(SUM(saldo), 0) AS total
FROM v_libro_mayor
WHERE tipo_cuenta = 'GASTO'
UNION ALL
SELECT 'UTILIDAD NETA' AS categoria,
       (SELECT COALESCE(SUM(saldo), 0) FROM v_libro_mayor WHERE tipo_cuenta = 'INGRESO') -
       (SELECT COALESCE(SUM(saldo), 0) FROM v_libro_mayor WHERE tipo_cuenta = 'GASTO') AS total;
