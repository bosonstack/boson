const path = require('path');

module.exports = {
  entry: './src/index.ts',
  output: {
    filename: 'index.js',
    path: path.resolve(__dirname, 'lib'),
    libraryTarget: 'amd',
    publicPath: ''
  },
  resolve: {
    extensions: ['.ts', '.js']
  },
  module: {
    rules: [{ test: /\.ts$/, use: 'ts-loader' }]
  },
  externals: [
    /^@jupyterlab\/.+/,
    /^@lumino\/.+/
  ],
  mode: 'development'
};
