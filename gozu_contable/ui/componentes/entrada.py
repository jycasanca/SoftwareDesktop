import customtkinter as ctk
from ui.tema import FUENTES, COLORES
from ui.componentes.label_seleccionable import agregar_menu_contextual

class Entrada(ctk.CTkEntry):
    def __init__(self, parent, **kwargs):
        # CTkEntry usa "placeholder_text", no "placeholder"
        if "placeholder" in kwargs:
            kwargs["placeholder_text"] = kwargs.pop("placeholder")
        super().__init__(parent,
            fg_color=COLORES["bg_input"],
            border_color=COLORES["borde"],
            text_color=COLORES["texto"],
            placeholder_text_color="#555566",   # gris visible sobre bg_input
            font=FUENTES["normal"],
            corner_radius=6,
            **kwargs)
        self.bind("<FocusIn>",  lambda e: self.configure(border_color=COLORES["azul"]))
        self.bind("<FocusOut>", lambda e: self.configure(border_color=COLORES["borde"]))
        
        agregar_menu_contextual(self)
