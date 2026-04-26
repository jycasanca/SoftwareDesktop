export function useSpeech() {
  const hablar = (texto, velocidad = 0.9) => {
    if (!window.speechSynthesis) return;
    const utterance = new SpeechSynthesisUtterance(texto);
    utterance.lang = navigator.language?.startsWith('es') ? navigator.language : 'es-PE';
    utterance.rate = velocidad;
    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(utterance);
  };

  const detener = () => {
    if (window.speechSynthesis) window.speechSynthesis.cancel();
  };

  return { hablar, detener };
}