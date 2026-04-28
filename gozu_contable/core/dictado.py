import config
import threading
import io
import wave
import numpy as np
import logging

class DictadoVoz:
    _instancia = None
    
    def __new__(cls):
        if cls._instancia is None:
            cls._instancia = super().__new__(cls)
            cls._instancia._iniciado = False
        return cls._instancia
        
    def __init__(self):
        if getattr(self, '_iniciado', False):
            return
            
        self.disponible = False
        self.grabando = False
        self.stop_listening_fn = None
        self.model = None
        self.r = None
        self.m = None
        self._cargando = False
        self._iniciado = True

    def cargar_modelo(self, callback_listo, callback_error):
        if self.disponible:
            callback_listo()
            return
        if self._cargando:
            return
            
        self._cargando = True
        
        def tarea():
            try:
                from faster_whisper import WhisperModel
                import speech_recognition as sr
                
                logging.info("⏳ INICIANDO DESCARGA: Cargando modelo de voz 'small' a la memoria...")
                # small model has much better accuracy for numbers and business terms
                self.model = WhisperModel("small", device="cpu", compute_type="int8")
                self.r = sr.Recognizer()
                self.m = sr.Microphone()
                
                with self.m as source:
                    self.r.adjust_for_ambient_noise(source, duration=0.5)
                    
                self.disponible = True
                logging.info("✅ DESCARGA COMPLETADA: Modelo de voz instalado y listo para usarse.")
                callback_listo()
            except Exception as e:
                logging.error(f"Error inicializando faster-whisper: {e}")
                callback_error(str(e))
            finally:
                self._cargando = False
                
        threading.Thread(target=tarea, daemon=True).start()
        
    def toggle_grabacion(self, callback_resultado, callback_estado):
        if not self.disponible:
            callback_estado("Microfono no disponible")
            return False
            
        if self.grabando:
            self.detener()
            callback_estado("Haz clic para hablar")
            return False
            
        self.grabando = True
        callback_estado("Escuchando (habla ahora)...")
        
        def tarea_escucha():
            import speech_recognition as sr
            import re
            
            try:
                # Re-instantiate Microphone per session to avoid context manager threading issues
                m = sr.Microphone()
                with m as source:
                    self.r.adjust_for_ambient_noise(source, duration=0.5)
                    
                    while self.grabando:
                        try:
                            # Listen with timeout so the loop can check self.grabando
                            audio_data = self.r.listen(source, timeout=1.0, phrase_time_limit=5)
                            
                            if not self.grabando:
                                break
                                
                            callback_estado("Transcribiendo...")
                            
                            # Get 16kHz mono audio directly
                            raw_data = audio_data.get_raw_data(convert_rate=16000, convert_width=2)
                            
                            # Convert to float32
                            audio_np = np.frombuffer(raw_data, dtype=np.int16).astype(np.float32) / 32768.0
                            
                            # Transcribe with context
                            prompt_contable = "Registro contable. Cantidades numéricas SIN separadores de miles. Ejemplo: 3000 soles, 25.50, 1500."
                            segments, info = self.model.transcribe(
                                audio_np, 
                                beam_size=1, 
                                language="es",
                                initial_prompt=prompt_contable
                            )
                            texto = " ".join([segment.text for segment in segments]).strip()
                            
                            if texto:
                                # Fix Whisper thousands separator issue: convert "3.000" to "3000"
                                texto = re.sub(r'(?<=\d)\.(?=\d{3}\b)', '', texto)
                                
                                logging.info(f"Dictado capturado: {texto}")
                                callback_resultado(texto)
                                
                            callback_estado("Escuchando (habla ahora)...")
                            
                        except sr.WaitTimeoutError:
                            # Timeout reached without voice, loop again
                            continue
                        except Exception as e:
                            logging.error(f"Error transcribiendo: {e}")
                            callback_estado("Error al procesar audio")
                            
            except Exception as e:
                logging.error(f"Error en micrófono: {e}")
                callback_estado("Error de micrófono")
                self.grabando = False

        threading.Thread(target=tarea_escucha, daemon=True).start()
        return True
            
    def detener(self):
        self.grabando = False
