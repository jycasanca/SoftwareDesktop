export function registerReportesRoutes(app, db) {
  app.get('/api/reportes/libro-mayor', async (_request, response, next) => {
    try {
      const rows = await db.all('SELECT codigo, descripcion, total_debe, total_haber, saldo FROM v_libro_mayor ORDER BY codigo');
      response.json(rows);
    } catch (error) {
      next(error);
    }
  });

  app.get('/api/reportes/balance-general', async (_request, response, next) => {
    try {
      const rows = await db.all('SELECT tipo_cuenta, total FROM v_balance_general');
      response.json({
        activos: rows.filter((row) => row.tipo_cuenta === 'ACTIVO'),
        pasivos: rows.filter((row) => row.tipo_cuenta === 'PASIVO'),
        patrimonio: rows.filter((row) => row.tipo_cuenta === 'PATRIMONIO'),
        total_activos: rows.find((row) => row.tipo_cuenta === 'ACTIVO')?.total || 0,
        total_pasivos_patrimonio: (rows.find((row) => row.tipo_cuenta === 'PASIVO')?.total || 0) + (rows.find((row) => row.tipo_cuenta === 'PATRIMONIO')?.total || 0)
      });
    } catch (error) {
      next(error);
    }
  });

  app.get('/api/reportes/estado-resultados', async (_request, response, next) => {
    try {
      const rows = await db.all('SELECT categoria, total FROM v_estado_resultados');
      const ingresos = rows.find((row) => row.categoria === 'INGRESOS')?.total || 0;
      const gastos = rows.find((row) => row.categoria === 'GASTOS')?.total || 0;
      const utilidadNeta = rows.find((row) => row.categoria === 'UTILIDAD NETA')?.total || 0;

      response.json({ ingresos, gastos, utilidad_neta: utilidadNeta, margen_porcentaje: ingresos ? (utilidadNeta * 100) / ingresos : 0 });
    } catch (error) {
      next(error);
    }
  });

  app.get('/api/reportes/flujo-caja', (request, response) => {
    const periodo = request.query.periodo || 'mes';
    response.json({ periodo, data: [] });
  });
}