import customtkinter as ctk
from ui.tema import COLORES, FUENTES

class SistemaToast:
    _instancia = None
    
    def __new__(cls):
        if cls._instancia is None:
            cls._instancia = super().__new__(cls)
            cls._instancia._toasts_activos = []
        return cls._instancia
    
    def mostrar(self, mensaje, tipo="info", duracion_ms=3000):
        colores = {
            "exito": "#a6e22e",
            "error": "#f92672",
            "info": "#66d9e8",
            "advertencia": "#fd971f"
        }
        import logging
        if tipo == "error":
            logging.error(f"UI Error: {mensaje}")
        elif tipo == "advertencia":
            logging.warning(f"UI Warning: {mensaje}")
        elif tipo == "exito":
            logging.info(f"UI Success: {mensaje}")
        else:
            logging.info(f"UI Info: {mensaje}")
            
        iconos = {
            "exito": "✓",
            "error": "✗",
            "info": "ℹ",
            "advertencia": "⚠"
        }
        
        toast = ctk.CTkToplevel()
        toast.overrideredirect(True)
        toast.configure(fg_color=COLORES["bg_panel"])
        
        # Calcular posición
        pantalla_w = toast.winfo_screenwidth()
        pantalla_h = toast.winfo_screenheight()
        offset_y = 80 + (len(self._toasts_activos) * 70)
        
        x = pantalla_w - 320
        y = pantalla_h - offset_y
        toast.geometry(f"300x60+{x}+{y}")
        
        # Frame principal
        frame = ctk.CTkFrame(toast, fg_color=COLORES["bg_panel"])
        frame.pack(fill="both", expand=True, padx=1, pady=1)
        
        # Borde izquierdo
        borde = ctk.CTkFrame(frame, width=4, fg_color=colores.get(tipo, COLORES["azul"]))
        borde.pack(side="left", fill="y")
        
        # Contenido
        contenido = ctk.CTkFrame(frame, fg_color=COLORES["bg_panel"])
        contenido.pack(side="left", fill="both", expand=True, padx=12, pady=8)
        
        icono_lbl = ctk.CTkLabel(
            contenido, text=iconos.get(tipo, "ℹ"),
            font=("Consolas", 16), text_color=colores.get(tipo, COLORES["azul"])
        )
        icono_lbl.pack(side="left", padx=(0, 8))
        
        msg_lbl = ctk.CTkLabel(
            contenido, text=mensaje,
            font=FUENTES["normal"], text_color=COLORES["texto"],
            anchor="w"
        )
        msg_lbl.pack(side="left", fill="x", expand=True)
        
        self._toasts_activos.append(toast)
        
        def cerrar():
            if toast in self._toasts_activos:
                self._toasts_activos.remove(toast)
            toast.destroy()
        
        toast.after(duracion_ms, cerrar)
