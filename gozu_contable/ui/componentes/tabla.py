import customtkinter as ctk
from ui.tema import COLORES, FUENTES

class TablaScrollable(ctk.CTkFrame):
    def __init__(self, parent, columnas, **kwargs):
        super().__init__(parent, fg_color=COLORES["bg_principal"], **kwargs)
        self.columnas = columnas
        self.filas_widgets = []
        
        # Canvas y scrollbar
        self.canvas = ctk.CTkCanvas(self, bg=COLORES["bg_principal"], highlightthickness=0)
        self.scrollbar = ctk.CTkScrollbar(self, command=self.canvas.yview)
        self.scrollable_frame = ctk.CTkFrame(self.canvas, fg_color=COLORES["bg_principal"])
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        # Header
        self._crear_header()
    
    def _crear_header(self):
        header_frame = ctk.CTkFrame(self.scrollable_frame, fg_color=COLORES["bg_panel"], height=35)
        header_frame.pack(side="top", fill="x")
        header_frame.pack_propagate(False)
        
        for col in self.columnas:
            lbl = ctk.CTkLabel(
                header_frame, text=col["nombre"].upper(),
                font=FUENTES["pequeña"], text_color=COLORES["texto_sec"],
                width=col["ancho"], anchor=col.get("alineacion", "w")
            )
            lbl.pack(side="left", padx=5, pady=8)
    
    def cargar_datos(self, filas):
        self.limpiar()
        
        for i, fila in enumerate(filas):
            bg = COLORES["bg_fila_par"] if i % 2 == 0 else COLORES["bg_fila_impar"]
            fila_frame = ctk.CTkFrame(self.scrollable_frame, fg_color=bg, height=40)
            fila_frame.pack(side="top", fill="x")
            fila_frame.pack_propagate(False)
            
            # Hover effect
            fila_frame.bind("<Enter>", lambda e, f=fila_frame: f.configure(fg_color=COLORES["bg_hover"]))
            fila_frame.bind("<Leave>", lambda e, f=fila_frame, b=bg: f.configure(fg_color=b))
            
            fila_widgets = []
            
            for j, valor in enumerate(fila):
                col = self.columnas[j]
                color = COLORES["azul"] if col.get("es_numero") else COLORES["texto"]
                
                if col["nombre"] == "acciones":
                    # Frame para botones de acción
                    acciones_frame = ctk.CTkFrame(fila_frame, fg_color=bg)
                    acciones_frame.pack(side="left", padx=5, pady=5)
                    lbl = ctk.CTkLabel(acciones_frame, text=valor, font=FUENTES["normal"])
                    lbl.pack()
                else:
                    lbl = ctk.CTkLabel(
                        fila_frame, text=str(valor),
                        font=FUENTES["normal"], text_color=color,
                        width=col["ancho"], anchor=col.get("alineacion", "w")
                    )
                    lbl.pack(side="left", padx=5, pady=8)
                    fila_widgets.append(lbl)
            
            self.filas_widgets.append(fila_widgets)
    
    def limpiar(self):
        for widget in self.scrollable_frame.winfo_children():
            if isinstance(widget, ctk.CTkFrame) and widget != self.scrollable_frame.winfo_children()[0]:
                widget.destroy()
        self.filas_widgets = []
