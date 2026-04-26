# Contable AI

Proyecto web de contabilidad con soporte de IA.

## Estructura

- `SoftwareFinancieraGozu/frontend/`: React 18 + Bootstrap 5 + React Router 6
- `SoftwareFinancieraGozu/backend/`: Node.js + Express 5 + better-sqlite3
- `SoftwareFinancieraGozu/database/`: `schema_contable_v2.sql` y `contable.db`

## Arranque

1. Ejecutar `SoftwareFinancieraGozu/iniciar_contable_ai.bat`
2. Abrir `http://localhost:3000`

## Base de datos

La base SQLite se crea automáticamente en `SoftwareFinancieraGozu/database/contable.db` al iniciar el backend.