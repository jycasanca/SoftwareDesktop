import { useMemo, useState } from 'react';
import { api } from '../services/api.js';
import { useCursor } from '../hooks/useCursor.js';
import { useSpeech } from '../hooks/useSpeech.js';
import SurfaceCard from '../components/common/SurfaceCard.jsx';

export default function Ingresar() {
  const [modo, setModo] = useState('texto');
  const [texto, setTexto] = useState('');
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [mensaje, setMensaje] = useState('');
  const { hablar } = useSpeech();
  const { marcarVisto, esPrimerVez } = useCursor();
  const progreso = useMemo(() => {
    if (!texto.trim()) return 20;
    if (!preview) return 65;
    return 100;
  }, [texto, preview]);

  const interpretar = async () => {
    setLoading(true);
    setMensaje('Analizando con IA...');
    try {
      const data = await api.previewFromText(texto, modo);
      setPreview(data.preview);
      setMensaje('Previsualización lista.');
      await marcarVisto('ingresar.texto');
    } catch (error) {
      setMensaje(error.message);
    } finally {
      setLoading(false);
    }
  };

  const confirmar = async () => {
    if (!preview) return;
    setLoading(true);
    try {
      await api.createAsiento(preview);
      setTexto('');
      setPreview(null);
      setMensaje('Asiento registrado correctamente.');
      hablar('El asiento fue registrado correctamente.');
    } catch (error) {
      setMensaje(error.message);
    } finally {
      setLoading(false);
    }
  };

  const explicar = () => {
    hablar('Aquí puedes escribir cualquier movimiento de dinero en palabras normales. También puedes grabar tu voz o subir una foto de una factura. La inteligencia artificial interpretará automáticamente la cuenta contable correcta.');
  };

  return (
    <section className="d-grid gap-4 mx-auto" style={{ maxWidth: 960 }}>
      <div className="legacy-header">
        <div>
          <h1 className="legacy-page-title mb-1">Registrar Asiento</h1>
          <p className="legacy-page-subtitle mb-0">Asistente IA para registro contable guiado</p>
        </div>
      </div>
      <SurfaceCard className="p-4 p-lg-5">
        <div className="d-flex flex-column flex-lg-row align-items-lg-center justify-content-between gap-3 mb-3">
          <div className="text-muted-soft">Texto, voz o imagen, todo en un flujo interactivo.</div>
          <div className="d-flex flex-wrap gap-2">
            <button className="btn btn-outline-light btn-sm" type="button" onClick={explicar}>Explicar seccion</button>
            {esPrimerVez('ingresar.texto') ? <span className="badge text-bg-warning align-self-center">Primera vez</span> : null}
          </div>
        </div>

        <div className="mb-3">
          <div className="progress" role="progressbar" aria-label="Progreso de registro" aria-valuemin="0" aria-valuemax="100" aria-valuenow={progreso} style={{ height: '10px' }}>
            <div className="progress-bar bg-light text-dark" style={{ width: `${progreso}%` }}></div>
          </div>
          <div className="text-muted-soft small mt-2">Progreso del flujo: {progreso}%</div>
        </div>

        <ul className="nav nav-pills mb-3 gap-2">
          <li className="nav-item"><button type="button" onClick={() => setModo('texto')} className={`btn ${modo === 'texto' ? 'btn-accent' : 'btn-outline-light'} btn-sm`}>Texto</button></li>
          <li className="nav-item"><button type="button" onClick={() => setModo('voz')} className={`btn ${modo === 'voz' ? 'btn-accent' : 'btn-outline-light'} btn-sm`}>Voz</button></li>
          <li className="nav-item"><button type="button" onClick={() => setModo('imagen')} className={`btn ${modo === 'imagen' ? 'btn-accent' : 'btn-outline-light'} btn-sm`}>Imagen</button></li>
        </ul>

        <textarea
          className="form-control form-control-lg mb-3"
          rows="6"
          value={texto}
          onChange={(event) => setTexto(event.target.value)}
          placeholder='Ej: "Vendí 500 soles en efectivo" o "Compré mercadería por 2000"'
        />
        <div className="d-flex flex-wrap gap-2 mb-4">
          <button className="btn btn-outline-light btn-sm" type="button" onClick={() => setTexto('Venta en efectivo de S/ 950 de servicio de consultoria')}>Demo rapida</button>
          <button className="btn btn-outline-light btn-sm" type="button" onClick={() => setTexto('Compra de mercaderia por S/ 2,000 pagada con transferencia bancaria')}>Plantilla compra</button>
          <button className="btn btn-outline-light btn-sm" type="button" onClick={() => setTexto('Pago de alquiler mensual por S/ 1,800 desde caja')}>Plantilla gasto</button>
        </div>

        <button className="btn btn-accent btn-lg w-100 mb-3" type="button" onClick={interpretar} disabled={loading || !texto.trim()}>
          {loading ? 'Procesando...' : 'Interpretar y registrar'}
        </button>
        {mensaje ? <div className="alert alert-secondary bg-dark text-light border-light-subtle">{mensaje}</div> : null}
      </SurfaceCard>

      {preview ? (
        <SurfaceCard className="p-4">
          <div className="d-flex flex-column flex-md-row justify-content-between align-items-md-center gap-3 mb-3">
            <h3 className="h4 mb-0">Previsualizacion del asiento</h3>
            <button className="btn btn-success" type="button" onClick={confirmar} disabled={loading}>Confirmar</button>
          </div>
          <div className="row g-3">
            <div className="col-12 col-md-6">
              <div className="surface-card p-3 h-100">
                <div className="text-muted-soft small">Cuenta debe</div>
                <div className="fw-semibold">{preview.cuenta_debe}</div>
              </div>
            </div>
            <div className="col-12 col-md-6">
              <div className="surface-card p-3 h-100">
                <div className="text-muted-soft small">Cuenta haber</div>
                <div className="fw-semibold">{preview.cuenta_haber}</div>
              </div>
            </div>
            <div className="col-12 col-md-6">
              <div className="surface-card p-3 h-100">
                <div className="text-muted-soft small">Fecha</div>
                <div className="fw-semibold">{preview.fecha}</div>
              </div>
            </div>
            <div className="col-12 col-md-6">
              <div className="surface-card p-3 h-100">
                <div className="text-muted-soft small">Monto</div>
                <div className="fw-semibold">S/ {preview.monto}</div>
              </div>
            </div>
          </div>
        </SurfaceCard>
      ) : (
        <SurfaceCard className="p-4">
          <div className="accordion accordion-flush" id="faqIngresar">
            <div className="accordion-item bg-transparent text-light border border-secondary-subtle rounded-3 mb-2">
              <h2 className="accordion-header">
                <button className="accordion-button collapsed bg-transparent text-light" type="button" data-bs-toggle="collapse" data-bs-target="#ingresoTip1">
                  Como funciona esta pantalla
                </button>
              </h2>
              <div id="ingresoTip1" className="accordion-collapse collapse" data-bs-parent="#faqIngresar">
                <div className="accordion-body text-muted-soft">
                  Escribe tu movimiento y la IA propone automaticamente el asiento contable para confirmar.
                </div>
              </div>
            </div>
          </div>
        </SurfaceCard>
      )}
    </section>
  );
}