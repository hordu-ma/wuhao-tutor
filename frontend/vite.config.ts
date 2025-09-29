import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'
import AutoImport from 'unplugin-auto-import/vite'
import Components from 'unplugin-vue-components/vite'
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'
import { VitePWA } from 'vite-plugin-pwa'
import { resolve } from 'path'

export default defineConfig(({ mode }) => {
  const isProduction = mode === 'production'

  return {
    plugins: [
      vue({
        template: {
          compilerOptions: {
            // 生产环境移除注释
            comments: !isProduction,
          },
        },
      }),
      AutoImport({
        imports: ['vue', 'vue-router', 'pinia'],
        resolvers: [ElementPlusResolver()],
        dts: true,
        // 自动导入响应式工具
        dirs: ['./src/composables', './src/utils'],
        vueTemplate: true,
      }),
      Components({
        resolvers: [ElementPlusResolver()],
        dts: true,
        // 自动导入组件目录
        dirs: ['src/components'],
        extensions: ['vue'],
        deep: true,
        include: [/\.vue$/, /\.vue\?vue/],
      }),
      // PWA 插件配置
      VitePWA({
        registerType: 'autoUpdate',
        workbox: {
          cleanupOutdatedCaches: true,
          skipWaiting: true,
          clientsClaim: true,
          runtimeCaching: [
            {
              urlPattern: /^https:\/\/fonts\.googleapis\.com\/.*/i,
              handler: 'CacheFirst',
              options: {
                cacheName: 'google-fonts-cache',
                expiration: {
                  maxEntries: 10,
                  maxAgeSeconds: 60 * 60 * 24 * 365, // 1 year
                },
              },
            },
            {
              urlPattern: /^https:\/\/fonts\.gstatic\.com\/.*/i,
              handler: 'CacheFirst',
              options: {
                cacheName: 'gstatic-fonts-cache',
                expiration: {
                  maxEntries: 10,
                  maxAgeSeconds: 60 * 60 * 24 * 365, // 1 year
                },
              },
            },
            {
              urlPattern: /^https:\/\/unpkg\.com\/.*/i,
              handler: 'StaleWhileRevalidate',
              options: {
                cacheName: 'unpkg-cache',
                expiration: {
                  maxEntries: 50,
                  maxAgeSeconds: 60 * 60 * 24 * 30, // 30 days
                },
              },
            },
            {
              urlPattern: ({ request }) => request.destination === 'image',
              handler: 'CacheFirst',
              options: {
                cacheName: 'images-cache',
                expiration: {
                  maxEntries: 100,
                  maxAgeSeconds: 60 * 60 * 24 * 30, // 30 days
                },
              },
            },
            {
              urlPattern: ({ url }) => url.pathname.startsWith('/api/'),
              handler: 'NetworkFirst',
              options: {
                cacheName: 'api-cache',
                networkTimeoutSeconds: 10,
                expiration: {
                  maxEntries: 50,
                  maxAgeSeconds: 60 * 5, // 5 minutes
                },
              },
            },
          ],
          // 预缓存资源配置
          navigateFallback: '/index.html',
          navigateFallbackDenylist: [/^\/_/, /\/[^/?]+\.[^/]+$/],
        },
        includeAssets: [
          'favicon.svg',
        ],
        manifest: false, // 使用独立的 manifest.json 文件
      }),
    ],
    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url)),
        '@/components': fileURLToPath(new URL('./src/components', import.meta.url)),
        '@/views': fileURLToPath(new URL('./src/views', import.meta.url)),
        '@/api': fileURLToPath(new URL('./src/api', import.meta.url)),
        '@/stores': fileURLToPath(new URL('./src/stores', import.meta.url)),
        '@/utils': fileURLToPath(new URL('./src/utils', import.meta.url)),
        '@/types': fileURLToPath(new URL('./src/types', import.meta.url)),
        '@/composables': fileURLToPath(new URL('./src/composables', import.meta.url)),
      },
    },
    define: {
      // 全局常量定义
      __APP_VERSION__: JSON.stringify(process.env.npm_package_version),
      __BUILD_DATE__: JSON.stringify(new Date().toISOString()),
    },
    server: {
      host: '0.0.0.0',
      port: 5173,
      open: false,
      cors: true,
      fs: {
        strict: false,
      },
      proxy: {
        '/api': {
          target: 'http://localhost:8000',
          changeOrigin: true,
          secure: false,
        },
      },
    },
    build: {
      target: ['es2020', 'edge88', 'firefox78', 'chrome87', 'safari14'],
      outDir: 'dist',
      assetsDir: 'assets',
      sourcemap: !isProduction, // 生产环境关闭 sourcemap
      minify: isProduction ? 'terser' : false,
      cssCodeSplit: true,
      chunkSizeWarningLimit: 1000,
      // Terser 压缩选项
      terserOptions: isProduction ? {
        compress: {
          drop_console: true,
          drop_debugger: true,
          pure_funcs: ['console.log'],
        },
        mangle: {
          safari10: true,
        },
      } : undefined,
      rollupOptions: {
        input: {
          main: resolve(__dirname, 'index.html'),
        },
        output: {
          // 代码分割优化
          manualChunks: {
            // Vue 生态系统
            'vue-vendor': ['vue', 'vue-router'],
            'pinia-vendor': ['pinia'],
            // UI 组件库
            'element-vendor': ['element-plus', '@element-plus/icons-vue'],
            // 工具库
            'utils-vendor': ['axios', 'dayjs', 'lodash-es'],
            // 图表库
            'chart-vendor': ['echarts'],
            // 第三方工具
            'third-party': ['nprogress'],
          },
          // 文件命名优化
          chunkFileNames: (chunkInfo) => {
            const facadeModuleId = chunkInfo.facadeModuleId
              ? chunkInfo.facadeModuleId.split('/').pop()?.replace(/\.\w+$/, '') ?? 'chunk'
              : 'chunk'
            return `assets/${facadeModuleId}-[hash].js`
          },
          entryFileNames: 'assets/[name]-[hash].js',
          assetFileNames: (assetInfo) => {
            const info = assetInfo.name?.split('.') ?? []
            const extType = info[info.length - 1]
            if (/\.(mp4|webm|ogg|mp3|wav|flac|aac)$/.test(assetInfo.name ?? '')) {
              return 'assets/media/[name]-[hash][extname]'
            }
            if (/\.(png|jpe?g|gif|svg|webp|avif)$/.test(assetInfo.name ?? '')) {
              return 'assets/images/[name]-[hash][extname]'
            }
            if (/\.(woff2?|eot|ttf|otf)$/.test(assetInfo.name ?? '')) {
              return 'assets/fonts/[name]-[hash][extname]'
            }
            if (extType === 'css') {
              return 'assets/styles/[name]-[hash][extname]'
            }
            return 'assets/[name]-[hash][extname]'
          },
        },
        // 外部依赖优化
        external: () => {
          // 在生产环境中不外部化任何依赖，确保 PWA 离线可用
          return false
        },
      },
      // 构建优化
      reportCompressedSize: false,
      cssTarget: 'chrome87',
    },
    optimizeDeps: {
      include: [
        'vue',
        'vue-router',
        'pinia',
        'axios',
        'element-plus',
        'dayjs',
        'lodash-es',
        'echarts',
        '@element-plus/icons-vue',
        'nprogress',
      ],
      exclude: ['@vueuse/core'],
      // 预构建优化
      force: false,
    },
    // CSS 配置
    css: {
      devSourcemap: !isProduction,
      preprocessorOptions: {
        scss: {
          additionalData: `
            @use "@/styles/variables" as *;
            @use "@/styles/mixins" as *;
          `,
        },
      },
      postcss: {
        plugins: [
          // 自动添加浏览器前缀
          {
            postcssPlugin: 'internal:charset-removal',
            AtRule: {
              charset: (atRule) => {
                if (atRule.name === 'charset') {
                  atRule.remove();
                }
              }
            }
          }
        ],
      },
    },
    // 环境变量配置
    envPrefix: ['VITE_', 'VUE_APP_'],
    // 实验性功能
    experimental: {
      renderBuiltUrl(filename, { hostType }) {
        if (hostType === 'js') {
          return { relative: true, runtime: `__vite__mapUrl("${filename}")` }
        } else {
          return `/${filename}`
        }
      },
    },
    // 日志级别
    logLevel: isProduction ? 'warn' : 'info',
  }
})
