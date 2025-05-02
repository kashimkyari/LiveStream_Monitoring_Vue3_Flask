import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  define: {
    __VUE_PROD_HYDRATION_MISMATCH_DETAILS__: false, // Disable detailed hydration mismatch warnings in production
  },
  server: {
    proxy: {
      '/api': {
        target: 'https://monitor-backend.jetcamstudio.com:5000',
        changeOrigin: true,
        rewrite: path => path.replace(/^\/api/, '/api')
      }
    }
  }
})