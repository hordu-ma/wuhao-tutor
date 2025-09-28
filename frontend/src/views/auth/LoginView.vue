<template>
  <div class="login-container">
    <div class="login-card">
      <div class="login-header">
        <h1 class="login-title">五好伴学</h1>
        <p class="login-subtitle">智能学习助手平台</p>
      </div>

      <el-form
        ref="loginFormRef"
        :model="loginForm"
        :rules="loginRules"
        class="login-form"
        size="large"
        @submit.prevent="handleLogin"
      >
        <el-form-item prop="username">
          <el-input
            v-model="loginForm.username"
            placeholder="用户名"
            prefix-icon="User"
            clearable
            @keyup.enter="handleLogin"
          />
        </el-form-item>

        <el-form-item prop="password">
          <el-input
            v-model="loginForm.password"
            type="password"
            placeholder="密码"
            prefix-icon="Lock"
            show-password
            clearable
            @keyup.enter="handleLogin"
          />
        </el-form-item>

        <el-form-item>
          <div class="login-options">
            <el-checkbox v-model="loginForm.remember_me">
              记住我
            </el-checkbox>
            <el-link type="primary" @click="$router.push('/forgot-password')">
              忘记密码？
            </el-link>
          </div>
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            class="login-button"
            :loading="loginLoading"
            @click="handleLogin"
          >
            {{ loginLoading ? '登录中...' : '登录' }}
          </el-button>
        </el-form-item>

        <el-form-item>
          <div class="register-link">
            还没有账号？
            <el-link type="primary" @click="$router.push('/register')">
              立即注册
            </el-link>
          </div>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElMessage, ElNotification } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'

const router = useRouter()
const authStore = useAuthStore()

// 表单引用
const loginFormRef = ref<FormInstance>()

// 登录表单数据
const loginForm = reactive({
  username: '',
  password: '',
  remember_me: false,
})

// 登录加载状态
const loginLoading = ref(false)

// 表单验证规则
const loginRules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 50, message: '用户名长度为3-50个字符', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 128, message: '密码长度为6-128个字符', trigger: 'blur' },
  ],
}

// 处理登录
const handleLogin = async () => {
  if (!loginFormRef.value) return

  try {
    // 表单验证
    const valid = await loginFormRef.value.validate()
    if (!valid) return

    loginLoading.value = true

    // 调用登录接口
    const success = await authStore.login(loginForm)

    if (success) {
      ElNotification({
        title: '登录成功',
        message: `欢迎回来，${authStore.userNickname}！`,
        type: 'success',
        duration: 3000,
      })

      // 跳转到目标页面或仪表板
      const redirect = router.currentRoute.value.query.redirect as string
      await router.push(redirect || '/dashboard')
    } else {
      ElMessage.error('登录失败，请检查用户名和密码')
    }
  } catch (error) {
    console.error('Login error:', error)
    ElMessage.error('登录过程中发生错误，请稍后重试')
  } finally {
    loginLoading.value = false
  }
}

// 组件挂载时检查登录状态
onMounted(() => {
  // 如果已经登录，直接跳转到仪表板
  if (authStore.isAuthenticated) {
    router.push('/dashboard')
    return
  }

  // 尝试从URL参数获取错误信息
  const error = router.currentRoute.value.query.error as string
  if (error) {
    ElMessage.error(decodeURIComponent(error))
  }

  // 开发环境下预填充测试账号
  if (import.meta.env.DEV) {
    loginForm.username = 'test_student'
    loginForm.password = 'password123'
  }
})
</script>

<style lang="scss" scoped>
.login-container {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
  position: relative;

  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-image: radial-gradient(
        circle at 20% 50%,
        rgba(120, 119, 198, 0.3) 0%,
        transparent 50%
      ),
      radial-gradient(
        circle at 80% 20%,
        rgba(255, 119, 198, 0.3) 0%,
        transparent 50%
      ),
      radial-gradient(
        circle at 40% 80%,
        rgba(120, 219, 255, 0.3) 0%,
        transparent 50%
      );
    pointer-events: none;
  }
}

.login-card {
  width: 100%;
  max-width: 420px;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 16px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  padding: 40px 32px;
  position: relative;
  z-index: 1;
}

.login-header {
  text-align: center;
  margin-bottom: 32px;

  .login-title {
    font-size: 32px;
    font-weight: 700;
    color: #2c3e50;
    margin: 0 0 8px 0;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }

  .login-subtitle {
    font-size: 16px;
    color: #7f8c8d;
    margin: 0;
    font-weight: 400;
  }
}

.login-form {
  .el-form-item {
    margin-bottom: 20px;

    :deep(.el-input__wrapper) {
      border-radius: 8px;
      box-shadow: 0 0 0 1px rgba(0, 0, 0, 0.1);
      transition: all 0.3s ease;

      &:hover {
        box-shadow: 0 0 0 1px var(--el-color-primary);
      }
    }

    :deep(.el-input__inner) {
      height: 48px;
      font-size: 16px;
    }
  }
}

.login-options {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  margin: 8px 0;

  .el-checkbox {
    :deep(.el-checkbox__label) {
      color: #666;
      font-size: 14px;
    }
  }

  .el-link {
    font-size: 14px;
    text-decoration: none;

    &:hover {
      text-decoration: underline;
    }
  }
}

.login-button {
  width: 100%;
  height: 48px;
  font-size: 16px;
  font-weight: 600;
  border-radius: 8px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  transition: all 0.3s ease;

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4);
  }

  &:active {
    transform: translateY(0);
  }

  &.is-loading {
    &:hover {
      transform: none;
      box-shadow: none;
    }
  }
}

.register-link {
  text-align: center;
  color: #666;
  font-size: 14px;

  .el-link {
    font-size: 14px;
    font-weight: 500;
    text-decoration: none;

    &:hover {
      text-decoration: underline;
    }
  }
}

// 响应式设计
@media (max-width: 480px) {
  .login-container {
    padding: 16px;
  }

  .login-card {
    padding: 32px 24px;
  }

  .login-header .login-title {
    font-size: 28px;
  }

  .login-form .el-form-item :deep(.el-input__inner) {
    height: 44px;
    font-size: 15px;
  }

  .login-button {
    height: 44px;
    font-size: 15px;
  }
}

// 动画效果
.login-card {
  animation: slideInUp 0.6s ease-out;
}

@keyframes slideInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

// 暗色模式适配
.dark {
  .login-card {
    background: rgba(31, 41, 55, 0.95);
    border: 1px solid rgba(75, 85, 99, 0.2);

    .login-title {
      color: #f9fafb;
    }

    .login-subtitle {
      color: #9ca3af;
    }

    .login-options .el-checkbox :deep(.el-checkbox__label) {
      color: #d1d5db;
    }

    .register-link {
      color: #9ca3af;
    }
  }
}
</style>
