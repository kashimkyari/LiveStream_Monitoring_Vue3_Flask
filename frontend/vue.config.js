const { defineConfig } = require('@vue/cli-service');

module.exports = defineConfig({
  transpileDependencies: true,
  publicPath: '/', // Ensure assets are served from root, compatible with Vercel
  devServer: {
    proxy: {
      '/api': {
        target: 'https://monitor-backend.jetcamstudio.com:5000',
        changeOrigin: true,
      },
    },
  },
  configureWebpack: {
    optimization: {
      splitChunks: {
        chunks: 'all', // Split vendor and app code into separate chunks
        cacheGroups: {
          vendors: {
            test: /[\\/]node_modules[\\/]/,
            name: 'vendors',
            chunks: 'all',
            priority: -10,
          },
          default: {
            minChunks: 2,
            priority: -20,
            reuseExistingChunk: true,
          },
        },
      },
    },
  },
  css: {
    extract: true, // Extract CSS into separate files for better caching
    loaderOptions: {
      css: {
        // Minimize CSS in production
        modules: {
          auto: true,
        },
      },
    },
  },
  chainWebpack: (config) => {
    // Optimize images to reduce bundle size
    config.module
      .rule('images')
      .use('url-loader')
      .loader('url-loader')
      .tap((options) => ({
        ...options,
        limit: 8192, // Inline images < 8KB, otherwise use file
      }));

    // Minimize and optimize output in production
    config.when(process.env.NODE_ENV === 'production', (config) => {
      config.optimization.minimize(true);
    });
  },
});