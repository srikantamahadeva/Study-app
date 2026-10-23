import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    strictPort: false,
    proxy: {
      // The FastAPI backend owns /api (auth cookies, CSRF, static file
      // serving). Vite forwards it during development so the SPA and API
      // share one origin and the session cookie works unchanged.
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: false,
      },
    },
  },
  build: {
    // FastAPI serves the built SPA from server/web/dist (single-process
    // production deploy), so the build writes straight there.
    outDir: 'server/web/dist',
    emptyOutDir: true,
  },
})
