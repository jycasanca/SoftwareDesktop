import customtkinter as ctk
from datetime import datetime
from ui.tema import COLORES, FUENTES
from ui.componentes.boton import Boton
from ui.componentes.entrada import Entrada
from ui.componentes.toast import SistemaToast
from ui.componentes.label_seleccionable import LabelSeleccionable
import core.motor_contable as MotorContable
from core.db import DB

class VistaResultados(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=COLORES["bg_principal"])
        
        ctk.CTkLabel(self, text="Estado de Resultados", font=FUENTES["titulo"],
                    text_color=COLORES["amarillo"]).pack(pady=(0, 20))
        
        # Toolbar
        toolbar = ctk.CTkFrame(self, fg_color=COLORES["bg_panel"])
        toolbar.pack(fill="x", pady=(0, 15))
        
        
        
        Boton(toolbar, "Calcular", variante="primario", command=self._calcular).pack(side="left", padx=5, pady=10)
        Boton(toolbar, "⬇ PDF", variante="morado", command=self._exportar_pdf).pack(side="right", padx=10, pady=10)
        
        # Contenido centrado
        self.frame_contenido = ctk.CTkFrame(self, fg_color=COLORES["bg_principal"])
        self.frame_contenido.pack(fill="both", expand=True, padx=100)
        
        ctk.CTkLabel(self.frame_contenido, text="Selecciona un período y haz clic en Calcular",
                    font=FUENTES["normal"], text_color=COLORES["texto_sec"]).pack(pady=50)
    
    def _calcular(self):
        datos = MotorContable.MotorContable().calcular_estado_resultados()
        
        # Limpiar
        for widget in self.frame_contenido.winfo_children():
            widget.destroy()
        
        self._fila("VENTAS NETAS", datos['total_ventas'], COLORES["verde"])
        for v in datos['ventas']:
            self._fila(f"  {v['descripcion']}", v['saldo'], COLORES["verde"], indentacion=20)
        
        self._fila("(-) COSTO DE LA VENTA", datos['total_costos_venta'], COLORES["rojo"])
        for c in datos['costos_venta']:
            self._fila(f"  {c['descripcion']}", abs(c['saldo']), COLORES["rojo"], indentacion=20)
            
        ctk.CTkFrame(self.frame_contenido, height=2, fg_color=COLORES["borde"]).pack(fill="x", pady=10)
        
        color_bruta = COLORES["verde"] if datos['utilidad_bruta'] >= 0 else COLORES["rojo"]
        self._fila("UTILIDAD BRUTA", datos['utilidad_bruta'], color_bruta, es_total=True)
        
        self._fila("(-) GASTOS OPERATIVOS", datos['total_gastos_op'], COLORES["rojo"])
        for go in datos['gastos_operativos']:
            self._fila(f"  {go['descripcion']}", abs(go['saldo']), COLORES["rojo"], indentacion=20)
            
        ctk.CTkFrame(self.frame_contenido, height=2, fg_color=COLORES["borde"]).pack(fill="x", pady=10)
        
        color_op = COLORES["azul"] if datos['utilidad_operativa'] >= 0 else COLORES["rojo"]
        self._fila("UTILIDAD OPERATIVA", datos['utilidad_operativa'], color_op, es_total=True)
        
        self._fila("(-) OTROS GASTOS (- PERDIDAS)", datos['total_otros_gastos'], COLORES["rojo"])
        for og in datos['otros_gastos']:
            self._fila(f"  {og['descripcion']}", abs(og['saldo']), COLORES["rojo"], indentacion=20)
            
        self._fila("(+) OTROS INGRESOS (+ DONACIONES)", datos['total_otros_ingresos'], COLORES["verde"])
        for oi in datos['otros_ingresos']:
            self._fila(f"  {oi['descripcion']}", oi['saldo'], COLORES["verde"], indentacion=20)
            
        ctk.CTkFrame(self.frame_contenido, height=2, fg_color=COLORES["amarillo"]).pack(fill="x", pady=10)
        
        color_antes = COLORES["amarillo"] if datos['utilidad_antes_impuestos'] >= 0 else COLORES["rojo"]
        self._fila("UTILIDAD ANTES DE IMPUESTOS", datos['utilidad_antes_impuestos'], color_antes, es_total=True)
        
        # Opcional (Impuestos y Neta)
        self._fila(f"(-) IMPUESTO A LA RENTA ({datos['tasa_ir']:.1f}%)", datos['impuesto_renta'], COLORES["rojo"])
        color_neta = COLORES["amarillo"] if datos['utilidad_neta'] >= 0 else COLORES["rojo"]
        self._fila("UTILIDAD NETA", datos['utilidad_neta'], color_neta, es_total=True)
        
        ctk.CTkLabel(self.frame_contenido, text=f"S/ {datos['utilidad_neta']:,.2f}",
                    font=("Consolas", 24, "bold"), text_color=color_neta).pack(pady=(10, 20))
        
        if datos['utilidad_neta'] < 0:
            ctk.CTkLabel(self.frame_contenido, text="⚠ PÉRDIDA DEL PERÍODO",
                        font=FUENTES["normal"], text_color=COLORES["rojo"]).pack(pady=(0, 20))
    
    def _fila(self, label, valor, color_val, indentacion=0, es_total=False):
        frame = ctk.CTkFrame(self.frame_contenido, fg_color="transparent")
        frame.pack(fill="x", pady=3)
        
        frame_int = ctk.CTkFrame(frame, fg_color="transparent")
        frame_int.pack(fill="x", padx=(indentacion, 0))
        
        font = FUENTES["normal"] if es_total else FUENTES["pequeña"]
        LabelSeleccionable(frame_int, text=label, font=font, text_color=COLORES["texto"], width=400).pack(side="left")
        LabelSeleccionable(frame_int, text=f"S/ {valor:,.2f}", font=font, text_color=color_val, width=150).pack(side="right")
    
    def _exportar_pdf(self):
        import os
        from tkinter import filedialog
        from core.reportes_pdf import GeneradorPDF
        ruta = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")],
            initialfile="Estado_Resultados.pdf"
        )
        if not ruta:
            return
        # Obtener asientos para simular PDF (podemos usar libro diario completo o crear reporte específico)
        filas = DB.fetchall("""
            SELECT ld.numero_asiento, ld.fecha, ld.cuenta_codigo,
                   p.descripcion as descripcion_cuenta, ld.descripcion,
                   ld.debe, ld.haber
            FROM libro_diario ld
            JOIN plan_contable p ON p.codigo = ld.cuenta_codigo
            WHERE ld.eliminado=0
            ORDER BY ld.fecha
        """)
        ok = GeneradorPDF().generar_libro_diario(ruta, filas, "Estado de Resultados (Detalle)")
        if ok:
            SistemaToast().mostrar("PDF generado correctamente", "exito")
            try:
                os.startfile(ruta)
            except Exception:
                pass
        else:
            SistemaToast().mostrar("Error al generar PDF", "error")
