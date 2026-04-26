export function registerCursorRoutes(app, db) {
  app.post('/api/cursor/marcar', async (request, response, next) => {
    try {
      const elemento = request.body?.elemento;
      if (!elemento) return response.status(400).json({ error: 'elemento es obligatorio' });

      await db.run('INSERT INTO cursor_sesiones (usuario_id, elemento) VALUES (1, ?)', [elemento]);
      response.json({ ok: true, elemento });
    } catch (error) {
      next(error);
    }
  });

  app.get('/api/cursor/vistos', async (_request, response, next) => {
    try {
      const rows = await db.all('SELECT DISTINCT elemento FROM cursor_sesiones WHERE usuario_id = 1 ORDER BY elemento');
      const vistos = rows.map((row) => row.elemento);
      response.json(vistos);
    } catch (error) {
      next(error);
    }
  });
}