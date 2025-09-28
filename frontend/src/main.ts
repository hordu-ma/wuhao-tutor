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
async function initApp() {
  // 恢复用户认证状态
  const authStore = useAuthStore()
  // 恢复用户认证状态
  if (authStore.restoreAuth()) {
    // 启动token自动刷新定时器
    authStore.startTokenRefreshTimer()
  }



  // 挂载应用
  app.mount('#app')

  console.log('🚀 五好伴学前端应用启动完成')
}

// 启动应用
initApp().catch(error => {
  console.error('应用启动失败:', error)
})

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
