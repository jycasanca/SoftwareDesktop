import 'dotenv/config';
import express from 'express';
import cors from 'cors';
import multer from 'multer';
import bodyParser from 'body-parser';
import { initializeDatabase } from './database/init.js';
import { registerAsientosRoutes } from './routes/asientos.js';
import { registerReportesRoutes } from './routes/reportes.js';
import { registerKpiRoutes } from './routes/kpis.js';
import { registerCursorRoutes } from './routes/cursor.js';
import { registerOllamaRoutes } from './routes/ollama.js';
import { registerAudioRoutes } from './routes/audio.js';
import { registerVisionRoutes } from './routes/vision.js';
import { registerCatalogosRoutes } from './routes/catalogos.js';

const app = express();
const upload = multer();
const port = Number(process.env.PORT || 3001);
const allowedOrigins = (process.env.CORS_ORIGIN || 'http://localhost:5173,http://localhost:3000')
  .split(',')
  .map((origin) => origin.trim())
  .filter(Boolean);
app.use(cors({
  origin(origin, callback) {
    if (!origin || allowedOrigins.includes(origin)) {
      callback(null, true);
      return;
    }
    callback(new Error(`Origen no permitido por CORS: ${origin}`));
  }
}));
app.use(bodyParser.json({ limit: '10mb' }));
app.use(bodyParser.urlencoded({ extended: true }));

app.get('/api/health', (_request, response) => {
  response.json({ status: 'ok', database: 'ready' });
});

async function startServer() {
  const db = await initializeDatabase();

  registerCatalogosRoutes(app, db);
  registerAsientosRoutes(app, db, upload);
  registerReportesRoutes(app, db);
  registerKpiRoutes(app, db);
  registerCursorRoutes(app, db);
  registerOllamaRoutes(app);
  registerAudioRoutes(app, db, upload);
  registerVisionRoutes(app, db, upload);

  app.use((error, _request, response, _next) => {
    console.error(error);
    response.status(500).json({ error: error.message || 'Error interno' });
  });

  app.listen(port, () => {
    console.log(`✅ Servidor Express iniciado en http://localhost:${port}`);
  });
}

startServer().catch((error) => {
  console.error('❌ Error al iniciar servidor:', error);
  process.exit(1);
});