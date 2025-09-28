<template>
  <div v-if="hasError" class="error-boundary">
    <div class="error-container" :class="containerClass">
      <!-- 错误图标 -->
      <div class="error-icon" :class="iconClass">
        <el-icon :size="iconSize">
          <component :is="getErrorIcon()" />
        </el-icon>
      </div>

      <!-- 错误标题 -->
      <h3 class="error-title" :class="titleClass">
        {{ errorTitle }}
      </h3>

      <!-- 错误描述 -->
      <p class="error-description" :class="descriptionClass">
        {{ errorDescription }}
      </p>

      <!-- 错误详情（开发环境） -->
      <details v-if="showDetails && isDevelopment" class="error-details">
        <summary class="error-details-summary">查看技术详情</summary>
        <div class="error-details-content">
          <pre class="error-stack">{{ errorStack }}</pre>
        </div>
      </details>

      <!-- 操作按钮 -->
      <div class="error-actions" :class="actionsClass">
        <el-button
          v-if="showRetry"
          type="primary"
          :size="buttonSize"
          :icon="Refresh"
          @click="handleRetry"
          :loading="retrying"
        >
          重试
        </el-button>

        <el-button
          v-if="showReload"
          type="default"
          :size="buttonSize"
          :icon="RefreshRight"
          @click="handleReload"
        >
          重新加载页面
        </el-button>

        <el-button
          v-if="showHome"
          type="default"
          :size="buttonSize"
          :icon="House"
          @click="handleGoHome"
        >
          返回首页
        </el-button>

        <el-button
          v-if="showReport"
          type="default"
          :size="buttonSize"
          :icon="Warning"
          @click="handleReport"
        >
          报告问题
        </el-button>
      </div>

      <!-- 联系信息 -->
      <div v-if="showContact" class="error-contact">
        <p class="contact-text">如果问题持续存在，请联系技术支持：</p>
        <a href="mailto:support@wuhao-tutor.com" class="contact-link">
          support@wuhao-tutor.com
        </a>
      </div>
    </div>

    <!-- 背景图案 -->
    <div v-if="showPattern" class="error-pattern">
      <div class="pattern-circle pattern-circle-1"></div>
      <div class="pattern-circle pattern-circle-2"></div>
      <div class="pattern-circle pattern-circle-3"></div>
    </div>
  </div>

  <!-- 正常内容 -->
  <div v-else>
    <slot />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onErrorCaptured, onMounted } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import {
  Refresh,
  RefreshRight,
  House,
  Warning,
  CircleCloseFilled,
  WarnTriangleFilled,
  InfoFilled,
} from "@element-plus/icons-vue";

interface Props {
  // 错误类型
  errorType?: "network" | "runtime" | "chunk" | "permission" | "unknown";
  // 尺寸
  size?: "small" | "medium" | "large";
  // 是否显示重试按钮
  showRetry?: boolean;
  // 是否显示重新加载按钮
  showReload?: boolean;
  // 是否显示返回首页按钮
  showHome?: boolean;
  // 是否显示报告问题按钮
  showReport?: boolean;
  // 是否显示联系信息
  showContact?: boolean;
  // 是否显示错误详情
  showDetails?: boolean;
  // 是否显示背景图案
  showPattern?: boolean;
  // 自定义错误标题
  customTitle?: string;
  // 自定义错误描述
  customDescription?: string;
  // 重试回调
  onRetry?: () => void | Promise<void>;
  // 报告问题回调
  onReport?: (error: Error) => void;
}

const props = withDefaults(defineProps<Props>(), {
  errorType: "unknown",
  size: "medium",
  showRetry: true,
  showReload: true,
  showHome: true,
  showReport: false,
  showContact: false,
  showDetails: false,
  showPattern: true,
});

const router = useRouter();

// 响应式状态
const hasError = ref(false);
const errorInfo = ref<Error | null>(null);
const retrying = ref(false);
const isDevelopment = computed(() => import.meta.env.DEV);

// 错误信息配置
const errorConfig = {
  network: {
    title: "网络连接失败",
    description: "请检查您的网络连接状态，然后重试",
    icon: "warning",
  },
  runtime: {
    title: "程序运行错误",
    description: "程序遇到了意外错误，请刷新页面重试",
    icon: "error",
  },
  chunk: {
    title: "资源加载失败",
    description: "部分页面资源加载失败，请刷新页面重新加载",
    icon: "warning",
  },
  permission: {
    title: "权限不足",
    description: "您没有访问此页面的权限，请联系管理员",
    icon: "warning",
  },
  unknown: {
    title: "出现了一些问题",
    description: "系统遇到了未知错误，请稍后重试",
    icon: "error",
  },
};

// 计算属性
const currentConfig = computed(
  () => errorConfig[props.errorType] || errorConfig.unknown,
);

const errorTitle = computed(() => {
  return props.customTitle || currentConfig.value.title;
});

const errorDescription = computed(() => {
  return props.customDescription || currentConfig.value.description;
});

const errorStack = computed(() => {
  if (!errorInfo.value) return "";
  return errorInfo.value.stack || errorInfo.value.toString();
});

