function mapAsientoRow(row) {
  return {
    id: row.id,
    fecha: row.fecha,
    cuenta_debe: row.cuenta_debe,
    cuenta_haber: row.cuenta_haber,
    monto: row.monto,
    descripcion: row.descripcion,
    concepto_std: row.concepto_std,
    eliminado: row.eliminado,
    fecha_eliminado: row.fecha_eliminado,
    motivo_eliminado: row.motivo_eliminado,
    debe_nombre: row.debe_nombre,
    haber_nombre: row.haber_nombre
  };
}

export function registerAsientosRoutes(app, db, upload) {
  app.get('/api/asientos', async (request, response, next) => {
    try {
      const page = Number(request.query.page || 1);
      const limit = Number(request.query.limit || 20);
      const offset = (page - 1) * limit;
      const incluirEliminados = String(request.query.incluir_eliminados || 'false') === 'true';
      const desde = request.query.desde;
      const hasta = request.query.hasta;

      const filters = [];
      const params = [];

      if (!incluirEliminados) filters.push('ld.eliminado = 0');
      if (desde) { filters.push('ld.fecha >= ?'); params.push(desde); }
      if (hasta) { filters.push('ld.fecha <= ?'); params.push(hasta); }

      const whereClause = filters.length ? `WHERE ${filters.join(' AND ')}` : '';
      const totalResult = await db.get(`SELECT COUNT(*) AS total FROM libro_diario ld ${whereClause}`, params);
      const total = totalResult?.total || 0;
      const rows = await db.all(`
        SELECT ld.*, debe.descripcion AS debe_nombre, haber.descripcion AS haber_nombre
        FROM libro_diario ld
        LEFT JOIN plan_contable debe ON debe.codigo = ld.cuenta_debe
        LEFT JOIN plan_contable haber ON haber.codigo = ld.cuenta_haber
        ${whereClause}
        ORDER BY ld.fecha DESC, ld.id DESC
        LIMIT ? OFFSET ?
      `, [...params, limit, offset]);

      response.json({ page, limit, total, data: rows.map(mapAsientoRow) });
    } catch (error) {
      next(error);
    }
  });

  app.get('/api/asientos/:id', async (request, response, next) => {
    try {
      const row = await db.get(`
      SELECT ld.*, debe.descripcion AS debe_nombre, haber.descripcion AS haber_nombre
      FROM libro_diario ld
      LEFT JOIN plan_contable debe ON debe.codigo = ld.cuenta_debe
      LEFT JOIN plan_contable haber ON haber.codigo = ld.cuenta_haber
      WHERE ld.id = ?
    `, [request.params.id]);

      if (!row) {
        return response.status(404).json({ error: 'Asiento no encontrado' });
      }

      response.json(mapAsientoRow(row));
    } catch (error) {
      next(error);
    }
  });

  app.post('/api/asientos', async (request, response, next) => {
    try {
      const { fecha = new Date().toISOString().slice(0, 10), cuenta_debe, cuenta_haber, monto, descripcion, id_recepcion } = request.body || {};

      if (!cuenta_debe || !cuenta_haber || !descripcion) return response.status(400).json({ error: 'Faltan campos requeridos' });

      const montoNumero = Number(monto);
      if (!Number.isFinite(montoNumero) || montoNumero <= 0) return response.status(400).json({ error: 'El monto debe ser mayor a 0' });

      const cuentaDebeExiste = await db.get('SELECT codigo FROM plan_contable WHERE codigo = ? AND activo = 1', [cuenta_debe]);
      const cuentaHaberExiste = await db.get('SELECT codigo FROM plan_contable WHERE codigo = ? AND activo = 1', [cuenta_haber]);

      if (!cuentaDebeExiste || !cuentaHaberExiste) return response.status(400).json({ error: 'Las cuentas no existen o están inactivas' });

      const result = await db.run(
        'INSERT INTO libro_diario (fecha, cuenta_debe, cuenta_haber, monto, descripcion, id_recepcion) VALUES (?, ?, ?, ?, ?, ?)',
        [fecha, cuenta_debe, cuenta_haber, montoNumero, descripcion, id_recepcion || null]
      );

      response.status(201).json({ id: result.lastInsertRowid, fecha, cuenta_debe, cuenta_haber, monto: montoNumero, descripcion, id_recepcion: id_recepcion || null });
    } catch (error) {
      next(error);
    }
  });

  app.post('/api/asientos/desde-texto', async (request, response, next) => {
    try {
      const { texto = '', tipo = 'texto' } = request.body || {};
      const montoDetectado = Number((texto.match(/\d+[\.,]?\d*/)?.[0] || '0').replace(',', '.')) || 0;
      const textoNormalizado = texto.toLowerCase();
      let cuentaDebe = '10';
      let cuentaHaber = '40';

      if (textoNormalizado.includes('banco') || textoNormalizado.includes('transferencia')) {
        cuentaDebe = '12';
        cuentaHaber = '40';
      } else if (textoNormalizado.includes('compra') || textoNormalizado.includes('alquiler') || textoNormalizado.includes('planilla') || textoNormalizado.includes('gasto')) {
        cuentaDebe = '50';
        cuentaHaber = '10';
      }

      const recepcion = await db.run(
        "INSERT INTO registro_recepcion (enunciado_raw, enunciado_norm, tipo, estado_proceso) VALUES (?, ?, ?, 'pendiente')",
        [texto, texto, tipo]
      );

      response.status(201).json({
        id_recepcion: recepcion.lastInsertRowid,
        preview: {
          fecha: new Date().toISOString().slice(0, 10),
          descripcion: texto,
          cuenta_debe: cuentaDebe,
          cuenta_haber: cuentaHaber,
          monto: montoDetectado > 0 ? montoDetectado : 1
        }
      });
    } catch (error) {
      next(error);
    }
  });

  app.post('/api/asientos/confirmar/:id_recepcion', (request, response) => {
    response.json({ ok: true, id_recepcion: Number(request.params.id_recepcion) });
  });

  app.delete('/api/asientos/:id', async (request, response, next) => {
    try {
      const motivo = request.body?.motivo || 'Sin motivo';
      const result = await db.run(
        'UPDATE libro_diario SET eliminado = 1, fecha_eliminado = CURRENT_TIMESTAMP, motivo_eliminado = ? WHERE id = ?',
        [motivo, request.params.id]
      );

      if (result.changes === 0) {
        return response.status(404).json({ error: 'Asiento no encontrado' });
      }

      response.json({ message: 'Asiento removido correctamente' });
    } catch (error) {
      next(error);
    }
  });
}