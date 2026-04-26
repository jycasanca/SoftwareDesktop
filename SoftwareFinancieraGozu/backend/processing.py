import sqlite3
import re
from pathlib import Path
from typing import List, Dict, Tuple

BASE_DIR = Path(__file__).resolve().parent
DATABASE_FILE = BASE_DIR.parent / 'database' / 'financiera.db'

def get_synonyms(db_path: str = None) -> Dict[str, str]:
    db_path = db_path or DATABASE_FILE

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT palabra_usuario, concepto_estandar FROM diccionario_sinonimos')
    synonyms = {row[0].lower(): row[1] for row in cursor.fetchall()}
    conn.close()
    return synonyms

def extract_keywords(text: str, synonyms: Dict[str, str]) -> List[str]:
    words = re.findall(r'\b\w+\b', text.lower())
    keywords = []
    for word in words:
        if word in synonyms:
            keywords.append(synonyms[word].upper())
    return list(dict.fromkeys(keywords))  # unique, preserve order

def get_behavior_matrix(db_path: str = None) -> List[Tuple[str, str, str, int]]:
    db_path = db_path or DATABASE_FILE
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT concepto_estandar, cuenta_asociada, naturaleza_default, prioridad FROM matriz_comportamiento')
    matrix = cursor.fetchall()
    conn.close()
    return matrix

def infer_accounts(keywords: List[str], matrix: List[Tuple[str, str, str, int]], amount: float) -> List[Dict]:
    payment_methods = {'EFECTIVO', 'CREDITO'}
    detected_payment = [k for k in keywords if k in payment_methods]
    non_payment = [k for k in keywords if k not in payment_methods]
    entries: List[Dict] = []

    def find_rule(concept: str):
        return next((row for row in matrix if row[0].upper() == concept.upper()), None)

    if non_payment:
        for concept in non_payment:
            rule = find_rule(concept)
            if rule:
                account = rule[1]
                nature = rule[2].upper()
                if nature == 'DEBE':
                    entries.append({'cuenta': account, 'naturaleza': 'DEBE', 'monto': amount})
                    if 'EFECTIVO' in detected_payment:
                        entries.append({'cuenta': '10', 'naturaleza': 'HABER', 'monto': amount})
                    elif 'CREDITO' in detected_payment:
                        entries.append({'cuenta': '12', 'naturaleza': 'HABER', 'monto': amount})
                    else:
                        entries.append({'cuenta': '10', 'naturaleza': 'HABER', 'monto': amount})
                else:
                    if 'EFECTIVO' in detected_payment:
                        entries.append({'cuenta': '10', 'naturaleza': 'DEBE', 'monto': amount})
                    elif 'CREDITO' in detected_payment:
                        entries.append({'cuenta': '12', 'naturaleza': 'DEBE', 'monto': amount})
                    else:
                        entries.append({'cuenta': '10', 'naturaleza': 'DEBE', 'monto': amount})
                    entries.append({'cuenta': account, 'naturaleza': 'HABER', 'monto': amount})
                break

    if not entries and detected_payment:
        if 'EFECTIVO' in detected_payment and 'CREDITO' in detected_payment:
            entries = [
                {'cuenta': '10', 'naturaleza': 'DEBE', 'monto': amount / 2},
                {'cuenta': '12', 'naturaleza': 'DEBE', 'monto': amount / 2},
                {'cuenta': '40', 'naturaleza': 'HABER', 'monto': amount}
            ]
        elif 'EFECTIVO' in detected_payment:
            entries = [
                {'cuenta': '10', 'naturaleza': 'DEBE', 'monto': amount},
                {'cuenta': '40', 'naturaleza': 'HABER', 'monto': amount}
            ]
        else:
            entries = [
                {'cuenta': '12', 'naturaleza': 'DEBE', 'monto': amount},
                {'cuenta': '40', 'naturaleza': 'HABER', 'monto': amount}
            ]

    return entries

def process_text(text: str, amount: float, db_path: str = None) -> List[Dict]:
    synonyms = get_synonyms(db_path)
    keywords = extract_keywords(text, synonyms)
    matrix = get_behavior_matrix(db_path)
    return infer_accounts(keywords, matrix, amount)