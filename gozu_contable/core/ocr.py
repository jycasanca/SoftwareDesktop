import config
import logging

class OCRProcesador:
    def __init__(self):
        try:
            import pytesseract
            import os
            from PIL import Image, ImageEnhance
            pytesseract.pytesseract.tesseract_cmd = config.TESSERACT_PATH
            self.tessdata_dir = os.path.join(config.BASE_DIR, "tessdata")
            self.disponible = True
        except:
            self.disponible = False
    
    def procesar_imagen(self, ruta):
        logging.info("=" * 80)
        logging.info("INICIANDO OCR - PROCESAMIENTO DE IMAGEN")
        logging.info("=" * 80)
        logging.info(f"RUTA IMAGEN: {ruta}")
        
        if not self.disponible:
            logging.error("OCR NO DISPONIBLE: Instala Tesseract y pytesseract")
            return {"error": "Instala Tesseract y pytesseract"}
        
        try:
            import pytesseract
            from PIL import Image, ImageEnhance
            
            logging.info("Abriendo imagen...")
            img = Image.open(ruta).convert('L')
            logging.info(f"Dimensiones: {img.size}, Modo: {img.mode}")
            
            logging.info("Aplicando mejoras de contraste y binarización...")
            img = ImageEnhance.Contrast(img).enhance(2.0)
            img = img.point(lambda x: 0 if x < 128 else 255)
            
            logging.info("Ejecutando OCR con Tesseract...")
            texto = pytesseract.image_to_string(img, lang='spa', config=f'--tessdata-dir {self.tessdata_dir} --psm 6')
            
            logging.info(f"TEXTO EXTRAÍDO ({len(texto)} caracteres):")
            logging.info("-" * 80)
            logging.info(texto if texto else "[SIN TEXTO]")
            logging.info("-" * 80)
            
            resultado = self._extraer_datos(texto)
            logging.info(f"DATOS EXTRAÍDOS:")
            logging.info(f"  RUC: {resultado.get('ruc', 'N/A')}")
            logging.info(f"  Total: S/. {resultado.get('total', 0)}")
            logging.info(f"  IGV: S/. {resultado.get('igv', 0)}")
            logging.info(f"  Subtotal: S/. {resultado.get('subtotal', 0)}")
            logging.info(f"  Fecha: {resultado.get('fecha', 'N/A')}")
            logging.info("=" * 80)
            
            return resultado
        except Exception as e:
            logging.error(f"ERROR EN OCR: {str(e)}")
            return {"error": str(e)}
    
    def procesar_pdf(self, ruta):
        logging.info("=" * 80)
        logging.info("INICIANDO OCR - PROCESAMIENTO DE PDF")
        logging.info("=" * 80)
        logging.info(f"RUTA PDF: {ruta}")
        
        if not self.disponible:
            logging.error("OCR NO DISPONIBLE: Instala Tesseract y pytesseract")
            return {"error": "Instala Tesseract y pytesseract"}
        
        try:
            import pdfplumber
            logging.info("Intentando extracción de texto nativa con pdfplumber...")
            
            with pdfplumber.open(ruta) as pdf:
                num_paginas = len(pdf.pages)
                logging.info(f"PDF tiene {num_paginas} páginas")
                texto = '\n'.join(p.extract_text() or '' for p in pdf.pages)
            
            logging.info(f"Texto nativo extraído: {len(texto)} caracteres")
            
            if len(texto.strip()) < 30:
                logging.warning("Texto nativo muy corto (< 30 caracteres), probablemente PDF escaneado")
                raise ValueError("PDF escaneado")
            
            logging.info("TEXTO EXTRAÍDO (PDF nativo):")
            logging.info("-" * 80)
            logging.info(texto[:500] + "..." if len(texto) > 500 else texto)
            logging.info("-" * 80)
            
            resultado = self._extraer_datos(texto)
            logging.info(f"DATOS EXTRAÍDOS:")
            logging.info(f"  RUC: {resultado.get('ruc', 'N/A')}")
            logging.info(f"  Total: S/. {resultado.get('total', 0)}")
            logging.info(f"  IGV: S/. {resultado.get('igv', 0)}")
            logging.info(f"  Subtotal: S/. {resultado.get('subtotal', 0)}")
            logging.info(f"  Fecha: {resultado.get('fecha', 'N/A')}")
            logging.info("=" * 80)
            
            return resultado
            
        except Exception as e1:
            logging.warning(f"Extracción nativa falló: {str(e1)}")
            logging.info("Intentando OCR en PDF escaneado con PyMuPDF...")
            
            try:
                import fitz  # PyMuPDF
                from PIL import Image
                import pytesseract
                
                doc = fitz.open(ruta)
                num_paginas = len(doc)
                logging.info(f"PDF escaneado: {num_paginas} páginas")
                
                texto_ocr = []
                for i, pagina in enumerate(doc):
                    logging.info(f"Procesando página {i + 1}/{num_paginas}...")
                    # Zoom 2x para mejor resolución en OCR
                    pix = pagina.get_pixmap(matrix=fitz.Matrix(2, 2))
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    texto_pagina = pytesseract.image_to_string(img, lang='spa', config=f'--tessdata-dir {self.tessdata_dir}')
                    texto_ocr.append(texto_pagina)
                    logging.info(f"  Página {i + 1}: {len(texto_pagina)} caracteres")
                    
                doc.close()
                texto_completo = '\n'.join(texto_ocr)
                
                logging.info("TEXTO EXTRAÍDO (OCR PDF):")
                logging.info("-" * 80)
                logging.info(texto_completo[:500] + "..." if len(texto_completo) > 500 else texto_completo)
                logging.info("-" * 80)
                
                resultado = self._extraer_datos(texto_completo)
                logging.info(f"DATOS EXTRAÍDOS:")
                logging.info(f"  RUC: {resultado.get('ruc', 'N/A')}")
                logging.info(f"  Total: S/. {resultado.get('total', 0)}")
                logging.info(f"  IGV: S/. {resultado.get('igv', 0)}")
                logging.info(f"  Subtotal: S/. {resultado.get('subtotal', 0)}")
                logging.info(f"  Fecha: {resultado.get('fecha', 'N/A')}")
                logging.info("=" * 80)
                
                return resultado
            except Exception as e2:
                logging.error(f"ERROR EN OCR PDF: {str(e2)}")
                return {"error": f"Error PDF OCR: {str(e2)}"}
    
    def _extraer_datos(self, texto):
        import re
        
        ruc_m = re.search(r'\b(\d{11})\b', texto)
        total_m = re.search(r'TOTAL[:\s]+S?/?\.?\s*([\d,]+\.?\d*)', texto, re.IGNORECASE)
        igv_m = re.search(r'IGV[:\s]+S?/?\.?\s*([\d,]+\.?\d*)', texto, re.IGNORECASE)
        fecha_m = re.search(r'(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})', texto)
        sub_m = re.search(r'(?:SUBTOTAL|BASE)[:\s]+S?/?\.?\s*([\d,]+\.?\d*)', texto, re.IGNORECASE)
        
        return {
            "texto_raw": texto,
            "ruc": ruc_m.group(1) if ruc_m else "",
            "total": float(total_m.group(1).replace(',','')) if total_m else 0.0,
            "igv": float(igv_m.group(1).replace(',','')) if igv_m else 0.0,
            "subtotal": float(sub_m.group(1).replace(',','')) if sub_m else 0.0,
            "fecha": fecha_m.group(0) if fecha_m else "",
        }
