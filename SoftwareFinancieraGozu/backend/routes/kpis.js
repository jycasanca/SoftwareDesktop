export function registerKpiRoutes(app, db) {
  app.get('/api/kpis', async (_request, response, next) => {
    try {
      const kpis = await db.all('SELECT nombre, formula_sql, descripcion, icono, unidad FROM kpi_config WHERE activo = 1 ORDER BY id');
      const values = [];
      for (const kpi of kpis) {
        const result = await db.get(kpi.formula_sql);
        const value = result ? Object.values(result)[0] : null;
        values.push({ nombre: kpi.nombre, valor: value, unidad: kpi.unidad, icono: kpi.icono, descripcion: kpi.descripcion });
      }

      response.json(values);
    } catch (error) {
      next(error);
    }
  });
}