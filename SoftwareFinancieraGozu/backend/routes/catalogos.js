export function registerCatalogosRoutes(app, db) {
  app.get('/api/plan-contable', async (_request, response, next) => {
    try {
      const rows = await db.all('SELECT codigo, descripcion, tipo_cuenta, naturaleza, nivel, cuenta_padre, activo FROM plan_contable WHERE activo = 1 ORDER BY codigo');
      response.json({ data: rows });
    } catch (error) {
      next(error);
    }
  });

  app.get('/api/diccionario', async (_request, response, next) => {
    try {
      const rows = await db.all('SELECT id, palabra_usuario, concepto_estandar, idioma, activo FROM diccionario_sinonimos WHERE activo = 1 ORDER BY palabra_usuario');
      response.json({ data: rows });
    } catch (error) {
      next(error);
    }
  });

  app.post('/api/diccionario', async (request, response, next) => {
    try {
      const { palabra_usuario, concepto_estandar, idioma = 'es' } = request.body || {};
      if (!palabra_usuario || !concepto_estandar) {
        return response.status(400).json({ error: 'palabra_usuario y concepto_estandar son obligatorios' });
      }

      const result = await db.run(
        'INSERT INTO diccionario_sinonimos (palabra_usuario, concepto_estandar, idioma, activo) VALUES (?, ?, ?, 1)',
        [palabra_usuario.trim(), concepto_estandar.trim().toUpperCase(), idioma]
      );
      response.status(201).json({ id: result.lastInsertRowid });
    } catch (error) {
      next(error);
    }
  });

  app.get('/api/config', async (_request, response, next) => {
    try {
      const rows = await db.all('SELECT clave, valor, descripcion FROM config_sistema ORDER BY clave');
      const config = rows.reduce((accumulator, row) => {
        accumulator[row.clave] = row.valor;
        return accumulator;
      }, {});
      response.json({ data: config, rows });
    } catch (error) {
      next(error);
    }
  });

  app.post('/api/config', async (request, response, next) => {
    try {
      const entries = Object.entries(request.body || {});
      await db.exec('BEGIN TRANSACTION;');
      for (const [clave, valor] of entries) {
        await db.run(
          'INSERT INTO config_sistema (clave, valor) VALUES (?, ?) ON CONFLICT(clave) DO UPDATE SET valor = excluded.valor',
          [clave, String(valor)]
        );
      }
      await db.exec('COMMIT;');
      response.json({ ok: true });
    } catch (error) {
      try {
        await db.exec('ROLLBACK;');
      } catch {
        // ignore rollback error
      }
      next(error);
    }
  });
}