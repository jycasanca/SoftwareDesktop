import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { SqliteClient } from './client.js';

const MODULE_DIR = path.dirname(fileURLToPath(import.meta.url));
const BACKEND_DIR = path.resolve(MODULE_DIR, '..');
const PROJECT_DIR = path.resolve(BACKEND_DIR, '..');

const DEFAULT_DB_FILE = path.join(BACKEND_DIR, 'database', 'contable.db');
const DEFAULT_SCHEMA_FILE = path.join(PROJECT_DIR, 'schema_contable_v2.sql');

async function executeStatements(db, sqlContent) {
  const statements = sqlContent
    .split(';')
    .map((statement) => statement.trim())
    .filter(Boolean);

  for (const statement of statements) {
    await db.exec(`${statement};`);
  }
}

export async function initializeDatabase(
  dbPath = process.env.DB_PATH || DEFAULT_DB_FILE,
  schemaPath = process.env.DB_SCHEMA_PATH || DEFAULT_SCHEMA_FILE,
) {
  if (!fs.existsSync(schemaPath)) {
    throw new Error(`No se encontro el schema SQL en: ${schemaPath}`);
  }

  const dbDir = path.dirname(dbPath);
  fs.mkdirSync(dbDir, { recursive: true });

  const sqlContent = fs.readFileSync(schemaPath, 'utf8');
  const db = new SqliteClient(dbPath);

  await db.exec('PRAGMA foreign_keys = ON;');
  await db.exec('PRAGMA journal_mode = WAL;');

  await executeStatements(db, sqlContent);

  const requiredTables = [
    'plan_contable',
    'diccionario_sinonimos',
    'matriz_comportamiento',
    'registro_recepcion',
    'libro_diario',
    'kpi_config',
    'cursor_sesiones',
    'config_sistema',
  ];

  const missingTables = [];
  for (const tableName of requiredTables) {
    const table = await db.get("SELECT name FROM sqlite_master WHERE type = 'table' AND name = ?", [tableName]);
    if (!table) {
      missingTables.push(tableName);
    }
  }

  if (missingTables.length > 0) {
    throw new Error(`Faltan tablas requeridas: ${missingTables.join(', ')}`);
  }

  console.log('✅ Base de datos inicializada');
  return db;
}
