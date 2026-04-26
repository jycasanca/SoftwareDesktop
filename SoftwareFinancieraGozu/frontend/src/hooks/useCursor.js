import { useEffect, useState } from 'react';
import { api } from '../services/api.js';

const STORAGE_KEY = 'contable-ai-cursor';

export function useCursor() {
  const [vistos, setVistos] = useState(() => JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]'));

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(vistos));
  }, [vistos]);

  const marcarVisto = async (elemento) => {
    if (!elemento || vistos.includes(elemento)) return;
    setVistos((current) => [...current, elemento]);
    try {
      await api.marcarCursor(elemento);
    } catch {
      // se conserva el estado local
    }
  };

  const esPrimerVez = (elemento) => !vistos.includes(elemento);

  return { vistos, marcarVisto, esPrimerVez };
}