const containerClass = computed(() => [
  `error-container-${props.size}`,
  `error-container-${props.errorType}`,
]);

const iconClass = computed(() => [
  `error-icon-${props.size}`,
  `error-icon-${currentConfig.value.icon}`,
]);

const titleClass = computed(() => [`error-title-${props.size}`]);

const descriptionClass = computed(() => [`error-description-${props.size}`]);

const actionsClass = computed(() => [`error-actions-${props.size}`]);

const iconSize = computed(() => {
  const sizeMap = {
    small: 32,
    medium: 48,
    large: 64,
  };
  return sizeMap[props.size];
});

const buttonSize = computed(() => {
  const sizeMap = {
    small: "small",
    medium: "default",
    large: "large",
  };
  return sizeMap[props.size] as "small" | "default" | "large";
});

// 获取错误图标
const getErrorIcon = () => {
  const iconMap = {
    error: CircleCloseFilled,
    warning: WarnTriangleFilled,
    info: InfoFilled,
  };
  return (
    iconMap[currentConfig.value.icon as keyof typeof iconMap] ||
    CircleCloseFilled
  );
};

// 错误捕获
onErrorCaptured((error: Error, _instance, info) => {
  console.error("Error caught by ErrorBoundary:", error);
  console.error("Error info:", info);

  hasError.value = true;
  errorInfo.value = error;

  // 发送错误报告到监控系统
  reportError(error, info);

  return false; // 阻止错误继续传播
});

// 全局错误监听
onMounted(() => {
  window.addEventListener("error", handleGlobalError);
  window.addEventListener("unhandledrejection", handleUnhandledRejection);
});

// 处理全局错误
const handleGlobalError = (event: ErrorEvent) => {
  console.error("Global error:", event.error);

  hasError.value = true;
  errorInfo.value = event.error;

  reportError(event.error, "Global error");
};

// 处理未捕获的Promise拒绝
const handleUnhandledRejection = (event: PromiseRejectionEvent) => {
  console.error("Unhandled promise rejection:", event.reason);

  hasError.value = true;
  errorInfo.value = new Error(event.reason);

  reportError(event.reason, "Unhandled promise rejection");
};

// 事件处理函数
const handleRetry = async () => {
  if (props.onRetry) {
    retrying.value = true;
    try {
      await props.onRetry();
      // 如果重试成功，重置错误状态
      hasError.value = false;
      errorInfo.value = null;
      ElMessage.success("重试成功");
    } catch (error) {
      ElMessage.error("重试失败，请稍后再试");
      console.error("Retry failed:", error);
    } finally {
      retrying.value = false;
    }
  } else {
    // 默认重试：重新加载当前路由
    const currentRoute = router.currentRoute.value;
    await router.replace({ path: "/loading" });
    await router.replace(currentRoute);

    hasError.value = false;
    errorInfo.value = null;
  }
};

const handleReload = () => {
  window.location.reload();
};

const handleGoHome = () => {
  router.replace("/");
};

const handleReport = () => {
  if (props.onReport && errorInfo.value) {
    props.onReport(errorInfo.value);
  } else {
    // 默认报告行为
    const errorDetails = {
      message: errorInfo.value?.message || "Unknown error",
      stack: errorInfo.value?.stack || "",
      url: window.location.href,
      userAgent: navigator.userAgent,
      timestamp: new Date().toISOString(),
    };

    // 这里可以发送到错误报告服务
    console.log("Error report:", errorDetails);
    ElMessage.success("问题已报告，感谢您的反馈");
  }
};

// 错误报告函数
const reportError = (error: any, info: string) => {
  // 这里可以集成第三方错误监控服务
  // 如 Sentry、LogRocket 等

  if (typeof error === "object" && error !== null) {
    const errorReport = {
      message: error.message || "Unknown error",
      stack: error.stack || "",
      info: info,
      url: window.location.href,
      userAgent: navigator.userAgent,
      timestamp: new Date().toISOString(),
      userId: "current-user-id", // 从用户状态获取
      errorType: props.errorType,
    };

    // 发送到监控服务
    // errorMonitoringService.captureException(errorReport)

    console.warn("Error reported:", errorReport);
  }
};

// 重置错误状态的方法
const resetError = () => {
  hasError.value = false;
  errorInfo.value = null;
};

// 暴露方法给父组件
defineExpose({
  resetError,
  hasError,
  errorInfo,
});
</script>

<style scoped>
.error-boundary {
  position: relative;
  min-height: 400px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  overflow: hidden;
}

.error-container {
  position: relative;
  z-index: 1;
  text-align: center;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 1rem;
  padding: 2rem;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
  max-width: 600px;
  width: 100%;
}

/* 容器尺寸变体 */
.error-container-small {
  padding: 1.5rem;
  max-width: 400px;
}

.error-container-medium {
  padding: 2rem;
  max-width: 600px;
}

.error-container-large {
  padding: 3rem;
  max-width: 800px;
}

/* 错误图标 */
.error-icon {
  margin-bottom: 1.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
}

.error-icon-small {
  margin-bottom: 1rem;
}

