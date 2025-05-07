import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { visualizer } from 'rollup-plugin-visualizer'

export default defineConfig({
  plugins: [
    vue(),
    // Bundle analyzer: generates build/bundle-analysis.html
    visualizer({
      filename: 'build/bundle-analysis.html',
      open: false,        // set to true to auto-open report
      gzipSize: true,     // show gzipped sizes
      brotliSize: true,   // show brotli sizes
    }),
  ],
  define: {
    __VUE_PROD_HYDRATION_MISMATCH_DETAILS__: false,
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '/api'),
      },
    },
  },
  build: {
    minify: 'esbuild',    // fast/minimal JS minification
    cssCodeSplit: true,   // split CSS per-chunk
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes('node_modules')) {
            // Split core Vue libs
            if (id.match(/\/node_modules\/vue(\/|$)/)) {
              return 'vendor-vue'
            }
            // Split UI libraries (Element Plus, Vuetify, etc.)
            if (id.match(/\/node_modules\/(element-plus|vuetify|ant-design-vue)(\/|$)/)) {
              return 'vendor-ui'
            }
            // Split charting/data libs
            if (id.match(/\/node_modules\/(echarts|d3|chart\.js)(\/|$)/)) {
              return 'vendor-charts'
            }
            // Everything else in node_modules
            return 'vendor-others'
          }
        },
      },
    },
  },
})
