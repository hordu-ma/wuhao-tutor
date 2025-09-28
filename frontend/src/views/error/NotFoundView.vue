<template>
  <div class="not-found-container">
    <div class="not-found-content">
      <!-- 404 图标 -->
      <div class="error-icon">
        <el-icon size="120" color="#409eff">
          <WarningFilled />
        </el-icon>
      </div>

      <!-- 错误信息 -->
      <div class="error-info">
        <h1 class="error-code">404</h1>
        <h2 class="error-title">页面不存在</h2>
        <p class="error-description">
          抱歉，您访问的页面不存在或已被删除
        </p>
      </div>

      <!-- 操作按钮 -->
      <div class="error-actions">
        <el-button
          type="primary"
          size="large"
          @click="goHome"
        >
          返回首页
        </el-button>
        <el-button
          size="large"
          @click="goBack"
        >
          返回上页
        </el-button>
      </div>

      <!-- 建议链接 -->
      <div class="suggestions">
        <h3>您可能需要：</h3>
        <div class="suggestion-links">
          <el-link
            type="primary"
            @click="$router.push('/dashboard')"
          >
            仪表板
          </el-link>
          <el-link
            type="primary"
            @click="$router.push('/learning')"
          >
            学习问答
          </el-link>
          <el-link
            type="primary"
            @click="$router.push('/homework')"
          >
            作业批改
          </el-link>
        </div>
      </div>
    </div>

    <!-- 装饰元素 -->
    <div class="decoration">
      <div class="floating-shape shape-1"></div>
      <div class="floating-shape shape-2"></div>
      <div class="floating-shape shape-3"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { WarningFilled } from '@element-plus/icons-vue'

const router = useRouter()

// 返回首页
const goHome = () => {
  router.push('/dashboard')
}

// 返回上一页
const goBack = () => {
  if (window.history.length > 1) {
    router.go(-1)
  } else {
    router.push('/dashboard')
  }
}
</script>

<style lang="scss" scoped>
.not-found-container {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
  position: relative;
  overflow: hidden;
}

.not-found-content {
  text-align: center;
  color: white;
  position: relative;
  z-index: 10;
  max-width: 600px;
  width: 100%;
}

.error-icon {
  margin-bottom: 24px;
  animation: bounce 2s infinite;
}

.error-info {
  margin-bottom: 40px;

  .error-code {
    font-size: 120px;
    font-weight: 900;
    margin: 0 0 16px 0;
    background: linear-gradient(45deg, #fff, #f0f0f0);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    text-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
  }

  .error-title {
    font-size: 32px;
    font-weight: 600;
    margin: 0 0 16px 0;
    color: rgba(255, 255, 255, 0.95);
  }

  .error-description {
    font-size: 18px;
    color: rgba(255, 255, 255, 0.8);
    margin: 0;
    line-height: 1.6;
  }
}

.error-actions {
  display: flex;
  gap: 16px;
  justify-content: center;
  margin-bottom: 40px;

  .el-button {
    border-radius: 8px;
    padding: 12px 24px;
    font-weight: 500;
    transition: all 0.3s ease;

    &:hover {
      transform: translateY(-2px);
      box-shadow: 0 8px 16px rgba(0, 0, 0, 0.2);
    }
  }
}

.suggestions {
  h3 {
    font-size: 18px;
    color: rgba(255, 255, 255, 0.9);
    margin: 0 0 16px 0;
    font-weight: 500;
  }

  .suggestion-links {
    display: flex;
    gap: 24px;
    justify-content: center;
    flex-wrap: wrap;

    .el-link {
      color: rgba(255, 255, 255, 0.8);
      font-size: 16px;
      text-decoration: none;
      transition: all 0.3s ease;

      &:hover {
        color: white;
        text-decoration: underline;
      }
    }
  }
}

.decoration {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  pointer-events: none;
  z-index: 1;
}

.floating-shape {
  position: absolute;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.1);
  animation: float 6s ease-in-out infinite;

  &.shape-1 {
    width: 100px;
    height: 100px;
    top: 10%;
    left: 10%;
    animation-delay: 0s;
  }

  &.shape-2 {
    width: 150px;
    height: 150px;
    top: 60%;
    right: 15%;
    animation-delay: 2s;
  }

  &.shape-3 {
    width: 80px;
    height: 80px;
    bottom: 20%;
    left: 15%;
    animation-delay: 4s;
  }
}

// 动画效果
@keyframes bounce {
  0%, 20%, 50%, 80%, 100% {
    transform: translateY(0);
  }
  40% {
    transform: translateY(-10px);
  }
  60% {
    transform: translateY(-5px);
  }
}

@keyframes float {
  0%, 100% {
    transform: translateY(0px);
  }
  50% {
    transform: translateY(-20px);
  }
}

// 响应式设计
@media (max-width: 768px) {
  .not-found-container {
    padding: 16px;
  }

  .error-info .error-code {
    font-size: 80px;
  }

  .error-info .error-title {
    font-size: 24px;
  }

  .error-info .error-description {
    font-size: 16px;
  }

  .error-actions {
    flex-direction: column;
    align-items: center;

    .el-button {
      width: 200px;
    }
  }

  .suggestion-links {
    flex-direction: column;
    gap: 16px !important;
  }

  .floating-shape {
    display: none;
  }
}

@media (max-width: 480px) {
  .error-info .error-code {
    font-size: 60px;
  }

  .error-info .error-title {
    font-size: 20px;
  }

  .error-actions .el-button {
    width: 100%;
    max-width: 300px;
  }
}
</style>
