export default function SurfaceCard({ title, subtitle, children, className = '' }) {
  return (
    <section className={`surface-card p-4 ${className}`.trim()}>
      {title ? <h2 className="h4 mb-1">{title}</h2> : null}
      {subtitle ? <div className="text-muted-soft mb-3">{subtitle}</div> : null}
      {children}
    </section>
  );
}