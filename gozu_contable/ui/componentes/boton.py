import customtkinter as ctk
from ui.tema import FUENTES, COLORES

class Boton(ctk.CTkButton):
    def __init__(self, parent, texto, variante="primario", comando=None, **kwargs):
        # Aceptar "command" como alias de "comando" para compatibilidad
        if "command" in kwargs:
            comando = kwargs.pop("command")
        estilos = {
            "primario":   {"fg_color": COLORES["verde"],  "text_color": COLORES["bg_principal"], "hover_color": "#B8D68A"},
            "peligro":    {"fg_color": COLORES["rojo"],   "text_color": COLORES["texto"],        "hover_color": "#D45A5A"},
            "secundario": {"fg_color": COLORES["bg_input"],"text_color": COLORES["texto"],       "hover_color": COLORES["bg_hover"],
                           "border_width": 1, "border_color": COLORES["borde"]},
            "fantasma":   {"fg_color": "transparent",     "text_color": COLORES["texto_sec"],    "hover_color": COLORES["bg_hover"]},
            "info":       {"fg_color": COLORES["azul"],   "text_color": COLORES["bg_principal"], "hover_color": "#9AC5BE"},
            "morado":     {"fg_color": COLORES["morado"], "text_color": COLORES["bg_principal"], "hover_color": "#B89FD0"},
        }
        self._original_text = texto
        fuente = kwargs.pop("font", FUENTES["normal"])
        super().__init__(parent, text=texto, command=comando,
                         corner_radius=6, font=fuente,
                         **estilos.get(variante, {}), **kwargs)

    def set_cargando(self, estado, texto_carga="Procesando..."):
        if estado:
            self.configure(state="disabled", text=texto_carga)
        else:
            self.configure(state="normal", text=self._original_text)
