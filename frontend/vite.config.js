import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,

    proxy: {
      '/api': {
        target: 'https://service-provider-backend-yea9.onrender.com',
        changeOrigin: true,
      },
      '/media': {
        target: 'https://service-provider-backend-yea9.onrender.com',
        changeOrigin: true,
      },
    },
  },
})

