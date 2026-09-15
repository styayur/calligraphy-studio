import react from '@vitejs/plugin-react'
import { defineConfig, loadEnv } from 'vite'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  return {
    base: env.VITE_BASE_PATH || '/',
    plugins: [react()],
    server: {
      port: 5173,
      proxy: {
        '/api': 'http://127.0.0.1:8000',
        '/assets': 'http://127.0.0.1:8000',
        '/health': 'http://127.0.0.1:8000',
      },
    },
    build: {
      rollupOptions: {
        output: {
          manualChunks(id) {
            if (id.includes('node_modules/konva') || id.includes('node_modules/react-konva')) return 'konva'
            if (id.includes('node_modules/react')) return 'react'
            if (id.includes('node_modules/lucide-react')) return 'icons'
          },
        },
      },
    },
  }
})
