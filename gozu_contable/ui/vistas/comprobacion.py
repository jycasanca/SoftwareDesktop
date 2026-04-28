import customtkinter as ctk
from datetime import datetime
from ui.tema import COLORES, FUENTES
from ui.componentes.boton import Boton
from ui.componentes.entrada import Entrada
from ui.componentes.toast import SistemaToast
from ui.componentes.label_seleccionable import LabelSeleccionable
from core.db import DB

class VistaComprobacion(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=COLORES["bg_principal"])
        
        ctk.CTkLabel(self, text="Balance de Comprobación", font=FUENTES["titulo"],
                    text_color=COLORES["amarillo"]).pack(pady=(0, 20))
        
        # Toolbar
        toolbar = ctk.CTkFrame(self, fg_color=COLORES["bg_panel"])
        toolbar.pack(fill="x", pady=(0, 15))
        
        
        
        Boton(toolbar, "Calcular", variante="primario", command=self._calcular).pack(side="left", padx=5, pady=10)
        Boton(toolbar, "⬇ PDF", variante="morado", command=self._exportar_pdf).pack(side="right", padx=10, pady=10)
        
        # Tabla
        self.frame_tabla = ctk.CTkFrame(self, fg_color=COLORES["bg_panel"])
        self.frame_tabla.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # Header
        header = ctk.CTkFrame(self.frame_tabla, fg_color=COLORES["bg_panel"], height=35)
        header.pack(fill="x")
        
        for col in ["Código", "Cuenta", "Sumas Debe", "Sumas Haber", "Saldo Deudor", "Saldo Acreedor"]:
            ctk.CTkLabel(header, text=col, font=FUENTES["pequeña"],
                        text_color=COLORES["texto_sec"]).pack(side="left", padx=5, pady=8)
        
        # Frame filas
        self.frame_filas = ctk.CTkFrame(self.frame_tabla, fg_color=COLORES["bg_principal"])
        self.frame_filas.pack(fill="both", expand=True)
        
        # Verificación
        self.frame_verif = ctk.CTkFrame(self, fg_color=COLORES["bg_panel"])
        self.frame_verif.pack(fill="x", pady=10)
        
        self.lbl_verif = ctk.CTkLabel(self.frame_verif, text="", font=FUENTES["normal"],
                                     text_color=COLORES["verde"])
        self.lbl_verif.pack(pady=10)
    
    def _calcular(self):
        for widget in self.frame_filas.winfo_children():
            widget.destroy()
        
        
        datos = DB.fetchall("""
            SELECT * FROM v_balance_comprobacion
        """)
        
        total_sumas_debe = 0
        total_sumas_haber = 0
        total_deudor = 0
        total_acreedor = 0
        
        for fila in datos:
            bg = COLORES["bg_fila_par"] if datos.index(fila) % 2 == 0 else COLORES["bg_fila_impar"]
            frame = ctk.CTkFrame(self.frame_filas, fg_color=bg, height=40)
            frame.pack(fill="x", pady=1)
            
            deudor = fila['saldo_deudor']
            acreedor = fila['saldo_acreedor']
            
            LabelSeleccionable(frame, text=str(fila['codigo']), font=FUENTES["pequeña"],
                        text_color=COLORES["amarillo"], width=50).pack(side="left", padx=5)
            LabelSeleccionable(frame, text=fila['descripcion'][:25], font=FUENTES["pequeña"],
                        text_color=COLORES["texto"], width=180).pack(side="left", padx=5)
            LabelSeleccionable(frame, text=f"S/ {fila['sumas_debe']:,.2f}", font=FUENTES["pequeña"],
                        text_color=COLORES["texto_sec"], width=80).pack(side="left", padx=5)
            LabelSeleccionable(frame, text=f"S/ {fila['sumas_haber']:,.2f}", font=FUENTES["pequeña"],
                        text_color=COLORES["texto_sec"], width=80).pack(side="left", padx=5)
            LabelSeleccionable(frame, text=f"S/ {deudor:,.2f}" if deudor > 0 else "", font=FUENTES["pequeña"],
                        text_color=COLORES["verde"], width=80).pack(side="left", padx=5)
            LabelSeleccionable(frame, text=f"S/ {acreedor:,.2f}" if acreedor > 0 else "", font=FUENTES["pequeña"],
                        text_color=COLORES["morado"], width=80).pack(side="left", padx=5)
            
            total_sumas_debe += fila['sumas_debe']
            total_sumas_haber += fila['sumas_haber']
            total_deudor += fila['saldo_deudor']
            total_acreedor += fila['saldo_acreedor']
        
        # Fila totales
        frame_tot = ctk.CTkFrame(self.frame_filas, fg_color=COLORES["bg_panel"], height=40)
        frame_tot.pack(fill="x", pady=5)
        
        ctk.CTkLabel(frame_tot, text="TOTALES", font=FUENTES["normal"],
                    text_color=COLORES["amarillo"]).pack(side="left", padx=5)
        ctk.CTkLabel(frame_tot, text=f"S/ {total_sumas_debe:,.2f}", font=FUENTES["normal"],
                    text_color=COLORES["texto_sec"]).pack(side="left", padx=5)
        ctk.CTkLabel(frame_tot, text=f"S/ {total_sumas_haber:,.2f}", font=FUENTES["normal"],
                    text_color=COLORES["texto_sec"]).pack(side="left", padx=5)
        ctk.CTkLabel(frame_tot, text=f"S/ {total_deudor:,.2f}", font=FUENTES["normal"],
                    text_color=COLORES["verde"]).pack(side="left", padx=5)
        ctk.CTkLabel(frame_tot, text=f"S/ {total_acreedor:,.2f}", font=FUENTES["normal"],
                    text_color=COLORES["morado"]).pack(side="left", padx=5)
        
        # Verificación
        cuadra = (abs(total_sumas_debe - total_sumas_haber) < 0.01 and
                  abs(total_deudor - total_acreedor) < 0.01)
        
        if cuadra:
            self.lbl_verif.configure(text="✓ BALANCE CUADRADO — Todas las sumas son iguales",
                                    text_color=COLORES["verde"])
        else:
            self.lbl_verif.configure(text="✗ DESCUADRADO — Revisa los asientos",
                                    text_color=COLORES["rojo"])
    
    def _exportar_pdf(self):
        import os
        from tkinter import filedialog
        from core.reportes_pdf import GeneradorPDF
        ruta = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")],
            initialfile="Balance_Comprobacion.pdf"
        )
        if not ruta:
            return
        filas = DB.fetchall("""
            SELECT ld.numero_asiento, ld.fecha, ld.cuenta_codigo,
                   p.descripcion as descripcion_cuenta, ld.descripcion,
                   ld.debe, ld.haber
            FROM libro_diario ld
            JOIN plan_contable p ON p.codigo = ld.cuenta_codigo
            WHERE ld.eliminado=0
            ORDER BY ld.cuenta_codigo
        """)
        ok = GeneradorPDF().generar_libro_diario(ruta, filas, "Balance de Comprobación")
        if ok:
            SistemaToast().mostrar("PDF generado correctamente", "exito")
            try:
                os.startfile(ruta)
            except Exception:
                pass
        else:
            SistemaToast().mostrar("Error al generar PDF", "error")
