import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'node:path'
import { defineConfig, loadEnv } from 'vite'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const apiBase = env.VITE_API_BASE_URL ?? ''
  // If VITE_API_BASE_URL is an absolute URL (e.g. http://host:5000/api), proxy to that origin.
  // If it's a relative path (e.g. /api), fall back to the local default.
  const proxyTarget = /^https?:\/\//.test(apiBase)
    ? new URL(apiBase).origin
    : 'http://127.0.0.1:5000'

  return {
    plugins: [react(), tailwindcss()],
    resolve: { alias: { '@': path.resolve(import.meta.dirname, './src') } },
    optimizeDeps: { exclude: ['maplibre-gl'] }, // its worker is resolved relative to the module
    server: {
      port: 5173,
      strictPort: true,
      proxy: { '/api': { target: proxyTarget } },
    },
  }
})
