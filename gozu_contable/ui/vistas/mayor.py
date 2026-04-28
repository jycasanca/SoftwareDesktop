import customtkinter as ctk
from datetime import datetime
from ui.tema import COLORES, FUENTES
from ui.componentes.boton import Boton
from ui.componentes.entrada import Entrada
from ui.componentes.toast import SistemaToast
from ui.componentes.label_seleccionable import LabelSeleccionable
from core.db import DB

class VistaMayor(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=COLORES["bg_principal"])
        
        # Título
        ctk.CTkLabel(self, text="MAYORES DEL CICLO CONTABLE (Cuentas T)", font=FUENTES["titulo"],
                     text_color=COLORES["amarillo"]).pack(pady=(0, 20))
        
        # Toolbar
        toolbar = ctk.CTkFrame(self, fg_color=COLORES["bg_panel"])
        toolbar.pack(fill="x", pady=(0, 15))
        
        Boton(toolbar, "Actualizar", variante="primario", command=self._cargar_todas_cuentas).pack(side="left", padx=10, pady=10)
        Boton(toolbar, "⬇ PDF", variante="morado", command=self._exportar_pdf).pack(side="right", padx=10, pady=10)
        
        # Scrollable Frame for T-Accounts
        self.frame_scroll = ctk.CTkScrollableFrame(self, fg_color=COLORES["bg_principal"])
        self.frame_scroll.pack(fill="both", expand=True, padx=10, pady=10)
        
        self._cargar_todas_cuentas()
        
    def _cargar_todas_cuentas(self):
        for widget in self.frame_scroll.winfo_children():
            widget.destroy()
            
        cuentas_db = DB.fetchall("""
            SELECT DISTINCT p.codigo, p.descripcion 
            FROM libro_diario ld
            JOIN plan_contable p ON p.codigo = ld.cuenta_codigo
            WHERE ld.eliminado=0
            ORDER BY p.codigo
        """)
        
        if not cuentas_db:
            ctk.CTkLabel(self.frame_scroll, text="No hay movimientos registrados para mostrar en el Mayor.",
                         font=FUENTES["normal"], text_color=COLORES["texto_sec"]).pack(pady=50)
            return
            
        for cuenta in cuentas_db:
            codigo = cuenta['codigo']
            desc = cuenta['descripcion']
            
            movs = DB.fetchall("""
                SELECT fecha, descripcion, debe, haber
                FROM libro_diario
                WHERE cuenta_codigo = ? AND eliminado=0
                ORDER BY fecha, id
            """, (codigo,))
            
            debes = [m for m in movs if m['debe'] > 0]
            haberes = [m for m in movs if m['haber'] > 0]
            
            if not debes and not haberes:
                continue
                
            self._crear_cuenta_t(codigo, desc, debes, haberes)
            
    def _crear_cuenta_t(self, codigo, desc, debes, haberes):
        frame_t = ctk.CTkFrame(self.frame_scroll, fg_color=COLORES["bg_panel"], corner_radius=0)
        frame_t.pack(fill="x", padx=100, pady=20)
        
        # Título de la cuenta
        bg_title = COLORES["bg_fila_impar"]
        if str(codigo).startswith('1') or str(codigo).startswith('2') or str(codigo).startswith('3'):
            bg_title = "#FDE68A" # Amarillo pastel
            text_col = "#000000"
        elif str(codigo).startswith('4'):
            bg_title = "#FECACA" # Rojo pastel
            text_col = "#000000"
        elif str(codigo).startswith('5'):
            bg_title = "#BFDBFE" # Azul pastel
            text_col = "#000000"
        else:
            bg_title = COLORES["borde"]
            text_col = COLORES["texto"]
            
        lbl_titulo = ctk.CTkLabel(frame_t, text=f"{codigo} {desc}", font=FUENTES["subtit"],
                                  text_color=text_col, fg_color=bg_title)
        lbl_titulo.pack(fill="x")
        
        # Línea Horizontal de la T
        ctk.CTkFrame(frame_t, height=4, fg_color="#000000").pack(fill="x", padx=50)
        
        # Contenido de la T
        frame_content = ctk.CTkFrame(frame_t, fg_color="transparent")
        frame_content.pack(fill="x", padx=50, pady=(0, 5))
        
        frame_content.columnconfigure(0, weight=1)
        frame_content.columnconfigure(1, weight=0, minsize=4) # Separador vertical grueso
        frame_content.columnconfigure(2, weight=1)
        
        sep = ctk.CTkFrame(frame_content, width=4, fg_color="#000000")
        sep.grid(row=0, column=1, sticky="ns", rowspan=max(len(debes), len(haberes))+3)
        
        max_rows = max(len(debes), len(haberes))
        total_debe = 0
        total_haber = 0
        
        for i in range(max_rows):
            if i < len(debes):
                d = debes[i]
                f_izq = ctk.CTkFrame(frame_content, fg_color="transparent")
                f_izq.grid(row=i, column=0, sticky="ew", padx=(0, 10))
                ctk.CTkLabel(f_izq, text=d['fecha'], font=FUENTES["pequeña"], text_color=COLORES["texto_sec"]).pack(side="left")
                ctk.CTkLabel(f_izq, text=f"{d['debe']:,.2f}", font=FUENTES["normal"], text_color=COLORES["texto"]).pack(side="right")
                total_debe += d['debe']
                
            if i < len(haberes):
                h = haberes[i]
                f_der = ctk.CTkFrame(frame_content, fg_color="transparent")
                f_der.grid(row=i, column=2, sticky="ew", padx=(10, 0))
                ctk.CTkLabel(f_der, text=f"{h['haber']:,.2f}", font=FUENTES["normal"], text_color=COLORES["texto"]).pack(side="left")
                
                desc_label = h.get('descripcion', '')[:20]
                if desc_label:
                    ctk.CTkLabel(f_der, text=f"{h['fecha']} {desc_label}", font=FUENTES["pequeña"], text_color=COLORES["texto_sec"]).pack(side="right")
                else:
                    ctk.CTkLabel(f_der, text=h['fecha'], font=FUENTES["pequeña"], text_color=COLORES["texto_sec"]).pack(side="right")
                total_haber += h['haber']
                
        sub_row = max_rows
        # Total line
        ctk.CTkFrame(frame_content, height=1, fg_color=COLORES["texto_sec"]).grid(row=sub_row, column=0, sticky="ew", pady=(2, 0), padx=(50, 10))
        ctk.CTkFrame(frame_content, height=1, fg_color=COLORES["texto_sec"]).grid(row=sub_row, column=2, sticky="ew", pady=(2, 0), padx=(10, 50))
        
        # Totales intermedios si hay más de 1
        sum_row = sub_row + 1
        if len(debes) > 1 or len(haberes) > 1:
            if len(debes) > 1:
                ctk.CTkLabel(frame_content, text=f"{total_debe:,.2f}", font=FUENTES["pequeña"], text_color=COLORES["texto_sec"]).grid(row=sum_row, column=0, sticky="e", padx=(0, 10))
            if len(haberes) > 1:
                ctk.CTkLabel(frame_content, text=f"{total_haber:,.2f}", font=FUENTES["pequeña"], text_color=COLORES["texto_sec"]).grid(row=sum_row, column=2, sticky="w", padx=(10, 0))
                
        # Saldo Final
        saldo = total_debe - total_haber
        saldo_row = sum_row + 1
        
        bg_saldo = "#CBD5E1" # Gris claro pastel
        
        if saldo > 0:
            f_saldo = ctk.CTkFrame(frame_content, fg_color=bg_saldo, corner_radius=0)
            f_saldo.grid(row=saldo_row, column=0, sticky="ew", pady=(5, 0), padx=(0, 0))
            ctk.CTkLabel(f_saldo, text="Saldo Final", font=FUENTES["normal"], text_color="#000000").pack(side="left", padx=10)
            ctk.CTkLabel(f_saldo, text=f"{saldo:,.2f}", font=("Consolas", 14, "bold"), text_color="#000000").pack(side="right", padx=10)
        elif saldo < 0:
            f_saldo = ctk.CTkFrame(frame_content, fg_color=bg_saldo, corner_radius=0)
            f_saldo.grid(row=saldo_row, column=2, sticky="ew", pady=(5, 0), padx=(0, 0))
            ctk.CTkLabel(f_saldo, text=f"{abs(saldo):,.2f}", font=("Consolas", 14, "bold"), text_color="#000000").pack(side="left", padx=10)
            ctk.CTkLabel(f_saldo, text="Saldo Final", font=FUENTES["normal"], text_color="#000000").pack(side="right", padx=10)
        else:
            f_saldo = ctk.CTkFrame(frame_content, fg_color=bg_saldo, corner_radius=0)
            f_saldo.grid(row=saldo_row, column=0, columnspan=3, sticky="ew", pady=(5, 0))
            ctk.CTkLabel(f_saldo, text="Saldo Saldado (Cero)", font=FUENTES["normal"], text_color="#000000").pack(pady=2)

    def _exportar_pdf(self):
        import os
        from tkinter import filedialog
        from core.reportes_pdf import GeneradorPDF
        ruta = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")],
            initialfile="Libro_Mayor_Cuentas_T.pdf"
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
            ORDER BY ld.cuenta_codigo, ld.fecha, ld.id
        """)
        ok = GeneradorPDF().generar_libro_diario(ruta, filas, "Libro Mayor - Cuentas T")
        if ok:
            SistemaToast().mostrar("PDF generado correctamente", "exito")
            try:
                os.startfile(ruta)
            except Exception:
                pass
        else:
            SistemaToast().mostrar("Error al generar PDF", "error")
