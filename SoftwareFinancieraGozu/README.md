# Sistema Financiera Gozu

Arquitectura:
- Frontend React 18 + Bootstrap 5 en `frontend/`
- Backend Node.js + Express 5 en `backend/`
- Base de datos SQLite en `database/contable.db`
- El esquema se crea automáticamente desde `backend/database.js`

Tablas clave en SQLite:
- `plan_contable`
- `diccionario_sinonimos`
- `matriz_comportamiento`
- `registro_recepcion`
- `libro_diario`

## Cómo iniciar

1. Ejecutar `iniciar_contable_ai.bat`.
2. Abrir `http://localhost:3000`.

## Funcionalidades implementadas

- Editor de diccionario de sinónimos.
- Editor de reglas de comportamiento para conceptos contables.
- Procesamiento de texto para extraer conceptos y proponer asientos.
- Validación de asientos antes de guardarlos en `libro_diario`.
- Balance de comprobación.
- KPIs, historial y configuración base.

## Notas

- La base SQLite se crea automáticamente en `database/contable.db`.
- El backend y el frontend se administran desde un único bat de inicio.
