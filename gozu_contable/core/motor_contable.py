from core.db import DB

class MotorContable:
    def validar_partida_doble(self, lineas):
        total_debe = sum(float(l.get('debe', 0)) for l in lineas)
        total_haber = sum(float(l.get('haber', 0)) for l in lineas)
        diferencia = abs(round(total_debe - total_haber, 2))
        return diferencia == 0, diferencia
    
    def registrar_asiento(self, fecha, descripcion, lineas):
        cuadra, dif = self.validar_partida_doble(lineas)
        if not cuadra:
            raise ValueError(f"Partida doble descuadrada. Diferencia: S/ {dif:.2f}")
        
        fila = DB.fetchone("SELECT MAX(numero_asiento) as max_num FROM libro_diario")
        siguiente = (fila['max_num'] or 0) + 1
        
        operaciones = []
        for linea in lineas:
            operaciones.append((
                """INSERT INTO libro_diario
                   (numero_asiento, fecha, cuenta_codigo, descripcion, debe, haber)
                   VALUES (?,?,?,?,?,?)""",
                (siguiente, fecha, linea['cuenta_codigo'],
                 linea.get('descripcion', descripcion),
                 linea.get('debe', 0), linea.get('haber', 0))
            ))
        DB.transaction(operaciones)
        return siguiente
    
    def eliminar_asiento(self, numero_asiento, motivo):
        if not motivo or len(motivo) < 5:
            raise ValueError("El motivo es obligatorio (mínimo 5 caracteres)")
        DB.execute("""
            UPDATE libro_diario
            SET eliminado=1,
                fecha_eliminado=datetime('now','localtime'),
                motivo_eliminado=?
            WHERE numero_asiento=?
        """, (motivo, numero_asiento))
    
    def editar_asiento(self, numero_asiento, fecha, descripcion, lineas):
        cuadra, dif = self.validar_partida_doble(lineas)
        if not cuadra:
            raise ValueError(f"Partida doble descuadrada. Diferencia: S/ {dif:.2f}")
        DB.execute("DELETE FROM libro_diario WHERE numero_asiento=?", (numero_asiento,))
        operaciones = []
        for linea in lineas:
            operaciones.append((
                """INSERT INTO libro_diario
                   (numero_asiento, fecha, cuenta_codigo, descripcion, debe, haber)
                   VALUES (?,?,?,?,?,?)""",
                (numero_asiento, fecha, linea['cuenta_codigo'],
                 linea.get('descripcion', descripcion),
                 linea.get('debe', 0), linea.get('haber', 0))
            ))
        DB.transaction(operaciones)
    
    def obtener_mayor(self, codigo, fecha_desde, fecha_hasta):
        filas = DB.fetchall("""
            SELECT ld.fecha, ld.numero_asiento, ld.descripcion, ld.debe, ld.haber
            FROM libro_diario ld
            WHERE ld.cuenta_codigo=?
              AND ld.eliminado=0
              AND ld.fecha BETWEEN ? AND ?
            ORDER BY ld.fecha, ld.id
        """, (codigo, fecha_desde, fecha_hasta))
        
        saldo_acumulado = 0.0
        resultado = []
        for fila in filas:
            saldo_acumulado += fila['debe'] - fila['haber']
            resultado.append({**dict(fila), "saldo_acumulado": saldo_acumulado})
        return resultado
    
    def calcular_balance_general(self):
        filas = DB.fetchall("""
            SELECT p.tipo_cuenta, p.codigo, p.descripcion,
                   SUM(ld.debe) as total_debe, SUM(ld.haber) as total_haber,
                   SUM(ld.debe)-SUM(ld.haber) as saldo
            FROM libro_diario ld
            JOIN plan_contable p ON p.codigo = ld.cuenta_codigo
            WHERE ld.eliminado=0
            GROUP BY p.codigo
        """)
        
        grupos = {
            'activo_corriente': [],
            'activo_no_corriente': [],
            'pasivo_corriente': [],
            'pasivo_no_corriente': [],
            'patrimonio': []
        }
        for fila in filas:
            tipo = fila['tipo_cuenta']
            if tipo in grupos:
                grupos[tipo].append(dict(fila))
        
        total_activo = sum(f['saldo'] for f in grupos['activo_corriente'] + grupos['activo_no_corriente'])
        total_pasivo = sum(abs(f['saldo']) for f in grupos['pasivo_corriente'] + grupos['pasivo_no_corriente'])
        total_patrimonio = sum(abs(f['saldo']) for f in grupos['patrimonio'])
        
        return {
            "grupos": grupos,
            "total_activo": total_activo,
            "total_pasivo": total_pasivo,
            "total_patrimonio": total_patrimonio,
            "cuadra": abs(total_activo - (total_pasivo + total_patrimonio)) < 0.01
        }
    
    def calcular_estado_resultados(self):
        filas = DB.fetchall("""
            SELECT p.tipo_cuenta, p.codigo, p.descripcion,
                   SUM(ld.haber)-SUM(ld.debe) as saldo
            FROM libro_diario ld
            JOIN plan_contable p ON p.codigo = ld.cuenta_codigo
            WHERE ld.eliminado=0
            GROUP BY p.codigo, p.tipo_cuenta, p.descripcion
        """)
        
        ventas = []
        costos_venta = []
        gastos_operativos = []
        otros_gastos = []
        otros_ingresos = []
        
        for f in filas:
            codigo_str = str(f['codigo'])
            if codigo_str.startswith('70'):
                ventas.append(f)
            elif codigo_str.startswith('69'):
                costos_venta.append(f)
            elif codigo_str[:2] in ('62', '63', '64', '65', '68'):
                gastos_operativos.append(f)
            elif codigo_str[:2] in ('66', '67', '97'):
                otros_gastos.append(f)
            elif codigo_str[:2] in ('73', '75', '76', '77'):
                otros_ingresos.append(f)
                
        total_ventas = sum(f['saldo'] for f in ventas)
        total_costos_venta = sum(abs(f['saldo']) for f in costos_venta)
        
        utilidad_bruta = total_ventas - total_costos_venta
        
        total_gastos_op = sum(abs(f['saldo']) for f in gastos_operativos)
        
        utilidad_operativa = utilidad_bruta - total_gastos_op
        
        total_otros_gastos = sum(abs(f['saldo']) for f in otros_gastos)
        total_otros_ingresos = sum(f['saldo'] for f in otros_ingresos)
        
        utilidad_antes_impuestos = utilidad_operativa - total_otros_gastos + total_otros_ingresos
        
        try:
            tasa_ir = float(DB.fetchone("SELECT valor FROM config_sistema WHERE clave='tasa_ir'")['valor']) / 100
        except:
            tasa_ir = 0.295
            
        impuesto_renta = max(0, utilidad_antes_impuestos * tasa_ir) if utilidad_antes_impuestos > 0 else 0
        utilidad_neta = utilidad_antes_impuestos - impuesto_renta

        return {
            "ventas": ventas, "total_ventas": total_ventas,
            "costos_venta": costos_venta, "total_costos_venta": total_costos_venta,
            "utilidad_bruta": utilidad_bruta,
            "gastos_operativos": gastos_operativos, "total_gastos_op": total_gastos_op,
            "utilidad_operativa": utilidad_operativa,
            "otros_gastos": otros_gastos, "total_otros_gastos": total_otros_gastos,
            "otros_ingresos": otros_ingresos, "total_otros_ingresos": total_otros_ingresos,
            "utilidad_antes_impuestos": utilidad_antes_impuestos,
            "impuesto_renta": impuesto_renta,
            "tasa_ir": tasa_ir * 100,
            "utilidad_neta": utilidad_neta
        }
