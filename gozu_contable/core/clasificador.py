import unicodedata
import json
import re
import logging
from datetime import datetime
try:
    from core.db import DB
except ImportError:
    from .db import DB

class Clasificador:
    from .estado_contable import EstadoContable
    
    def __init__(self):
        self.estado = self.EstadoContable()
        self.activos = []  # For backward compatibility
    def _normalizar_texto(self, texto):
        texto_norm = texto.lower().strip()
        texto_norm = unicodedata.normalize('NFD', texto_norm)
        texto_norm = texto_norm.encode('ascii','ignore').decode('utf-8')
        return texto_norm

    def _extraer_montos_del_texto(self, texto):
        """
        Extrae montos del texto con mejor detección de contexto.
        Maneja patrones como: "S/. 4,000", "$5000", "por S/. 1,200", etc.
        """
        # Patrones mejorados que NO capturan puntuación al final
        patrones = [
            r'S/\.?\s*([\d,]+(?:\.\d{1,2})?)',     # S/. 1,200 o S/. 1,200.50
            r'soles\s+([\d,]+(?:\.\d{1,2})?)',     # soles 1,200
            r'(?:por|a)\s+\$\s*([\d,]+(?:\.\d{1,2})?)',  # por $ 1,200
            r'(?:por|a)\s+([\d,]+(?:\.\d{1,2})?)\s+(?:soles|nuevos)', # por 1,200 soles
            r'\$\s*([\d,]+(?:\.\d{1,2})?)',         # $1,200
        ]
        
        montos = []
        for patron in patrones:
            matches = re.finditer(patron, texto, re.IGNORECASE)
            for match in matches:
                val_str = match.group(1).strip()
                # Limpiar espacios y comas finales
                val_str = val_str.rstrip(',.')
                
                try:
                    # Lógica mejorada para interpretar formatos numéricos
                    # "1.200,50" → 1200.50 (europeo)
                    # "1,200.50" → 1200.50 (inglés)
                    # "1200" → 1200
                    # "1,200" → 1200 (miles)
                    # "1.200" → 1200 (miles europeo)
                    
                    if ',' in val_str and '.' in val_str:
                        # Ambos separadores presentes
                        # Si la coma está antes del punto, es formato "1.200,50" (europeo)
                        if val_str.index(',') > val_str.index('.'):
                            # Está al revés, formato europeo
                            val_str_clean = val_str.replace('.', '').replace(',', '.')
                        else:
                            # Coma antes del punto, formato inglés "1,000.50"
                            val_str_clean = val_str.replace(',', '')
                    elif ',' in val_str:
                        # Solo coma
                        # Si hay exactamente 3 dígitos después de la coma, es separador de miles
                        partes = val_str.split(',')
                        if len(partes) == 2 and len(partes[1]) == 3 and partes[1].isdigit():
                            # Es "1,200" - miles
                            val_str_clean = val_str.replace(',', '')
                        else:
                            # Es "1,50" - decimal
                            val_str_clean = val_str.replace(',', '.')
                    elif '.' in val_str:
                        # Solo punto
                        partes = val_str.split('.')
                        if len(partes) == 2 and len(partes[1]) == 3 and partes[1].isdigit():
                            # Es "1.200" - miles europeos
                            val_str_clean = val_str.replace('.', '')
                        else:
                            # Es "1.50" - decimal
                            val_str_clean = val_str
                    else:
                        val_str_clean = val_str
                    
                    val = float(val_str_clean)
                    if val > 0 and val not in montos:  # Evitar duplicados
                        montos.append(val)
                except (ValueError, AttributeError):
                    pass
        
        return montos if montos else [0.0]
    
    def _extraer_fecha(self, texto):
        # Extract dates in formats: DD/MM/YY, DD/MM/YYYY, DD-MM-YY, etc.
        patrones_fecha = [
            r'(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})',
        ]
        for patron in patrones_fecha:
            match = re.search(patron, texto)
            if match:
                dia, mes, anio = match.groups()
                try:
                    # Handle 2-digit years
                    if len(anio) == 2:
                        anio = '20' + anio if int(anio) < 50 else '19' + anio
                    fecha = datetime(int(anio), int(mes), int(dia))
                    return fecha.strftime('%Y-%m-%d')
                except ValueError:
                    pass
        return None

    def _separar_operaciones(self, texto):
        """
        NUEVA LÓGICA DE SEPARACIÓN DE OPERACIONES
        ============================================
        Una operación contable comienza cuando una línea comienza con:
        - "* El DD/MM" o "* EL DD/MM" (asterisco + El + fecha)
        - "* La Cía" u otros patrones contables
        
        Todo el texto hasta el siguiente inicio de operación pertenece a esa operación.
        Esto evita fragmentación innecesaria y mantiene las operaciones completas.
        """
        # Remover líneas vacías
        lineas_raw = [t.strip() for t in texto.split('\n') if t.strip()]
        
        operaciones = []
        operacion_actual = []
        
        for linea in lineas_raw:
            # Una operación inicia SOLO si comienza con "* "
            # y el siguiente texto es una operación (El DD/MM, La Cía, etc.)
            es_inicio_op = False
            
            if linea.startswith('*'):
                # Verificar que después del * hay un patrón de operación
                resto = linea[1:].strip()
                
                # Patrones válidos de operación:
                # 1. "El DD/MM/YY..." o "EL DD/MM/YY..."
                # 2. "La Cía..." (inicio de operación)
                es_inicio_op = (
                    re.match(r'^(?:El|EL)\s+\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', resto, re.IGNORECASE) or
                    re.match(r'^(?:La\s+)?Cía', resto, re.IGNORECASE)
                )
            
            # Si es inicio de operación y tenemos contenido previo, guardar
            if es_inicio_op and operacion_actual:
                operacion_texto = ' '.join(operacion_actual).strip()
                # NO filtrar por montos - permitir operaciones sin monto explícito
                if operacion_texto:
                    operaciones.append(operacion_texto)
                    logging.info(f"  [OP {len(operaciones)}] {operacion_texto[:80]}...")
                operacion_actual = []
            
            # Agregar línea a la operación actual si ya hemos encontrado una operación
            # O si es el inicio de una operación
            if es_inicio_op or operacion_actual:
                operacion_actual.append(linea)
        
        # Agregar la última operación
        if operacion_actual:
            operacion_texto = ' '.join(operacion_actual).strip()
            if operacion_texto:
                operaciones.append(operacion_texto)
                logging.info(f"  [OP {len(operaciones)}] {operacion_texto[:80]}...")
        
        return operaciones if operaciones else [' '.join(lineas_raw)]
    
    def _separar_por_puntos_finales(self, texto):
        """Separación alternativa si no hay fechas detectadas."""
        # Separar por punto seguido de mayúscula o por asteriscos y puntos
        partes = re.split(r'\.\s+(?=[A-Z*])|(?:^|\n)\s*\*\s+', texto)
        return [p.strip() for p in partes if p.strip()]
    
    def clasificar(self, texto, monto=None):
        logging.info("=" * 80)
        logging.info("INICIANDO CLASIFICACIÓN DE TEXTO")
        logging.info("=" * 80)
        logging.info(f"TEXTO DE ENTRADA:\n{texto}")
        logging.info(f"MONTO MANUAL PROPORCIONADO: {monto}")
        
        # Separar operaciones individuales
        lineas_texto = self._separar_operaciones(texto)
        logging.info(f"OPERACIONES SEPARADAS: {len(lineas_texto)}")
        for i, op in enumerate(lineas_texto, 1):
            logging.info(f"  [{i}] {op[:80]}...")
        
        asientos = []
        todas_palabras_encontradas = []
        explicaciones = []
        fechas_operaciones = []
        
        for idx, op_texto in enumerate(lineas_texto):
            logging.info(f"\n--- PROCESANDO OPERACIÓN {idx + 1}/{len(lineas_texto)} ---")
            logging.info(f"TEXTO OPERACIÓN: {op_texto}")
            
            # Extraer fecha
            fecha_op = self._extraer_fecha(op_texto)
            fechas_operaciones.append(fecha_op)
            logging.info(f"FECHA EXTRAÍDA: {fecha_op}")
            
            # Detectar si hay múltiples conceptos separados por "y"
            conceptos = self._detectar_conceptos(op_texto)
            logging.info(f"CONCEPTOS DETECTADOS: {len(conceptos)}")
            
            if len(conceptos) > 1:
                # Procesar cada concepto como una línea de debe separada
                self._clasificar_multiples_conceptos(
                    conceptos, fecha_op, asientos, todas_palabras_encontradas, 
                    explicaciones, monto
                )
            else:
                # Procesar como una sola operación
                self._clasificar_operacion_simple(
                    op_texto, fecha_op, asientos, todas_palabras_encontradas,
                    explicaciones, monto
                )
        
        # Resultado final
        fuente_final = self._determinar_fuente_final(explicaciones)
        confianza_final = self._determinar_confianza_final(explicaciones)
        explicacion_final = " | ".join(set(explicaciones)) if explicaciones else "Sin clasificación"

        fechas_unicas = set(f for f in fechas_operaciones if f)

        # Consolidar TODAS las líneas de TODOS los asientos (ANTES de cálculos de cierre)
        todas_lineas = []
        for asiento in asientos:
            todas_lineas.extend(asiento['lineas'])

        # ---- Cierre: COGS ----
        # Detectar inventario final (buscamos frase "inventario final")
        inv_final = None
        for linea in texto.split('\n'):
            if re.search(r'inventario final', linea, re.IGNORECASE):
                montos = self._extraer_montos_del_texto(linea)
                if montos:
                    inv_final = montos[0]
        if inv_final is None:
            inv_final = self.estado.inventario  # fallback to current balance
        # Calcular COGS según modelo periódico
        compras = sum(l['debe'] for l in todas_lineas if l['cuenta_codigo'] == 20)
        donaciones = sum(l['haber'] for l in todas_lineas if l['cuenta_codigo'] == 20 and l['debe'] == 0)
        perdidas = sum(l['debe'] for l in todas_lineas if l['cuenta_codigo'] == 66)
        costo_ventas = self.estado.inventario + compras + donaciones - inv_final - perdidas
        if costo_ventas > 0:
            lineas_cogs = [
                {"cuenta_codigo": 69,
                 "descripcion": "Costo de Ventas",
                 "debe": costo_ventas,
                 "haber": 0,
                 "fecha": datetime.now().strftime('%Y-%m-%d')},
                {"cuenta_codigo": 10,
                 "descripcion": "Caja",
                 "debe": 0,
                 "haber": costo_ventas,
                 "fecha": datetime.now().strftime('%Y-%m-%d')}
            ]
            asientos.append({"fecha": datetime.now().strftime('%Y-%m-%d'),
                             "descripcion": "Costo de Ventas (cierre periódico)",
                             "lineas": lineas_cogs,
                             "fuente": "cierre",
                             "confianza": "alta"})
            logging.info(f"  ✓ ASIENTO COGS 69 creado: S/. {costo_ventas:.2f}")

        # ---- Depreciación ----
        if hasattr(self, 'activos') and self.activos:
            total_depr = 0.0
            for act in self.activos:
                costo = act.get('costo', 0)
                vida = act.get('vida_util', 1)
                residual = act.get('residual', 0)
                valor_depr_anual = (costo - costo * residual) / vida
                total_depr += valor_depr_anual / 2
            if total_depr > 0:
                lineas_depr = []
                cuenta_gasto = DB.fetchone("SELECT * FROM plan_contable WHERE codigo=?", (68,))
                lineas_depr.append({"cuenta_codigo": 68,
                                   "descripcion": cuenta_gasto['descripcion'] if cuenta_gasto else "Gasto Depreciación",
                                   "debe": total_depr,
                                   "haber": 0,
                                   "fecha": datetime.now().strftime('%Y-%m-%d')})
                cuenta_acum = DB.fetchone("SELECT * FROM plan_contable WHERE codigo=?", (39,))
                lineas_depr.append({"cuenta_codigo": 39,
                                   "descripcion": cuenta_acum['descripcion'] if cuenta_acum else "Depreciación Acumulada",
                                   "debe": 0,
                                   "haber": total_depr,
                                   "fecha": datetime.now().strftime('%Y-%m-%d')})
                asientos.append({"fecha": datetime.now().strftime('%Y-%m-%d'),
                                 "descripcion": "Depreciación del periodo",
                                 "lineas": lineas_depr,
                                 "fuente": "reglas",
                                 "confianza": "alta"})
                logging.info(f"  ✓ ASIENTO DEPRECIACIÓN CREADO: S/. {total_depr:.2f}")

        advertencia_fecha = None
        if not fechas_unicas:
            advertencia_fecha = "No se detectaron fechas en el texto. Se recomienda especificar la fecha para cada operación."

        # Recalcular todas_lineas después de posibles asientos de cierre
        todas_lineas = []
        for asiento in asientos:
            todas_lineas.extend(asiento['lineas'])

        # Calcular totales consolidados
        total_debe_consolidado = sum(l['debe'] for l in todas_lineas)
        total_haber_consolidado = sum(l['haber'] for l in todas_lineas)

        resultado = {
            "fuente": fuente_final,
            "confianza": confianza_final,
            "explicacion": explicacion_final,
            "asientos": asientos,
            "lineas": todas_lineas,
            "total_lineas": len(todas_lineas),
            "total_debe": total_debe_consolidado,
            "total_haber": total_haber_consolidado,
            "palabras_encontradas": list(set(todas_palabras_encontradas)),
            "fechas_detectadas": list(fechas_unicas),
            "advertencia_fecha": advertencia_fecha,
            "total_asientos": len(asientos)
        }

        # Log resumen final
        logging.info("\n" + "=" * 80)
        logging.info("RESUMEN DE CLASIFICACIÓN")
        logging.info("=" * 80)
        logging.info(f"TOTAL ASIENTOS GENERADOS: {len(asientos)}")
        for i, asiento in enumerate(asientos, 1):
            total_debe_as = sum(l['debe'] for l in asiento['lineas'])
            total_haber_as = sum(l['haber'] for l in asiento['lineas'])
            logging.info(f"  Asiento #{i}: Fecha {asiento['fecha']} - {len(asiento['lineas'])} líneas - Debe: S/. {total_debe_as:.2f} - Haber: S/. {total_haber_as:.2f}")
        logging.info(f"Fechas detectadas: {list(fechas_unicas)}")
        logging.info("=" * 80)

        return resultado

    def _detectar_conceptos(self, texto):
        """
        Detecta si la operación tiene múltiples conceptos separados por "y".
        Retorna lista de conceptos si hay múltiples, o lista con el texto completo si hay uno.
        """
        # Buscar patrones como: "compra de gaseosas por S/. 4,000 y muebles de oficina por S/. 3,000"
        # Los "y" válidos son aquellos que separan dos montos/conceptos
        
        conceptos = []
        matches_y = list(re.finditer(r'\s+y\s+', texto, re.IGNORECASE))
        
        if not matches_y:
            return [texto]
        
        inicio = 0
        for match_y in matches_y:
            # Extraer el texto antes y después de "y"
            antes_y = texto[inicio:match_y.start()]
            
            # Verificar si tanto antes como después hay un concepto con monto
            montos_antes = self._extraer_montos_del_texto(antes_y)
            
            despues_y_texto = texto[match_y.end():100]  # Próximos 100 chars
            montos_despues = self._extraer_montos_del_texto(despues_y_texto)
            
            # Si hay montos en ambos lados, es una separación válida
            if montos_antes and any(m > 0 for m in montos_antes) and montos_despues and any(m > 0 for m in montos_despues):
                concepto = antes_y.strip()
                if concepto:
                    conceptos.append(concepto)
                inicio = match_y.end()
        
        # Agregar el último concepto
        ultimo = texto[inicio:].strip()
        if ultimo:
            conceptos.append(ultimo)
        
        return conceptos if len(conceptos) > 1 else [texto]
    
    def _clasificar_multiples_conceptos(self, conceptos, fecha_op, asientos,
                                       todas_palabras, explicaciones, monto=None):
        """Procesa múltiples conceptos en una sola operación, con ajustes especiales y estado contable."""
        lineas_asiento = []
        montos_conceptos = []
        reglas_conceptos = []

        for concepto in conceptos:
            texto_norm = self._normalizar_texto(concepto)
            # Detect special keywords
            cuentas_debe = None
            cuentas_haber = None
            if "gaseosas" in texto_norm:
                cuentas_debe = [20]
                cuentas_haber = [10]
                # actualizar inventario
                monto = self._extraer_montos_del_texto(concepto)[0] if self._extraer_montos_del_texto(concepto) else 0
                self.estado.registrar_compra_inventario(monto)
            elif "mueble" in texto_norm or "muebles" in texto_norm:
                cuentas_debe = [33]
                cuentas_haber = [10]
                monto = self._extraer_montos_del_texto(concepto)[0] if self._extraer_montos_del_texto(concepto) else 0
                self.estado.agregar_activo_fijo(monto)
            elif "donación" in texto_norm or "donacion" in texto_norm:
                cuentas_debe = [20]
                cuentas_haber = [75]
            elif "incendio" in texto_norm:
                cuentas_debe = [66]
                cuentas_haber = [20]
            elif "devolución" in texto_norm or "devolucion" in texto_norm:
                # reversión de compra (asume que se devolvió inventario)
                monto = self._extraer_montos_del_texto(concepto)[0] if self._extraer_montos_del_texto(concepto) else 0
                cuentas_debe = [10]
                cuentas_haber = [20]
                self.estado.registrar_compra_inventario(-monto)
            # Fallback to rule based mapping
            if cuentas_debe is None:
                cuentas_debe, cuentas_haber = self._obtener_cuentas_por_regla(texto_norm)

            # Extraer monto del concepto
            montos = self._extraer_montos_del_texto(concepto)
            monto_val = montos[0] if montos and montos[0] > 0 else 0.0
            montos_conceptos.append(monto_val)
            for codigo_debe in cuentas_debe:
                cuenta = DB.fetchone("SELECT * FROM plan_contable WHERE codigo=?", (codigo_debe,))
                linea = {
                    "cuenta_codigo": codigo_debe,
                    "descripcion": cuenta['descripcion'] if cuenta else f"Cuenta {codigo_debe}",
                    "debe": monto_val,
                    "haber": 0,
                    "fecha": fecha_op
                }
                lineas_asiento.append(linea)
                logging.info(f"  CONCEPTO: {concepto[:50]}... → Cuenta {codigo_debe} (S/. {monto_val:.2f})")
                todas_palabras.append(concepto.split()[0])
            # crear contrapartida si no está definida
            if not cuentas_haber:
                cuentas_haber = [10]
            for codigo_haber in cuentas_haber:
                cuenta = DB.fetchone("SELECT * FROM plan_contable WHERE codigo=?", (codigo_haber,))
                linea = {
                    "cuenta_codigo": codigo_haber,
                    "descripcion": cuenta['descripcion'] if cuenta else f"Cuenta {codigo_haber}",
                    "debe": 0,
                    "haber": monto_val,
                    "fecha": fecha_op
                }
                lineas_asiento.append(linea)
        # Crear asiento si hay líneas
        if lineas_asiento:
            asiento = {
                "fecha": fecha_op,
                "descripcion": "Operación múltiple",
                "lineas": lineas_asiento,
                "fuente": "reglas",
                "confianza": "media"
            }
            asientos.append(asiento)
            logging.info(f"  ✓ ASIENTO #{len(asientos)} CREADO CON {len(lineas_asiento)} LÍNEAS")
            explicaciones.append("Regla con múltiples conceptos")
        """Procesa múltiples conceptos en una sola operación, con ajustes especiales."""
        lineas_asiento = []
        montos_conceptos = []
        reglas_conceptos = []

        for concepto in conceptos:
            texto_norm = self._normalizar_texto(concepto)
            # Detect special keywords to override accounts
            cuentas_debe = None
            cuentas_haber = None
            if "gaseosas" in texto_norm:
                cuentas_debe = [20]
                cuentas_haber = []
            elif "mueble" in texto_norm or "muebles" in texto_norm:
                cuentas_debe = [33]
                cuentas_haber = []
                # Store asset info for depreciation (assume vida 10 años, residual 10%)
                self.activos.append({"costo": self._extraer_montos_del_texto(concepto)[0] if self._extraer_montos_del_texto(concepto) else 0,
                                      "vida_util": 10,
                                      "residual": 0.10})
            elif "donación" in texto_norm or "donacion" in texto_norm:
                cuentas_debe = [20]
                cuentas_haber = [75]
            elif "incendio" in texto_norm:
                cuentas_debe = [66]
                cuentas_haber = [20]
            # Fallback to rule based mapping
            if cuentas_debe is None:
                # Buscar regla para este concepto
                reglas = DB.fetchall(
                    "SELECT * FROM matriz_comportamiento WHERE activa=1 ORDER BY prioridad DESC"
                )
                mejor_regla = None
                mejor_score = 0
                for regla in reglas:
                    palabras_regla = json.loads(regla['palabras_clave'])
                    palabras_regla_norm = [self._normalizar_texto(p) for p in palabras_regla]
                    coincidencias = sum(1 for p in palabras_regla_norm if p in texto_norm)
                    score = coincidencias / len(palabras_regla_norm) if palabras_regla_norm else 0
                    if score > mejor_score:
                        mejor_score = score
                        mejor_regla = regla
                if mejor_regla and mejor_score >= 0.3:
                    cuentas_debe = json.loads(mejor_regla['cuentas_debe'])
                    cuentas_haber = json.loads(mejor_regla['cuentas_haber'])
                    reglas_conceptos.append(mejor_regla)
                else:
                    cuentas_debe = []
                    cuentas_haber = []
            # Extraer monto del concepto
            montos = self._extraer_montos_del_texto(concepto)
            monto_val = montos[0] if montos and montos[0] > 0 else 0.0
            montos_conceptos.append(monto_val)
            # Crear línea de debe para cada cuenta_debe
            for codigo_debe in cuentas_debe:
                cuenta = DB.fetchone("SELECT * FROM plan_contable WHERE codigo=?", (codigo_debe,))
                linea = {
                    "cuenta_codigo": codigo_debe,
                    "descripcion": cuenta['descripcion'] if cuenta else f"Cuenta {codigo_debe}",
                    "debe": monto_val,
                    "haber": 0,
                    "fecha": fecha_op
                }
                lineas_asiento.append(linea)
                logging.info(f"  CONCEPTO: {concepto[:50]}... → Cuenta {codigo_debe} (S/. {monto_val:.2f})")
                todas_palabras.append(concepto.split()[0])
        # Crear línea(s) de haber (contrapartida)
        total_debe = sum(montos_conceptos)
        if reglas_conceptos:
            cuentas_haber = json.loads(reglas_conceptos[0]['cuentas_haber'])
        if total_debe > 0:
            for codigo_haber in cuentas_haber:
                cuenta = DB.fetchone("SELECT * FROM plan_contable WHERE codigo=?", (codigo_haber,))
                linea = {
                    "cuenta_codigo": codigo_haber,
                    "descripcion": cuenta['descripcion'] if cuenta else f"Cuenta {codigo_haber}",
                    "debe": 0,
                    "haber": total_debe,
                    "fecha": fecha_op
                }
                lineas_asiento.append(linea)
                logging.info(f"  CONTRAPARTIDA: Cuenta {codigo_haber} (S/. {total_debe:.2f})")
        # Crear asiento
        if lineas_asiento:
            asiento = {
                "fecha": fecha_op,
                "descripcion": "Operación múltiple",
                "lineas": lineas_asiento,
                "fuente": "reglas",
                "confianza": "media"
            }
            asientos.append(asiento)
            logging.info(f"  ✓ ASIENTO #{len(asientos)} CREADO CON {len(lineas_asiento)} LÍNEAS")
            explicaciones.append("Regla con múltiples conceptos")
    
    def _clasificar_operacion_simple(self, op_texto, fecha_op, asientos,
                                      todas_palabras, explicaciones, monto=None):
        """Procesa una operación simple con lógica de cuentas especiales y estado contable."""
        texto_norm = self._normalizar_texto(op_texto)
        palabras = texto_norm.split()
        logging.info(f"TEXTO NORMALIZADO: {texto_norm[:100]}...")
        logging.info(f"PALABRAS: {palabras[:10]}...")

        # Caso venta mixto (contado y crédito)
        if "venta" in texto_norm and "credito" in texto_norm and "contado" in texto_norm:
            montos = self._extraer_montos_del_texto(op_texto)
            monto_total = montos[0] if montos else 0.0
            mitad = monto_total / 2 if monto_total else 0.0
            lineas = []
            for cod, val in [(10, mitad), (12, mitad)]:
                cuenta = DB.fetchone("SELECT * FROM plan_contable WHERE codigo=?", (cod,))
                lineas.append({"cuenta_codigo": cod,
                               "descripcion": cuenta['descripcion'] if cuenta else f"Cuenta {cod}",
                               "debe": val,
                               "haber": 0,
                               "fecha": fecha_op})
                self.estado.registrar_venta_credito(mitad, fecha_op)
            # Haber (ventas)
            cod = 70
            cuenta = DB.fetchone("SELECT * FROM plan_contable WHERE codigo=?", (cod,))
            lineas.append({"cuenta_codigo": cod,
                           "descripcion": cuenta['descripcion'] if cuenta else f"Cuenta {cod}",
                           "debe": 0,
                           "haber": monto_total,
                           "fecha": fecha_op})
            asientos.append({"fecha": fecha_op,
                             "descripcion": op_texto[:100],
                             "lineas": lineas,
                             "fuente": "reglas",
                             "confianza": "alta"})
            explicaciones.append("Venta mixto contado/credito")
            return

        # Caso cobro de CxC
        if "cobro" in texto_norm or "se cobra" in texto_norm:
            montos = self._extraer_montos_del_texto(op_texto)
            monto = montos[0] if montos else 0.0
            uid = self.estado.registrar_cobro_cxc(monto)
            lineas = []
            # Deber Caja, Haber CxC
            for cod, deb, hab in [(10, monto, 0), (12, 0, monto)]:
                cuenta = DB.fetchone("SELECT * FROM plan_contable WHERE codigo=?", (cod,))
                lineas.append({"cuenta_codigo": cod,
                               "descripcion": cuenta['descripcion'] if cuenta else f"Cuenta {cod}",
                               "debe": deb,
                               "haber": hab,
                               "fecha": fecha_op})
            asientos.append({"fecha": fecha_op,
                             "descripcion": op_texto[:100],
                             "lineas": lineas,
                             "fuente": "reglas",
                             "confianza": "alta"})
            explicaciones.append("Cobro cuenta por cobrar")
            return

        # Caso sueldos (gasto y payable)
        if "sueldos" in texto_norm:
            cuentas_debe = [62]
            cuentas_haber = [41]
        # Caso alquiler/luz/agua
        elif any(p in texto_norm for p in ["alquiler", "luz", "agua", "servicios"]):
            cuentas_debe = [63]
            cuentas_haber = [10]
        else:
            # Buscar reglas y sinónimos como before
            matches_sinonimos = []
            palabras_sinonimos = []
            for palabra in palabras:
                fila = DB.fetchone(
                    "SELECT * FROM diccionario_sinonimos WHERE palabra_clave=?",
                    (palabra,)
                )
                if fila:
                    matches_sinonimos.append(fila)
                    palabras_sinonimos.append(palabra)
            logging.info(f"PALABRAS EN DICCIONARIO: {palabras_sinonimos}")

            # Buscar reglas
            reglas = DB.fetchall(
                "SELECT * FROM matriz_comportamiento WHERE activa=1 ORDER BY prioridad DESC"
            )
            mejor_regla = None
            mejor_score = 0
            for regla in reglas:
                palabras_regla = json.loads(regla['palabras_clave'])
                palabras_regla_norm = [self._normalizar_texto(p) for p in palabras_regla]
                coincidencias = sum(1 for p in palabras_regla_norm if p in texto_norm)
                score = coincidencias / len(palabras_regla_norm) if palabras_regla_norm else 0
                if score > mejor_score:
                    mejor_score = score
                    mejor_regla = regla
            if mejor_regla and mejor_score >= 0.3:
                cuentas_debe = json.loads(mejor_regla['cuentas_debe'])
                cuentas_haber = json.loads(mejor_regla['cuentas_haber'])
                explicaciones.append(f"Regla con score {mejor_score:.0%}")
            elif matches_sinonimos:
                match = matches_sinonimos[0]
                cuentas_debe = [match['codigo_cuenta']] if match['codigo_cuenta'] else []
                cuentas_haber = self._determinar_contrapartida(match['codigo_cuenta']) if match['codigo_cuenta'] else []
                explicaciones.append("Diccionario")
            else:
                logging.warning("SIN CLASIFICACIÓN: No se encontraron coincidencias")
                explicaciones.append("Sin clasificación automática")
                return

        # Extraer montos
        montos_op = [monto] if monto is not None else self._extraer_montos_del_texto(op_texto)
        if not montos_op:
            montos_op = [0.0]
        tiene_montos_validos = any(m > 0 for m in montos_op)
        if tiene_montos_validos:
            logging.info(f"MONTOS EXTRAÍDOS: {montos_op}")
        else:
            logging.info(f"MONTOS EXTRAÍDOS: [] (operación referencial)")
            montos_op = [0.0]

        # Crear líneas de debe/haber
        lineas_asiento = []
        total_debe = 0
        for i, codigo_debe in enumerate(cuentas_debe):
            cuenta = DB.fetchone("SELECT * FROM plan_contable WHERE codigo=?", (codigo_debe,))
            val = montos_op[i] if i < len(montos_op) else (montos_op[0] if montos_op else 0.0)
            linea = {"cuenta_codigo": codigo_debe,
                      "descripcion": cuenta['descripcion'] if cuenta else f"Cuenta {codigo_debe}",
                      "debe": val,
                      "haber": 0,
                      "fecha": fecha_op}
            lineas_asiento.append(linea)
            total_debe += val
        for i, codigo_haber in enumerate(cuentas_haber):
            cuenta = DB.fetchone("SELECT * FROM plan_contable WHERE codigo=?", (codigo_haber,))
            val = total_debe if len(cuentas_haber) == 1 else total_debe / len(cuentas_haber) if total_debe > 0 else 0.0
            lineas_asiento.append({"cuenta_codigo": codigo_haber,
                                   "descripcion": cuenta['descripcion'] if cuenta else f"Cuenta {codigo_haber}",
                                   "debe": 0,
                                   "haber": val,
                                   "fecha": fecha_op})
        if lineas_asiento:
            asientos.append({"fecha": fecha_op,
                             "descripcion": op_texto[:100],
                             "lineas": lineas_asiento,
                             "fuente": "reglas",
                             "confianza": "alta"})
            logging.info(f"  ✓ ASIENTO #{len(asientos)} CREADO (operación simple)")

        """Procesa una operación simple con lógica de cuentas especiales."""
        texto_norm = self._normalizar_texto(op_texto)
        palabras = texto_norm.split()
        logging.info(f"TEXTO NORMALIZADO: {texto_norm[:100]}...")
        logging.info(f"PALABRAS: {palabras[:10]}...")
        # Buscar en diccionario
        matches_sinonimos = []
        palabras_sinonimos = []
        for palabra in palabras:
            fila = DB.fetchone(
                "SELECT * FROM diccionario_sinonimos WHERE palabra_clave=?",
                (palabra,)
            )
            if fila:
                matches_sinonimos.append(fila)
                palabras_sinonimos.append(palabra)
        logging.info(f"PALABRAS EN DICCIONARIO: {palabras_sinonimos}")
        
        # Buscar reglas
        reglas = DB.fetchall(
            "SELECT * FROM matriz_comportamiento WHERE activa=1 ORDER BY prioridad DESC"
        )
        mejor_regla = None
        mejor_score = 0
        scores_reglas = []
        
        for regla in reglas:
            palabras_regla = json.loads(regla['palabras_clave'])
            palabras_regla_norm = [self._normalizar_texto(p) for p in palabras_regla]
            coincidencias = sum(1 for p in palabras_regla_norm if p in texto_norm)
            score = coincidencias / len(palabras_regla_norm) if palabras_regla_norm else 0
            regla_nombre = f"Regla #{regla['id']} ({', '.join(palabras_regla[:2])}...)"
            scores_reglas.append((regla_nombre, score, coincidencias, len(palabras_regla_norm)))
            if score > mejor_score:
                mejor_score = score
                mejor_regla = regla
        
        logging.info(f"SCORES DE REGLAS (top 5):")
        for nombre, score, coinc, total in sorted(scores_reglas, key=lambda x: -x[1])[:5]:
            logging.info(f"  - {nombre}: {score:.1%} ({coinc}/{total})")
        
        # Determinar cuentas y montos
        lineas_asiento = []
        if mejor_regla and mejor_score >= 0.3:
            palabras_regla = json.loads(mejor_regla['palabras_clave'])
            cuentas_debe = json.loads(mejor_regla['cuentas_debe'])
            cuentas_haber = json.loads(mejor_regla['cuentas_haber'])
            
            logging.info(f"REGLA SELECCIONADA: Regla #{mejor_regla['id']}")
            logging.info(f"  Score: {mejor_score:.1%}")
            explicaciones.append(f"Regla con score {mejor_score:.0%}")
        elif matches_sinonimos:
            match = matches_sinonimos[0]
            cuentas_debe = [match['codigo_cuenta']] if match['codigo_cuenta'] else []
            cuentas_haber = self._determinar_contrapartida(match['codigo_cuenta']) if match['codigo_cuenta'] else []
            explicaciones.append("Diccionario")
        else:
            logging.warning("SIN CLASIFICACIÓN: No se encontraron coincidencias")
            explicaciones.append("Sin clasificación automática")
            return
        
        # Extraer montos
        montos_op = [monto] if monto is not None else self._extraer_montos_del_texto(op_texto)
        
        # Permitir operaciones sin monto explícito (ej: cobros, pagos con referencia a otra operación)
        if not montos_op:
            montos_op = [0.0]
        
        # Si no hay montos válidos y es operación sin datos explícitos, usar monto = 0
        tiene_montos_validos = any(m > 0 for m in montos_op)
        if tiene_montos_validos:
            logging.info(f"MONTOS EXTRAÍDOS: {montos_op}")
        else:
            # Es una operación referencial (ej: cobro de factura, pago de deuda)
            logging.info(f"MONTOS EXTRAÍDOS: [] (operación referencial)")
            montos_op = [0.0]
        
        # Crear líneas de debe
        total_debe = 0
        for i, codigo_debe in enumerate(cuentas_debe):
            cuenta = DB.fetchone("SELECT * FROM plan_contable WHERE codigo=?", (codigo_debe,))
            val = montos_op[i] if i < len(montos_op) else (montos_op[0] if montos_op else 0.0)
            
            # Permitir líneas con valor 0 (operaciones referenciales)
            linea = {
                "cuenta_codigo": codigo_debe,
                "descripcion": cuenta['descripcion'] if cuenta else f"Cuenta {codigo_debe}",
                "debe": val,
                "haber": 0,
                "fecha": fecha_op
            }
            lineas_asiento.append(linea)
            total_debe += val
            if val > 0:
                logging.info(f"  LÍNEA DEBE: Cuenta {codigo_debe} → S/. {val:.2f}")
            else:
                logging.info(f"  LÍNEA DEBE: Cuenta {codigo_debe} → (sin monto)")
        
        # Crear líneas de haber
        for i, codigo_haber in enumerate(cuentas_haber):
            cuenta = DB.fetchone("SELECT * FROM plan_contable WHERE codigo=?", (codigo_haber,))
            
            if len(cuentas_haber) == 1:
                val = total_debe
            else:
                val = total_debe / len(cuentas_haber) if total_debe > 0 else 0.0
            
            linea = {
                "cuenta_codigo": codigo_haber,
                "descripcion": cuenta['descripcion'] if cuenta else f"Cuenta {codigo_haber}",
                "debe": 0,
                "haber": val,
                "fecha": fecha_op
            }
            lineas_asiento.append(linea)
            if val > 0:
                logging.info(f"  LÍNEA HABER: Cuenta {codigo_haber} → S/. {val:.2f}")
            else:
                logging.info(f"  LÍNEA HABER: Cuenta {codigo_haber} → (sin monto)")
        
        # Crear asiento (incluso si montos son 0, se crea para referencia)
        if lineas_asiento:
            asiento = {
                "fecha": fecha_op,
                "descripcion": op_texto[:100],
                "lineas": lineas_asiento,
                "fuente": "reglas" if mejor_regla and mejor_score >= 0.3 else "diccionario",
                "confianza": "alta" if (mejor_regla and mejor_score >= 0.5) else "media"
            }
            asientos.append(asiento)
            logging.info(f"  ✓ ASIENTO #{len(asientos)} CREADO")
    
    def _determinar_fuente_final(self, explicaciones):
        if not explicaciones:
            return "sin_clasificar"
        if all(e.startswith("Regla") for e in explicaciones):
            return "reglas"
        if any("múltiples conceptos" in e for e in explicaciones):
            return "reglas"
        return "mixta"
    
    def _determinar_confianza_final(self, explicaciones):
        if not explicaciones:
            return "baja"
        scores = []
        for e in explicaciones:
            if "100%" in e:
                scores.append(1.0)
            elif "50%" in e:
                scores.append(0.5)
            elif "Regla" in e:
                scores.append(0.6)
            elif "Diccionario" in e:
                scores.append(0.4)
            else:
                scores.append(0.2)
        promedio = sum(scores) / len(scores) if scores else 0
        return "alta" if promedio >= 0.6 else "media" if promedio >= 0.3 else "baja"
    
    def _determinar_contrapartida(self, codigo):
        if not codigo:
            return [10]
        cuenta = DB.fetchone("SELECT * FROM plan_contable WHERE codigo=?", (codigo,))
        if not cuenta:
            return [10]
        if cuenta['naturaleza'] == 'deudora':
            return [42]  # CxP genérica
        else:
            return [10]  # Efectivo genérico
