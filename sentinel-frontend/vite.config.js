import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    strictPort: true,
    hmr: {
      overlay: true
    }
  },
  optimizeDeps: {
    include: [
      'react-gauge-chart',
      'react-force-graph-2d',
      'lodash/isEqual'
    ]
  },
  resolve: {
    alias: {
      'lodash/isEqual': 'lodash.isequal'
    }
  }
})
