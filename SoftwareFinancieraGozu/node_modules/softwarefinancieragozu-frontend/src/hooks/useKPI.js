import { useEffect, useState } from 'react';
import { api } from '../services/api.js';

export function useKPI() {
  const [kpis, setKpis] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let cancelled = false;

    api.getKpis()
      .then((data) => { if (!cancelled) { setKpis(data); setError(''); } })
      .catch((fetchError) => { if (!cancelled) { setError(fetchError.message); setKpis([]); } })
      .finally(() => { if (!cancelled) setLoading(false); });

    return () => { cancelled = true; };
  }, []);

  return { kpis, loading, error };
}