/**
 * Vue CLI 配置
 */
const path = require('path')
const CompressionPlugin = require('compression-webpack-plugin')
const webpack = require('webpack')

const IS_PRODUCTION = process.env.NODE_ENV === 'production'

module.exports = {
  publicPath: process.env.VUE_APP_PUBLIC_PATH || '/',
  outputDir: 'dist',
  assetsDir: 'static',
  lintOnSave: !IS_PRODUCTION,
  productionSourceMap: false,
  pages: {
    app: {
      entry: './src/main.js',
      template: 'public/index.html',
      filename: 'index.html'
    }
  },
  
  configureWebpack: {
    resolve: {
      alias: {
        '@': path.resolve(__dirname, 'src')
      },
      extensions: ['.js', '.vue', '.json', '.ts']
    },
    plugins: [
      new webpack.IgnorePlugin({
        resourceRegExp: /^\.\/locale$/,
        contextRegExp: /moment$/
      })
    ],
    optimization: {
      splitChunks: {
        chunks: 'all',
        cacheGroups: {
          vendor: {
            name: 'vendor',
            test: /[\\/]node_modules[\\/]/,
            priority: 10,
            chunks: 'initial'
          },
          elementPlus: {
            name: 'element-plus',
            test: /[\\/]node_modules[\\/]element-plus[\\/]/,
            priority: 20
          },
          vueVendor: {
            name: 'vue-vendor',
            test: /[\\/]node_modules[\\/](vue|vue-router|pinia)[\\/]/,
            priority: 20
          },
          common: {
            name: 'common',
            minChunks: 2,
            priority: 5,
            reuseExistingChunk: true
          }
        }
      }
    },
    performance: {
      hints: IS_PRODUCTION ? 'warning' : false,
      maxAssetSize: 512 * 1024,
      maxEntrypointSize: 512 * 1024
    }
  },
  
  chainWebpack: config => {
    if (IS_PRODUCTION) {
      config.plugin('compression').use(CompressionPlugin, [{
        algorithm: 'gzip',
        test: /\.(js|css|html|svg)$/,
        threshold: 10240,
        minRatio: 0.8
      }])
      
      config.optimization.minimize(true)
      config.optimization.usedExports(true)
      config.optimization.sideEffects(true)
    }
    
    config.module
      .rule('svg')
      .exclude.add(path.resolve(__dirname, 'src/assets/icons'))
      .end()
    
    config.module
      .rule('icons')
      .test(/\.svg$/)
      .include.add(path.resolve(__dirname, 'src/assets/icons'))
      .end()
      .use('svg-sprite-loader')
      .loader('svg-sprite-loader')
      .options({
        symbolId: 'icon-[name]'
      })
      .end()
  },
  
  css: {
    extract: IS_PRODUCTION,
    sourceMap: !IS_PRODUCTION,
    loaderOptions: {
      scss: {
        additionalData: `@use "@/assets/styles/variables.scss" as *;`,
        sassOptions: {
          silenceDeprecations: ['legacy-js-api'],
          includePaths: [path.resolve(__dirname, 'src')]
        }
      }
    }
  },
  
  devServer: {
    port: 8081,
    host: '0.0.0.0',
    open: false,
    historyApiFallback: true,
    proxy: {
      '/api': {
        target: process.env.VUE_APP_API_URL || 'http://localhost:8000',
        changeOrigin: true,
        ws: true
      },
      '/media': {
        target: process.env.VUE_APP_API_URL || 'http://localhost:8000',
        changeOrigin: true
      },
      '/static': {
        target: process.env.VUE_APP_API_URL || 'http://localhost:8000',
        changeOrigin: true
      },
      '/admin': {
        target: process.env.VUE_APP_API_URL || 'http://localhost:8000',
        changeOrigin: true
      }
    }
  },
  
  parallel: require('os').cpus().length > 1,
  
  pwa: {
    name: '天齐AI大模型投标平台',
    themeColor: '#667eea',
    msTileColor: '#667eea',
    workboxPluginMode: 'GenerateSW',
    workboxOptions: {
      skipWaiting: true,
      clientsClaim: true
    }
  }
}
