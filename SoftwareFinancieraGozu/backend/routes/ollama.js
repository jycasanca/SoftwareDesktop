export function registerOllamaRoutes(app) {
  app.get('/api/ollama/modelos', async (_request, response) => {
    try {
      const ollamaUrl = process.env.OLLAMA_URL || 'http://localhost:11434';
      const result = await fetch(`${ollamaUrl}/api/tags`);
      response.status(result.ok ? 200 : 502).json(await result.json());
    } catch (error) {
      response.status(502).json({ error: 'Ollama no disponible', detail: error.message });
    }
  });

  app.get('/api/ollama/estado', async (_request, response) => {
    try {
      const ollamaUrl = process.env.OLLAMA_URL || 'http://localhost:11434';
      const result = await fetch(`${ollamaUrl}/api/tags`);
      response.json({ ok: result.ok });
    } catch {
      response.json({ ok: false });
    }
  });

  app.post('/api/ollama/interpretar', (_request, response) => {
    response.json({ error: 'Integración Ollama pendiente de conectar al modelo local.' });
  });
}