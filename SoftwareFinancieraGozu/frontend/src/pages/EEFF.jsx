import { useEffect, useState } from 'react';
import SurfaceCard from '../components/common/SurfaceCard.jsx';
import { api } from '../services/api.js';

export default function EEFF() {
  const [estado, setEstado] = useState({ ingresos: 0, gastos: 0, utilidad_neta: 0, margen_porcentaje: 0 });
  const [balance, setBalance] = useState({ total_activos: 0, total_pasivos_patrimonio: 0 });

  useEffect(() => {
    Promise.all([api.getEstadoResultados(), api.getBalanceGeneral()])
      .then(([estadoData, balanceData]) => {
        setEstado(estadoData || {});
        setBalance(balanceData || {});
      })
      .catch(() => {});
  }, []);

  return (
    <section>
      <div className="legacy-header">
        <div>
          <h1 className="legacy-page-title mb-1">Estados Financieros</h1>
          <p className="legacy-page-subtitle mb-0">Situación financiera y estado de resultados</p>
        </div>
        <button className="btn btn-outline-light btn-sm" type="button">Exportar PDF</button>
      </div>

      <ul className="nav nav-tabs mb-3 border-secondary">
        <li className="nav-item">
          <button className="nav-link active bg-transparent text-light" data-bs-toggle="tab" data-bs-target="#situacion" type="button">Situación Financiera</button>
        </li>
        <li className="nav-item">
          <button className="nav-link bg-transparent text-light" data-bs-toggle="tab" data-bs-target="#resultados" type="button">Estado de Resultados</button>
        </li>
      </ul>

      <div className="tab-content">
        <div className="tab-pane fade show active" id="situacion">
          <SurfaceCard className="p-4">
            <div className="d-flex justify-content-between mb-2"><span>Total Activos</span><strong>{balance.total_activos ?? 0}</strong></div>
            <div className="d-flex justify-content-between"><span>Total Pasivos + Patrimonio</span><strong>{balance.total_pasivos_patrimonio ?? 0}</strong></div>
          </SurfaceCard>
        </div>
        <div className="tab-pane fade" id="resultados">
          <SurfaceCard className="p-4">
            <div className="d-flex justify-content-between mb-2"><span>Ingresos</span><strong>{estado.ingresos ?? 0}</strong></div>
            <div className="d-flex justify-content-between mb-2"><span>Gastos</span><strong>{estado.gastos ?? 0}</strong></div>
            <div className="d-flex justify-content-between mb-2"><span>Utilidad Neta</span><strong>{estado.utilidad_neta ?? 0}</strong></div>
            <div className="d-flex justify-content-between"><span>Margen %</span><strong>{Number(estado.margen_porcentaje ?? 0).toFixed(2)}%</strong></div>
          </SurfaceCard>
        </div>
      </div>
    </section>
  );
}
