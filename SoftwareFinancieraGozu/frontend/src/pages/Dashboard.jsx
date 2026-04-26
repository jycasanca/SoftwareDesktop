import { Link } from 'react-router-dom';
import { useEffect, useState } from 'react';
import { api } from '../services/api.js';
import SurfaceCard from '../components/common/SurfaceCard.jsx';

export default function Dashboard() {
  const [kpis, setKpis] = useState([]);

  useEffect(() => {
    api.getKpis().then(setKpis).catch(() => setKpis([]));
  }, []);

  return (
    <section>
      <div className="legacy-header">
        <div>
          <h1 className="legacy-page-title mb-1">Dashboard</h1>
          <p className="legacy-page-subtitle mb-0">Resumen general del periodo contable</p>
        </div>
        <Link className="btn btn-accent" to="/registrar">Nuevo Asiento</Link>
      </div>

      <div className="row g-3 mb-4">
        {kpis.slice(0, 4).map((kpi) => (
          <div className="col-12 col-sm-6 col-xl-3" key={kpi.nombre}>
            <SurfaceCard className="p-3 h-100">
              <div className="text-muted-soft small">{kpi.nombre}</div>
              <div className="fs-3 fw-semibold">{kpi.valor ?? 0}</div>
              <div className="text-muted-soft small">{kpi.unidad || 'indicador'}</div>
            </SurfaceCard>
          </div>
        ))}
      </div>

      <div className="row g-3">
        <div className="col-12 col-lg-6">
          <SurfaceCard title="Acceso rápido" className="p-4">
            <div className="d-grid gap-2">
              <Link className="btn btn-outline-light text-start" to="/libro-diario">Libro Diario</Link>
              <Link className="btn btn-outline-light text-start" to="/libro-mayor">Libro Mayor</Link>
              <Link className="btn btn-outline-light text-start" to="/balance">Balance Comprobación</Link>
              <Link className="btn btn-outline-light text-start" to="/eeff">Estados Financieros</Link>
            </div>
          </SurfaceCard>
        </div>
        <div className="col-12 col-lg-6">
          <SurfaceCard title="Estado del sistema" className="p-4">
            <p className="text-muted-soft mb-3">Motor IA activo, registro centralizado y reportes listos para exportar.</p>
            <div className="d-flex gap-2 flex-wrap">
              <span className="kpi-badge">Asientos</span>
              <span className="kpi-badge">Reportes</span>
              <span className="kpi-badge">Configuración</span>
            </div>
          </SurfaceCard>
        </div>
      </div>
    </section>
  );
}
