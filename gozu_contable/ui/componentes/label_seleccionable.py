import customtkinter as ctk
import tkinter as tk
from ui.tema import COLORES, FUENTES

def agregar_menu_contextual(widget):
    """Agrega menú contextual de Copiar/Pegar/Cortar a un widget (Entry/Textbox)"""
    menu = tk.Menu(widget, tearoff=0, bg=COLORES["bg_panel"], fg=COLORES["texto"], 
                   activebackground=COLORES["bg_hover"], activeforeground=COLORES["verde"],
                   font=("Segoe UI", 10))
    
    def comando_copiar():
        try:
            widget.event_generate("<<Copy>>")
        except:
            pass

    def comando_pegar():
        try:
            if widget.cget("state") != "disabled":
                widget.event_generate("<<Paste>>")
        except:
            pass

    def comando_cortar():
        try:
            if widget.cget("state") != "disabled":
                widget.event_generate("<<Cut>>")
        except:
            pass
            
    def comando_seleccionar_todo():
        try:
            widget.focus()
            widget.select_range(0, 'end')
        except:
            pass

    menu.add_command(label="Copiar", command=comando_copiar)
    menu.add_command(label="Pegar", command=comando_pegar)
    menu.add_command(label="Cortar", command=comando_cortar)
    menu.add_separator()
    menu.add_command(label="Seleccionar Todo", command=comando_seleccionar_todo)

    def mostrar_menu(event):
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    # Bind click derecho (Button-3 en Windows/Linux, Button-2 en Mac a veces, pero asumiendo Windows)
    widget.bind("<Button-3>", mostrar_menu)


class LabelSeleccionable(ctk.CTkFrame):
    """Un frame ligero con un label que fuerza el ancho estricto para evitar descuadres en tablas."""
    def __init__(self, parent, text="", font=None, text_color=None, width=120, **kwargs):
        super().__init__(parent, width=width, height=30, fg_color="transparent")
        self.pack_propagate(False)
        
        font = font or FUENTES["pequeña"]
        self.default_color = text_color or COLORES["texto"]
        
        self.label = ctk.CTkLabel(self, text=str(text), font=font,
                                  text_color=self.default_color, anchor="w", justify="left")
        self.label.pack(side="left", fill="both", expand=True)
            
        # Bind doble clic para copiar
        self.label.bind("<Double-Button-1>", self._copiar_texto)
        self.bind("<Double-Button-1>", self._copiar_texto)
        
    def _copiar_texto(self, event):
        try:
            self.clipboard_clear()
            self.clipboard_append(self.label.cget("text"))
            # Destello visual
            self.label.configure(text_color=COLORES["verde"])
            self.after(300, lambda: self.winfo_exists() and self.label.configure(text_color=self.default_color))
        except:
            pass

    # --- Compatibilidad con CTkEntry API ---
    def get(self, *args, **kwargs):
        return self.label.cget("text")
        
    def delete(self, *args, **kwargs):
        self.label.configure(text="")
        
    def insert(self, index, text):
        current = self.label.cget("text")
        # Aproximación simple: solo concatenamos o reemplazamos
        self.label.configure(text=str(text))
        
    def configure(self, **kwargs):
        if "state" in kwargs:
            kwargs.pop("state") # Ignoramos readonly
        if "text" in kwargs:
            self.label.configure(text=kwargs.pop("text"))
        if "text_color" in kwargs:
            self.default_color = kwargs["text_color"]
            self.label.configure(text_color=self.default_color)
            kwargs.pop("text_color")
        if kwargs:
            super().configure(**kwargs)
