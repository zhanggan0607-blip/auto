import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'
import compression from 'vite-plugin-compression'
import { readFileSync } from 'fs'

const pkg = JSON.parse(readFileSync('./package.json', 'utf-8'))

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')

  return {
    plugins: [
      vue(),
      compression({
        algorithm: 'gzip',
        threshold: 10240,
        filter: /\.(js|css|html|svg)$/,
        deleteOriginFile: false
      })
    ],

    resolve: {
      alias: {
        '@': path.resolve(__dirname, 'src')
      },
      extensions: ['.js', '.vue', '.json', '.ts']
    },

    css: {
      preprocessorOptions: {
        scss: {
          additionalData: `@use "@/assets/styles/variables.scss" as *;`,
          api: 'modern-compiler'
        }
      }
    },

    server: {
      port: 9081,
      host: '0.0.0.0',
      open: false,
      proxy: {
        '/api': {
          target: env.VITE_API_URL || 'http://localhost:8100',
          changeOrigin: true,
          ws: true
        },
        '/media': {
          target: env.VITE_API_URL || 'http://localhost:8100',
          changeOrigin: true
        },
        '/static': {
          target: env.VITE_API_URL || 'http://localhost:8100',
          changeOrigin: true
        },
        '/admin': {
          target: env.VITE_API_URL || 'http://localhost:8100',
          changeOrigin: true
        }
      }
    },

    build: {
      outDir: 'dist',
      assetsDir: 'assets',
      sourcemap: false,
      chunkSizeWarningLimit: 512,
      rollupOptions: {
        output: {
          manualChunks: {
            vendor: Object.keys(pkg.dependencies).filter(
              d => !['vue', 'vue-router', 'pinia', 'element-plus', '@element-plus/icons-vue', 'echarts', 'vue-echarts'].includes(d)
            ),
            'vue-vendor': ['vue', 'vue-router', 'pinia'],
            'element-plus': ['element-plus', '@element-plus/icons-vue'],
            'echarts': ['echarts', 'vue-echarts']
          }
        }
      }
    }
  }
})
