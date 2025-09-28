<template>
  <div class="error-fallback">
    <div class="error-content">
      <div class="error-icon">
        <el-icon :size="64" color="#f56565">
          <WarningFilled />
        </el-icon>
      </div>

      <div class="error-info">
        <h2 class="error-title">页面加载失败</h2>
        <p class="error-message">
          {{ errorMessage || "抱歉，该页面暂时无法加载，请稍后重试。" }}
        </p>

        <div class="error-actions">
          <el-button type="primary" @click="handleRetry">
            <el-icon class="mr-2">
              <Refresh />
            </el-icon>
            重新加载
          </el-button>

          <el-button @click="handleGoBack">
            <el-icon class="mr-2">
              <ArrowLeft />
            </el-icon>
            返回上页
          </el-button>

          <el-button @click="handleGoHome">
            <el-icon class="mr-2">
              <House />
            </el-icon>
            回到首页
          </el-button>
        </div>
      </div>
    </div>

    <!-- 开发环境下显示详细错误信息 -->
    <div v-if="isDev && errorDetails" class="error-details">
      <el-collapse v-model="showDetails">
        <el-collapse-item title="查看详细错误信息" name="details">
          <pre class="error-stack">{{ errorDetails }}</pre>
        </el-collapse-item>
      </el-collapse>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from "vue";
import { useRouter } from "vue-router";

import {
  WarningFilled,
  Refresh,
  ArrowLeft,
  House,
} from "@element-plus/icons-vue";

// Props
interface Props {
  error?: Error | string;
  retry?: () => void;
}

const props = withDefaults(defineProps<Props>(), {
  error: undefined,
  retry: undefined,
});

// 响应式数据
const showDetails = ref([]);
const router = useRouter();

// 计算属性
const isDev = computed(() => import.meta.env.DEV);

const errorMessage = computed(() => {
  if (typeof props.error === "string") {
    return props.error;
  }
  if (props.error instanceof Error) {
    return props.error.message;
  }
  return null;
});

const errorDetails = computed(() => {
  if (props.error instanceof Error) {
    return props.error.stack || props.error.toString();
  }
  return null;
});

// 方法
const handleRetry = () => {
  if (props.retry) {
    props.retry();
  } else {
    // 默认刷新页面
    window.location.reload();
  }
};

const handleGoBack = () => {
  if (window.history.length > 1) {
    router.go(-1);
  } else {
    router.push("/");
  }
};

const handleGoHome = () => {
  router.push("/");
};
</script>

<style scoped lang="scss">
.error-fallback {
  min-height: 400px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  background-color: #fafafa;
  border-radius: 8px;
  margin: 1rem;

  .error-content {
    text-align: center;
    max-width: 500px;

    .error-icon {
      margin-bottom: 1.5rem;
      animation: shake 0.5s ease-in-out;
    }

    .error-info {
      .error-title {
        font-size: 1.5rem;
        font-weight: 600;
        color: #2d3748;
        margin-bottom: 0.75rem;
      }

      .error-message {
        color: #718096;
        font-size: 1rem;
        line-height: 1.5;
        margin-bottom: 2rem;
      }

      .error-actions {
        display: flex;
        gap: 0.75rem;
        justify-content: center;
        flex-wrap: wrap;

        .el-button {
          .mr-2 {
            margin-right: 0.5rem;
          }
        }
      }
    }
  }

  .error-details {
    margin-top: 2rem;
    width: 100%;
    max-width: 800px;

    .error-stack {
      background-color: #1a202c;
      color: #e2e8f0;
      padding: 1rem;
      border-radius: 4px;
      font-family: "Courier New", monospace;
      font-size: 0.875rem;
      line-height: 1.4;
      overflow-x: auto;
      white-space: pre-wrap;
      word-break: break-all;
    }
  }
}

@keyframes shake {
  0%,
  100% {
    transform: translateX(0);
  }
  10%,
  30%,
  50%,
  70%,
  90% {
    transform: translateX(-5px);
  }
  20%,
  40%,
  60%,
  80% {
    transform: translateX(5px);
  }
}

// 响应式设计
@media (max-width: 768px) {
  .error-fallback {
    padding: 1rem;
    margin: 0.5rem;

    .error-content {
      .error-info {
        .error-title {
          font-size: 1.25rem;
        }

        .error-message {
          font-size: 0.875rem;
        }

        .error-actions {
          flex-direction: column;
          align-items: center;

          .el-button {
            width: 100%;
            max-width: 200px;
          }
        }
      }
    }

    .error-details {
      margin-top: 1rem;

      .error-stack {
        font-size: 0.75rem;
        padding: 0.75rem;
      }
    }
  }
}
</style>
