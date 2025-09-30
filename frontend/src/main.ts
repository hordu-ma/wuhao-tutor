/**
 * Vue应用主入口文件
 * 初始化Vue应用、配置插件、挂载应用
 */

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import 'element-plus/theme-chalk/dark/css-vars.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import zhCn from 'element-plus/es/locale/lang/zh-cn'

import 'dayjs/locale/zh-cn'

import App from './App.vue'
import router from './router'
import { useAuthStore } from './stores/auth'

// 样式导入
import './styles/index.css'
import './styles/responsive.scss'
import './styles/element-plus.scss'

// 创建Vue应用实例
const app = createApp(App)

// 创建Pinia实例
const pinia = createPinia()

// 注册Pinia
app.use(pinia)

// 注册路由
app.use(router)

// 注册Element Plus
app.use(ElementPlus, {
  locale: zhCn,
  size: 'default',
})

// 注册Element Plus图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

// 全局属性配置
app.config.globalProperties.$ELEMENT = {
  size: 'default',
  zIndex: 3000,
}

// 全局错误处理
app.config.errorHandler = (error, instance, info) => {
  console.error('Vue Global Error:', error)
  console.error('Component:', instance)
  console.error('Error Info:', info)

  // 在生产环境中可以发送错误到监控服务
  if (import.meta.env.PROD) {
    // TODO: 发送错误报告到监控服务
    // sendErrorReport(error, instance, info)
  }
}

// 警告处理
app.config.warnHandler = (msg, instance, trace) => {
  if (import.meta.env.DEV) {
    console.warn('Vue Warning:', msg)
    console.warn('Component:', instance)
    console.warn('Trace:', trace)
  }
}

// 应用初始化
function initApp() {
  try {
    console.log('🚀 开始初始化五好伴学应用...')

    // 挂载应用到DOM
    app.mount('#app')
    console.log('✅ Vue应用已挂载到DOM')

    // 初始化认证状态（异步，不阻塞应用启动）
    setTimeout(() => {
      try {
        const authStore = useAuthStore()
        console.log('🔐 开始恢复认证状态...')

        if (authStore.restoreAuth()) {
          console.log('✅ 认证状态已恢复')
          authStore.startTokenRefreshTimer()
        } else {
          console.log('ℹ️ 未找到有效的认证状态')
        }
      } catch (authError) {
        console.warn('⚠️ 认证状态恢复失败:', authError)
      }
    }, 100)

    console.log('🎉 五好伴学前端应用启动完成')

  } catch (error) {
    console.error('❌ 应用启动失败:', error)

    // 显示错误信息到页面
    const appElement = document.getElementById('app')
    if (appElement) {
      const errorMessage = error instanceof Error ? error.message : String(error)
      appElement.innerHTML = `
        <div style="
          padding: 40px 20px;
          text-align: center;
          font-family: Arial, sans-serif;
          max-width: 600px;
          margin: 0 auto;
        ">
          <h2 style="color: #dc3545; margin-bottom: 16px;">应用启动失败</h2>
          <p style="color: #666; margin-bottom: 24px;">
            抱歉，应用无法正常启动。错误信息：<br>
            <code style="background: #f8f9fa; padding: 4px 8px; border-radius: 4px;">${errorMessage}</code>
          </p>
          <button onclick="location.reload()" style="
            background: #007bff;
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 16px;
          ">重新加载</button>
        </div>
      `
    }
    throw error
  }
}

// 启动应用
try {
  initApp()
} catch (error) {
  console.error('严重错误: 应用无法启动', error)
}

// 开发环境配置
if (import.meta.env.DEV) {
  // 开发工具
  app.config.performance = true

    // 全局调试工具
    ; (window as any).__VUE_APP__ = app
    ; (window as any).__ROUTER__ = router
    ; (window as any).__PINIA__ = pinia

  console.log('🛠️  开发模式已启用')
  console.log('Vue版本:', app.version)
  console.log('环境变量:', import.meta.env)
}

// 页面卸载时清理
window.addEventListener('beforeunload', () => {
  console.log('应用即将卸载')
})
