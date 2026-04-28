import customtkinter as ctk
from ui.tema import COLORES, FUENTES

class Modal(ctk.CTkToplevel):
    def __init__(self, parent, titulo, ancho=500, alto=400):
        super().__init__(parent)
        self.title(titulo)
        self.geometry(f"{ancho}x{alto}")
        self.configure(fg_color=COLORES["bg_panel"])
        self.resizable(False, False)
        self.grab_set()
        
        # Centrar ventana
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (ancho // 2)
        y = (self.winfo_screenheight() // 2) - (alto // 2)
        self.geometry(f"{ancho}x{alto}+{x}+{y}")
        
        # Header
        self.header_frame = ctk.CTkFrame(self, fg_color=COLORES["bg_panel"], height=60)
        self.header_frame.pack(side="top", fill="x", padx=20, pady=(20, 10))
        self.header_frame.pack_propagate(False)
        
        self.lbl_titulo = ctk.CTkLabel(
            self.header_frame, text=titulo,
            font=FUENTES["subtit"], text_color=COLORES["amarillo"]
        )
        self.lbl_titulo.pack(side="left", pady=15)
        
        self.btn_cerrar = ctk.CTkButton(
            self.header_frame, text="✕", width=30, height=30,
            fg_color="transparent", text_color=COLORES["texto_sec"],
            hover_color=COLORES["rojo"], font=("Consolas", 16),
            command=self.destruir
        )
        self.btn_cerrar.pack(side="right", pady=15)
        
        # Separador
        ctk.CTkFrame(self, height=1, fg_color=COLORES["borde"]).pack(side="top", fill="x")
        
        # Frame contenido
        self.frame_contenido = ctk.CTkFrame(self, fg_color=COLORES["bg_panel"])
        self.frame_contenido.pack(side="top", fill="both", expand=True, padx=20, pady=20)
        
        # Frame footer (opcional, creado por el caller si es necesario)
        self.frame_footer = None
    
    def crear_footer(self, botones):
        if self.frame_footer:
            self.frame_footer.destroy()
        
        self.frame_footer = ctk.CTkFrame(self, fg_color=COLORES["bg_panel"])
        self.frame_footer.pack(side="bottom", fill="x", padx=20, pady=(0, 20))
        
        for btn in botones:
            btn.pack(side="right", padx=(5, 0))
    
    def destruir(self):
        self.grab_release()
        self.destroy()
