<template>
  <div class="debug-view">
    <div class="debug-header">
      <h1>🔧 应用调试信息</h1>
      <p>当前时间: {{ currentTime }}</p>
    </div>

    <div class="debug-sections">
      <!-- 基础信息 -->
      <div class="debug-section">
        <h2>📊 基础信息</h2>
        <div class="debug-item">
          <strong>Vue版本:</strong> {{ vueVersion }}
        </div>
        <div class="debug-item">
          <strong>环境:</strong> {{ environment }}
        </div>
        <div class="debug-item">
          <strong>基础URL:</strong> {{ baseUrl }}
        </div>
        <div class="debug-item">
          <strong>API地址:</strong> {{ apiUrl }}
        </div>
      </div>

      <!-- 路由信息 -->
      <div class="debug-section">
        <h2>🛣️ 路由信息</h2>
        <div class="debug-item">
          <strong>当前路径:</strong> {{ $route.path }}
        </div>
        <div class="debug-item">
          <strong>路由名称:</strong> {{ $route.name }}
        </div>
        <div class="debug-item">
          <strong>路由参数:</strong> {{ JSON.stringify($route.params) }}
        </div>
        <div class="debug-item">
          <strong>查询参数:</strong> {{ JSON.stringify($route.query) }}
        </div>
        <div class="debug-item">
          <strong>路由元信息:</strong>
          <pre>{{ JSON.stringify($route.meta, null, 2) }}</pre>
        </div>
      </div>

      <!-- 认证状态 -->
      <div class="debug-section">
        <h2>🔐 认证状态</h2>
        <div class="debug-item">
          <strong>是否已认证:</strong>
          <span :class="authStore.isAuthenticated ? 'status-success' : 'status-error'">
            {{ authStore.isAuthenticated ? '✅ 是' : '❌ 否' }}
          </span>
        </div>
        <div class="debug-item">
          <strong>访问令牌:</strong>
          <span v-if="authStore.accessToken" class="token-preview">
            {{ authStore.accessToken.substring(0, 20) }}...
          </span>
          <span v-else class="status-error">未设置</span>
        </div>
        <div class="debug-item">
          <strong>用户信息:</strong>
          <pre v-if="authStore.user">{{ JSON.stringify(authStore.user, null, 2) }}</pre>
          <span v-else class="status-error">未设置</span>
        </div>
        <div class="debug-item">
          <strong>用户角色:</strong> {{ authStore.userRole }}
        </div>
        <div class="debug-item">
          <strong>记住我:</strong> {{ authStore.rememberMe ? '是' : '否' }}
        </div>
      </div>

      <!-- 存储信息 -->
      <div class="debug-section">
        <h2>💾 本地存储</h2>
        <div class="debug-item">
          <strong>localStorage数据:</strong>
          <pre>{{ localStorageData }}</pre>
        </div>
        <div class="debug-item">
          <strong>sessionStorage数据:</strong>
          <pre>{{ sessionStorageData }}</pre>
        </div>
      </div>

      <!-- Token信息 -->
      <div class="debug-section" v-if="authStore.accessToken">
        <h2>🔑 Token 详情</h2>
        <div class="debug-item">
          <strong>Token是否过期:</strong>
          <span :class="tokenExpired ? 'status-error' : 'status-success'">
            {{ tokenExpired ? '❌ 是' : '✅ 否' }}
          </span>
        </div>
        <div class="debug-item">
          <strong>Token过期时间:</strong> {{ tokenExpiryTime }}
        </div>
        <div class="debug-item">
          <strong>Token负载:</strong>
          <pre>{{ tokenPayload }}</pre>
        </div>
      </div>

      <!-- 网络状态 -->
      <div class="debug-section">
        <h2>🌐 网络状态</h2>
        <div class="debug-item">
          <strong>在线状态:</strong>
          <span :class="isOnline ? 'status-success' : 'status-error'">
            {{ isOnline ? '✅ 在线' : '❌ 离线' }}
          </span>
        </div>
        <div class="debug-item">
          <strong>用户代理:</strong> {{ userAgent }}
        </div>
      </div>

      <!-- 操作按钮 -->
      <div class="debug-section">
        <h2>⚡ 调试操作</h2>
        <div class="debug-actions">
          <el-button @click="refreshData" type="primary">刷新数据</el-button>
          <el-button @click="clearStorage" type="warning">清除存储</el-button>
          <el-button @click="testApiConnection" type="info">测试API连接</el-button>
          <el-button @click="simulateLogin" type="success">模拟登录</el-button>
          <el-button @click="goToDashboard" type="primary">前往仪表板</el-button>
        </div>
      </div>

      <!-- API测试结果 -->
      <div class="debug-section" v-if="apiTestResult">
        <h2>🔍 API测试结果</h2>
        <div class="debug-item">
          <strong>健康检查:</strong>
          <pre>{{ apiTestResult }}</pre>
        </div>
      </div>

      <!-- 错误日志 -->
      <div class="debug-section" v-if="errorLogs.length > 0">
        <h2>❌ 错误日志</h2>
        <div v-for="(error, index) in errorLogs" :key="index" class="error-log">
          <div class="error-time">{{ error.time }}</div>
          <div class="error-message">{{ error.message }}</div>
          <pre class="error-stack">{{ error.stack }}</pre>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElMessage, ElButton } from 'element-plus'
