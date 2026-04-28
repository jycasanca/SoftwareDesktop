import customtkinter as ctk
from datetime import datetime
from ui.tema import COLORES, FUENTES
from ui.componentes.boton import Boton
from ui.componentes.entrada import Entrada
from ui.componentes.toast import SistemaToast
from ui.componentes.label_seleccionable import LabelSeleccionable
from core.db import DB

class VistaDiario(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=COLORES["bg_principal"])
        
        # Título
        ctk.CTkLabel(self, text="Libro Diario", font=FUENTES["titulo"],
                     text_color=COLORES["amarillo"]).pack(pady=(0, 20))
        
        # Toolbar
        toolbar = ctk.CTkFrame(self, fg_color=COLORES["bg_panel"])
        toolbar.pack(fill="x", pady=(0, 15))
        
        frame_filtros = ctk.CTkFrame(toolbar, fg_color="transparent")
        frame_filtros.pack(side="left", padx=10, pady=10)
        
        self.entry_busqueda = Entrada(frame_filtros, placeholder="🔍 Buscar descripción...", width=200)
        self.entry_busqueda.pack(side="left", padx=5)
        
        self.combobox_estado = ctk.CTkOptionMenu(frame_filtros, values=["Todos", "Activos", "Eliminados"],
                                                  fg_color=COLORES["bg_input"], button_color=COLORES["borde"],
                                                  text_color=COLORES["texto"])
        self.combobox_estado.pack(side="left", padx=5)
        self.combobox_estado.set("Todos")
        
        Boton(frame_filtros, "Filtrar", variante="info", command=self._cargar_datos).pack(side="left", padx=5)
        Boton(frame_filtros, "Limpiar", variante="fantasma", command=self._limpiar_filtros).pack(side="left", padx=5)
        
        Boton(toolbar, "⬇ PDF", variante="morado", command=self._exportar_pdf).pack(side="right", padx=10, pady=10)
        
        # Tabla
        self.frame_tabla = ctk.CTkFrame(self, fg_color=COLORES["bg_panel"])
        self.frame_tabla.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # Header
        header = ctk.CTkFrame(self.frame_tabla, fg_color=COLORES["bg_panel"], height=35)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        columns = [
            ("N° Asiento", 80), ("Fecha", 90), ("Código", 50), ("Cuenta", 130),
            ("Descripción", 180), ("Debe", 70), ("Haber", 70), ("", 30)
        ]
        for col, width in columns:
            ctk.CTkLabel(header, text=col, font=FUENTES["pequeña"],
                        text_color=COLORES["texto_sec"], width=width).pack(side="left", padx=5, pady=8)
        
        # Frame para filas
        self.frame_filas = ctk.CTkFrame(self.frame_tabla, fg_color=COLORES["bg_principal"])
        self.frame_filas.pack(fill="both", expand=True)
        
        # Footer
        footer = ctk.CTkFrame(self, fg_color=COLORES["bg_panel"])
        footer.pack(fill="x", pady=10)
        
        self.lbl_totales = ctk.CTkLabel(footer, text="Total: 0 registros", font=FUENTES["pequeña"],
                                        text_color=COLORES["texto_sec"])
        self.lbl_totales.pack(side="left", padx=10, pady=10)
        
        self.lbl_balance = ctk.CTkLabel(footer, text="", font=FUENTES["normal"],
                                        text_color=COLORES["verde"])
        self.lbl_balance.pack(side="right", padx=10, pady=10)
        
        self._cargar_datos()
    
    def _cargar_datos(self):
        # Limpiar filas
        for widget in self.frame_filas.winfo_children():
            widget.destroy()

        busqueda = self.entry_busqueda.get()
        estado = self.combobox_estado.get()

        # Construir SQL - mostrar todo el detalle
        sql = """
            SELECT ld.*, p.descripcion as desc_cuenta
            FROM libro_diario ld
            JOIN plan_contable p ON p.codigo = ld.cuenta_codigo
            WHERE 1=1
        """
        params = []

        if busqueda:
            sql += " AND (ld.descripcion LIKE ? OR p.descripcion LIKE ?)"
            params.extend([f"%{busqueda}%", f"%{busqueda}%"])

        if estado == "Activos":
            sql += " AND ld.eliminado = 0"
        elif estado == "Eliminados":
            sql += " AND ld.eliminado = 1"

        sql += " ORDER BY ld.fecha DESC, ld.numero_asiento DESC, ld.id"

        filas = DB.fetchall(sql, tuple(params))

        total_debe = 0
        total_haber = 0
        fecha_actual = None
        numero_asiento_actual = None

        for fila in filas:
            # Separador visual cuando cambia la fecha o el número de asiento
            cambio_grupo = False
            if fecha_actual != fila['fecha']:
                fecha_actual = fila['fecha']
                cambio_grupo = True

            if numero_asiento_actual != fila['numero_asiento']:
                numero_asiento_actual = fila['numero_asiento']
                cambio_grupo = True

            # Color alternado por grupo
            if cambio_grupo:
                bg = COLORES["bg_fila_par"]
            else:
                bg = COLORES["bg_fila_impar"]

            frame_fila = ctk.CTkFrame(self.frame_filas, fg_color=bg, height=40)
            frame_fila.pack(fill="x", pady=1)
            frame_fila.pack_propagate(False)

            # N° Asiento (con badge si es nuevo)
            if cambio_grupo:
                LabelSeleccionable(frame_fila, text=f"N° {fila['numero_asiento']}", font=FUENTES["pequeña"],
                            text_color=COLORES["amarillo"], width=80).pack(side="left", padx=5)
            else:
                LabelSeleccionable(frame_fila, text="", font=FUENTES["pequeña"],
                            text_color=COLORES["amarillo"], width=80).pack(side="left", padx=5)

            # Fecha (solo mostrar si cambia)
            if cambio_grupo:
                LabelSeleccionable(frame_fila, text=fila['fecha'], font=FUENTES["pequeña"],
                            text_color=COLORES["texto"], width=90).pack(side="left", padx=5)
            else:
                LabelSeleccionable(frame_fila, text="", font=FUENTES["pequeña"],
                            text_color=COLORES["texto"], width=90).pack(side="left", padx=5)

            LabelSeleccionable(frame_fila, text=str(fila['cuenta_codigo']), font=FUENTES["pequeña"],
                        text_color=COLORES["morado"], width=50).pack(side="left", padx=5)
            LabelSeleccionable(frame_fila, text=fila['desc_cuenta'][:25], font=FUENTES["pequeña"],
                        text_color=COLORES["texto"], width=130).pack(side="left", padx=5)
            LabelSeleccionable(frame_fila, text=fila['descripcion'][:30], font=FUENTES["pequeña"],
                        text_color=COLORES["texto_sec"], width=180).pack(side="left", padx=5)
            LabelSeleccionable(frame_fila, text=f"S/ {fila['debe']:,.2f}" if fila['debe'] else "",
                        font=FUENTES["pequeña"], text_color=COLORES["verde"], width=70).pack(side="left", padx=5)
            LabelSeleccionable(frame_fila, text=f"S/ {fila['haber']:,.2f}" if fila['haber'] else "",
                        font=FUENTES["pequeña"], text_color=COLORES["morado"], width=70).pack(side="left", padx=5)

            estado_text = "✓" if fila['eliminado'] == 0 else "🗑"
            estado_color = COLORES["verde"] if fila['eliminado'] == 0 else COLORES["rojo"]
            ctk.CTkLabel(frame_fila, text=estado_text, font=FUENTES["pequeña"],
                        text_color=estado_color, width=30).pack(side="left", padx=5)

            total_debe += fila['debe']
            total_haber += fila['haber']

        self.lbl_totales.configure(text=f"Total: {len(filas)} registros | Debe: S/ {total_debe:,.2f} | Haber: S/ {total_haber:,.2f}")

        dif = abs(total_debe - total_haber)
        if dif < 0.01:
            self.lbl_balance.configure(text="✓ Balance cuadrado", text_color=COLORES["verde"])
        else:
            self.lbl_balance.configure(text=f"✗ Descuadrado: S/ {dif:.2f}", text_color=COLORES["rojo"])
    
    def _limpiar_filtros(self):
        self.entry_busqueda.delete(0, "end")
        self.combobox_estado.set("Todos")
        self._cargar_datos()
    
    def _exportar_pdf(self):
        import os, subprocess
        from tkinter import filedialog
        from core.reportes_pdf import GeneradorPDF
        ruta = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")],
            initialfile="Libro_Diario.pdf"
        )
        if not ruta:
            return
        # Obtener datos actuales
        filas = DB.fetchall("""
            SELECT ld.numero_asiento, ld.fecha, ld.cuenta_codigo,
                   p.descripcion as descripcion_cuenta, ld.descripcion,
                   ld.debe, ld.haber
            FROM libro_diario ld
            JOIN plan_contable p ON p.codigo = ld.cuenta_codigo
            ORDER BY ld.fecha, ld.numero_asiento, ld.id
        """)
        ok = GeneradorPDF().generar_libro_diario(ruta, filas, "Período completo")
        if ok:
            SistemaToast().mostrar("PDF generado correctamente", "exito")
            try:
                os.startfile(ruta)
            except Exception:
                pass
        else:
            SistemaToast().mostrar("Error al generar PDF (¿ReportLab instalado?)", "error")
