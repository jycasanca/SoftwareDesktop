import customtkinter as ctk
from ui.tema import COLORES, FUENTES
from ui.componentes.boton import Boton
from ui.componentes.entrada import Entrada
from ui.componentes.toast import SistemaToast
from core.db import DB


class VistaConfiguracion(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=COLORES["bg_principal"])

        ctk.CTkLabel(self, text="Configuración", font=FUENTES["titulo"],
                     text_color=COLORES["amarillo"]).pack(pady=(0, 15))

        # Layout horizontal: tabs izquierda + contenido derecha
        frame_layout = ctk.CTkFrame(self, fg_color="transparent")
        frame_layout.pack(fill="both", expand=True)

        # Tabs laterales
        frame_tabs = ctk.CTkFrame(frame_layout, fg_color=COLORES["bg_panel"], width=190)
        frame_tabs.pack(side="left", fill="y", padx=(0, 10))
        frame_tabs.pack_propagate(False)

        self._botones_tabs = {}
        tabs = [
            ("🏢  Empresa",        "empresa"),
            ("📒  Plan Contable",  "plan"),
            ("⚙  Reglas IA",      "reglas"),
            ("📖  Sinónimos",      "sinonimos"),
            ("📜  Logs del Sist.", "logs"),
        ]

        ctk.CTkLabel(frame_tabs, text="SECCIÓN", font=FUENTES["pequeña"],
                     text_color=COLORES["texto_desact"]).pack(anchor="w", padx=14, pady=(14, 4))

        for texto, clave in tabs:
            btn = ctk.CTkButton(frame_tabs, text=texto, fg_color="transparent",
                                text_color=COLORES["texto_sec"], hover_color=COLORES["bg_hover"],
                                anchor="w", font=FUENTES["normal"], height=36,
                                command=lambda c=clave: self._cargar_tab(c))
            btn.pack(fill="x", padx=8, pady=2)
            self._botones_tabs[clave] = btn

        # Área contenido
        self.frame_contenido = ctk.CTkScrollableFrame(frame_layout, fg_color=COLORES["bg_principal"])
        self.frame_contenido.pack(side="right", fill="both", expand=True)

        self._cargar_tab("empresa")

    # ─── Utilidad ───────────────────────────────────────────────────────────
    def _cargar_tab(self, clave):
        for k, btn in self._botones_tabs.items():
            btn.configure(fg_color=COLORES["bg_hover"] if k == clave else "transparent",
                          text_color=COLORES["verde"] if k == clave else COLORES["texto_sec"])
        for widget in self.frame_contenido.winfo_children():
            widget.destroy()
        getattr(self, f"_tab_{clave}")()

    def _separador(self, parent):
        ctk.CTkFrame(parent, height=1, fg_color=COLORES["borde"]).pack(fill="x", pady=8)

    # ─── TAB EMPRESA ────────────────────────────────────────────────────────
    def _tab_empresa(self):
        ctk.CTkLabel(self.frame_contenido, text="Datos de la Empresa",
                     font=FUENTES["subtit"], text_color=COLORES["amarillo"]).pack(anchor="w", pady=(0, 15))

        frame = ctk.CTkFrame(self.frame_contenido, fg_color=COLORES["bg_panel"], corner_radius=8)
        frame.pack(fill="x", pady=(0, 10))

        config = DB.fetchall("SELECT clave, valor FROM config_sistema")
        config_dict = {c['clave']: c['valor'] for c in config}

        campos = [
            ("empresa_nombre",    "Razón Social / Nombre:"),
            ("empresa_ruc",       "RUC:"),
            ("empresa_direccion", "Dirección:"),
            ("empresa_moneda",    "Símbolo de Moneda:"),
            ("tasa_ir",           "Tasa Impuesto a la Renta (%):"),
        ]

        self.entries = {}
        for clave, label in campos:
            ctk.CTkLabel(frame, text=label, font=FUENTES["normal"],
                         text_color=COLORES["texto"]).pack(anchor="w", padx=16, pady=(12, 4))
            e = Entrada(frame)
            e.pack(fill="x", padx=16, pady=(0, 4))
            e.insert(0, config_dict.get(clave, ""))
            self.entries[clave] = e

        Boton(frame, "💾  Guardar cambios", variante="primario",
              command=self._guardar_empresa).pack(pady=16)

    def _guardar_empresa(self):
        try:
            for clave, entry in self.entries.items():
                valor = entry.get()
                DB.execute(
                    "INSERT OR REPLACE INTO config_sistema (clave, valor) VALUES (?, ?)",
                    (clave, valor))
            SistemaToast().mostrar("Configuración guardada correctamente", "exito")
        except Exception as e:
            SistemaToast().mostrar(f"Error: {e}", "error")

    # ─── TAB PLAN CONTABLE ──────────────────────────────────────────────────
    def _tab_plan(self):
        ctk.CTkLabel(self.frame_contenido, text="Plan Contable",
                     font=FUENTES["subtit"], text_color=COLORES["amarillo"]).pack(anchor="w", pady=(0, 10))

        # Formulario nueva cuenta
        frame_form = ctk.CTkFrame(self.frame_contenido, fg_color=COLORES["bg_panel"], corner_radius=8)
        frame_form.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(frame_form, text="AGREGAR / EDITAR CUENTA",
                     font=FUENTES["pequeña"], text_color=COLORES["texto_desact"]).pack(anchor="w", padx=14, pady=(12, 6))

        row1 = ctk.CTkFrame(frame_form, fg_color="transparent")
        row1.pack(fill="x", padx=14, pady=4)
        row1.columnconfigure(0, weight=1)
        row1.columnconfigure(1, weight=3)

        ctk.CTkLabel(row1, text="Código:", font=FUENTES["normal"],
                     text_color=COLORES["texto"]).grid(row=0, column=0, sticky="w")
        self._plan_codigo = Entrada(row1)
        self._plan_codigo.grid(row=1, column=0, sticky="ew", padx=(0, 8))

        ctk.CTkLabel(row1, text="Descripción:", font=FUENTES["normal"],
                     text_color=COLORES["texto"]).grid(row=0, column=1, sticky="w")
        self._plan_desc = Entrada(row1)
        self._plan_desc.grid(row=1, column=1, sticky="ew")

        row2 = ctk.CTkFrame(frame_form, fg_color="transparent")
        row2.pack(fill="x", padx=14, pady=4)
        row2.columnconfigure(0, weight=1)
        row2.columnconfigure(1, weight=1)

        ctk.CTkLabel(row2, text="Tipo:", font=FUENTES["normal"],
                     text_color=COLORES["texto"]).grid(row=0, column=0, sticky="w")
        self._plan_tipo = ctk.CTkOptionMenu(
            row2, values=["activo_corriente", "activo_no_corriente",
                          "pasivo_corriente", "pasivo_no_corriente",
                          "patrimonio", "ingreso", "gasto", "costo"],
            fg_color=COLORES["bg_input"], button_color=COLORES["borde"],
            text_color=COLORES["texto"])
        self._plan_tipo.grid(row=1, column=0, sticky="ew", padx=(0, 8))

        ctk.CTkLabel(row2, text="Naturaleza:", font=FUENTES["normal"],
                     text_color=COLORES["texto"]).grid(row=0, column=1, sticky="w")
        self._plan_nat = ctk.CTkOptionMenu(
            row2, values=["deudora", "acreedora"],
            fg_color=COLORES["bg_input"], button_color=COLORES["borde"],
            text_color=COLORES["texto"])
        self._plan_nat.grid(row=1, column=1, sticky="ew")

        Boton(frame_form, "➕  Agregar cuenta", variante="primario",
              command=self._guardar_plan).pack(padx=14, pady=12, anchor="e")

        self._separador(self.frame_contenido)

        # Tabla de cuentas
        self._plan_tabla = ctk.CTkFrame(self.frame_contenido, fg_color="transparent")
        self._plan_tabla.pack(fill="x")
        self._refrescar_plan()

    def _refrescar_plan(self):
        for w in self._plan_tabla.winfo_children():
            w.destroy()

        header = ctk.CTkFrame(self._plan_tabla, fg_color=COLORES["bg_panel"], height=32)
        header.pack(fill="x")
        header.pack_propagate(False)
        for col, ancho in [("Código", 70), ("Descripción", 300), ("Tipo", 160), ("Nat.", 90), ("", 60)]:
            ctk.CTkLabel(header, text=col, font=FUENTES["pequeña"],
                         text_color=COLORES["texto_sec"], width=ancho).pack(side="left", padx=5)

        cuentas = DB.fetchall("SELECT * FROM plan_contable WHERE activa=1 ORDER BY codigo")
        for i, c in enumerate(cuentas):
            bg = COLORES["bg_fila_par"] if i % 2 == 0 else COLORES["bg_fila_impar"]
            row = ctk.CTkFrame(self._plan_tabla, fg_color=bg, height=34)
            row.pack(fill="x", pady=1)
            row.pack_propagate(False)
            ctk.CTkLabel(row, text=str(c['codigo']), font=FUENTES["pequeña"],
                         text_color=COLORES["morado"], width=70).pack(side="left", padx=5)
            ctk.CTkLabel(row, text=c['descripcion'][:40], font=FUENTES["pequeña"],
                         text_color=COLORES["texto"], width=300).pack(side="left", padx=5)
            ctk.CTkLabel(row, text=c['tipo_cuenta'], font=FUENTES["pequeña"],
                         text_color=COLORES["azul"], width=160).pack(side="left", padx=5)
            ctk.CTkLabel(row, text=c['naturaleza'][:4], font=FUENTES["pequeña"],
                         text_color=COLORES["texto_sec"], width=90).pack(side="left", padx=5)
            ctk.CTkButton(row, text="✕", width=28, height=24,
                          fg_color="transparent", text_color=COLORES["rojo"],
                          hover_color=COLORES["bg_hover"],
                          command=lambda cod=c['codigo']: self._eliminar_plan(cod)
                          ).pack(side="left", padx=4)

    def _guardar_plan(self):
        try:
            codigo = int(self._plan_codigo.get())
            desc = self._plan_desc.get().strip()
            tipo = self._plan_tipo.get()
            nat = self._plan_nat.get()
            if not desc:
                SistemaToast().mostrar("La descripción es obligatoria", "advertencia")
                return
            DB.execute(
                "INSERT OR REPLACE INTO plan_contable (codigo,descripcion,tipo_cuenta,naturaleza) VALUES(?,?,?,?)",
                (codigo, desc, tipo, nat))
            self._plan_codigo.delete(0, "end")
            self._plan_desc.delete(0, "end")
            self._refrescar_plan()
            SistemaToast().mostrar(f"Cuenta {codigo} guardada", "exito")
        except ValueError:
            SistemaToast().mostrar("El código debe ser un número", "error")
        except Exception as e:
            SistemaToast().mostrar(str(e), "error")

    def _eliminar_plan(self, codigo):
        DB.execute("UPDATE plan_contable SET activa=0 WHERE codigo=?", (codigo,))
        self._refrescar_plan()
        SistemaToast().mostrar(f"Cuenta {codigo} desactivada", "info")

    # ─── TAB REGLAS ─────────────────────────────────────────────────────────
    def _tab_reglas(self):
        ctk.CTkLabel(self.frame_contenido, text="Reglas de Clasificación IA",
                     font=FUENTES["subtit"], text_color=COLORES["amarillo"]).pack(anchor="w", pady=(0, 10))

        frame_form = ctk.CTkFrame(self.frame_contenido, fg_color=COLORES["bg_panel"], corner_radius=8)
        frame_form.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(frame_form, text="NUEVA REGLA",
                     font=FUENTES["pequeña"], text_color=COLORES["texto_desact"]).pack(anchor="w", padx=14, pady=(12, 6))

        ctk.CTkLabel(frame_form, text='Palabras clave (separadas por coma):',
                     font=FUENTES["normal"], text_color=COLORES["texto"]).pack(anchor="w", padx=14, pady=(4, 2))
        self._reg_palabras = Entrada(frame_form, placeholder_text='compra, mercaderia, inventario')
        self._reg_palabras.pack(fill="x", padx=14, pady=(0, 6))

        row = ctk.CTkFrame(frame_form, fg_color="transparent")
        row.pack(fill="x", padx=14, pady=4)
        row.columnconfigure(0, weight=1)
        row.columnconfigure(1, weight=1)

        ctk.CTkLabel(row, text='Cuentas DEBE (cód, separados por coma):',
                     font=FUENTES["normal"], text_color=COLORES["texto"]).grid(row=0, column=0, sticky="w")
        self._reg_debe = Entrada(row, placeholder_text='60, 20')
        self._reg_debe.grid(row=1, column=0, sticky="ew", padx=(0, 8))

        ctk.CTkLabel(row, text='Cuentas HABER (cód, separados por coma):',
                     font=FUENTES["normal"], text_color=COLORES["texto"]).grid(row=0, column=1, sticky="w")
        self._reg_haber = Entrada(row, placeholder_text='42, 10')
        self._reg_haber.grid(row=1, column=1, sticky="ew")

        ctk.CTkLabel(frame_form, text='Prioridad (mayor = primero):',
                     font=FUENTES["normal"], text_color=COLORES["texto"]).pack(anchor="w", padx=14, pady=(6, 2))
        self._reg_prior = Entrada(frame_form, placeholder_text='10', width=100)
        self._reg_prior.pack(anchor="w", padx=14, pady=(0, 4))
        self._reg_prior.insert(0, "10")

        Boton(frame_form, "➕  Agregar regla", variante="primario",
              command=self._guardar_regla).pack(padx=14, pady=12, anchor="e")

        self._separador(self.frame_contenido)
        self._reg_tabla = ctk.CTkFrame(self.frame_contenido, fg_color="transparent")
        self._reg_tabla.pack(fill="x")
        self._refrescar_reglas()

    def _refrescar_reglas(self):
        for w in self._reg_tabla.winfo_children():
            w.destroy()
        reglas = DB.fetchall("SELECT * FROM matriz_comportamiento WHERE activa=1 ORDER BY prioridad DESC")
        if not reglas:
            ctk.CTkLabel(self._reg_tabla, text="Sin reglas definidas",
                         font=FUENTES["normal"], text_color=COLORES["texto_sec"]).pack(pady=20)
            return

        header = ctk.CTkFrame(self._reg_tabla, fg_color=COLORES["bg_panel"], height=32)
        header.pack(fill="x")
        header.pack_propagate(False)
        for col, ancho in [("Palabras clave", 250), ("DEBE", 100), ("HABER", 100), ("Prior.", 70), ("", 50)]:
            ctk.CTkLabel(header, text=col, font=FUENTES["pequeña"],
                         text_color=COLORES["texto_sec"], width=ancho).pack(side="left", padx=5)

        for i, r in enumerate(reglas):
            bg = COLORES["bg_fila_par"] if i % 2 == 0 else COLORES["bg_fila_impar"]
            row = ctk.CTkFrame(self._reg_tabla, fg_color=bg, height=34)
            row.pack(fill="x", pady=1)
            row.pack_propagate(False)
            import json
            palabras = ", ".join(json.loads(r['palabras_clave']))[:30]
            debe = ", ".join(str(x) for x in json.loads(r['cuentas_debe']))
            haber = ", ".join(str(x) for x in json.loads(r['cuentas_haber']))
            ctk.CTkLabel(row, text=palabras, font=FUENTES["pequeña"],
                         text_color=COLORES["texto"], width=250).pack(side="left", padx=5)
            ctk.CTkLabel(row, text=debe, font=FUENTES["pequeña"],
                         text_color=COLORES["verde"], width=100).pack(side="left", padx=5)
            ctk.CTkLabel(row, text=haber, font=FUENTES["pequeña"],
                         text_color=COLORES["morado"], width=100).pack(side="left", padx=5)
            ctk.CTkLabel(row, text=str(r['prioridad']), font=FUENTES["pequeña"],
                         text_color=COLORES["amarillo"], width=70).pack(side="left", padx=5)
            ctk.CTkButton(row, text="✕", width=28, height=24,
                          fg_color="transparent", text_color=COLORES["rojo"],
                          hover_color=COLORES["bg_hover"],
                          command=lambda rid=r['id']: self._eliminar_regla(rid)
                          ).pack(side="left", padx=4)

    def _guardar_regla(self):
        import json
        try:
            palabras = [p.strip() for p in self._reg_palabras.get().split(",") if p.strip()]
            debe = [int(x.strip()) for x in self._reg_debe.get().split(",") if x.strip()]
            haber = [int(x.strip()) for x in self._reg_haber.get().split(",") if x.strip()]
            prior = int(self._reg_prior.get() or 10)
            if not palabras:
                SistemaToast().mostrar("Ingresa al menos una palabra clave", "advertencia")
                return
            DB.execute(
                "INSERT INTO matriz_comportamiento (palabras_clave,cuentas_debe,cuentas_haber,prioridad,activa) VALUES(?,?,?,?,1)",
                (json.dumps(palabras), json.dumps(debe), json.dumps(haber), prior))
            self._reg_palabras.delete(0, "end")
            self._reg_debe.delete(0, "end")
            self._reg_haber.delete(0, "end")
            self._refrescar_reglas()
            SistemaToast().mostrar("Regla guardada", "exito")
        except Exception as e:
            SistemaToast().mostrar(str(e), "error")

    def _eliminar_regla(self, rid):
        DB.execute("UPDATE matriz_comportamiento SET activa=0 WHERE id=?", (rid,))
        self._refrescar_reglas()

    # ─── TAB SINÓNIMOS ──────────────────────────────────────────────────────
    def _tab_sinonimos(self):
        ctk.CTkLabel(self.frame_contenido, text="Diccionario de Sinónimos",
                     font=FUENTES["subtit"], text_color=COLORES["amarillo"]).pack(anchor="w", pady=(0, 10))

        frame_form = ctk.CTkFrame(self.frame_contenido, fg_color=COLORES["bg_panel"], corner_radius=8)
        frame_form.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(frame_form, text="NUEVO SINÓNIMO",
                     font=FUENTES["pequeña"], text_color=COLORES["texto_desact"]).pack(anchor="w", padx=14, pady=(12, 6))

        row = ctk.CTkFrame(frame_form, fg_color="transparent")
        row.pack(fill="x", padx=14, pady=4)
        row.columnconfigure(0, weight=1)
        row.columnconfigure(1, weight=1)
        row.columnconfigure(2, weight=1)

        ctk.CTkLabel(row, text="Palabra clave:", font=FUENTES["normal"],
                     text_color=COLORES["texto"]).grid(row=0, column=0, sticky="w")
        self._sin_palabra = Entrada(row, placeholder_text="caja")
        self._sin_palabra.grid(row=1, column=0, sticky="ew", padx=(0, 8))

        ctk.CTkLabel(row, text="Término estándar:", font=FUENTES["normal"],
                     text_color=COLORES["texto"]).grid(row=0, column=1, sticky="w")
        self._sin_termino = Entrada(row, placeholder_text="efectivo")
        self._sin_termino.grid(row=1, column=1, sticky="ew", padx=(0, 8))

        ctk.CTkLabel(row, text="Código cuenta:", font=FUENTES["normal"],
                     text_color=COLORES["texto"]).grid(row=0, column=2, sticky="w")
        self._sin_codigo = Entrada(row, placeholder_text="10")
        self._sin_codigo.grid(row=1, column=2, sticky="ew")

        Boton(frame_form, "➕  Agregar sinónimo", variante="primario",
              command=self._guardar_sinonimo).pack(padx=14, pady=12, anchor="e")

        self._separador(self.frame_contenido)
        self._sin_tabla = ctk.CTkFrame(self.frame_contenido, fg_color="transparent")
        self._sin_tabla.pack(fill="x")
        self._refrescar_sinonimos()

    def _refrescar_sinonimos(self):
        for w in self._sin_tabla.winfo_children():
            w.destroy()
        sinonimos = DB.fetchall("SELECT * FROM diccionario_sinonimos ORDER BY palabra_clave")
        if not sinonimos:
            ctk.CTkLabel(self._sin_tabla, text="Sin sinónimos definidos",
                         font=FUENTES["normal"], text_color=COLORES["texto_sec"]).pack(pady=20)
            return

        header = ctk.CTkFrame(self._sin_tabla, fg_color=COLORES["bg_panel"], height=32)
        header.pack(fill="x")
        header.pack_propagate(False)
        for col, ancho in [("Palabra clave", 160), ("Término estándar", 200), ("Código", 80), ("", 50)]:
            ctk.CTkLabel(header, text=col, font=FUENTES["pequeña"],
                         text_color=COLORES["texto_sec"], width=ancho).pack(side="left", padx=5)

        for i, s in enumerate(sinonimos):
            bg = COLORES["bg_fila_par"] if i % 2 == 0 else COLORES["bg_fila_impar"]
            row = ctk.CTkFrame(self._sin_tabla, fg_color=bg, height=34)
            row.pack(fill="x", pady=1)
            row.pack_propagate(False)
            ctk.CTkLabel(row, text=s['palabra_clave'], font=FUENTES["pequeña"],
                         text_color=COLORES["verde"], width=160).pack(side="left", padx=5)
            ctk.CTkLabel(row, text=s['termino_estandar'], font=FUENTES["pequeña"],
                         text_color=COLORES["texto"], width=200).pack(side="left", padx=5)
            ctk.CTkLabel(row, text=str(s['codigo_cuenta'] or "—"), font=FUENTES["pequeña"],
                         text_color=COLORES["morado"], width=80).pack(side="left", padx=5)
            ctk.CTkButton(row, text="✕", width=28, height=24,
                          fg_color="transparent", text_color=COLORES["rojo"],
                          hover_color=COLORES["bg_hover"],
                          command=lambda sid=s['id']: self._eliminar_sinonimo(sid)
                          ).pack(side="left", padx=4)

    def _guardar_sinonimo(self):
        try:
            palabra = self._sin_palabra.get().strip().lower()
            termino = self._sin_termino.get().strip().lower()
            codigo_str = self._sin_codigo.get().strip()
            codigo = int(codigo_str) if codigo_str else None
            if not palabra or not termino:
                SistemaToast().mostrar("Palabra y término son obligatorios", "advertencia")
                return
            DB.execute(
                "INSERT INTO diccionario_sinonimos (palabra_clave,termino_estandar,codigo_cuenta) VALUES(?,?,?)",
                (palabra, termino, codigo))
            self._sin_palabra.delete(0, "end")
            self._sin_termino.delete(0, "end")
            self._sin_codigo.delete(0, "end")
            self._refrescar_sinonimos()
            SistemaToast().mostrar("Sinónimo agregado", "exito")
        except Exception as e:
            SistemaToast().mostrar(str(e), "error")

    def _eliminar_sinonimo(self, sid):
        DB.execute("DELETE FROM diccionario_sinonimos WHERE id=?", (sid,))
        self._refrescar_sinonimos()

    # ─── TAB LOGS ───────────────────────────────────────────────────────────
    def _tab_logs(self):
        ctk.CTkLabel(self.frame_contenido, text="Logs del Sistema",
                     font=FUENTES["subtit"], text_color=COLORES["amarillo"]).pack(anchor="w", pady=(0, 10))

        frame_controles = ctk.CTkFrame(self.frame_contenido, fg_color="transparent")
        frame_controles.pack(fill="x", pady=(0, 10))
        
        Boton(frame_controles, "🔄 Refrescar", variante="secundario",
              command=self._cargar_logs).pack(side="left", padx=(0, 10))
        Boton(frame_controles, "🗑 Limpiar Logs", variante="fantasma",
              command=self._limpiar_logs).pack(side="left")

        self.textbox_logs = ctk.CTkTextbox(self.frame_contenido, height=400, fg_color=COLORES["bg_panel"],
                                           text_color=COLORES["texto"], font=("Consolas", 12))
        self.textbox_logs.pack(fill="both", expand=True, pady=(0, 10))
        
        self.textbox_logs.tag_config("error", foreground=COLORES["rojo"])
        self.textbox_logs.tag_config("warning", foreground=COLORES["naranja"])
        self.textbox_logs.tag_config("info", foreground=COLORES["verde"])
        
        self._cargar_logs()
        
    def _cargar_logs(self):
        self.textbox_logs.delete("1.0", "end")
        import os
        from config import LOG_PATH
        if not os.path.exists(LOG_PATH):
            self.textbox_logs.insert("end", "No hay logs registrados.")
            return
            
        try:
            with open(LOG_PATH, "r", encoding="utf-8", errors="replace") as f:
                lineas = f.readlines()
                # Mostrar últimas 1000 líneas
                for linea in lineas[-1000:]:
                    self.textbox_logs.insert("end", linea)
            
            # Resaltar colores
            self._colorear_logs()
            # Scroll al final
            self.textbox_logs.see("end")
        except Exception as e:
            self.textbox_logs.insert("end", f"Error al leer logs: {str(e)}")
            
    def _colorear_logs(self):
        contenido = self.textbox_logs.get("1.0", "end-1c")
        # Remove tags first
        for tag in ["error", "warning", "info"]:
            self.textbox_logs.tag_remove(tag, "1.0", "end")
            
        lineas = contenido.split('\n')
        linea_idx = 1
        for linea in lineas:
            if "[ERROR]" in linea or "UI Error:" in linea:
                self.textbox_logs.tag_add("error", f"{linea_idx}.0", f"{linea_idx}.end")
            elif "[WARNING]" in linea or "UI Warning:" in linea:
                self.textbox_logs.tag_add("warning", f"{linea_idx}.0", f"{linea_idx}.end")
            elif "[INFO]" in linea:
                self.textbox_logs.tag_add("info", f"{linea_idx}.0", f"{linea_idx}.end")
            linea_idx += 1
            
    def _limpiar_logs(self):
        import os
        from config import LOG_PATH
        if os.path.exists(LOG_PATH):
            with open(LOG_PATH, "w", encoding="utf-8") as f:
                f.write("")
        self._cargar_logs()
        SistemaToast().mostrar("Logs limpiados", "exito")

