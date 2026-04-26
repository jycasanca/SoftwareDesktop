import { useEffect, useState } from 'react';
import { api } from '../services/api.js';
import { useSpeech } from '../hooks/useSpeech.js';
import { useCursor } from '../hooks/useCursor.js';
import StatCard from '../components/common/StatCard.jsx';
import SurfaceCard from '../components/common/SurfaceCard.jsx';

export default function Reportes() {
  const [kpis, setKpis] = useState([]);
  const [estado, setEstado] = useState(null);
  const [periodo, setPeriodo] = useState('mensual');
  const { hablar } = useSpeech();
  const { marcarVisto } = useCursor();

  useEffect(() => {
    Promise.all([api.getKpis(), api.getEstadoResultados()])
      .then(([kpiData, estadoData]) => {
        setKpis(kpiData);
        setEstado(estadoData);
        marcarVisto('reportes.principal');
      })
      .catch(() => {
        setKpis([]);
        setEstado(null);
      });
  }, []);

  return (
    <section className="d-grid gap-4">
      <SurfaceCard title="Reportes" subtitle="KPIs, estado de resultados y balance general" className="p-4">
        <div className="d-flex flex-column flex-md-row justify-content-between gap-3 mb-3">
          <div className="btn-group" role="group" aria-label="Selector de periodo">
            <button type="button" className={`btn btn-sm ${periodo === 'semanal' ? 'btn-accent' : 'btn-outline-light'}`} onClick={() => setPeriodo('semanal')}>Semanal</button>
            <button type="button" className={`btn btn-sm ${periodo === 'mensual' ? 'btn-accent' : 'btn-outline-light'}`} onClick={() => setPeriodo('mensual')}>Mensual</button>
            <button type="button" className={`btn btn-sm ${periodo === 'anual' ? 'btn-accent' : 'btn-outline-light'}`} onClick={() => setPeriodo('anual')}>Anual</button>
          </div>
          <button className="btn btn-outline-light btn-sm" type="button" onClick={() => hablar('Aquí puedes revisar los indicadores de desempeño, el estado de resultados y el balance general de la empresa.')}>Explicar seccion</button>
        </div>
        <div className="row g-3">
          {kpis.map((kpi) => (
            <div className="col-12 col-md-6 col-xl-4" key={kpi.nombre}>
              <StatCard icon={kpi.icono} title={kpi.nombre} value={kpi.valor ?? 0} unit={kpi.unidad} description={kpi.descripcion} />
            </div>
          ))}
        </div>
      </SurfaceCard>

      <SurfaceCard title="Estado de Resultados" className="p-4">
        <div className="alert bg-dark text-light border-light-subtle">
          Vista {periodo}: los datos se cargan desde la API y se presentan en tiempo real.
        </div>
        <div className="table-responsive">
          <table className="table table-dark mb-0">
            <thead><tr><th>Ingresos</th><th>Gastos</th><th>Utilidad Neta</th></tr></thead>
            <tbody><tr><td>{estado?.ingresos ?? 0}</td><td>{estado?.gastos ?? 0}</td><td>{estado?.utilidad_neta ?? 0}</td></tr></tbody>
          </table>
        </div>
      </SurfaceCard>

      <SurfaceCard title="Insights Financieros" subtitle="Resumen ejecutivo interactivo" className="p-4">
        <div id="insightsCarousel" className="carousel slide" data-bs-ride="carousel">
          <div className="carousel-inner">
            <div className="carousel-item active">
              <div className="p-4 rounded-4 border border-secondary-subtle">
                <div className="text-muted-soft small">01</div>
                <div className="h5 mt-2">Flujo controlado</div>
                <p className="mb-0 text-muted-soft">Tus asientos mantienen trazabilidad y consistencia entre DEBE y HABER.</p>
              </div>
            </div>
            <div className="carousel-item">
              <div className="p-4 rounded-4 border border-secondary-subtle">
                <div className="text-muted-soft small">02</div>
                <div className="h5 mt-2">KPI accionables</div>
                <p className="mb-0 text-muted-soft">Monitorea margen, liquidez y rentabilidad para tomar decisiones mas rapidas.</p>
              </div>
            </div>
            <div className="carousel-item">
              <div className="p-4 rounded-4 border border-secondary-subtle">
                <div className="text-muted-soft small">03</div>
                <div className="h5 mt-2">Escalable</div>
                <p className="mb-0 text-muted-soft">Frontend modular listo para crecer con nuevos reportes y dashboards.</p>
              </div>
            </div>
          </div>
          <button className="carousel-control-prev" type="button" data-bs-target="#insightsCarousel" data-bs-slide="prev">
            <span className="carousel-control-prev-icon" aria-hidden="true"></span>
            <span className="visually-hidden">Anterior</span>
          </button>
          <button className="carousel-control-next" type="button" data-bs-target="#insightsCarousel" data-bs-slide="next">
            <span className="carousel-control-next-icon" aria-hidden="true"></span>
            <span className="visually-hidden">Siguiente</span>
          </button>
        </div>
      </SurfaceCard>
    </section>
  );
}