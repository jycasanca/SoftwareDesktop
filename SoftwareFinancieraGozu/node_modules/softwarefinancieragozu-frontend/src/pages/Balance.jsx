import { useEffect, useState } from 'react';
import SurfaceCard from '../components/common/SurfaceCard.jsx';
import { api } from '../services/api.js';

export default function Balance() {
  const [balance, setBalance] = useState({ activos: [], pasivos: [], patrimonio: [], total_activos: 0, total_pasivos_patrimonio: 0 });

  useEffect(() => {
    api.getBalanceGeneral().then((data) => setBalance(data || {})).catch(() => {});
  }, []);

  return (
    <section>
      <div className="legacy-header">
        <div>
          <h1 className="legacy-page-title mb-1">Balance Comprobación</h1>
          <p className="legacy-page-subtitle mb-0">Activos, pasivos y patrimonio consolidados</p>
        </div>
        <button className="btn btn-outline-light btn-sm" type="button">Exportar PDF</button>
      </div>

      <SurfaceCard className="p-4">
        <div className="table-responsive">
          <table className="table table-dark mb-0">
            <thead>
              <tr>
                <th>Tipo</th>
                <th>Total</th>
              </tr>
            </thead>
            <tbody>
              <tr><td>Activos</td><td>{balance.total_activos ?? 0}</td></tr>
              <tr><td>Pasivos + Patrimonio</td><td>{balance.total_pasivos_patrimonio ?? 0}</td></tr>
            </tbody>
          </table>
        </div>
      </SurfaceCard>
    </section>
  );
}
