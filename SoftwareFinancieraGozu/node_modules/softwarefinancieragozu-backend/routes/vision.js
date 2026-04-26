export function registerVisionRoutes(app, _db, upload) {
  app.post('/api/vision/analizar', upload.single('image'), (_request, response) => {
    response.status(501).json({ error: 'Análisis de imágenes pendiente de implementación.' });
  });
}