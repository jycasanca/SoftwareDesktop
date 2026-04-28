import customtkinter as ctk
from tkinterdnd2 import TkinterDnD
from ui.tema import COLORES, FUENTES, aplicar_tema
from config import APP_VERSION
from core.db import DB

class TkinterDnD_CTk(ctk.CTk, TkinterDnD.DnDWrapper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.TkdndVersion = TkinterDnD._require(self)

class VentanaPrincipal(TkinterDnD_CTk):
    def __init__(self):
        super().__init__()
        self.title("GOZU — Sistema Contable")
        self.geometry("1280x800")
        self.minsize(1024, 600)
        self.configure(fg_color=COLORES["bg_principal"])
        aplicar_tema(self)
        
        self._vista_actual = None
        self._botones_nav = {}
        
        self._construir_sidebar()
        self._construir_area_contenido()
        self._iniciar_log_global()
        self.cargar_vista("dashboard")
        
        self.protocol("WM_DELETE_WINDOW", self._al_cerrar)
        
    def _iniciar_log_global(self):
        self.bind_all("<Key>", self._log_teclado, add="+")
        self.bind_all("<Button-1>", self._log_clic, add="+")
        
    def _log_teclado(self, event):
        import logging
        if event.keysym and len(event.keysym) == 1:
            logging.info(f"UI Event: Usuario escribió letra '{event.keysym}'")
        elif getattr(event, 'keysym', None) in ("BackSpace", "Return", "Delete", "Tab", "space"):
            logging.info(f"UI Event: Presionó tecla especial '{event.keysym}'")
            
    def _log_clic(self, event):
        import logging
        try:
            widget_str = str(event.widget).split("!")[-1] or "Ventana"
            logging.info(f"UI Event: Clic de ratón en componente ({widget_str}) pos ({event.x}, {event.y})")
        except:
            pass
    
    def _construir_sidebar(self):
        sidebar = ctk.CTkFrame(self, width=220, fg_color=COLORES["bg_panel"],
                               corner_radius=0)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)
        
        # Logo
        ctk.CTkLabel(sidebar, text="GOZU", font=FUENTES["titulo"],
                     text_color=COLORES["amarillo"]).pack(pady=(20, 2))
        ctk.CTkLabel(sidebar, text="Sistema Contable", font=FUENTES["pequeña"],
                     text_color=COLORES["texto_sec"]).pack()
        
        # Separador
        ctk.CTkFrame(sidebar, height=1, fg_color=COLORES["borde"]).pack(
            fill="x", padx=16, pady=8)
        
        # Items de navegación — dentro de un frame NO expansivo
        nav_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        nav_frame.pack(fill="x", pady=(0, 8))

        items = [
            ("🏠  Dashboard",      "dashboard"),
            ("✏️   Registrar",      "registrar"),
            ("📋  Diario",         "diario"),
            ("�  Historial",      "historial"),
            ("�  Mayor",          "mayor"),
            ("⚖️   Comprobación",   "comprobacion"),
            ("📈  Balance Gral.",   "balance_general"),
            ("📉  Resultados",     "resultados"),
            ("⚙️   Configuración",  "configuracion"),
        ]
        
        for texto, clave in items:
            frame_item = ctk.CTkFrame(nav_frame, fg_color="transparent", height=36)
            frame_item.pack(fill="x", padx=6, pady=1)
            frame_item.pack_propagate(False)  # ← impide que el emoji expanda el frame

            indicador = ctk.CTkFrame(frame_item, width=3, fg_color="transparent")
            indicador.pack(side="left", fill="y")

            btn = ctk.CTkButton(
                frame_item, text=texto,
                fg_color="transparent", text_color=COLORES["texto_sec"],
                hover_color=COLORES["bg_hover"],
                anchor="w", font=FUENTES["normal"],
                height=36,
                command=lambda c=clave: self.cargar_vista(c)
            )
            btn.pack(side="left", fill="x", expand=True, padx=(6, 0))

            self._botones_nav[clave] = {"frame": frame_item, "btn": btn, "indicador": indicador}
        
        # Footer sidebar
        ctk.CTkFrame(sidebar, height=1, fg_color=COLORES["borde"]).pack(
            side="bottom", fill="x", padx=16, pady=4)
        ctk.CTkLabel(sidebar, text=f"v{APP_VERSION}",
                     font=FUENTES["pequeña"], text_color=COLORES["texto_desact"]).pack(side="bottom", pady=(0, 6))
    
    def _construir_area_contenido(self):
        self._frame_contenido = ctk.CTkFrame(self, fg_color=COLORES["bg_principal"],
                                              corner_radius=0)
        self._frame_contenido.pack(side="right", fill="both", expand=True)
    
    def cargar_vista(self, clave):
        from ui.vistas.dashboard import Dashboard
        from ui.vistas.registrar import VistaRegistrar
        from ui.vistas.diario import VistaDiario
        from ui.vistas.historial import VistaHistorial
        from ui.vistas.mayor import VistaMayor
        from ui.vistas.comprobacion import VistaComprobacion
        from ui.vistas.balance_general import VistaBalanceGeneral
        from ui.vistas.resultados import VistaResultados
        from ui.vistas.configuracion import VistaConfiguracion

        mapa_vistas = {
            "dashboard":      Dashboard,
            "registrar":      VistaRegistrar,
            "diario":         VistaDiario,
            "historial":      VistaHistorial,
            "mayor":          VistaMayor,
            "comprobacion":   VistaComprobacion,
            "balance_general":VistaBalanceGeneral,
            "resultados":     VistaResultados,
            "configuracion":  VistaConfiguracion,
        }
        
        if self._vista_actual:
            self._vista_actual.destroy()
        
        clase = mapa_vistas.get(clave)
        if clase:
            import logging
            logging.info(f"UI Event: Cambio de pantalla a '{clave.upper()}'")
            self._vista_actual = clase(self._frame_contenido)
            self._vista_actual.pack(fill="both", expand=True, padx=32, pady=24)
        
        self._actualizar_nav_activa(clave)
    
    def _actualizar_nav_activa(self, clave_activa):
        for clave, widgets in self._botones_nav.items():
            if clave == clave_activa:
                widgets["btn"].configure(fg_color=COLORES["bg_hover"], text_color=COLORES["verde"])
                widgets["indicador"].configure(fg_color=COLORES["verde"])
            else:
                widgets["btn"].configure(fg_color="transparent", text_color=COLORES["texto_sec"])
                widgets["indicador"].configure(fg_color="transparent")
    
    def _al_cerrar(self):
        self.destroy()
