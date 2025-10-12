<template>
  <div class="registration-disabled-container">
    <div class="registration-disabled-card">
      <div class="registration-disabled-header">
        <div class="icon-wrapper">
          <el-icon :size="80" color="#667eea">
            <Lock />
          </el-icon>
        </div>
        <h1 class="title">注册暂不开放</h1>
        <p class="subtitle">五好伴学 · 智能学习助手平台</p>
      </div>

      <div class="content">
        <div class="message-box">
          <h2 class="main-message">系统暂不支持自主注册</h2>
          <p class="description">
            为了给您提供更优质的学习体验，我们采用<strong>机构专属账户</strong>的方式管理用户。
          </p>
        </div>

        <div class="instruction-box">
          <h3 class="instruction-title">如何开通账户？</h3>
          <div class="steps">
            <div class="step">
              <div class="step-number">1</div>
              <div class="step-content">
                <h4>联系助教老师</h4>
                <p>请联系您所在辅导机构的助教老师</p>
              </div>
            </div>
            <div class="step">
              <div class="step-number">2</div>
              <div class="step-content">
                <h4>完成缴费流程</h4>
                <p>根据机构的要求完成相关缴费</p>
              </div>
            </div>
            <div class="step">
              <div class="step-number">3</div>
              <div class="step-content">
                <h4>获取账户信息</h4>
                <p>助教老师会为您开通账户并提供登录信息</p>
              </div>
            </div>
          </div>
        </div>

        <div class="help-box">
          <el-icon :size="20" color="#409eff">
            <InfoFilled />
          </el-icon>
          <span>已有账户？请直接<strong>返回登录</strong>页面使用您的账号密码登录。</span>
        </div>
      </div>

      <div class="actions">
        <el-button
          type="primary"
          size="large"
          class="login-button"
          @click="goToLogin"
        >
          返回登录
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { Lock, InfoFilled } from '@element-plus/icons-vue'

const router = useRouter()

// 返回登录页
const goToLogin = () => {
  router.push('/login')
}
</script>

<style lang="scss" scoped>
.registration-disabled-container {
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
    background-image:
      radial-gradient(circle at 20% 50%, rgba(120, 119, 198, 0.3) 0%, transparent 50%),
      radial-gradient(circle at 80% 20%, rgba(255, 119, 198, 0.3) 0%, transparent 50%),
      radial-gradient(circle at 40% 80%, rgba(120, 219, 255, 0.3) 0%, transparent 50%);
    pointer-events: none;
  }
}

.registration-disabled-card {
  width: 100%;
  max-width: 600px;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 16px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  padding: 40px 32px;
  position: relative;
  z-index: 1;
  animation: slideInUp 0.6s ease-out;
}

.registration-disabled-header {
  text-align: center;
  margin-bottom: 32px;

  .icon-wrapper {
    margin-bottom: 24px;
    animation: pulse 2s ease-in-out infinite;
  }

  .title {
    font-size: 32px;
    font-weight: 700;
    color: #2c3e50;
    margin: 0 0 8px 0;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }

  .subtitle {
    font-size: 16px;
    color: #7f8c8d;
    margin: 0;
    font-weight: 400;
  }
}

.content {
  margin-bottom: 32px;
}

.message-box {
  text-align: center;
  margin-bottom: 32px;

  .main-message {
    font-size: 24px;
    font-weight: 600;
    color: #2c3e50;
    margin: 0 0 16px 0;
  }

  .description {
    font-size: 16px;
    color: #666;
    line-height: 1.6;
    margin: 0;

    strong {
      color: #667eea;
      font-weight: 600;
    }
  }
}

.instruction-box {
  background: linear-gradient(135deg, #f5f7fa 0%, #e8ecf1 100%);
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 24px;

  .instruction-title {
    font-size: 18px;
    font-weight: 600;
    color: #2c3e50;
    margin: 0 0 20px 0;
    text-align: center;
  }

  .steps {
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  .step {
    display: flex;
    align-items: flex-start;
    gap: 16px;

    .step-number {
      flex-shrink: 0;
      width: 36px;
      height: 36px;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 16px;
      font-weight: 600;
      box-shadow: 0 4px 8px rgba(102, 126, 234, 0.3);
    }

    .step-content {
      flex: 1;

      h4 {
        font-size: 16px;
        font-weight: 600;
        color: #2c3e50;
        margin: 0 0 4px 0;
      }

      p {
        font-size: 14px;
        color: #666;
        margin: 0;
        line-height: 1.5;
      }
    }
  }
}

.help-box {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: #e8f4fd;
  border-left: 4px solid #409eff;
  border-radius: 8px;
  font-size: 14px;
  color: #606266;
  line-height: 1.6;

  strong {
    color: #409eff;
    font-weight: 600;
  }
}

.actions {
  display: flex;
  justify-content: center;

  .login-button {
    width: 100%;
    max-width: 300px;
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
  }
}

// 动画效果
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

@keyframes pulse {
  0%,
  100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.05);
  }
}

// 响应式设计
@media (max-width: 768px) {
  .registration-disabled-container {
    padding: 16px;
  }

  .registration-disabled-card {
    padding: 32px 24px;
  }

  .registration-disabled-header {
    .icon-wrapper {
      :deep(.el-icon) {
        font-size: 64px;
      }
    }

    .title {
      font-size: 28px;
    }

    .subtitle {
      font-size: 14px;
    }
  }

  .message-box {
    .main-message {
      font-size: 20px;
    }

    .description {
      font-size: 15px;
    }
  }

  .instruction-box {
    padding: 20px 16px;

    .instruction-title {
      font-size: 16px;
    }

    .step {
      .step-number {
        width: 32px;
        height: 32px;
        font-size: 14px;
      }

      .step-content {
        h4 {
          font-size: 15px;
        }

        p {
          font-size: 13px;
        }
      }
    }
  }

  .help-box {
    padding: 12px;
    font-size: 13px;

    :deep(.el-icon) {
      font-size: 18px;
    }
  }

  .login-button {
    height: 44px;
    font-size: 15px;
  }
}

@media (max-width: 480px) {
  .registration-disabled-card {
    padding: 24px 20px;
  }

  .registration-disabled-header {
    margin-bottom: 24px;

    .icon-wrapper {
      margin-bottom: 16px;

      :deep(.el-icon) {
        font-size: 56px;
      }
    }

    .title {
      font-size: 24px;
    }
  }

  .message-box {
    margin-bottom: 24px;

    .main-message {
      font-size: 18px;
    }

    .description {
      font-size: 14px;
    }
  }

  .instruction-box {
    padding: 16px 12px;
    margin-bottom: 16px;

    .steps {
      gap: 12px;
    }
  }
}

// 暗色模式适配
.dark {
  .registration-disabled-card {
    background: rgba(31, 41, 55, 0.95);
    border: 1px solid rgba(75, 85, 99, 0.2);

    .title {
      color: #f9fafb;
    }

    .subtitle {
      color: #9ca3af;
    }
  }

  .message-box {
    .main-message {
      color: #f9fafb;
    }

    .description {
      color: #d1d5db;
    }
  }

  .instruction-box {
    background: rgba(55, 65, 81, 0.6);

    .instruction-title {
      color: #f9fafb;
    }

    .step-content {
      h4 {
        color: #f9fafb;
      }

      p {
        color: #d1d5db;
      }
    }
  }

  .help-box {
    background: rgba(59, 130, 246, 0.1);
    border-left-color: #3b82f6;
    color: #d1d5db;
  }
}
</style>
