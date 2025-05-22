const { defineConfig } = require("@vue/cli-service");

module.exports = defineConfig({
  transpileDependencies: true,
  publicPath: "/", // Ensure assets are served from root, compatible with Vercel
  devServer: {
    proxy: {
      "/api": {
        target: "     http://localhost:5000",
        changeOrigin: true,
      },
    },
  },
  configureWebpack: {
    performance: {
      hints: false,
    },
    optimization: {
      splitChunks: {
        minSize: 10000,
        maxSize: 250000,

        chunks: "all", // Split vendor and app code into separate chunks
        cacheGroups: {
          vendors: {
            test: /[\\/]node_modules[\\/]/,
            name: "vendors",
            chunks: "all",
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
        modules: {
          auto: true,
        },
      },
    },
  },
  chainWebpack: (config) => {
    // Use default Vue CLI image handling (file-loader)
    config.module
      .rule("images")
      .test(/\.(png|jpe?g|gif|webp)(\?.*)?$/)
      .use("file-loader")
      .loader("file-loader")
      .options({
        name: "img/[name].[hash:8].[ext]", // Output images to img/ folder
        limit: 8192, // Inline images < 8KB (optional, can remove if not needed)
      });

    // Minimize and optimize output in production
    config.when(process.env.NODE_ENV === "production", (config) => {
      config.optimization.minimize(true);
    });
  },
});
