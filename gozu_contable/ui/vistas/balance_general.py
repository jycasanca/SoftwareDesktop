import customtkinter as ctk
from datetime import datetime
from ui.tema import COLORES, FUENTES
from ui.componentes.boton import Boton
from ui.componentes.entrada import Entrada
from ui.componentes.toast import SistemaToast
from ui.componentes.label_seleccionable import LabelSeleccionable
from core.db import DB
import core.motor_contable as MotorContable

class VistaBalanceGeneral(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=COLORES["bg_principal"])
        
        ctk.CTkLabel(self, text="Balance General", font=FUENTES["titulo"],
                    text_color=COLORES["amarillo"]).pack(pady=(0, 20))
        
        # Toolbar
        toolbar = ctk.CTkFrame(self, fg_color=COLORES["bg_panel"])
        toolbar.pack(fill="x", pady=(0, 15))
        
        
        
        Boton(toolbar, "Calcular", variante="primario", command=self._calcular).pack(side="left", padx=5, pady=10)
        Boton(toolbar, "⬇ PDF", variante="morado", command=self._exportar_pdf).pack(side="right", padx=10, pady=10)
        
        # Frame principal 2 columnas
        frame_principal = ctk.CTkFrame(self, fg_color=COLORES["bg_principal"])
        frame_principal.pack(fill="both", expand=True, padx=10)
        frame_principal.columnconfigure(0, weight=1)
        frame_principal.columnconfigure(1, weight=1)
        
        # Columna Activo
        self.col_activo = ctk.CTkFrame(frame_principal, fg_color=COLORES["bg_panel"], corner_radius=8)
        self.col_activo.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        
        # Columna Pasivo y Patrimonio
        self.col_pasivo = ctk.CTkFrame(frame_principal, fg_color=COLORES["bg_panel"], corner_radius=8)
        self.col_pasivo.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        
        # Verificación
        self.frame_verif = ctk.CTkFrame(self, fg_color=COLORES["bg_panel"])
        self.frame_verif.pack(fill="x", pady=15)
        
        self.lbl_verif = ctk.CTkLabel(self.frame_verif, text="", font=FUENTES["normal"],
                                     text_color=COLORES["verde"])
        self.lbl_verif.pack(pady=15)
    
    def _calcular(self):
        datos = MotorContable.MotorContable().calcular_balance_general()
        
        # Limpiar columnas
        for widget in self.col_activo.winfo_children():
            widget.destroy()
        for widget in self.col_pasivo.winfo_children():
            widget.destroy()
        
        # ACTIVO
        ctk.CTkLabel(self.col_activo, text="ACTIVO", font=FUENTES["subtit"],
                    text_color=COLORES["verde"]).pack(pady=(15, 10))
        
        self._seccion_cuentas(self.col_activo, "ACTIVO CORRIENTE", datos['grupos']['activo_corriente'])
        self._seccion_cuentas(self.col_activo, "ACTIVO NO CORRIENTE", datos['grupos']['activo_no_corriente'])
        
        ctk.CTkFrame(self.col_activo, height=2, fg_color=COLORES["borde"]).pack(fill="x", padx=15, pady=10)
        
        ctk.CTkLabel(self.col_activo, text="TOTAL ACTIVO", font=FUENTES["normal"],
                    text_color=COLORES["amarillo"]).pack(anchor="w", padx=15, pady=5)
        ctk.CTkLabel(self.col_activo, text=f"S/ {datos['total_activo']:,.2f}", font=FUENTES["titulo"],
                    text_color=COLORES["amarillo"]).pack(anchor="e", padx=15, pady=(0, 15))
        
        # PASIVO Y PATRIMONIO
        ctk.CTkLabel(self.col_pasivo, text="PASIVO Y PATRIMONIO", font=FUENTES["subtit"],
                    text_color=COLORES["rojo"]).pack(pady=(15, 10))
        
        self._seccion_cuentas(self.col_pasivo, "PASIVO CORRIENTE", datos['grupos']['pasivo_corriente'])
        self._seccion_cuentas(self.col_pasivo, "PASIVO NO CORRIENTE", datos['grupos']['pasivo_no_corriente'])
        
        total_pasivo = sum(abs(f['saldo']) for f in datos['grupos']['pasivo_corriente'] + datos['grupos']['pasivo_no_corriente'])
        
        ctk.CTkLabel(self.col_pasivo, text="TOTAL PASIVO", font=FUENTES["normal"],
                    text_color=COLORES["rojo"]).pack(anchor="w", padx=15, pady=5)
        ctk.CTkLabel(self.col_pasivo, text=f"S/ {total_pasivo:,.2f}", font=FUENTES["subtit"],
                    text_color=COLORES["rojo"]).pack(anchor="e", padx=15, pady=(0, 5))
        
        ctk.CTkFrame(self.col_pasivo, height=1, fg_color=COLORES["borde"]).pack(fill="x", padx=15, pady=5)
        
        self._seccion_cuentas(self.col_pasivo, "PATRIMONIO", datos['grupos']['patrimonio'])
        
        total_patrimonio = sum(abs(f['saldo']) for f in datos['grupos']['patrimonio'])
        
        ctk.CTkFrame(self.col_pasivo, height=2, fg_color=COLORES["borde"]).pack(fill="x", padx=15, pady=10)
        
        total_pp = total_pasivo + total_patrimonio
        
        ctk.CTkLabel(self.col_pasivo, text="TOTAL PASIVO + PATRIMONIO", font=FUENTES["normal"],
                    text_color=COLORES["amarillo"]).pack(anchor="w", padx=15, pady=5)
        ctk.CTkLabel(self.col_pasivo, text=f"S/ {total_pp:,.2f}", font=FUENTES["titulo"],
                    text_color=COLORES["amarillo"]).pack(anchor="e", padx=15, pady=(0, 15))
        
        # Verificación
        if datos['cuadra']:
            self.lbl_verif.configure(text="✓  A = P + C  —  ECUACIÓN CONTABLE CUADRADA",
                                    text_color=COLORES["verde"])
            self.frame_verif.configure(fg_color=COLORES["bg_hover"])
        else:
            dif = abs(datos['total_activo'] - total_pp)
            self.lbl_verif.configure(text=f"✗  DESCUADRADO  —  Diferencia: S/ {dif:,.2f}",
                                    text_color=COLORES["rojo"])
            self.frame_verif.configure(fg_color=COLORES["bg_hover"])
    
    def _seccion_cuentas(self, parent, titulo, cuentas):
        ctk.CTkLabel(parent, text=titulo, font=FUENTES["pequeña"],
                    text_color=COLORES["azul"]).pack(anchor="w", padx=15, pady=(10, 5))
        
        subtotal = 0
        for cuenta in cuentas:
            frame = ctk.CTkFrame(parent, fg_color="transparent")
            frame.pack(fill="x", padx=15, pady=2)
            
            LabelSeleccionable(frame, text=cuenta['descripcion'][:30], font=FUENTES["pequeña"],
                        text_color=COLORES["texto"], width=250).pack(side="left")
            LabelSeleccionable(frame, text=f"S/ {abs(cuenta['saldo']):,.2f}", font=FUENTES["pequeña"],
                        text_color=COLORES["texto"], width=100).pack(side="right")
            
            subtotal += cuenta['saldo']
        
        ctk.CTkLabel(parent, text=f"Total {titulo.lower()}", font=FUENTES["pequeña"],
                    text_color=COLORES["azul"]).pack(anchor="w", padx=15, pady=(5, 0))
        ctk.CTkLabel(parent, text=f"S/ {abs(subtotal):,.2f}", font=FUENTES["pequeña"],
                    text_color=COLORES["azul"]).pack(anchor="e", padx=15, pady=(0, 10))
    
    def _exportar_pdf(self):
        import os
        from tkinter import filedialog
        from core.reportes_pdf import GeneradorPDF
        ruta = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")],
            initialfile="Balance_General.pdf"
        )
        if not ruta:
            return
        # Simular PDF del balance
        filas = DB.fetchall("""
            SELECT ld.numero_asiento, ld.fecha, ld.cuenta_codigo,
                   p.descripcion as descripcion_cuenta, ld.descripcion,
                   ld.debe, ld.haber
            FROM libro_diario ld
            JOIN plan_contable p ON p.codigo = ld.cuenta_codigo
            WHERE ld.eliminado=0
            ORDER BY ld.cuenta_codigo
        """)
        ok = GeneradorPDF().generar_libro_diario(ruta, filas, "Balance General")
        if ok:
            SistemaToast().mostrar("PDF generado correctamente", "exito")
            try:
                os.startfile(ruta)
            except Exception:
                pass
        else:
            SistemaToast().mostrar("Error al generar PDF", "error")
