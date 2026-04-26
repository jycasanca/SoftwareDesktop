export function registerAudioRoutes(app, _db, upload) {
  app.post('/api/audio/transcribir', upload.single('audio'), (_request, response) => {
    response.status(501).json({ error: 'Transcripción Whisper pendiente de implementación.' });
  });
}