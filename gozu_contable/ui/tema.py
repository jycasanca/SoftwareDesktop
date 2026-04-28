COLORES = {
    "bg_principal":  "#1F1F28",   # background
    "bg_panel":      "#16161D",   # surface
    "bg_input":      "#2A2A37",   # border usado como fondo de inputs
    "bg_fila_par":   "#1F1F28",
    "bg_fila_impar": "#16161D",
    "bg_hover":      "#2A2A37",   # border como hover
    "borde":         "#2A2A37",   # border
    "texto":         "#DCD7BA",   # text
    "texto_sec":     "#727169",   # muted
    "texto_desact":  "#414152",
    "amarillo":      "#FFA066",   # number (naranja cálido)
    "naranja":       "#FFA066",   # number
    "verde":         "#98BB6C",   # string
    "exito":         "#98BB6C",   # verde para éxito (alias)
    "azul":          "#7AA89F",   # accent
    "morado":        "#957FB8",   # keyword
    "rojo":          "#C34043",   # rojo Kanagawa
}

FUENTES = {
    "normal":  ("Cascadia Code", 14),
    "pequeña": ("Cascadia Code", 12),
    "grande":  ("Cascadia Code", 17),
    "titulo":  ("Cascadia Code", 24, "bold"),
    "subtit":  ("Cascadia Code", 17, "bold"),
    "label":   ("Cascadia Code", 12),
    "numero":  ("Cascadia Code", 14),
    "bold":    ("Cascadia Code", 14, "bold"),
}

def aplicar_tema(root):
    import customtkinter as ctk
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")
    root.configure(bg=COLORES["bg_principal"])
