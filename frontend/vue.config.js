const { defineConfig } = require('@vue/cli-service')
module.exports = defineConfig({
  transpileDependencies: true,
  publicPath: '/',
  devServer: {
    proxy: {
      '/api': {
        target: 'https://monitor-backend.jetcamstudio.com:5000',
        changeOrigin: true
      }
    }
  }
})