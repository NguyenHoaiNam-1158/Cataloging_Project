import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    // Proxy để gọi backend FastAPI mà không vướng CORS khi dev.
    // Frontend gọi '/api/...' -> Vite chuyển tiếp sang http://localhost:8000
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
