const { defineConfig } = require('@vue/cli-service')

module.exports = defineConfig({
  transpileDependencies: true,
  publicPath: '/', // keep as is
  
  productionSourceMap: false, // Disable sourcemaps in production for faster build & better security

  configureWebpack: {
    infrastructureLogging: {
      level: 'warn', // Only show important Webpack logs
    },
    bail: true, // Critical: stop build on first error
  }
})