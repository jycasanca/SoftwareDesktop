import { useEffect, useState } from 'react';
import { api } from '../services/api.js';
import SurfaceCard from '../components/common/SurfaceCard.jsx';

export default function Historial() {
  const [asientos, setAsientos] = useState([]);
  const [mostrarEliminados, setMostrarEliminados] = useState(true);
  const [filtro, setFiltro] = useState('');

  useEffect(() => {
    api.getAsientos(`?page=1&limit=20&incluir_eliminados=${mostrarEliminados}`)
      .then((data) => setAsientos(data.data || []))
      .catch(() => setAsientos([]));
  }, [mostrarEliminados]);

  const items = asientos.filter((item) => {
    const query = filtro.trim().toLowerCase();
    if (!query) return true;
    return (
      (item.descripcion || '').toLowerCase().includes(query) ||
      (item.debe_nombre || item.cuenta_debe || '').toLowerCase().includes(query) ||
      (item.haber_nombre || item.cuenta_haber || '').toLowerCase().includes(query)
    );
  });

  return (
    <section>
      <div className="legacy-header">
        <div>
          <h1 className="legacy-page-title mb-1">Libro Diario</h1>
          <p className="legacy-page-subtitle mb-0">Asientos activos y removidos</p>
        </div>
        <button className="btn btn-outline-light btn-sm" type="button">Exportar PDF</button>
      </div>
      <SurfaceCard className="p-4">
      <div className="d-flex flex-column flex-lg-row gap-3 mb-3">
        <div className="form-check form-switch align-self-center mb-0">
          <input className="form-check-input" type="checkbox" id="mostrarEliminados" checked={mostrarEliminados} onChange={(event) => setMostrarEliminados(event.target.checked)} />
          <label className="form-check-label" htmlFor="mostrarEliminados">Mostrar eliminados</label>
        </div>
        <input
          className="form-control"
          placeholder="Filtrar por descripcion o cuenta..."
          value={filtro}
          onChange={(event) => setFiltro(event.target.value)}
        />
      </div>
      <div className="table-responsive">
        <table className="table table-dark table-hover align-middle mb-0">
          <thead>
            <tr>
              <th>Fecha</th>
              <th>Descripción</th>
              <th>DEBE</th>
              <th>HABER</th>
              <th>Monto</th>
              <th>Estado</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item) => (
              <tr key={item.id}>
                <td>{item.fecha}</td>
                <td>{item.descripcion}</td>
                <td>{item.debe_nombre || item.cuenta_debe}</td>
                <td>{item.haber_nombre || item.cuenta_haber}</td>
                <td>S/ {item.monto}</td>
                <td><span className={`badge ${item.eliminado ? 'text-bg-danger' : 'text-bg-success'}`}>{item.eliminado ? 'REMOVIDO' : 'ACTIVO'}</span></td>
              </tr>
            ))}
            {!items.length ? (
              <tr>
                <td colSpan="6" className="text-center text-muted-soft py-4">No hay registros con ese filtro.</td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </div>
      </SurfaceCard>
    </section>
  );
}