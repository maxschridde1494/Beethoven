import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  base: '/dash',
  plugins: [react()],
  server: {
    host: true,        // listen on 0.0.0.0  (HTTP)
    port: 5173,
    hmr: {
      host: "0.0.0.0",
      port: 3036, // HMR port
    },
  },
  build: {
    sourcemap: true,
  },
})
