module.exports = (env, argv) => {
    const mode = argv.mode || 'development'
  
    const config = {
      entry: './src/index.js',
      output: {
        path: `${__dirname}/lib`,
        filename: 'index.js',
        library: 'my-library',
        libraryTarget: 'umd',
      },
      module: {
        rules: [
          {
            test: /\.(js|jsx)$/,
            exclude: /node_modules/,
            use: ['babel-loader'],
          },
        ],
      },
      devtool: mode === 'development' ? 'cheap-module-eval-source-map' : false,
    }
    return config
  }