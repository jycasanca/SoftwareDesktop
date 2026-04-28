import customtkinter as ctk
from datetime import datetime, timedelta
from ui.tema import COLORES, FUENTES
from ui.componentes.boton import Boton
from ui.componentes.entrada import Entrada
from ui.componentes.toast import SistemaToast
from ui.componentes.modal import Modal
from ui.componentes.label_seleccionable import LabelSeleccionable
from core.db import DB

class VistaHistorial(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=COLORES["bg_principal"])

        # Título
        ctk.CTkLabel(self, text="📚 Historial de Asientos", font=FUENTES["titulo"],
                     text_color=COLORES["amarillo"]).pack(pady=(0, 10))

        ctk.CTkLabel(self, text="Gestiona los asientos registrados. Puedes eliminar o restaurar asientos.",
                     font=FUENTES["normal"], text_color=COLORES["texto_sec"]).pack(pady=(0, 15))

        # Toolbar
        toolbar = ctk.CTkFrame(self, fg_color=COLORES["bg_panel"])
        toolbar.pack(fill="x", pady=(0, 15))

        frame_filtros = ctk.CTkFrame(toolbar, fg_color="transparent")
        frame_filtros.pack(side="left", padx=10, pady=10)

        self.entry_busqueda = Entrada(frame_filtros, placeholder="🔍 Buscar descripción o cuenta...", width=250)
        self.entry_busqueda.pack(side="left", padx=5)

        self.combobox_estado = ctk.CTkOptionMenu(frame_filtros, values=["Activos", "Eliminados", "Todos"],
                                                  fg_color=COLORES["bg_input"], button_color=COLORES["borde"],
                                                  text_color=COLORES["texto"])
        self.combobox_estado.pack(side="left", padx=5)
        self.combobox_estado.set("Todos")

        Boton(frame_filtros, "Filtrar", variante="info", command=self._cargar_datos).pack(side="left", padx=5)
        Boton(frame_filtros, "Limpiar", variante="fantasma", command=self._limpiar_filtros).pack(side="left", padx=5)

        # Stats
        self.frame_stats = ctk.CTkFrame(toolbar, fg_color="transparent")
        self.frame_stats.pack(side="right", padx=10, pady=10)

        self.lbl_stats = ctk.CTkLabel(self.frame_stats, text="", font=FUENTES["pequeña"],
                                      text_color=COLORES["texto_sec"])
        self.lbl_stats.pack()

        # Tabla
        self.frame_tabla = ctk.CTkScrollableFrame(self, fg_color=COLORES["bg_panel"])
        self.frame_tabla.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Header
        self._crear_header()

        # Footer con acciones masivas
        footer = ctk.CTkFrame(self, fg_color=COLORES["bg_panel"])
        footer.pack(fill="x", pady=10)

        self.lbl_seleccionados = ctk.CTkLabel(footer, text="0 asientos seleccionados", font=FUENTES["pequeña"],
                                              text_color=COLORES["texto_sec"])
        self.lbl_seleccionados.pack(side="left", padx=10, pady=10)

        frame_acciones = ctk.CTkFrame(footer, fg_color="transparent")
        frame_acciones.pack(side="right", padx=10, pady=10)

        self.btn_eliminar_sel = Boton(frame_acciones, "🗑 Eliminar Seleccionados", variante="peligro",
                                      command=self._eliminar_seleccionados)
        self.btn_eliminar_sel.pack(side="left", padx=5)
        self.btn_eliminar_sel.configure(state="disabled")

        self.btn_restaurar_sel = Boton(frame_acciones, "♻️ Restaurar Seleccionados", variante="info",
                                       command=self._restaurar_seleccionados)
        self.btn_restaurar_sel.pack(side="left", padx=5)
        self.btn_restaurar_sel.configure(state="disabled")

        self.asientos_seleccionados = set()
        self._cargar_datos()

    def _crear_header(self):
        header = ctk.CTkFrame(self.frame_tabla, fg_color=COLORES["bg_principal"], height=35)
        header.pack(fill="x", pady=(0, 5))
        header.pack_propagate(False)

        # Checkbox para seleccionar todos
        self.var_sel_todos = ctk.BooleanVar(value=False)
        chk_todos = ctk.CTkCheckBox(header, text="", variable=self.var_sel_todos,
                                     width=30, command=self._seleccionar_todos)
        chk_todos.pack(side="left", padx=5, pady=5)

        columns = [
            ("N° Asiento", 80),
            ("Fecha", 90),
            ("Cuenta", 150),
            ("Descripción", 200),
            ("Debe", 80),
            ("Haber", 80),
            ("Estado", 80),
            ("Acción", 80)
        ]

        for col, width in columns:
            ctk.CTkLabel(header, text=col, font=FUENTES["pequeña"],
                        text_color=COLORES["texto_sec"], width=width).pack(side="left", padx=5, pady=5)

    def _cargar_datos(self):
        # Limpiar filas existentes (excepto header)
        for widget in self.frame_tabla.winfo_children()[1:]:
            widget.destroy()

        self.asientos_seleccionados.clear()
        self._actualizar_botones_seleccion()

        busqueda = self.entry_busqueda.get()
        estado = self.combobox_estado.get()

        # Construir SQL - agrupar por numero_asiento para mostrar resumen
        sql = """
            SELECT
                ld.numero_asiento,
                ld.fecha,
                COUNT(DISTINCT ld.id) as num_lineas,
                SUM(ld.debe) as total_debe,
                SUM(ld.haber) as total_haber,
                MAX(ld.eliminado) as eliminado,
                MAX(ld.fecha_eliminado) as fecha_eliminado,
                MAX(ld.motivo_eliminado) as motivo_eliminado,
                GROUP_CONCAT(DISTINCT p.descripcion) as cuentas
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

        sql += " GROUP BY ld.numero_asiento, ld.fecha ORDER BY ld.fecha DESC, ld.numero_asiento DESC"

        filas = DB.fetchall(sql, tuple(params))

        # Actualizar stats
        total_activos = sum(1 for f in filas if f['eliminado'] == 0)
        total_eliminados = sum(1 for f in filas if f['eliminado'] == 1)
        self.lbl_stats.configure(text=f"Mostrando: {len(filas)} asientos ({total_activos} activos, {total_eliminados} eliminados)")

        for fila in filas:
            self._crear_fila_asiento(fila)

    def _crear_fila_asiento(self, datos):
        numero = datos['numero_asiento']
        eliminado = datos['eliminado'] == 1

        bg = COLORES["bg_fila_impar"] if eliminado else COLORES["bg_fila_par"]
        frame_fila = ctk.CTkFrame(self.frame_tabla, fg_color=bg, height=40)
        frame_fila.pack(fill="x", pady=1)
        frame_fila.pack_propagate(False)

        # Checkbox de selección
        var_sel = ctk.BooleanVar(value=False)
        def on_check(*args, num=numero, var=var_sel):
            if var.get():
                self.asientos_seleccionados.add(num)
            else:
                self.asientos_seleccionados.discard(num)
            self._actualizar_botones_seleccion()

        var_sel.trace_add("write", on_check)
        chk = ctk.CTkCheckBox(frame_fila, text="", variable=var_sel, width=30)
        chk.pack(side="left", padx=5, pady=5)

        # Datos del asiento
        LabelSeleccionable(frame_fila, text=str(numero), font=FUENTES["pequeña"],
                    text_color=COLORES["amarillo"], width=80).pack(side="left", padx=5)

        LabelSeleccionable(frame_fila, text=datos['fecha'], font=FUENTES["pequeña"],
                    text_color=COLORES["texto"], width=90).pack(side="left", padx=5)

        # Cuentas (resumen)
        cuentas_text = datos['cuentas'][:30] + "..." if len(datos['cuentas']) > 30 else datos['cuentas']
        LabelSeleccionable(frame_fila, text=cuentas_text, font=FUENTES["pequeña"],
                    text_color=COLORES["texto_sec"], width=150).pack(side="left", padx=5)

        # Descripción
        desc_text = datos.get('motivo_eliminado', '') or f"{datos['num_lineas']} líneas"
        LabelSeleccionable(frame_fila, text=desc_text, font=FUENTES["pequeña"],
                    text_color=COLORES["texto_sec"], width=200).pack(side="left", padx=5)

        # Debe
        LabelSeleccionable(frame_fila, text=f"S/ {datos['total_debe']:,.2f}" if datos['total_debe'] else "",
                    font=FUENTES["pequeña"], text_color=COLORES["verde"], width=80).pack(side="left", padx=5)

        # Haber
        LabelSeleccionable(frame_fila, text=f"S/ {datos['total_haber']:,.2f}" if datos['total_haber'] else "",
                    font=FUENTES["pequeña"], text_color=COLORES["morado"], width=80).pack(side="left", padx=5)

        # Estado
        estado_text = "ELIMINADO" if eliminado else "ACTIVO"
        estado_color = COLORES["rojo"] if eliminado else COLORES["verde"]
        ctk.CTkLabel(frame_fila, text=estado_text, font=FUENTES["pequeña"],
                    text_color=estado_color, width=80).pack(side="left", padx=5)

        # Botón de acción
        if eliminado:
            btn_accion = Boton(frame_fila, "♻️ Restaurar", variante="info", width=80, font=FUENTES["pequeña"],
                               command=lambda n=numero: self._restaurar_asiento(n))
        else:
            btn_accion = Boton(frame_fila, "🗑 Eliminar", variante="peligro", width=80, font=FUENTES["pequeña"],
                               command=lambda n=numero: self._eliminar_asiento(n))
        btn_accion.pack(side="left", padx=5)

    def _seleccionar_todos(self):
        if self.var_sel_todos.get():
            # Seleccionar todos los visibles
            for widget in self.frame_tabla.winfo_children()[1:]:
                for child in widget.winfo_children():
                    if isinstance(child, ctk.CTkCheckBox):
                        child.select()
        else:
            # Deseleccionar todos
            for widget in self.frame_tabla.winfo_children()[1:]:
                for child in widget.winfo_children():
                    if isinstance(child, ctk.CTkCheckBox):
                        child.deselect()

    def _actualizar_botones_seleccion(self):
        cantidad = len(self.asientos_seleccionados)
        self.lbl_seleccionados.configure(text=f"{cantidad} asiento(s) seleccionado(s)")

        estado_actual = self.combobox_estado.get()

        if cantidad > 0:
            if estado_actual == "Eliminados":
                self.btn_restaurar_sel.configure(state="normal")
                self.btn_eliminar_sel.configure(state="disabled")
            elif estado_actual == "Activos":
                self.btn_restaurar_sel.configure(state="disabled")
                self.btn_eliminar_sel.configure(state="normal")
            else:  # Todos
                self.btn_restaurar_sel.configure(state="normal")
                self.btn_eliminar_sel.configure(state="normal")
        else:
            self.btn_restaurar_sel.configure(state="disabled")
            self.btn_eliminar_sel.configure(state="disabled")

    def _eliminar_asiento(self, numero_asiento):
        def confirmar_eliminar(motivo=""):
            try:
                hoy = datetime.now().strftime("%Y-%m-%d")
                DB.execute("""
                    UPDATE libro_diario
                    SET eliminado = 1,
                        fecha_eliminado = ?,
                        motivo_eliminado = ?
                    WHERE numero_asiento = ?
                """, (hoy, motivo or "Eliminado desde historial", numero_asiento))

                SistemaToast().mostrar(f"Asiento N° {numero_asiento} eliminado", "exito")
                self._cargar_datos()
            except Exception as e:
                SistemaToast().mostrar(f"Error: {str(e)}", "error")

        # Modal para pedir motivo
        modal = Modal(self.winfo_toplevel(), "Confirmar Eliminación", ancho=350, alto=350)
        ctk.CTkLabel(modal.frame_contenido, text=f"¿Eliminar el asiento N° {numero_asiento}?",
                     font=FUENTES["normal"]).pack(pady=10)
        ctk.CTkLabel(modal.frame_contenido, text="Motivo (opcional):",
                     font=FUENTES["pequeña"], text_color=COLORES["texto_sec"]).pack()

        entry_motivo = Entrada(modal.frame_contenido, placeholder="Ej: Error de registro")
        entry_motivo.pack(pady=5, padx=20, fill="x")

        def on_confirmar():
            confirmar_eliminar(entry_motivo.get())
            modal.destroy()

        def on_cancelar():
            modal.destroy()

        Boton(modal.frame_contenido, "Eliminar", variante="peligro", command=on_confirmar).pack(pady=10)
        Boton(modal.frame_contenido, "Cancelar", variante="fantasma", command=on_cancelar).pack()

    def _restaurar_asiento(self, numero_asiento):
        try:
            DB.execute("""
                UPDATE libro_diario
                SET eliminado = 0,
                    fecha_eliminado = NULL,
                    motivo_eliminado = NULL
                WHERE numero_asiento = ?
            """, (numero_asiento,))

            SistemaToast().mostrar(f"Asiento N° {numero_asiento} restaurado", "exito")
            self._cargar_datos()
        except Exception as e:
            SistemaToast().mostrar(f"Error: {str(e)}", "error")

    def _eliminar_seleccionados(self):
        if not self.asientos_seleccionados:
            return

        def confirmar():
            try:
                hoy = datetime.now().strftime("%Y-%m-%d")
                for numero in self.asientos_seleccionados:
                    DB.execute("""
                        UPDATE libro_diario
                        SET eliminado = 1,
                            fecha_eliminado = ?,
                            motivo_eliminado = ?
                        WHERE numero_asiento = ?
                    """, (hoy, "Eliminado en batch desde historial", numero))

                SistemaToast().mostrar(f"{len(self.asientos_seleccionados)} asiento(s) eliminado(s)", "exito")
                self.asientos_seleccionados.clear()
                self._cargar_datos()
            except Exception as e:
                SistemaToast().mostrar(f"Error: {str(e)}", "error")

        # Modal de confirmación
        modal = Modal(self.winfo_toplevel(), "Confirmar Eliminación Masiva", ancho=400, alto=300)
        ctk.CTkLabel(modal.frame_contenido,
                     text=f"¿Eliminar {len(self.asientos_seleccionados)} asiento(s)?",
                     font=FUENTES["subtit"]).pack(pady=20)

        Boton(modal.frame_contenido, "Sí, Eliminar", variante="peligro", command=lambda: [confirmar(), modal.destroy()]).pack(pady=5)
        Boton(modal.frame_contenido, "Cancelar", variante="fantasma", command=modal.destroy).pack()

    def _restaurar_seleccionados(self):
        if not self.asientos_seleccionados:
            return

        try:
            for numero in self.asientos_seleccionados:
                DB.execute("""
                    UPDATE libro_diario
                    SET eliminado = 0,
                        fecha_eliminado = NULL,
                        motivo_eliminado = NULL
                    WHERE numero_asiento = ?
                """, (numero,))

            SistemaToast().mostrar(f"{len(self.asientos_seleccionados)} asiento(s) restaurado(s)", "exito")
            self.asientos_seleccionados.clear()
            self._cargar_datos()
        except Exception as e:
            SistemaToast().mostrar(f"Error: {str(e)}", "error")

    def _limpiar_filtros(self):
        self.entry_busqueda.delete(0, "end")
        self.combobox_estado.set("Activos")
        self.var_sel_todos.set(False)
        self._cargar_datos()
