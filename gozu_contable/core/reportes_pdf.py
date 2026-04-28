from core.db import DB

class GeneradorPDF:
    def _obtener_config(self):
        filas = DB.fetchall("SELECT clave, valor FROM config_sistema")
        return {f['clave']: f['valor'] for f in filas}
    
    def _membrete(self, canvas, doc, titulo):
        cfg = self._obtener_config()
        canvas.saveState()
        
        # Empresa arriba izquierda
        canvas.setFont("Helvetica-Bold", 14)
        canvas.drawString(40, doc.pagesize[1]-40, cfg.get('empresa_nombre', ''))
        canvas.setFont("Helvetica", 10)
        canvas.drawString(40, doc.pagesize[1]-55, f"RUC: {cfg.get('empresa_ruc', '')}")
        
        # Fecha arriba derecha
        from datetime import date
        canvas.drawRightString(doc.pagesize[0]-40, doc.pagesize[1]-40,
                               f"Generado: {date.today().strftime('%d/%m/%Y')}")
        
        # Título centrado
        canvas.setFont("Helvetica-Bold", 13)
        canvas.drawCentredString(doc.pagesize[0]/2, doc.pagesize[1]-70, titulo)
        
        # Línea separadora
        canvas.line(40, doc.pagesize[1]-78, doc.pagesize[0]-40, doc.pagesize[1]-78)
        
        # Pie de página
        canvas.setFont("Helvetica", 9)
        canvas.drawCentredString(doc.pagesize[0]/2, 25,
                                 f"Página {doc.page} — {cfg.get('empresa_nombre', '')}")
        canvas.restoreState()
    
    def generar_libro_diario(self, ruta_salida, asientos, periodo):
        try:
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
            from reportlab.lib.pagesizes import A4, landscape
            from reportlab.lib import colors
            
            doc = SimpleDocTemplate(ruta_salida, pagesize=landscape(A4),
                                    topMargin=90, bottomMargin=40)
            
            cabecera = ['N° Asiento', 'Fecha', 'Código', 'Cuenta', 'Descripción', 'Debe', 'Haber']
            datos = [cabecera]
            
            for asiento in asientos:
                datos.append([
                    str(asiento['numero_asiento']),
                    asiento['fecha'],
                    str(asiento['cuenta_codigo']),
                    asiento['descripcion_cuenta'],
                    asiento['descripcion'],
                    f"S/ {asiento['debe']:,.2f}" if asiento['debe'] else '',
                    f"S/ {asiento['haber']:,.2f}" if asiento['haber'] else '',
                ])
            
            # Fila de totales
            total_d = sum(a['debe'] for a in asientos)
            total_h = sum(a['haber'] for a in asientos)
            datos.append(['', '', '', '', 'TOTALES',
                          f"S/ {total_d:,.2f}", f"S/ {total_h:,.2f}"])
            
            tabla = Table(datos, repeatRows=1)
            estilo = TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#cccccc')),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('FONTSIZE', (0,0), (-1,-1), 9),
                ('ALIGN', (5,0), (6,-1), 'RIGHT'),
                ('ROWBACKGROUNDS', (0,1), (-1,-2), [colors.white, colors.HexColor('#f5f5f5')]),
                ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'),
                ('LINEBELOW', (0,-1), (-1,-1), 1, colors.black),
                ('GRID', (0,0), (-1,-1), 0.25, colors.HexColor('#cccccc')),
            ])
            tabla.setStyle(estilo)
            
            def _p(canvas, doc):
                self._membrete(canvas, doc, f"Libro Diario — {periodo}")
            
            doc.build([tabla], onFirstPage=_p, onLaterPages=_p)
            return True
        except Exception as e:
            print(f"Error generando PDF: {e}")
            return False
