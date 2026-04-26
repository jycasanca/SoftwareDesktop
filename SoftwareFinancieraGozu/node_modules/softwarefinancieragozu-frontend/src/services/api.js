const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:3001/api';

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      ...(options.body instanceof FormData ? {} : { 'Content-Type': 'application/json' }),
      ...(options.headers || {})
    },
    ...options
  });

  if (!response.ok) {
    const errorBody = await response.json().catch(() => ({}));
    throw new Error(errorBody.error || 'Error de API');
  }

  return response.json();
}

export const api = {
  health: () => request('/health'),
  getAsientos: (params = '') => request(`/asientos${params}`),
  getAsiento: (id) => request(`/asientos/${id}`),
  createAsiento: (payload) => request('/asientos', { method: 'POST', body: JSON.stringify(payload) }),
  previewFromText: (texto, tipo = 'texto') => request('/asientos/desde-texto', { method: 'POST', body: JSON.stringify({ texto, tipo }) }),
  confirmarRecepcion: (idRecepcion) => request(`/asientos/confirmar/${idRecepcion}`, { method: 'POST', body: '{}' }),
  deleteAsiento: (id, motivo) => request(`/asientos/${id}`, { method: 'DELETE', body: JSON.stringify({ motivo }) }),
  getPlanContable: () => request('/plan-contable'),
  getDiccionario: () => request('/diccionario'),
  addSinonimo: (payload) => request('/diccionario', { method: 'POST', body: JSON.stringify(payload) }),
  getConfig: () => request('/config'),
  saveConfig: (payload) => request('/config', { method: 'POST', body: JSON.stringify(payload) }),
  getKpis: () => request('/kpis'),
  getLibroMayor: () => request('/reportes/libro-mayor'),
  getBalanceGeneral: () => request('/reportes/balance-general'),
  getEstadoResultados: () => request('/reportes/estado-resultados'),
  marcarCursor: (elemento) => request('/cursor/marcar', { method: 'POST', body: JSON.stringify({ elemento }) }),
  vistosCursor: () => request('/cursor/vistos')
};