import customtkinter as ctk
import logging
import sys
import os
from config import LOG_PATH, APP_NOMBRE
from core.db import DB
from ui.tema import aplicar_tema
from ui.vistas.ventana_principal import VentanaPrincipal

def configurar_logging():
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    logging.basicConfig(
        filename=LOG_PATH,
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        encoding='utf-8'
    )
    logging.info(f"Iniciando {APP_NOMBRE}")

def main():
    configurar_logging()
    try:
        DB.inicializar()
        logging.info("Base de datos inicializada correctamente")
    except Exception as e:
        logging.critical(f"Error crítico en BD: {e}")
        sys.exit(1)

    app = VentanaPrincipal()
    aplicar_tema(app)
    app.mainloop()

if __name__ == "__main__":
    main()
