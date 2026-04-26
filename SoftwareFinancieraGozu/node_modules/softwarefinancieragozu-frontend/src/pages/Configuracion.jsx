import { useEffect, useState } from 'react';
import { api } from '../services/api.js';
import SurfaceCard from '../components/common/SurfaceCard.jsx';

export default function Configuracion() {
  const [config, setConfig] = useState({ empresa_nombre: '', moneda: 'PEN', ollama_url: 'http://localhost:11434', ollama_model: 'llama3.2' });
  const [diccionario, setDiccionario] = useState([]);
  const [plan, setPlan] = useState([]);
  const [nuevoSinonimo, setNuevoSinonimo] = useState({ palabra_usuario: '', concepto_estandar: '' });
  const [estadoGuardado, setEstadoGuardado] = useState('');

  useEffect(() => {
    Promise.all([api.getConfig(), api.getDiccionario(), api.getPlanContable()])
      .then(([configData, diccionarioData, planData]) => {
        setConfig((current) => ({ ...current, ...(configData.data || {}) }));
        setDiccionario(diccionarioData.data || []);
        setPlan(planData.data || []);
      })
      .catch(() => {});
  }, []);

  const guardar = async () => {
    await api.saveConfig(config);
    setEstadoGuardado('Configuracion guardada correctamente.');
    setTimeout(() => setEstadoGuardado(''), 2500);
  };

  const agregarSinonimo = async () => {
    await api.addSinonimo(nuevoSinonimo);
    setNuevoSinonimo({ palabra_usuario: '', concepto_estandar: '' });
    const diccionarioData = await api.getDiccionario();
    setDiccionario(diccionarioData.data || []);
  };

  return (
    <section className="d-grid gap-3">
      <div className="legacy-header">
        <div>
          <h1 className="legacy-page-title mb-1">Configuración</h1>
          <p className="legacy-page-subtitle mb-0">Diccionario, plan contable y reglas del sistema</p>
        </div>
      </div>

      <ul className="nav nav-tabs border-secondary">
        <li className="nav-item"><button className="nav-link active bg-transparent text-light" data-bs-toggle="tab" data-bs-target="#cfg-general" type="button">General</button></li>
        <li className="nav-item"><button className="nav-link bg-transparent text-light" data-bs-toggle="tab" data-bs-target="#cfg-plan" type="button">Plan</button></li>
        <li className="nav-item"><button className="nav-link bg-transparent text-light" data-bs-toggle="tab" data-bs-target="#cfg-diccionario" type="button">Diccionario</button></li>
      </ul>

      <div className="tab-content d-grid gap-4">
        <div className="tab-pane fade show active" id="cfg-general">
          <SurfaceCard title="Configuración general" subtitle="Nombre, moneda y conectividad" className="p-4">
        <div className="row g-3">
          <div className="col-12 col-md-6"><label className="form-label">Nombre de empresa</label><input className="form-control" value={config.empresa_nombre || ''} onChange={(event) => setConfig({ ...config, empresa_nombre: event.target.value })} /></div>
          <div className="col-12 col-md-3"><label className="form-label">Moneda</label><select className="form-select" value={config.moneda || 'PEN'} onChange={(event) => setConfig({ ...config, moneda: event.target.value })}><option value="PEN">PEN</option><option value="USD">USD</option><option value="EUR">EUR</option></select></div>
          <div className="col-12 col-md-6"><label className="form-label">URL de Ollama</label><input className="form-control" value={config.ollama_url || ''} onChange={(event) => setConfig({ ...config, ollama_url: event.target.value })} /></div>
          <div className="col-12 col-md-3"><label className="form-label">Modelo Ollama</label><input className="form-control" value={config.ollama_model || ''} onChange={(event) => setConfig({ ...config, ollama_model: event.target.value })} /></div>
        </div>
        <div className="mt-3 d-flex flex-wrap gap-2">
          <button className="btn btn-accent" type="button" onClick={guardar}>Guardar configuracion</button>
          <button className="btn btn-outline-light" type="button" data-bs-toggle="modal" data-bs-target="#previewConfigModal">Vista previa</button>
        </div>
        {estadoGuardado ? <div className="alert bg-dark text-light border-light-subtle mt-3 mb-0">{estadoGuardado}</div> : null}
          </SurfaceCard>
        </div>

        <div className="tab-pane fade" id="cfg-plan">
          <SurfaceCard title="Cuentas contables" subtitle="Vista del plan contable activo" className="p-4">
        <div className="table-responsive"><table className="table table-dark table-sm mb-0"><thead><tr><th>Código</th><th>Descripción</th><th>Tipo</th><th>Naturaleza</th></tr></thead><tbody>{plan.map((row) => (<tr key={row.codigo}><td>{row.codigo}</td><td>{row.descripcion}</td><td>{row.tipo_cuenta}</td><td>{row.naturaleza}</td></tr>))}</tbody></table></div>
          </SurfaceCard>
        </div>

        <div className="tab-pane fade" id="cfg-diccionario">
          <SurfaceCard title="Sinónimos y palabras clave" subtitle="Entrenamiento del diccionario" className="p-4">
        <div className="row g-2 mb-3">
          <div className="col-12 col-md-5"><input className="form-control" placeholder="Palabra usuario" value={nuevoSinonimo.palabra_usuario} onChange={(event) => setNuevoSinonimo({ ...nuevoSinonimo, palabra_usuario: event.target.value })} /></div>
          <div className="col-12 col-md-5"><input className="form-control" placeholder="Concepto estándar" value={nuevoSinonimo.concepto_estandar} onChange={(event) => setNuevoSinonimo({ ...nuevoSinonimo, concepto_estandar: event.target.value })} /></div>
          <div className="col-12 col-md-2"><button className="btn btn-success w-100" type="button" onClick={agregarSinonimo}>Agregar</button></div>
        </div>
        <div className="small text-muted-soft mb-2">Total: {diccionario.length}</div>
          </SurfaceCard>
        </div>
      </div>

      <div className="modal fade" id="previewConfigModal" tabIndex="-1" aria-labelledby="previewConfigModalLabel" aria-hidden="true">
        <div className="modal-dialog modal-dialog-centered">
          <div className="modal-content bg-black text-white border border-secondary">
            <div className="modal-header border-secondary">
              <h5 className="modal-title" id="previewConfigModalLabel">Vista previa de configuracion</h5>
              <button type="button" className="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
            </div>
            <div className="modal-body">
              <div><strong>Empresa:</strong> {config.empresa_nombre || 'Sin definir'}</div>
              <div><strong>Moneda:</strong> {config.moneda}</div>
              <div><strong>Ollama URL:</strong> {config.ollama_url}</div>
              <div><strong>Modelo:</strong> {config.ollama_model}</div>
            </div>
            <div className="modal-footer border-secondary">
              <button type="button" className="btn btn-outline-light" data-bs-dismiss="modal">Cerrar</button>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}