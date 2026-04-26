export default function StatCard({ icon, title, value, unit, tone = 'accent', description }) {
  const toneClass = tone === 'success' ? 'text-success' : tone === 'danger' ? 'text-danger' : 'text-info';

  return (
    <div className="surface-card p-3 h-100">
      <div className={`fs-3 ${toneClass}`}>{icon}</div>
      <div className="fw-semibold mb-1">{title}</div>
      <div className="display-6 mb-1" style={{ fontSize: '2rem' }}>{value ?? 0}</div>
      {unit ? <div className="text-muted-soft small">{unit}</div> : null}
      {description ? <div className="text-muted-soft small mt-2">{description}</div> : null}
    </div>
  );
}