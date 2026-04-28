import customtkinter as ctk
from datetime import datetime
import logging
from ui.tema import COLORES, FUENTES
from ui.componentes.boton import Boton
from ui.componentes.entrada import Entrada
from ui.componentes.badge import Badge
from ui.componentes.toast import SistemaToast
from ui.componentes.label_seleccionable import LabelSeleccionable, agregar_menu_contextual
from core.db import DB
import core.clasificador as Clasificador
import core.motor_contable as MotorContable
import threading

class VistaRegistrar(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=COLORES["bg_principal"])
        self.grid_rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=35)
        self.columnconfigure(1, weight=65)
        
        self.filas_asiento = []
        self.grabando = False
        
        self.panel_izquierdo = ctk.CTkScrollableFrame(self, fg_color=COLORES["bg_principal"])
        self.panel_izquierdo.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        
        self._construir_columna_entrada()
        self._construir_columna_confirmacion()
        self._construir_columna_preview()
        
        # Agregar 2 filas iniciales
        self._agregar_fila()
        self._agregar_fila()
    
    def _construir_columna_entrada(self):
        col_entrada = ctk.CTkFrame(self.panel_izquierdo, fg_color=COLORES["bg_principal"])
        col_entrada.pack(fill="x", padx=0, pady=(0, 10))
        
        # Título
        ctk.CTkLabel(col_entrada, text="Registrar Asiento", font=FUENTES["titulo"],
                     text_color=COLORES["amarillo"]).pack(pady=(0, 5))
        ctk.CTkLabel(col_entrada, text="Ingresa el asiento por texto, voz, imagen o PDF",
                     font=FUENTES["pequeña"], text_color=COLORES["texto_sec"]).pack(pady=(0, 20))
        
        # Tabview con altura fija para que no redimensione al cambiar tab
        self.tabview = ctk.CTkTabview(col_entrada, fg_color=COLORES["bg_panel"], height=400)
        self.tabview.pack(fill="both", expand=True)
        self.tabview.pack_propagate(False)
        
        self.tabview.add("✏️ Texto")
        self.tabview.add("🎤 Voz")
        self.tabview.add("🖼️ Imagen")
        self.tabview.add("📄 PDF")
        
        self.tabview.set("✏️ Texto")
        self.tabview._segmented_button.configure(
            fg_color=COLORES["bg_panel"],
            selected_color=COLORES["verde"],
            selected_hover_color=COLORES["verde"],
            unselected_color=COLORES["bg_panel"],
            text_color=COLORES["texto_sec"],
        )
        
        self._construir_tab_texto()
        self._construir_tab_voz()
        self._construir_tab_imagen()
        self._construir_tab_pdf()
    
    def _construir_tab_texto(self):
        tab = self.tabview.tab("✏️ Texto")
        
        ctk.CTkLabel(tab, text="DESCRIPCIÓN DEL ASIENTO", font=FUENTES["pequeña"],
                     text_color=COLORES["texto_sec"]).pack(anchor="w", pady=(10, 5))
        
        self.textbox_descripcion = ctk.CTkTextbox(tab, height=120, fg_color=COLORES["bg_input"],
                                                   text_color=COLORES["texto"], font=FUENTES["normal"])
        self.textbox_descripcion.pack(fill="x", pady=(0, 10))
        self.textbox_descripcion.insert("1.0", "Ejemplo: Compra de mercadería por S/ 5,000 al contado")
        self.textbox_descripcion.bind("<FocusIn>", self._limpiar_placeholder)
        agregar_menu_contextual(self.textbox_descripcion)
        
        ctk.CTkFrame(tab, height=1, fg_color=COLORES["borde"]).pack(fill="x", pady=15)

        self.btn_clasificar = Boton(tab, "🔍 Clasificar", variante="primario", command=self._clasificar)
        self.btn_clasificar.pack(fill="x", pady=10)
    
    def _construir_tab_voz(self):
        tab = self.tabview.tab("🎤 Voz")
        
        frame_centro = ctk.CTkFrame(tab, fg_color="transparent")
        frame_centro.pack(fill="x", padx=10, pady=10)
        
        # Canvas micrófono más pequeño para no empujar layout
        self.canvas_mic = ctk.CTkCanvas(frame_centro, width=100, height=100, bg=COLORES["bg_panel"],
                                        highlightthickness=0)
        self.canvas_mic.pack(pady=10)
        self._dibujar_mic(False)
        
        self.lbl_estado_voz = ctk.CTkLabel(frame_centro, text="Haz clic para hablar",
                                          font=FUENTES["normal"], text_color=COLORES["texto_sec"])
        self.lbl_estado_voz.pack(pady=5)
        
        self.btn_grabar = Boton(frame_centro, "🎤 Iniciar grabación", variante="primario",
                                command=self._toggle_grabacion)
        self.btn_grabar.pack(pady=5, fill="x")
        
        self.textbox_transcripcion = ctk.CTkTextbox(tab, height=100, fg_color=COLORES["bg_panel"],
                                                    text_color=COLORES["texto"], font=FUENTES["pequeña"])
        self.textbox_transcripcion.pack(fill="x", padx=20, pady=10)
        self.textbox_transcripcion.configure(state="disabled")
        self.textbox_transcripcion.tag_config("keyword", foreground=COLORES["bg_principal"], background=COLORES["amarillo"])
        agregar_menu_contextual(self.textbox_transcripcion)
        
        ctk.CTkLabel(tab, text="Dictado automático con IA. Habla y se registrará al instante.",
                     font=FUENTES["pequeña"], text_color=COLORES["texto_desact"]).pack(pady=(0, 5))
    
    def _construir_tab_imagen(self):
        tab = self.tabview.tab("🖼️ Imagen")
        
        self.drop_zone = ctk.CTkFrame(tab, height=130, fg_color=COLORES["bg_panel"])
        self.drop_zone.pack(fill="x", padx=20, pady=(10, 5))
        self.drop_zone.pack_propagate(False)
        
        self.lbl_imagen = ctk.CTkLabel(self.drop_zone, text="📁 Arrastra una imagen aquí",
                     font=FUENTES["normal"], text_color=COLORES["texto_sec"])
        self.lbl_imagen.pack(pady=(15, 5))
        ctk.CTkLabel(self.drop_zone, text="JPG  PNG  WEBP",
                     font=FUENTES["pequeña"], text_color=COLORES["texto_desact"]).pack(pady=0)
        
        # Opcion de portapapeles
        Boton(self.drop_zone, "📋 Pegar del portapapeles", variante="fantasma", 
              command=self._pegar_imagen_portapapeles).pack(pady=5)
        
        try:
            from tkinterdnd2 import DND_FILES
            self.drop_zone.drop_target_register(DND_FILES)
            self.drop_zone.dnd_bind('<<Drop>>', self._al_soltar_imagen)
        except ImportError:
            pass
        
        self.textbox_img_preview = ctk.CTkTextbox(tab, height=120, fg_color=COLORES["bg_input"],
                                              text_color=COLORES["texto"], font=FUENTES["pequeña"])
        self.textbox_img_preview.pack(fill="both", expand=True, padx=20, pady=(5, 10))
        self.textbox_img_preview.tag_config("keyword", foreground=COLORES["bg_principal"], background=COLORES["amarillo"])
        self.textbox_img_preview.insert("1.0", "El texto extraído aparecerá aquí...")
        
        self.ruta_imagen = None
    
    def _construir_tab_pdf(self):
        tab = self.tabview.tab("📄 PDF")
        
        self.drop_zone_pdf = ctk.CTkFrame(tab, height=130, fg_color=COLORES["bg_panel"])
        self.drop_zone_pdf.pack(fill="x", padx=20, pady=(10, 5))
        self.drop_zone_pdf.pack_propagate(False)
        
        self.lbl_pdf = ctk.CTkLabel(self.drop_zone_pdf, text="📁 Arrastra un PDF aquí",
                     font=FUENTES["normal"], text_color=COLORES["texto_sec"])
        self.lbl_pdf.pack(pady=20)
        ctk.CTkLabel(self.drop_zone_pdf, text="PDF",
                     font=FUENTES["pequeña"], text_color=COLORES["texto_desact"]).pack()
        
        try:
            from tkinterdnd2 import DND_FILES
            self.drop_zone_pdf.drop_target_register(DND_FILES)
            self.drop_zone_pdf.dnd_bind('<<Drop>>', self._al_soltar_pdf)
        except ImportError:
            pass
            
        self.textbox_pdf_preview = ctk.CTkTextbox(tab, height=120, fg_color=COLORES["bg_input"],
                                              text_color=COLORES["texto"], font=FUENTES["pequeña"])
        self.textbox_pdf_preview.pack(fill="both", expand=True, padx=20, pady=(5, 10))
        self.textbox_pdf_preview.tag_config("keyword", foreground=COLORES["bg_principal"], background=COLORES["amarillo"])
        self.textbox_pdf_preview.insert("1.0", "El texto extraído aparecerá aquí...")
        
        self.ruta_pdf = None
    
    def _construir_columna_preview(self):
        self.frame_preview = ctk.CTkScrollableFrame(self, fg_color=COLORES["bg_principal"])
        self.frame_preview.grid(row=0, column=1, sticky="nsew", padx=6)
        
        ctk.CTkLabel(self.frame_preview, text="Vista Previa", font=FUENTES["subtit"],
                     text_color=COLORES["verde"]).pack(pady=(0, 10))
        
        # Info clasificación
        self.frame_info_clasif = ctk.CTkFrame(self.frame_preview, fg_color=COLORES["bg_panel"], corner_radius=10)
        self.frame_info_clasif.pack(fill="x", pady=(0, 10))
        
        self.lbl_tipo_operacion = ctk.CTkLabel(self.frame_info_clasif, text="",
                                               font=FUENTES["normal"], text_color=COLORES["naranja"])
        self.lbl_tipo_operacion.pack(anchor="w", padx=10, pady=(10, 5))
        
        self.lbl_explicacion = ctk.CTkLabel(self.frame_info_clasif, text="",
                                            font=FUENTES["pequeña"], text_color=COLORES["texto_sec"],
                                            wraplength=320, justify="left")
        self.lbl_explicacion.pack(anchor="w", padx=10, pady=(0, 5))
        
        self.frame_badges = ctk.CTkFrame(self.frame_info_clasif, fg_color="transparent")
        self.frame_badges.pack(anchor="w", padx=10, pady=(0, 10))
        
        self.badge_fuente = Badge(self.frame_badges, "manual")
        self.badge_fuente.pack(side="left", padx=(0, 5))
        self.badge_confianza = Badge(self.frame_badges, "baja")
        self.badge_confianza.pack(side="left")
        
        self.frame_info_clasif.pack_forget()
        
        ctk.CTkFrame(self.frame_preview, height=1, fg_color=COLORES["borde"]).pack(fill="x", pady=10)
        
        # Tabla editable
        self.frame_tabla = ctk.CTkFrame(self.frame_preview, fg_color=COLORES["bg_panel"], corner_radius=10)
        self.frame_tabla.pack(fill="x", pady=(0, 10))

        toolbar_tabla = ctk.CTkFrame(self.frame_tabla, fg_color="transparent")
        toolbar_tabla.pack(fill="x", padx=10, pady=(10, 6))

        ctk.CTkLabel(toolbar_tabla, text="Líneas del asiento", font=FUENTES["normal"],
                     text_color=COLORES["texto"]).pack(side="left")

        Boton(toolbar_tabla, "+ Línea", variante="fantasma", font=FUENTES["pequeña"],
              command=self._agregar_fila).pack(side="right")
        
        # Header tabla (con columna FECHA)
        header = ctk.CTkFrame(self.frame_tabla, fg_color=COLORES["bg_principal"], height=30)
        header.pack(fill="x", padx=10)
        header.pack_propagate(False)

        anchos = {"FECHA": 90, "CTA": 30, "CÓDIGO": 60, "DESCRIPCIÓN": 280, "DEBE": 80, "HABER": 80, "": 35}
        for col in ["FECHA", "CTA", "CÓDIGO", "DESCRIPCIÓN", "DEBE", "HABER", ""]:
            ctk.CTkLabel(header, text=col, font=FUENTES["pequeña"],
                        text_color=COLORES["texto_sec"], width=anchos[col]).pack(side="left", padx=5, pady=5)
        
        # Frame para filas (expande naturalmente ya que el padre tiene scroll)
        self.frame_filas = ctk.CTkFrame(self.frame_tabla, fg_color=COLORES["bg_panel"])
        self.frame_filas.pack(fill="x", expand=False, padx=10, pady=(6, 10))
        
        ctk.CTkFrame(self.frame_preview, height=1, fg_color=COLORES["borde"]).pack(fill="x", pady=10)
        
        # Totales
        frame_totales = ctk.CTkFrame(self.frame_preview, fg_color=COLORES["bg_panel"], corner_radius=10)
        frame_totales.pack(fill="x", pady=5)
        
        ctk.CTkLabel(frame_totales, text="TOTAL DEBE:", font=FUENTES["pequeña"],
                    text_color=COLORES["texto_sec"]).grid(row=0, column=0, sticky="w", padx=10, pady=5)
        self.lbl_total_debe = ctk.CTkLabel(frame_totales, text="S/ 0.00",
                                           font=FUENTES["bold"], text_color=COLORES["verde"])
        self.lbl_total_debe.grid(row=0, column=1, sticky="e", padx=10, pady=5)
        
        ctk.CTkLabel(frame_totales, text="TOTAL HABER:", font=FUENTES["pequeña"],
                    text_color=COLORES["texto_sec"]).grid(row=1, column=0, sticky="w", padx=10, pady=5)
        self.lbl_total_haber = ctk.CTkLabel(frame_totales, text="S/ 0.00",
                                            font=FUENTES["bold"], text_color=COLORES["morado"])
        self.lbl_total_haber.grid(row=1, column=1, sticky="e", padx=10, pady=5)
        
        self.lbl_cuadre = ctk.CTkLabel(frame_totales, text="✓ CUADRADO",
                                      font=FUENTES["normal"], text_color=COLORES["verde"])
        self.lbl_cuadre.grid(row=2, column=0, columnspan=2, sticky="ew", padx=10, pady=5)
        
        ctk.CTkFrame(self.frame_preview, height=1, fg_color=COLORES["borde"]).pack(fill="x", pady=10)

        # Descripción general del asiento (se aplica a todos)
        frame_asiento = ctk.CTkFrame(self.frame_preview, fg_color=COLORES["bg_panel"], corner_radius=10)
        frame_asiento.pack(fill="x", pady=5)
        frame_asiento.columnconfigure(1, weight=1)

        ctk.CTkLabel(frame_asiento, text="DESCRIPCIÓN GENERAL:", font=FUENTES["pequeña"],
                    text_color=COLORES["texto_sec"]).grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.entry_desc_asiento = Entrada(frame_asiento, placeholder="Descripción para todos los asientos")
        self.entry_desc_asiento.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
    
    def _construir_columna_confirmacion(self):
        col_conf = ctk.CTkFrame(self.panel_izquierdo, fg_color=COLORES["bg_principal"])
        col_conf.pack(fill="x", padx=0, pady=(10, 0))
        
        card = ctk.CTkFrame(col_conf, fg_color=COLORES["bg_panel"], corner_radius=8)
        card.pack(fill="both", expand=True, padx=0, pady=0)
        
        ctk.CTkLabel(card, text="Confirmar Registro", font=FUENTES["subtit"],
                     text_color=COLORES["amarillo"]).pack(pady=(15, 10))
        
        # Checklist
        self.frame_checklist = ctk.CTkFrame(card, fg_color="transparent")
        self.frame_checklist.pack(fill="x", padx=20, pady=5)
        
        self._crear_check_item("Partida doble cuadrada", lambda: self._verificar_cuadre())
        self._crear_check_item("Fecha válida", lambda: self._verificar_fecha())
        self._crear_check_item("Mínimo 2 líneas", lambda: len(self.filas_asiento) >= 2)
        self._crear_check_item("Todas las cuentas válidas", lambda: self._verificar_cuentas())
        
        ctk.CTkFrame(card, height=1, fg_color=COLORES["borde"]).pack(fill="x", pady=10)
        
        self.btn_registrar = Boton(card, "✓ Registrar Todos", variante="primario",
                                   height=42, font=FUENTES["subtit"], command=self._registrar_todos_asientos)
        self.btn_registrar.pack(fill="x", padx=20, pady=(5, 8))
        self.btn_registrar.configure(state="disabled")
        
        Boton(card, "🗑 Limpiar todo", variante="fantasma", command=self._limpiar_todo).pack(fill="x", padx=20, pady=(0, 10))
        
        ctk.CTkFrame(card, height=1, fg_color=COLORES["borde"]).pack(fill="x", pady=5)
        
        # Historial
        ctk.CTkLabel(card, text="ÚLTIMOS HOY", font=FUENTES["pequeña"],
                    text_color=COLORES["texto_sec"]).pack(anchor="w", padx=20, pady=(5, 2))
        
        self.frame_historial = ctk.CTkFrame(card, fg_color="transparent")
        self.frame_historial.pack(fill="x", padx=20, pady=(0, 10))
        
        self._cargar_historial()
        

    
    def _ajustar_altura_tabla(self):
        # Ya no es necesario porque el panel principal (frame_preview) ahora es scrolleable
        pass
        
    def _crear_check_item(self, texto, condicion_fn):
        frame = ctk.CTkFrame(self.frame_checklist, fg_color="transparent")
        frame.pack(fill="x", pady=3)
        
        lbl_check = ctk.CTkLabel(frame, text="✗", font=("Consolas", 12), text_color=COLORES["rojo"])
        lbl_check.pack(side="left", padx=(0, 8))
        
        lbl_texto = ctk.CTkLabel(frame, text=texto, font=FUENTES["pequeña"], text_color=COLORES["texto"])
        lbl_texto.pack(side="left")
        
        def actualizar():
            if condicion_fn():
                lbl_check.configure(text="✓", text_color=COLORES["verde"])
            else:
                lbl_check.configure(text="✗", text_color=COLORES["rojo"])
        
        frame.actualizar = actualizar
        return frame
    
    def _agregar_fila(self, cuenta_codigo=None, descripcion="", debe=0, haber=0, fecha=None):
        idx = len(self.filas_asiento)
        bg = COLORES["bg_fila_par"] if idx % 2 == 0 else COLORES["bg_fila_impar"]

        frame_fila = ctk.CTkFrame(self.frame_filas, fg_color=bg, height=40)
        frame_fila.pack(fill="x", pady=2)
        frame_fila.pack_propagate(False)

        # Fecha (ahora cada fila tiene su fecha)
        entry_fecha_fila = Entrada(frame_fila, width=90, placeholder="DD/MM/YYYY")
        entry_fecha_fila.pack(side="left", padx=5)
        if fecha:
            # Convertir de YYYY-MM-DD a DD/MM/YYYY
            try:
                fecha_dt = datetime.strptime(fecha, "%Y-%m-%d")
                entry_fecha_fila.insert(0, fecha_dt.strftime("%d/%m/%Y"))
            except:
                entry_fecha_fila.insert(0, fecha)
        else:
            entry_fecha_fila.insert(0, datetime.now().strftime("%d/%m/%Y"))
        entry_fecha_fila.bind("<KeyRelease>", lambda e: self._actualizar_checklist())

        # N° fila
        lbl_nro = ctk.CTkLabel(frame_fila, text=str(idx + 1), font=FUENTES["pequeña"],
                               text_color=COLORES["texto_desact"], width=30)
        lbl_nro.pack(side="left", padx=5)

        # Código
        entry_codigo = Entrada(frame_fila, width=60, placeholder="Código")
        entry_codigo.pack(side="left", padx=5)
        if cuenta_codigo:
            entry_codigo.insert(0, str(cuenta_codigo))
        entry_codigo.bind("<KeyRelease>", lambda e: self._buscar_cuenta(entry_codigo))

        # Descripción (ahora seleccionable)
        lbl_desc = LabelSeleccionable(frame_fila, text=descripcion[:40] + "..." if len(descripcion) > 40 else descripcion,
                               font=FUENTES["normal"], text_color=COLORES["texto"], width=270)
        lbl_desc.pack(side="left", padx=5)

        # Debe
        entry_debe = Entrada(frame_fila, width=80, placeholder="0.00")
        entry_debe.pack(side="left", padx=5)
        if debe:
            entry_debe.insert(0, str(debe))
        entry_debe.bind("<KeyRelease>", lambda e: self._actualizar_totales())

        # Haber
        entry_haber = Entrada(frame_fila, width=80, placeholder="0.00")
        entry_haber.pack(side="left", padx=5)
        if haber:
            entry_haber.insert(0, str(haber))
        entry_haber.bind("<KeyRelease>", lambda e: self._actualizar_totales())

        # Botón eliminar
        btn_eliminar = ctk.CTkButton(frame_fila, text="✕", width=28, height=28,
                                    fg_color="transparent", text_color=COLORES["rojo"],
                                    hover_color=COLORES["rojo"], font=("Consolas", 12),
                                    command=lambda: self._eliminar_fila(frame_fila))
        btn_eliminar.pack(side="left", padx=5)

        self.filas_asiento.append({
            "frame": frame_fila,
            "entry_fecha": entry_fecha_fila,
            "entry_codigo": entry_codigo,
            "lbl_desc": lbl_desc,
            "entry_debe": entry_debe,
            "entry_haber": entry_haber,
            "btn_eliminar": btn_eliminar
        })

        self._ajustar_altura_tabla()
        self._actualizar_totales()
        self._actualizar_checklist()
    
    def _eliminar_fila(self, frame_fila):
        if len(self.filas_asiento) <= 2:
            SistemaToast().mostrar("Mínimo 2 líneas requeridas", "advertencia")
            return
        
        for i, fila in enumerate(self.filas_asiento):
            if fila["frame"] == frame_fila:
                fila["frame"].destroy()
                self.filas_asiento.pop(i)
                break
        
        # Reenumerar
        for i, fila in enumerate(self.filas_asiento):
            for widget in fila["frame"].winfo_children():
                if isinstance(widget, ctk.CTkLabel) and widget.cget("text").isdigit():
                    widget.configure(text=str(i + 1))
        
        self._ajustar_altura_tabla()
        self._actualizar_totales()
        self._actualizar_checklist()
    
    def _limpiar_placeholder(self, event):
        if self.textbox_descripcion.get("1.0", "end-1c") == "Ejemplo: Compra de mercadería por S/ 5,000 al contado":
            self.textbox_descripcion.delete("1.0", "end")
    
    def _clasificar(self, origen="texto"):
        logging.info("=" * 80)
        logging.info(f"INICIANDO CLASIFICACIÓN DESDE UI - ORIGEN: {origen.upper()}")
        logging.info("=" * 80)
        
        if origen == "imagen":
            texto = self.textbox_img_preview.get("1.0", "end-1c").strip()
        elif origen == "pdf":
            texto = self.textbox_pdf_preview.get("1.0", "end-1c").strip()
        elif origen == "voz":
            texto = self.textbox_transcripcion.get("1.0", "end-1c").strip()
        else:
            texto = self.textbox_descripcion.get("1.0", "end-1c").strip()
        
        logging.info(f"TEXTO A CLASIFICAR ({len(texto)} caracteres):")
        logging.info("-" * 80)
        logging.info(texto if texto else "[TEXTO VACÍO]")
        logging.info("-" * 80)
            
        if not texto or texto == "Ejemplo: Compra de mercadería por S/ 5,000 al contado":
            logging.warning("Texto vacío o es el placeholder de ejemplo")
            SistemaToast().mostrar("Escribe una descripción o procesa un archivo", "advertencia")
            return
        
        self.btn_clasificar.set_cargando(True)

        def tarea():
            try:
                resultado = Clasificador.Clasificador().clasificar(texto, None)
                
                # Log del resultado de clasificación
                logging.info("=" * 80)
                logging.info("RESULTADO DE CLASIFICACIÓN EN UI")
                logging.info("=" * 80)
                logging.info(f"Fuente: {resultado.get('fuente', 'N/A')}")
                logging.info(f"Confianza: {resultado.get('confianza', 'N/A')}")
                logging.info(f"Explicación: {resultado.get('explicacion', 'N/A')}")
                logging.info(f"Fechas detectadas: {resultado.get('fechas_detectadas', [])}")
                logging.info(f"Palabras encontradas: {resultado.get('palabras_encontradas', [])}")
                logging.info(f"Total líneas: {len(resultado.get('lineas', []))}")
                for i, linea in enumerate(resultado.get('lineas', []), 1):
                    logging.info(f"  Línea {i}: Cuenta {linea['cuenta_codigo']} - {linea['descripcion'][:40]} - Debe: {linea['debe']:.2f} - Haber: {linea['haber']:.2f}")
                logging.info("=" * 80)
                
                self.after(0, lambda: self._actualizar_preview(resultado, origen))
            except Exception as e:
                logging.error(f"ERROR EN CLASIFICACIÓN: {str(e)}", exc_info=True)
                self.after(0, lambda: SistemaToast().mostrar(f"Error: {str(e)}", "error"))
            finally:
                self.after(0, lambda: self.btn_clasificar.set_cargando(False))
        
        threading.Thread(target=tarea, daemon=True).start()
    
    def _actualizar_preview(self, resultado, origen="texto"):
        # Guardar asientos para registro
        self.asientos_generados = resultado.get("asientos", [])

        # Si no hay asientos pero hay líneas (compatibilidad hacia atrás)
        if not self.asientos_generados and resultado.get("lineas"):
            self.asientos_generados = [{
                "fecha": None,
                "descripcion": "Asiento",
                "lineas": resultado["lineas"],
                "fuente": resultado.get("fuente", "mixta"),
                "confianza": resultado.get("confianza", "media")
            }]

        if not self.asientos_generados:
            SistemaToast().mostrar("No se generaron asientos válidos", "advertencia")
            return

        # Mostrar TODOS los asientos en una sola tabla consolidada
        self._mostrar_todos_asientos()

        # Highlight keywords
        palabras = resultado.get("palabras_encontradas", [])
        textbox = None
        if origen == "imagen":
            textbox = self.textbox_img_preview
        elif origen == "pdf":
            textbox = self.textbox_pdf_preview
        elif origen == "voz":
            textbox = self.textbox_transcripcion
            self.textbox_transcripcion.configure(state="normal")
        elif origen == "texto":
            textbox = self.textbox_descripcion

        if textbox and palabras:
            textbox.tag_remove("keyword", "1.0", "end")
            contenido = textbox.get("1.0", "end-1c").lower()
            for palabra in palabras:
                idx = 0
                while True:
                    idx = contenido.find(palabra, idx)
                    if idx == -1: break
                    prefix = contenido[:idx]
                    linea = prefix.count('\n') + 1
                    col = len(prefix.split('\n')[-1])
                    start = f"{linea}.{col}"
                    end = f"{linea}.{col + len(palabra)}"
                    textbox.tag_add("keyword", start, end)
                    idx += len(palabra)

        if origen == "voz" and textbox:
            self.textbox_transcripcion.configure(state="disabled")
    
    def _mostrar_todos_asientos(self):
        """Mostrar TODOS los asientos en una sola tabla consolidada"""
        # Limpiar filas actuales
        for fila in self.filas_asiento:
            fila["frame"].destroy()
        self.filas_asiento = []

        total_asientos = len(self.asientos_generados)

        # Actualizar info general
        fuentes = set(a.get("fuente", "mixta") for a in self.asientos_generados)
        confianzas = set(a.get("confianza", "media") for a in self.asientos_generados)
        self.lbl_tipo_operacion.configure(text=f"{total_asientos} ASIENTO{'S' if total_asientos > 1 else ''}")

        # Descripción consolidada
        descs = [a.get('descripcion', '')[:40] for a in self.asientos_generados]
        self.lbl_explicacion.configure(text=" | ".join(descs[:3]) + ("..." if len(descs) > 3 else ""))

        for widget in self.frame_badges.winfo_children():
            widget.destroy()
        self.badge_fuente = Badge(self.frame_badges, list(fuentes)[0] if len(fuentes) == 1 else "mixta")
        self.badge_confianza = Badge(self.frame_badges, list(confianzas)[0] if len(confianzas) == 1 else "media")
        self.badge_fuente.pack(side="left", padx=(0, 5))
        self.badge_confianza.pack(side="left")

        # Badge con cantidad total
        badge_total = Badge(self.frame_badges, f"Total: {total_asientos}")
        badge_total.pack(side="left", padx=(5, 0))

        self.frame_info_clasif.pack(fill="x", pady=(0, 10))

        # Agregar TODAS las líneas de TODOS los asientos con su fecha respectiva
        for idx_asiento, asiento in enumerate(self.asientos_generados):
            fecha_asiento = asiento.get("fecha")
            for linea in asiento.get("lineas", []):
                self._agregar_fila(
                    cuenta_codigo=linea["cuenta_codigo"],
                    descripcion=linea["descripcion"],
                    debe=linea["debe"],
                    haber=linea["haber"],
                    fecha=fecha_asiento
                )
    
    def _crear_controles_asientos(self):
        """Ya no se usan controles de navegación - todos los asientos se muestran juntos"""
        # Eliminar controles anteriores si existen (de versiones previas)
        if hasattr(self, 'frame_nav_asientos'):
            self.frame_nav_asientos.destroy()
        # Ya no creamos navegación - todos los asientos se muestran en una sola tabla
    
    def _actualizar_estado_botones_nav(self):
        """Método obsoleto - ya no hay navegación entre asientos"""
        pass
    
    def _asiento_anterior(self):
        """Mostrar asiento anterior"""
        if self.asiento_actual_idx > 0:
            self._mostrar_asiento(self.asiento_actual_idx - 1)
            self._actualizar_estado_botones_nav()
    
    def _asiento_siguiente(self):
        """Mostrar siguiente asiento"""
        if self.asiento_actual_idx < len(self.asientos_generados) - 1:
            self._mostrar_asiento(self.asiento_actual_idx + 1)
            self._actualizar_estado_botones_nav()
    
    def _registrar_todos_asientos(self):
        """Registrar TODAS las líneas de la tabla como asientos (agrupando por fecha)"""
        logging.info("=" * 80)
        logging.info("INICIANDO REGISTRO DE TODOS LOS ASIENTOS")
        logging.info(f"Total filas en tabla: {len(self.filas_asiento)}")
        logging.info("=" * 80)

        self.btn_registrar.set_cargando(True, "Registrando...")

        def tarea():
            try:
                # Agrupar líneas por fecha para crear asientos separados
                from collections import defaultdict
                asientos_por_fecha = defaultdict(list)

                for i, fila in enumerate(self.filas_asiento, 1):
                    codigo = fila["entry_codigo"].get()
                    if not codigo:
                        logging.info(f"  Línea {i}: Sin código, ignorada")
                        continue

                    fecha_str = fila["entry_fecha"].get() or datetime.now().strftime("%d/%m/%Y")
                    descripcion = fila["lbl_desc"].get()
                    debe = float(fila["entry_debe"].get() or 0)
                    haber = float(fila["entry_haber"].get() or 0)

                    # Convertir fecha a YYYY-MM-DD para agrupar
                    try:
                        fecha_dt = datetime.strptime(fecha_str, "%d/%m/%Y")
                        fecha_bd = fecha_dt.strftime("%Y-%m-%d")
                    except:
                        fecha_bd = datetime.now().strftime("%Y-%m-%d")

                    linea = {
                        "cuenta_codigo": int(codigo),
                        "descripcion": descripcion,
                        "debe": debe,
                        "haber": haber
                    }
                    asientos_por_fecha[fecha_bd].append(linea)
                    logging.info(f"  Línea {i}: Cuenta {codigo} - Fecha {fecha_bd} - Debe: {debe:.2f} - Haber: {haber:.2f}")

                # Registrar un asiento por cada fecha
                exitosos = 0
                numeros_asientos = []
                for fecha_bd, lineas in asientos_por_fecha.items():
                    if not lineas:
                        continue
                    try:
                        # Verificar que el asiento cuadre por fecha
                        total_debe = sum(l['debe'] for l in lineas)
                        total_haber = sum(l['haber'] for l in lineas)

                        if abs(total_debe - total_haber) > 0.01:
                            logging.warning(f"Asiento del {fecha_bd} descuadrado: Debe {total_debe:.2f} vs Haber {total_haber:.2f}")

                        descripcion = self.entry_desc_asiento.get() or f"Asiento del {fecha_bd}"
                        num = MotorContable.MotorContable().registrar_asiento(fecha_bd, descripcion, lineas)
                        numeros_asientos.append(num)
                        logging.info(f"✓ Asiento registrado - N° {num} (Fecha: {fecha_bd}, {len(lineas)} líneas)")
                        exitosos += 1
                    except Exception as e:
                        logging.error(f"✗ Error registrando asiento del {fecha_bd}: {e}")

                mensaje = f"Registrados {exitosos} asiento(s) exitosamente"
                if numeros_asientos:
                    mensaje += f" (N° {', '.join(map(str, numeros_asientos))})"

                self.after(0, lambda: SistemaToast().mostrar(mensaje, "exito" if exitosos > 0 else "error"))
                self.after(0, self._limpiar_todo)
                self.after(0, self._cargar_historial)
            except Exception as e:
                logging.error(f"ERROR AL REGISTRAR: {str(e)}", exc_info=True)
                self.after(0, lambda: SistemaToast().mostrar(str(e), "error"))
            finally:
                self.after(0, lambda: self.btn_registrar.set_cargando(False))

        threading.Thread(target=tarea, daemon=True).start()
    
    def _buscar_cuenta(self, entry_codigo):
        codigo_str = entry_codigo.get()
        if not codigo_str or not codigo_str.isdigit():
            return
        
        try:
            codigo = int(codigo_str)
            cuenta = DB.fetchone("SELECT * FROM plan_contable WHERE codigo=?", (codigo,))
            if cuenta:
                for fila in self.filas_asiento:
                    if fila["entry_codigo"] == entry_codigo:
                        fila["lbl_desc"].configure(state="normal")
                        fila["lbl_desc"].delete(0, "end")
                        fila["lbl_desc"].insert(0, cuenta["descripcion"])
                        fila["lbl_desc"].configure(state="readonly")
                        break
        except:
            pass
    
    def _actualizar_totales(self):
        total_debe = 0
        total_haber = 0
        
        for fila in self.filas_asiento:
            try:
                debe = float(fila["entry_debe"].get() or 0)
                haber = float(fila["entry_haber"].get() or 0)
                total_debe += debe
                total_haber += haber
            except:
                pass
        
        self.lbl_total_debe.configure(text=f"S/ {total_debe:,.2f}")
        self.lbl_total_haber.configure(text=f"S/ {total_haber:,.2f}")
        
        dif = abs(total_debe - total_haber)
        if dif < 0.01:
            self.lbl_cuadre.configure(text="✓ CUADRADO", text_color=COLORES["verde"])
        else:
            self.lbl_cuadre.configure(text=f"✗ DIF: S/ {dif:.2f}", text_color=COLORES["rojo"])
        
        self._actualizar_checklist()
    
    def _actualizar_checklist(self):
        for widget in self.frame_checklist.winfo_children():
            if hasattr(widget, "actualizar"):
                widget.actualizar()
        
        # Verificar si todo está OK para habilitar botón
        cuadra = self._verificar_cuadre()
        fecha_ok = self._verificar_fecha()
        lineas_ok = len(self.filas_asiento) >= 2
        cuentas_ok = self._verificar_cuentas()
        
        if cuadra and fecha_ok and lineas_ok and cuentas_ok:
            self.btn_registrar.configure(state="normal")
        else:
            self.btn_registrar.configure(state="disabled")
    
    def _verificar_cuadre(self):
        total_debe = sum(float(f["entry_debe"].get() or 0) for f in self.filas_asiento)
        total_haber = sum(float(f["entry_haber"].get() or 0) for f in self.filas_asiento)
        return abs(total_debe - total_haber) < 0.01
    
    def _verificar_fecha(self):
        """Verificar que todas las filas con código tengan fechas válidas"""
        for fila in self.filas_asiento:
            codigo = fila["entry_codigo"].get()
            if not codigo:  # Ignorar filas sin código
                continue
            fecha = fila["entry_fecha"].get()
            try:
                datetime.strptime(fecha, "%d/%m/%Y")
            except:
                return False
        return True
    
    def _verificar_cuentas(self):
        for fila in self.filas_asiento:
            codigo = fila["entry_codigo"].get()
            if codigo:
                cuenta = DB.fetchone("SELECT * FROM plan_contable WHERE codigo=?", (codigo,))
                if not cuenta:
                    return False
        return True
    
    def _registrar_asiento(self):
        logging.info("=" * 80)
        logging.info("INICIANDO REGISTRO DE ASIENTO")
        logging.info("=" * 80)
        
        self.btn_registrar.set_cargando(True, "Registrando...")
        
        def tarea():
            try:
                lineas = []
                fecha_asiento = None
                logging.info("RECOLECTANDO LÍNEAS DEL ASIENTO:")
                for i, fila in enumerate(self.filas_asiento, 1):
                    codigo = fila["entry_codigo"].get()
                    if not codigo:
                        logging.info(f"  Línea {i}: Sin código, ignorada")
                        continue

                    descripcion_linea = fila["lbl_desc"].get()
                    debe = float(fila["entry_debe"].get() or 0)
                    haber = float(fila["entry_haber"].get() or 0)
                    fecha_linea = fila["entry_fecha"].get()

                    # Usar la primera fecha válida encontrada
                    if fecha_asiento is None and fecha_linea:
                        try:
                            datetime.strptime(fecha_linea, "%d/%m/%Y")
                            fecha_asiento = fecha_linea
                        except:
                            pass

                    linea = {
                        "cuenta_codigo": int(codigo),
                        "descripcion": descripcion_linea,
                        "debe": debe,
                        "haber": haber
                    }
                    lineas.append(linea)
                    logging.info(f"  Línea {i}: Cuenta {codigo} - {descripcion_linea[:35]} - Debe: {debe:.2f} - Haber: {haber:.2f}")

                descripcion = self.entry_desc_asiento.get()

                # Usar fecha de la primera línea o fecha actual
                if fecha_asiento:
                    fecha_dt = datetime.strptime(fecha_asiento, "%d/%m/%Y")
                    fecha_bd = fecha_dt.strftime("%Y-%m-%d")
                else:
                    fecha_bd = datetime.now().strftime("%Y-%m-%d")
                
                logging.info(f"FECHA ASIENTO: {fecha_asiento or fecha_bd} → {fecha_bd}")
                logging.info(f"DESCRIPCIÓN ASIENTO: {descripcion}")
                logging.info(f"TOTAL LÍNEAS A REGISTRAR: {len(lineas)}")
                
                total_debe = sum(l['debe'] for l in lineas)
                total_haber = sum(l['haber'] for l in lineas)
                logging.info(f"TOTAL DEBE: S/. {total_debe:.2f}")
                logging.info(f"TOTAL HABER: S/. {total_haber:.2f}")
                logging.info(f"CUADRE: {'✓ SÍ' if abs(total_debe - total_haber) < 0.01 else '✗ NO'}")
                
                logging.info("Llamando a MotorContable.registrar_asiento()...")
                num = MotorContable.MotorContable().registrar_asiento(fecha_bd, descripcion, lineas)
                
                logging.info(f"✓ ASIENTO REGISTRADO EXITOSAMENTE - NÚMERO: {num}")
                logging.info("=" * 80)
                
                self.after(0, lambda: SistemaToast().mostrar(f"Asiento N° {num} registrado correctamente", "exito"))
                self.after(0, self._limpiar_todo)
                self.after(0, self._cargar_historial)
            except Exception as e:
                logging.error(f"ERROR AL REGISTRAR ASIENTO: {str(e)}", exc_info=True)
                self.after(0, lambda: SistemaToast().mostrar(str(e), "error"))
            finally:
                self.after(0, lambda: self.btn_registrar.set_cargando(False))
        
        threading.Thread(target=tarea, daemon=True).start()
    
    def _limpiar_todo(self):
        self.textbox_descripcion.delete("1.0", "end")
        self.textbox_descripcion.insert("1.0", "Ejemplo: Compra de mercadería por S/ 5,000 al contado")

        for fila in self.filas_asiento:
            fila["frame"].destroy()
        self.filas_asiento = []

        self._agregar_fila()
        self._agregar_fila()

        self.frame_info_clasif.pack_forget()

        self.entry_desc_asiento.delete(0, "end")

        self._actualizar_totales()
        self._actualizar_checklist()
    
    def _cargar_historial(self):
        for widget in self.frame_historial.winfo_children():
            widget.destroy()
        
        hoy = datetime.now().strftime("%Y-%m-%d")
        asientos = DB.fetchall("""
            SELECT DISTINCT numero_asiento, descripcion, SUM(debe) as total
            FROM libro_diario
            WHERE fecha = ? AND eliminado = 0
            GROUP BY numero_asiento
            ORDER BY numero_asiento DESC
            LIMIT 3
        """, (hoy,))
        
        for asiento in asientos:
            card = ctk.CTkFrame(self.frame_historial, fg_color=COLORES["bg_fila_impar"],
                               corner_radius=6)
            card.pack(fill="x", pady=3)
            
            frame = ctk.CTkFrame(card, fg_color="transparent")
            frame.pack(fill="x", padx=10, pady=8)
            
            ctk.CTkLabel(frame, text=f"N° {asiento['numero_asiento']}",
                        font=FUENTES["pequeña"], text_color=COLORES["amarillo"]).pack(side="left")
            
            desc = asiento['descripcion'][:20] + "..." if len(asiento['descripcion']) > 20 else asiento['descripcion']
            ctk.CTkLabel(frame, text=desc, font=FUENTES["pequeña"],
                        text_color=COLORES["texto"]).pack(side="left", padx=10)
            
            ctk.CTkLabel(frame, text=f"S/ {asiento['total']:,.2f}",
                        font=FUENTES["pequeña"], text_color=COLORES["verde"]).pack(side="right")
    
    def _dibujar_mic(self, grabando):
        self.canvas_mic.delete("all")
        color = COLORES["rojo"] if grabando else COLORES["borde"]
        fill = COLORES["rojo"] if grabando else COLORES["bg_input"]

        self.canvas_mic.create_oval(10, 10, 90, 90, outline=color, width=3, fill=fill)
        self.canvas_mic.create_text(50, 50, text="🎤", font=("Segoe UI Emoji", 32))
    
    def _toggle_grabacion(self):
        from core.dictado import DictadoVoz
        dictado = DictadoVoz()
        
        if not dictado.disponible:
            self.animando_descarga = True
            
            def animar_btn(puntos=""):
                if not getattr(self, "animando_descarga", False):
                    return
                if len(puntos) > 3:
                    puntos = ""
                self.btn_grabar.configure(state="disabled", text=f"Descargando modelo IA (~240MB){puntos}")
                self.lbl_estado_voz.configure(text=f"Esto puede tomar varios minutos{puntos} (¡no cierre!)")
                self.after(500, lambda: animar_btn(puntos + "."))
                
            animar_btn()
            
            def on_listo():
                self.animando_descarga = False
                self.after(0, lambda: self.btn_grabar.configure(state="normal"))
                self.after(0, self._toggle_grabacion_iniciar)
                
            def on_error(err):
                self.animando_descarga = False
                self.after(0, lambda: self.btn_grabar.configure(state="normal", text="🎤 Iniciar grabación"))
                self.after(0, lambda: self.lbl_estado_voz.configure(text="Error al descargar (verifique internet)"))
                
            dictado.cargar_modelo(on_listo, on_error)
            return
            
        self._toggle_grabacion_iniciar()
        
    def _toggle_grabacion_iniciar(self):
        from core.dictado import DictadoVoz
        dictado = DictadoVoz()
        
        def cb_resultado(texto):
            self.after(0, lambda: self.textbox_transcripcion.configure(state="normal"))
            self.after(0, lambda: self.textbox_transcripcion.delete("1.0", "end"))
            self.after(0, lambda: self.textbox_transcripcion.insert("end", texto))
            self.after(0, lambda: self.textbox_transcripcion.see("end"))
            self.after(0, lambda: self.textbox_transcripcion.configure(state="disabled"))
            
            # Clasificar automáticamente
            self.after(0, lambda: self._clasificar(origen="voz"))
            
        def cb_estado(estado):
            self.after(0, lambda: self.lbl_estado_voz.configure(text=estado))
            
        dictado.toggle_grabacion(cb_resultado, cb_estado)
        
        if dictado.grabando:
            self._dibujar_mic(True)
            self.btn_grabar.configure(text="⏹ Detener grabación")
        else:
            self._dibujar_mic(False)
            self.btn_grabar.configure(text="🎤 Iniciar grabación")
    
    def _al_soltar_imagen(self, event):
        archivos = self.winfo_toplevel().tk.splitlist(event.data)
        if archivos:
            logging.info(f"Imagen arrastrada: {archivos[0]}")
            self._procesar_archivo(archivos[0], "imagen")
        
    def _al_soltar_pdf(self, event):
        archivos = self.winfo_toplevel().tk.splitlist(event.data)
        if archivos:
            logging.info(f"PDF arrastrado: {archivos[0]}")
            self._procesar_archivo(archivos[0], "pdf")
        
    def _pegar_imagen_portapapeles(self):
        try:
            from PIL import ImageGrab
            import tempfile, os
            img = ImageGrab.grabclipboard()
            if img:
                temp_dir = tempfile.gettempdir()
                ruta = os.path.join(temp_dir, 'clipboard_img.png')
                img.save(ruta, 'PNG')
                self._procesar_archivo(ruta, "imagen")
            else:
                SistemaToast().mostrar("No hay imagen en el portapapeles", "advertencia")
        except Exception as e:
            SistemaToast().mostrar(f"Error al pegar: {e}", "error")
            
    def _procesar_archivo(self, ruta, tipo):
        logging.info("=" * 80)
        logging.info(f"PROCESANDO ARCHIVO - TIPO: {tipo.upper()}")
        logging.info(f"RUTA: {ruta}")
        logging.info("=" * 80)
        
        textbox = self.textbox_img_preview if tipo == "imagen" else self.textbox_pdf_preview
        textbox.delete("1.0", "end")
        textbox.insert("1.0", f"Procesando {tipo}...")
        self.btn_clasificar.configure(state="disabled")
        
        def tarea():
            try:
                from core.ocr import OCRProcesador
                ocr = OCRProcesador()
                
                if not ocr.disponible:
                    logging.error("OCR no disponible - Tesseract no instalado")
                    self.after(0, lambda: SistemaToast().mostrar("OCR no disponible. Instala Tesseract.", "error"))
                    return
                
                if tipo == "imagen":
                    datos = ocr.procesar_imagen(ruta)
                else:
                    datos = ocr.procesar_pdf(ruta)
                
                if "error" in datos:
                    logging.error(f"Error en OCR: {datos['error']}")
                    self.after(0, lambda: SistemaToast().mostrar(f"Error OCR: {datos['error']}", "error"))
                    self.after(0, lambda: textbox.delete("1.0", "end"))
                else:
                    logging.info(f"OCR exitoso - Texto extraído: {len(datos.get('texto_raw', ''))} caracteres")
                    self.after(0, lambda d=datos: self._cargar_datos_ocr(d, tipo))
            except Exception as e:
                logging.error(f"Error en procesar_archivo: {str(e)}", exc_info=True)
                self.after(0, lambda e=e: SistemaToast().mostrar(f"Error en procesar_archivo: {str(e)}", "error"))
            finally:
                self.after(0, lambda: self.btn_clasificar.configure(state="normal"))
                
        threading.Thread(target=tarea, daemon=True).start()
        
    def _cargar_datos_ocr(self, datos, tipo):
        logging.info("=" * 80)
        logging.info(f"CARGANDO DATOS OCR EN UI - TIPO: {tipo.upper()}")
        logging.info("=" * 80)
        
        textbox = self.textbox_img_preview if tipo == "imagen" else self.textbox_pdf_preview
        textbox.delete("1.0", "end")
        textbox.insert("1.0", datos["texto_raw"])
        
        logging.info(f"Texto cargado en preview ({len(datos['texto_raw'])} caracteres)")
        
        if datos["total"] > 0:
            logging.info(f"Monto total detectado: S/. {datos['total']}")
        else:
            logging.info("No se detectó monto total")
        
        # La fecha detectada se usará directamente en el clasificador
        # para asignar a cada línea su fecha correspondiente
        SistemaToast().mostrar("Datos extraídos correctamente", "exito")
        self._clasificar(tipo)
