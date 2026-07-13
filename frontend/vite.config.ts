import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/execute': 'http://localhost:8000',
      '/status': 'http://localhost:8000',
      '/health': 'http://localhost:8000',
      '/applications': 'http://localhost:8000',
      '/folders': 'http://localhost:8000',
      '/websites': 'http://localhost:8000',
      '/capabilities': 'http://localhost:8000',
    },
  },
})
