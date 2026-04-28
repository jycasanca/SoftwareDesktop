import logging
from datetime import datetime

class EstadoContable:
    """Mantiene la información contable que necesita persistir durante la clasificación.

    - inventario: saldo de la cuenta 20 (A+)
    - cxc_pendientes: dict{id: monto} de cuentas por cobrar pendientes
    - activos: lista de activos fijos con costo, vida útil y residual
    - asientos_generados: historial opcional de asientos
    """

    def __init__(self):
        self.inventario = 0.0                # saldo de la cuenta 20 (activo)
        self.cxc_pendientes = {}             # clave = id único, valor = monto
        self.activos = []                    # lista de dicts: {'costo':…, 'vida':…, 'residual':…}
        self.asientos_generados = []         # historial de asientos para posibles reversión

    # ---------- Métodos de actualización ----------
    def registrar_compra_inventario(self, monto: float):
        self.inventario += monto
        logging.debug(f"[Estado] Inventario ↑ {monto:.2f} → {self.inventario:.2f}")

    def registrar_venta_credito(self, monto: float, fecha: str):
        uid = f"{fecha}_{len(self.cxc_pendientes)+1}"
        self.cxc_pendientes[uid] = monto
        logging.debug(f"[Estado] CxC +{monto:.2f} (id={uid})")
        return uid

    def registrar_cobro_cxc(self, monto: float):
        """Busca un pendiente que cubra *monto* (simple, primero encontrado)."""
        for uid, pendiente in list(self.cxc_pendientes.items()):
            if pendiente >= monto:
                self.cxc_pendientes[uid] = pendiente - monto
                if self.cxc_pendientes[uid] == 0:
                    del self.cxc_pendientes[uid]
                logging.debug(f"[Estado] CxC -{monto:.2f} (id={uid})")
                return uid
        logging.warning("[Estado] Cobro sin CxC pendiente")
        return None

    def agregar_activo_fijo(self, costo: float, vida_util: int = 10, residual: float = 0.10):
        self.activos.append({
            "costo": costo,
            "vida_util": vida_util,
            "residual": residual,
        })
        logging.debug(f"[Estado] Activo añadido: {costo:.2f}, vida {vida_util}a, residual {residual:.0%}")

    # ---------- Cálculos de cierre ----------
    def calcular_depreciacion(self) -> float:
        """Calcula la depreciación acumulada proporcional al semestre (asumiendo 6 meses)."""
        total = 0.0
        for act in self.activos:
            base = act["costo"] - act["costo"] * act["residual"]
            anual = base / act["vida_util"]
            total += anual / 2  # primer semestre
        return total

    def total_cxc(self) -> float:
        return sum(self.cxc_pendientes.values())

    # ---------- Cálculo de Costo de Ventas (COGS) ----------
    def calcular_cogs(self, inventario_inicial: float = 0.0, 
                      compras: float = 0.0,
                      donaciones: float = 0.0,
                      perdidas: float = 0.0,
                      inventario_final: float = 0.0) -> float:
        """
        COGS = Inventario Inicial + Compras + Donaciones - Pérdidas - Inventario Final
        """
        cogs = inventario_inicial + compras + donaciones - perdidas - inventario_final
        return max(0.0, cogs)

    def obtener_resumen_inventario(self) -> dict:
        """Retorna resumen para cálculo de COGS."""
        return {
            'inventario_actual': self.inventario,
            'cxc_total': self.total_cxc(),
            'num_activos': len(self.activos),
            'depreciacion_acumulada': self.calcular_depreciacion()
        }

    # ---------- Persistencia temporal (opcional) ----------
    def to_dict(self) -> dict:
        return {
            'inventario': self.inventario,
            'cxc_pendientes': self.cxc_pendientes,
            'activos': self.activos,
            'asientos_generados': self.asientos_generados
        }

    @classmethod
    def from_dict(cls, data: dict):
        estado = cls()
        estado.inventario = data.get('inventario', 0.0)
        estado.cxc_pendientes = data.get('cxc_pendientes', {})
        estado.activos = data.get('activos', [])
        estado.asientos_generados = data.get('asientos_generados', [])
        return estado
