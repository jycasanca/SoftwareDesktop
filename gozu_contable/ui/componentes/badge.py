import customtkinter as ctk
from ui.tema import FUENTES

class Badge(ctk.CTkLabel):
    variantes = {
        "activo":    {"fg_color":"#1a2e0a","text_color":"#a6e22e","text":"ACTIVO"},
        "eliminado": {"fg_color":"#2e0a15","text_color":"#f92672","text":"ELIMINADO"},
        "pendiente": {"fg_color":"#2e1f0a","text_color":"#fd971f","text":"PENDIENTE"},
        "alta":      {"fg_color":"#1a2e0a","text_color":"#a6e22e","text":"ALTA"},
        "media":     {"fg_color":"#2e1f0a","text_color":"#fd971f","text":"MEDIA"},
        "baja":      {"fg_color":"#2e0a15","text_color":"#f92672","text":"BAJA"},
        "diccionario":{"fg_color":"#0a1f2e","text_color":"#66d9e8","text":"DICCIONARIO"},
        "reglas":    {"fg_color":"#1a0a2e","text_color":"#ae81ff","text":"REGLAS"},
        "manual":    {"fg_color":"#2e2a0a","text_color":"#e6db74","text":"MANUAL"},
    }
    def __init__(self, parent, variante="activo"):
        v = self.variantes.get(variante, self.variantes["pendiente"])
        super().__init__(parent, text=v["text"],
                         fg_color=v["fg_color"], text_color=v["text_color"],
                         font=FUENTES["pequeña"], corner_radius=4,
                         padx=6, pady=2)
