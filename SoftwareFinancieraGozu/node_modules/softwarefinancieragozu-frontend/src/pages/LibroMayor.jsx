import { useEffect, useState } from 'react';
import SurfaceCard from '../components/common/SurfaceCard.jsx';
import { api } from '../services/api.js';

export default function LibroMayor() {
  const [items, setItems] = useState([]);

  useEffect(() => {
    api.getLibroMayor().then((data) => setItems(data || [])).catch(() => setItems([]));
  }, []);

  return (
    <section>
      <div className="legacy-header">
        <div>
          <h1 className="legacy-page-title mb-1">Libro Mayor</h1>
          <p className="legacy-page-subtitle mb-0">Movimientos agrupados por cuenta contable</p>
        </div>
      </div>

      <SurfaceCard className="p-4">
        <div className="table-responsive">
          <table className="table table-dark table-hover mb-0">
            <thead>
              <tr>
                <th>Codigo</th>
                <th>Descripcion</th>
                <th>Total Debe</th>
                <th>Total Haber</th>
                <th>Saldo</th>
              </tr>
            </thead>
            <tbody>
              {items.map((row) => (
                <tr key={row.codigo}>
                  <td className="font-monospace">{row.codigo}</td>
                  <td>{row.descripcion}</td>
                  <td>{row.total_debe}</td>
                  <td>{row.total_haber}</td>
                  <td>{row.saldo}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </SurfaceCard>
    </section>
  );
}
