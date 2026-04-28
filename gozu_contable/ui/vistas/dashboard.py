import customtkinter as ctk
from datetime import datetime
from ui.tema import COLORES, FUENTES
from ui.componentes.boton import Boton
from ui.componentes.toast import SistemaToast
from core.db import DB

class Dashboard(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=COLORES["bg_principal"])
        
        # Título
        ctk.CTkLabel(self, text="Dashboard", font=FUENTES["titulo"],
                    text_color=COLORES["amarillo"]).pack(pady=(0, 5))
        
        hoy = datetime.now().strftime("%A, %d de %B de %Y")
        ctk.CTkLabel(self, text=hoy, font=FUENTES["pequeña"],
                    text_color=COLORES["texto_sec"]).pack(pady=(0, 20))
        
        # KPIs
        frame_kpis = ctk.CTkFrame(self, fg_color=COLORES["bg_principal"])
        frame_kpis.pack(fill="x", pady=(0, 20))
        frame_kpis.columnconfigure(0, weight=1)
        frame_kpis.columnconfigure(1, weight=1)
        frame_kpis.columnconfigure(2, weight=1)
        frame_kpis.columnconfigure(3, weight=1)
        
        self._crear_kpi(frame_kpis, 0, "💰", "Ventas del Mes", "S/ 0.00", COLORES["verde"])
        self._crear_kpi(frame_kpis, 1, "📉", "Gastos del Mes", "S/ 0.00", COLORES["rojo"])
        self._crear_kpi(frame_kpis, 2, "📊", "Utilidad Neta", "S/ 0.00", COLORES["verde"])
        self._crear_kpi(frame_kpis, 3, "✏️", "Asientos Hoy", "0", COLORES["azul"])
        
        # Contenido principal
        frame_principal = ctk.CTkFrame(self, fg_color=COLORES["bg_principal"])
        frame_principal.pack(fill="both", expand=True)
        frame_principal.columnconfigure(0, weight=6)
        frame_principal.columnconfigure(1, weight=4)
        
        # Panel izquierdo - Últimos asientos
        panel_izq = ctk.CTkFrame(frame_principal, fg_color=COLORES["bg_panel"], corner_radius=8)
        panel_izq.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        
        ctk.CTkLabel(panel_izq, text="ÚLTIMOS ASIENTOS REGISTRADOS",
                    font=FUENTES["normal"], text_color=COLORES["texto_sec"]).pack(anchor="w", padx=15, pady=(15, 10))
        
        frame_asientos = ctk.CTkFrame(panel_izq, fg_color=COLORES["bg_principal"])
        frame_asientos.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        hoy = datetime.now().strftime("%Y-%m-%d")
        asientos = DB.fetchall("""
            SELECT DISTINCT numero_asiento, descripcion, SUM(debe) as total
            FROM libro_diario
            WHERE fecha = ? AND eliminado = 0
            GROUP BY numero_asiento
            ORDER BY numero_asiento DESC
            LIMIT 5
        """, (hoy,))
        
        if asientos:
            for asiento in asientos:
                frame = ctk.CTkFrame(frame_asientos, fg_color=COLORES["bg_fila_impar"], corner_radius=6)
                frame.pack(fill="x", pady=3)
                
                ctk.CTkLabel(frame, text=f"N° {asiento['numero_asiento']}",
                            font=FUENTES["pequeña"], text_color=COLORES["amarillo"]).pack(side="left", padx=10, pady=8)
                
                desc = asiento['descripcion'][:30] + "..." if len(asiento['descripcion']) > 30 else asiento['descripcion']
                ctk.CTkLabel(frame, text=desc, font=FUENTES["pequeña"],
                            text_color=COLORES["texto"]).pack(side="left", padx=5)
                
                ctk.CTkLabel(frame, text=f"S/ {asiento['total']:,.2f}",
                            font=FUENTES["pequeña"], text_color=COLORES["verde"]).pack(side="right", padx=10, pady=8)
        else:
            ctk.CTkLabel(frame_asientos, text="No hay asientos registrados hoy",
                        font=FUENTES["normal"], text_color=COLORES["texto_sec"]).pack(pady=20)
        
        Boton(panel_izq, "Ver todos →", variante="fantasma").pack(anchor="e", padx=15, pady=(0, 15))
        
        # Panel derecho - Resumen
        panel_der = ctk.CTkFrame(frame_principal, fg_color=COLORES["bg_panel"], corner_radius=8)
        panel_der.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        
        ctk.CTkLabel(panel_der, text="RESUMEN DEL MES",
                    font=FUENTES["normal"], text_color=COLORES["texto_sec"]).pack(anchor="w", padx=15, pady=(15, 10))
        
        frame_resumen = ctk.CTkFrame(panel_der, fg_color=COLORES["bg_principal"])
        frame_resumen.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        self._crear_barra_resumen(frame_resumen, "Activos", COLORES["verde"], 100000, 50000)
        self._crear_barra_resumen(frame_resumen, "Pasivos", COLORES["rojo"], 100000, 30000)
        self._crear_barra_resumen(frame_resumen, "Patrimonio", COLORES["morado"], 100000, 20000)
        
        # Estado del sistema
        frame_estado = ctk.CTkFrame(self, fg_color=COLORES["bg_panel"], corner_radius=6)
        frame_estado.pack(fill="x", pady=15)
        
        ctk.CTkLabel(frame_estado, text="ESTADO DEL SISTEMA:",
                    font=FUENTES["pequeña"], text_color=COLORES["texto_sec"]).pack(anchor="w", padx=12, pady=(12, 5))
        
        ctk.CTkLabel(frame_estado, text="✓ Base de datos conectada",
                    font=FUENTES["pequeña"], text_color=COLORES["verde"]).pack(anchor="w", padx=12, pady=3)
        ctk.CTkLabel(frame_estado, text="✓ OCR: No disponible",
                    font=FUENTES["pequeña"], text_color=COLORES["texto_sec"]).pack(anchor="w", padx=12, pady=3)
        ctk.CTkLabel(frame_estado, text="✓ Voz: No disponible",
                    font=FUENTES["pequeña"], text_color=COLORES["texto_sec"]).pack(anchor="w", padx=12, pady=(3, 12))
        
        self._actualizar_kpis()
    
    def _crear_kpi(self, parent, col, icono, label, valor, color):
        card = ctk.CTkFrame(parent, fg_color=COLORES["bg_panel"], corner_radius=8)
        card.grid(row=0, column=col, sticky="nsew", padx=5, pady=5)
        
        ctk.CTkLabel(card, text=icono, font=("Segoe UI Emoji", 28)).pack(pady=(15, 5))
        
        self.kpi_labels = getattr(self, "kpi_labels", {})
        self.kpi_labels[label] = ctk.CTkLabel(card, text=valor, font=FUENTES["titulo"], text_color=color)
        self.kpi_labels[label].pack(pady=(0, 5))
        
        ctk.CTkLabel(card, text=label.upper(), font=FUENTES["pequeña"],
                    text_color=COLORES["texto_sec"]).pack(pady=(0, 15))
    
    def _crear_barra_resumen(self, parent, label, color, total, valor):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(frame, text=label, font=FUENTES["normal"], text_color=color).pack(anchor="w")
        
        frame_barra = ctk.CTkFrame(frame, fg_color=COLORES["bg_input"], height=20)
        frame_barra.pack(fill="x", pady=5)
        
        porcentaje = (valor / total) * 100 if total > 0 else 0
        frame_lleno = ctk.CTkFrame(frame_barra, fg_color=color, height=20)
        frame_lleno.pack(side="left", fill="y")
        frame_lleno.pack_propagate(False)
        frame_lleno.configure(width=int(porcentaje * 2))
        
        ctk.CTkLabel(frame, text=f"S/ {valor:,.2f}", font=FUENTES["normal"],
                    text_color=COLORES["texto"]).pack(anchor="e")
    
    def _actualizar_kpis(self):
        hoy = datetime.now().strftime("%Y-%m")
        
        # Ventas del mes
        ventas = DB.fetchone("""
            SELECT SUM(haber) as total FROM libro_diario ld
            JOIN plan_contable p ON p.codigo = ld.cuenta_codigo
            WHERE p.tipo_cuenta = 'ingreso' AND ld.fecha LIKE ? AND ld.eliminado = 0
        """, (f"{hoy}%",))
        
        if ventas and ventas['total']:
            self.kpi_labels["Ventas del Mes"].configure(text=f"S/ {ventas['total']:,.2f}")
        
        # Gastos del mes
        gastos = DB.fetchone("""
            SELECT SUM(debe) as total FROM libro_diario ld
            JOIN plan_contable p ON p.codigo = ld.cuenta_codigo
            WHERE p.tipo_cuenta IN ('gasto', 'costo') AND ld.fecha LIKE ? AND ld.eliminado = 0
        """, (f"{hoy}%",))
        
        if gastos and gastos['total']:
            self.kpi_labels["Gastos del Mes"].configure(text=f"S/ {gastos['total']:,.2f}")
        
        # Asientos hoy
        hoy_completo = datetime.now().strftime("%Y-%m-%d")
        asientos_hoy = DB.fetchone("""
            SELECT COUNT(DISTINCT numero_asiento) as total
            FROM libro_diario
            WHERE fecha = ? AND eliminado = 0
        """, (hoy_completo,))
        
        if asientos_hoy and asientos_hoy['total']:
            self.kpi_labels["Asientos Hoy"].configure(text=str(asientos_hoy['total']))
