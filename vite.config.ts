import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: true,
    proxy: {
      '/api': 'http://localhost:8000',
      '/health': 'http://localhost:8000',
      '/entity': 'http://localhost:8000',
      '/transaction': 'http://localhost:8000',
      '/graph': 'http://localhost:8000',
      '/trace': 'http://localhost:8000',
      '/taint': 'http://localhost:8000',
      '/alerts': 'http://localhost:8000',
      '/search': 'http://localhost:8000',
      '/scenarios': 'http://localhost:8000',
      '/stats': 'http://localhost:8000',
      '/eval': 'http://localhost:8000',
      '/anomaly': 'http://localhost:8000',
      '/dossier': 'http://localhost:8000',
      '/intel': 'http://localhost:8000',
      '/stream': 'http://localhost:8000'
    }
  }
});
