import { NavLink } from 'react-router-dom';
import { BookOpenText, ChartColumn, ClipboardList, LayoutDashboard, Menu, Settings, FileBarChart2, Sparkles } from 'lucide-react';

const navItems = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/registrar', label: 'Registrar Asiento', icon: BookOpenText },
  { to: '/libro-diario', label: 'Libro Diario', icon: ClipboardList },
  { to: '/libro-mayor', label: 'Libro Mayor', icon: ChartColumn },
  { to: '/balance', label: 'Balance Comprobación', icon: FileBarChart2 },
  { to: '/eeff', label: 'Estados Financieros', icon: ChartColumn },
  { to: '/configuracion', label: 'Configuración', icon: Settings }
];

function Sidebar() {
  return (
    <aside className="sidebar d-none d-md-flex flex-column" style={{ width: 256 }}>
      <div className="mb-4">
        <div className="fw-semibold d-flex align-items-center gap-2 px-3 pt-4">
          <Sparkles size={18} className="text-light floating-pulse" />
          <span className="legacy-brand">Contador IA</span>
        </div>
        <div className="text-muted-soft small px-3">Asistente Contable</div>
      </div>
      <nav className="nav flex-column gap-1 px-2">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink key={item.to} end={item.to === '/'} className="nav-link nav-link-custom px-3 py-2 d-flex align-items-center gap-2" to={item.to}>
              <Icon size={18} />
              {item.label}
            </NavLink>
          );
        })}
      </nav>
      <div className="mt-auto text-muted-soft legacy-side-footer">
        Metodo contable activo
      </div>
    </aside>
  );
}

function Topbar() {
  return (
    <div className="topbar-mobile d-md-none sticky-top p-3 border-bottom">
      <div className="d-flex align-items-center justify-content-between">
        <div className="fw-semibold legacy-brand">Contador IA</div>
        <button className="btn btn-outline-light btn-sm" type="button" data-bs-toggle="offcanvas" data-bs-target="#mobileNav" aria-controls="mobileNav">
          <Menu size={18} className="me-1" /> Menú
        </button>
      </div>
      <div className="offcanvas offcanvas-start bg-dark text-light" tabIndex="-1" id="mobileNav" aria-labelledby="mobileNavLabel">
        <div className="offcanvas-header">
          <h5 className="offcanvas-title" id="mobileNavLabel">Contable AI</h5>
          <button type="button" className="btn-close btn-close-white" data-bs-dismiss="offcanvas" aria-label="Cerrar"></button>
        </div>
        <div className="offcanvas-body">
          <nav className="nav flex-column gap-2">
            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink key={item.to} end={item.to === '/'} className="nav-link nav-link-custom px-3 py-2 d-flex align-items-center gap-2" to={item.to} data-bs-dismiss="offcanvas">
                  <Icon size={18} />
                  {item.label}
                </NavLink>
              );
            })}
          </nav>
        </div>
      </div>
    </div>
  );
}

export default function AppLayout({ children }) {
  return (
    <div className="app-shell d-flex flex-column flex-md-row">
      <div className="hero-glow" style={{ top: '-18rem', left: '-11rem' }}></div>
      <div className="hero-glow" style={{ right: '-12rem', top: '14rem' }}></div>
      <Sidebar />
      <Topbar />
      <main className="flex-grow-1 min-vw-0">
        <div className="legacy-page-wrap">
          {children}
        </div>
      </main>
    </div>
  );
}