import { Navigate, Route, Routes } from 'react-router-dom';
import AppLayout from './components/layout/AppLayout.jsx';
import Dashboard from './pages/Dashboard.jsx';
import Ingresar from './pages/Ingresar.jsx';
import Historial from './pages/Historial.jsx';
import LibroMayor from './pages/LibroMayor.jsx';
import Balance from './pages/Balance.jsx';
import EEFF from './pages/EEFF.jsx';
import Configuracion from './pages/Configuracion.jsx';

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<AppLayout><Dashboard /></AppLayout>} />
      <Route path="/registrar" element={<AppLayout><Ingresar /></AppLayout>} />
      <Route path="/libro-diario" element={<AppLayout><Historial /></AppLayout>} />
      <Route path="/libro-mayor" element={<AppLayout><LibroMayor /></AppLayout>} />
      <Route path="/balance" element={<AppLayout><Balance /></AppLayout>} />
      <Route path="/eeff" element={<AppLayout><EEFF /></AppLayout>} />
      <Route path="/configuracion" element={<AppLayout><Configuracion /></AppLayout>} />
      <Route path="/ingresar" element={<Navigate to="/registrar" replace />} />
      <Route path="/historial" element={<Navigate to="/libro-diario" replace />} />
      <Route path="/reportes" element={<Navigate to="/eeff" replace />} />
      <Route path="/config" element={<Navigate to="/configuracion" replace />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}