import { version } from 'vue'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

// 响应式数据
const currentTime = ref('')
const isOnline = ref(navigator.onLine)
const apiTestResult = ref('')
const errorLogs = ref<Array<{ time: string; message: string; stack?: string }>>([])

// 定时器
let timeInterval: NodeJS.Timeout | null = null

// 计算属性
const vueVersion = computed(() => version)
const environment = computed(() => import.meta.env.MODE)
const baseUrl = computed(() => import.meta.env.BASE_URL)
const apiUrl = computed(() => import.meta.env.VITE_API_BASE_URL || 'Not set')
const userAgent = computed(() => navigator.userAgent)

const localStorageData = computed(() => {
  const data: Record<string, any> = {}
  for (let i = 0; i < localStorage.length; i++) {
    const key = localStorage.key(i)
    if (key) {
      try {
        data[key] = JSON.parse(localStorage.getItem(key) || '')
      } catch {
        data[key] = localStorage.getItem(key)
      }
    }
  }
  return JSON.stringify(data, null, 2)
})

const sessionStorageData = computed(() => {
  const data: Record<string, any> = {}
  for (let i = 0; i < sessionStorage.length; i++) {
    const key = sessionStorage.key(i)
    if (key) {
      try {
        data[key] = JSON.parse(sessionStorage.getItem(key) || '')
      } catch {
        data[key] = sessionStorage.getItem(key)
      }
    }
  }
  return JSON.stringify(data, null, 2)
})

const tokenExpired = computed(() => {
  if (!authStore.accessToken) return true
  return authStore.isTokenExpired()
})

const tokenExpiryTime = computed(() => {
  const expiry = authStore.getTokenExpiry()
  return expiry ? new Date(expiry).toLocaleString() : '未知'
})

const tokenPayload = computed(() => {
  if (!authStore.accessToken) return null
  try {
    const payload = JSON.parse(atob(authStore.accessToken.split('.')[1]))
    return JSON.stringify(payload, null, 2)
  } catch (error) {
    return 'Token解析失败'
  }
})

// 方法
const updateTime = () => {
  currentTime.value = new Date().toLocaleString()
}

const refreshData = () => {
  updateTime()
  ElMessage.success('数据已刷新')
}

const clearStorage = () => {
  localStorage.clear()
  sessionStorage.clear()
  authStore.clearAuth()
  ElMessage.success('存储已清除')
  refreshData()
}

const testApiConnection = async () => {
  try {
    const baseApiUrl = apiUrl.value.replace('/api/v1', '')
    const response = await fetch(`${baseApiUrl}/health`)

    if (response.ok) {
      const data = await response.json()
      apiTestResult.value = JSON.stringify(data, null, 2)
      ElMessage.success('API连接正常')
    } else {
      apiTestResult.value = `HTTP ${response.status}: ${response.statusText}`
      ElMessage.error('API连接失败')
    }
  } catch (error) {
    apiTestResult.value = `连接错误: ${error}`
    ElMessage.error('无法连接到API')
  }
}

