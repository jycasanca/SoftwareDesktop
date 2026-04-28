import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database", "contable.db")
LOG_PATH = os.path.join(BASE_DIR, "logs", "app.log")
TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
VOSK_MODEL_PATH = os.path.join(BASE_DIR, "assets", "vosk_model_es")
APP_NOMBRE = "GOZU — Sistema Contable"
APP_VERSION = "1.0.0"