.error-icon-large {
  margin-bottom: 2rem;
}

.error-icon-error {
  color: #ef4444;
}

.error-icon-warning {
  color: #f59e0b;
}

.error-icon-info {
  color: #3b82f6;
}

/* 错误标题 */
.error-title {
  margin-bottom: 1rem;
  font-weight: 600;
  color: #1f2937;
}

.error-title-small {
  font-size: 1.25rem;
  margin-bottom: 0.75rem;
}

.error-title-medium {
  font-size: 1.5rem;
  margin-bottom: 1rem;
}

.error-title-large {
  font-size: 1.875rem;
  margin-bottom: 1.25rem;
}

/* 错误描述 */
.error-description {
  margin-bottom: 2rem;
  color: #6b7280;
  line-height: 1.6;
}

.error-description-small {
  font-size: 0.875rem;
  margin-bottom: 1.5rem;
}

.error-description-medium {
  font-size: 1rem;
  margin-bottom: 2rem;
}

.error-description-large {
  font-size: 1.125rem;
  margin-bottom: 2.5rem;
}

/* 错误详情 */
.error-details {
  margin: 1.5rem 0;
  text-align: left;
  border: 1px solid #e5e7eb;
  border-radius: 0.5rem;
  overflow: hidden;
}

.error-details-summary {
  padding: 0.75rem 1rem;
  background: #f9fafb;
  border-bottom: 1px solid #e5e7eb;
  cursor: pointer;
  font-size: 0.875rem;
  font-weight: 500;
  color: #374151;
}

.error-details-summary:hover {
  background: #f3f4f6;
}

.error-details-content {
  padding: 1rem;
  background: #fafafa;
}

.error-stack {
  font-family: "Monaco", "Consolas", monospace;
  font-size: 0.75rem;
  color: #dc2626;
  white-space: pre-wrap;
  word-break: break-all;
  margin: 0;
  max-height: 200px;
  overflow-y: auto;
}

/* 操作按钮 */
.error-actions {
  display: flex;
  gap: 0.75rem;
  justify-content: center;
  flex-wrap: wrap;
  margin-bottom: 1.5rem;
}

.error-actions-small .el-button {
  min-width: auto;
}

.error-actions-large {
  gap: 1rem;
}

.error-actions-large .el-button {
  min-width: 120px;
}

/* 联系信息 */
.error-contact {
  margin-top: 1.5rem;
  padding-top: 1.5rem;
  border-top: 1px solid #e5e7eb;
}

.contact-text {
  font-size: 0.875rem;
  color: #6b7280;
  margin-bottom: 0.5rem;
}

.contact-link {
  color: #3b82f6;
  text-decoration: none;
  font-size: 0.875rem;
  font-weight: 500;
}

.contact-link:hover {
  text-decoration: underline;
}

/* 背景图案 */
.error-pattern {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  pointer-events: none;
  overflow: hidden;
}

.pattern-circle {
  position: absolute;
  border-radius: 50%;
  background: linear-gradient(
    45deg,
    rgba(59, 130, 246, 0.1),
    rgba(147, 197, 253, 0.1)
  );
  animation: float 6s ease-in-out infinite;
}

.pattern-circle-1 {
  width: 120px;
  height: 120px;
  top: 10%;
  right: 10%;
  animation-delay: 0s;
}

.pattern-circle-2 {
  width: 80px;
  height: 80px;
  bottom: 20%;
  left: 15%;
  animation-delay: 2s;
}

.pattern-circle-3 {
  width: 60px;
  height: 60px;
  top: 60%;
  right: 20%;
  animation-delay: 4s;
}

/* 动画定义 */
@keyframes float {
  0%,
  100% {
    transform: translateY(0px) rotate(0deg);
    opacity: 0.5;
  }
  50% {
    transform: translateY(-20px) rotate(180deg);
    opacity: 0.8;
  }
}

/* 响应式设计 */
@media (max-width: 640px) {
  .error-boundary {
    padding: 1rem;
    min-height: 300px;
  }

  .error-container {
    padding: 1.5rem;
  }

  .error-actions {
    flex-direction: column;
    align-items: stretch;
  }

  .error-actions .el-button {
    width: 100%;
  }

  .pattern-circle {
    display: none;
  }
}

/* 深色模式支持 */
@media (prefers-color-scheme: dark) {
  .error-container {
    background: rgba(31, 41, 55, 0.95);
    color: #f9fafb;
  }

  .error-title {
    color: #f9fafb;
  }

  .error-description {
    color: #d1d5db;
  }

  .error-details {
    border-color: #4b5563;
  }

  .error-details-summary {
    background: #374151;
    border-color: #4b5563;
    color: #f9fafb;
  }

  .error-details-summary:hover {
    background: #4b5563;
  }

  .error-details-content {
    background: #1f2937;
  }

  .contact-text {
    color: #9ca3af;
  }

  .error-contact {
    border-color: #4b5563;
  }
}

/* 减少动画模式支持 */
@media (prefers-reduced-motion: reduce) {
  .pattern-circle {
    animation: none;
  }
}
</style>