const simulateLogin = () => {
  // 模拟登录状态
  const mockUser = {
    id: 1,
    username: 'debug_user',
    nickname: '调试用户',
    email: 'debug@example.com',
    role: 'student',
    avatar: '',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString()
  }

  const mockToken = 'debug.token.here'

  authStore.setAuth({
    access_token: mockToken,
    user: mockUser,
    expires_in: 3600
  }, false)

  ElMessage.success('已模拟登录状态')
  refreshData()
}

const goToDashboard = () => {
  router.push('/dashboard')
}

const handleError = (error: ErrorEvent) => {
  errorLogs.value.unshift({
    time: new Date().toLocaleString(),
    message: error.message,
    stack: error.error?.stack
  })

  // 只保留最近10条错误
  if (errorLogs.value.length > 10) {
    errorLogs.value = errorLogs.value.slice(0, 10)
  }
}

const handleOnlineStatusChange = () => {
  isOnline.value = navigator.onLine
}

// 生命周期
onMounted(() => {
  updateTime()
  timeInterval = setInterval(updateTime, 1000)

  // 监听错误
  window.addEventListener('error', handleError)

  // 监听网络状态变化
  window.addEventListener('online', handleOnlineStatusChange)
  window.addEventListener('offline', handleOnlineStatusChange)

  console.log('🔧 调试页面已加载')
})

onUnmounted(() => {
  if (timeInterval) {
    clearInterval(timeInterval)
  }

  window.removeEventListener('error', handleError)
  window.removeEventListener('online', handleOnlineStatusChange)
  window.removeEventListener('offline', handleOnlineStatusChange)
})
</script>

<style scoped>
.debug-view {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
}

.debug-header {
  text-align: center;
  margin-bottom: 30px;
  padding: 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 10px;
}

.debug-header h1 {
  margin: 0 0 10px 0;
  font-size: 24px;
}

.debug-sections {
  display: grid;
  grid-template-columns: 1fr;
  gap: 20px;
}

.debug-section {
  background: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 20px;
}

.debug-section h2 {
  margin: 0 0 15px 0;
  color: #495057;
  font-size: 18px;
  border-bottom: 2px solid #dee2e6;
  padding-bottom: 8px;
}

.debug-item {
  margin-bottom: 12px;
  padding: 8px 0;
  border-bottom: 1px solid #e9ecef;
}

.debug-item:last-child {
  border-bottom: none;
}

.debug-item strong {
  display: inline-block;
  min-width: 120px;
  color: #343a40;
}

.debug-item pre {
  background: #ffffff;
  border: 1px solid #dee2e6;
  border-radius: 4px;
  padding: 10px;
  margin: 8px 0 0 0;
  font-size: 12px;
  overflow-x: auto;
  white-space: pre-wrap;
  word-break: break-all;
}

.status-success {
  color: #28a745;
  font-weight: bold;
}

.status-error {
  color: #dc3545;
  font-weight: bold;
}

.token-preview {
  font-family: monospace;
  background: #e9ecef;
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 12px;
}

.debug-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.error-log {
  background: #fff5f5;
  border: 1px solid #feb2b2;
  border-radius: 4px;
  padding: 10px;
  margin-bottom: 10px;
}

.error-time {
  font-size: 12px;
  color: #718096;
  margin-bottom: 5px;
}

.error-message {
  color: #e53e3e;
  font-weight: bold;
  margin-bottom: 5px;
}

.error-stack {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 3px;
  padding: 8px;
  font-size: 11px;
  color: #4a5568;
  margin: 0;
}

@media (min-width: 768px) {
  .debug-sections {
    grid-template-columns: 1fr 1fr;
  }
}

@media (min-width: 1024px) {
  .debug-actions {
    justify-content: flex-start;
  }
}
</style>
