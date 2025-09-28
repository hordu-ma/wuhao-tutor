<template>
  <div class="pwa-manager">
    <!-- PWA 安装提示 -->
    <div
      v-if="showInstallPrompt"
      class="install-prompt"
      :class="{ 'mobile-prompt': isMobile }"
    >
      <div class="prompt-content">
        <div class="prompt-icon">
          <el-icon :size="24">
            <Download />
          </el-icon>
        </div>
        <div class="prompt-text">
          <div class="prompt-title">安装应用</div>
          <div class="prompt-message">
            将五好伴学添加到主屏幕，获得更好的使用体验
          </div>
        </div>
        <div class="prompt-actions">
          <el-button size="small" @click="dismissInstallPrompt">
            稍后
          </el-button>
          <el-button type="primary" size="small" @click="installApp">
            安装
          </el-button>
        </div>
      </div>
      <button class="close-button" @click="dismissInstallPrompt">
        <el-icon :size="16">
          <Close />
        </el-icon>
      </button>
    </div>

    <!-- 更新提示 -->
    <div v-if="showUpdatePrompt" class="update-prompt">
      <div class="update-content">
        <div class="update-icon">
          <el-icon :size="20" color="#10b981">
            <Refresh />
          </el-icon>
        </div>
        <div class="update-text">
          <div class="update-title">发现新版本</div>
          <div class="update-message">点击刷新以获取最新功能和修复</div>
        </div>
        <div class="update-actions">
          <el-button size="small" @click="dismissUpdatePrompt">
            稍后
          </el-button>
          <el-button type="success" size="small" @click="updateApp">
            立即更新
          </el-button>
        </div>
      </div>
    </div>

    <!-- 网络状态指示器 -->
    <transition name="slide-down">
      <div
        v-if="showNetworkStatus"
        class="network-status"
        :class="networkStatusClass"
      >
        <el-icon :size="16">
          <component :is="networkIcon" />
        </el-icon>
        <span>{{ networkMessage }}</span>
      </div>
    </transition>

    <!-- 离线指示器 -->
    <div v-if="isOffline" class="offline-indicator">
      <el-icon :size="16">
        <Warning />
      </el-icon>
      <span>离线模式</span>
      <el-button size="small" text @click="checkConnection">
        重试连接
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from "vue";
import { ElMessage } from "element-plus";
import { Download, Close, Refresh, Warning } from "@element-plus/icons-vue";

// 响应式数据
const showInstallPrompt = ref(false);
const showUpdatePrompt = ref(false);
const showNetworkStatus = ref(false);
const isOffline = ref(!navigator.onLine);
const isMobile = ref(false);

// 安装相关
let deferredPrompt: any = null;
const isInstalled = ref(false);

// 更新相关
let registration: ServiceWorkerRegistration | null = null;

// 网络状态
const networkStatus = ref<"online" | "offline" | "slow">("online");
const networkMessage = ref("");

// 计算属性
const networkStatusClass = computed(() => {
  return {
    "status-online": networkStatus.value === "online",
    "status-offline": networkStatus.value === "offline",
    "status-slow": networkStatus.value === "slow",
  };
});

const networkIcon = computed(() => {
  switch (networkStatus.value) {
    case "online":
      return "SuccessFilled";
    case "offline":
      return "Warning";
    case "slow":
      return "Warning";
    default:
      return "Warning";
  }
});

// PWA 安装管理
const initPWA = () => {
  // 检测移动设备
  isMobile.value =
    /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(
      navigator.userAgent,
    );

  // 监听安装提示事件
  window.addEventListener("beforeinstallprompt", (e) => {
    e.preventDefault();
    deferredPrompt = e;

    // 延迟显示安装提示
    setTimeout(() => {
      if (
        !isInstalled.value &&
        !localStorage.getItem("pwa-install-dismissed")
      ) {
        showInstallPrompt.value = true;
      }
    }, 10000);
  });

  // 监听安装完成事件
  window.addEventListener("appinstalled", () => {
    isInstalled.value = true;
    showInstallPrompt.value = false;
    ElMessage.success("应用安装成功！");
  });

  // 检查是否已安装
  if (
    window.matchMedia("(display-mode: standalone)").matches ||
    (window as any).navigator.standalone === true
  ) {
    isInstalled.value = true;
  }
};

const installApp = async () => {
  if (!deferredPrompt) return;

  try {
    const result = await deferredPrompt.prompt();

    if (result.outcome === "accepted") {
      ElMessage.success("开始安装应用...");
    } else {
      ElMessage.info("取消安装");
    }
  } catch (error) {
    console.error("安装失败:", error);
    ElMessage.error("安装失败，请稍后重试");
  }

  deferredPrompt = null;
  showInstallPrompt.value = false;
};

const dismissInstallPrompt = () => {
  showInstallPrompt.value = false;
  localStorage.setItem("pwa-install-dismissed", Date.now().toString());
};

// Service Worker 和更新管理
const initServiceWorker = async () => {
  if ("serviceWorker" in navigator) {
    try {
      registration = await navigator.serviceWorker.register("/sw.js");

      registration.addEventListener("updatefound", () => {
        const newWorker = registration!.installing;
        if (newWorker) {
          newWorker.addEventListener("statechange", () => {
            if (
              newWorker.state === "installed" &&
              navigator.serviceWorker.controller
            ) {
              showUpdatePrompt.value = true;
            }
          });
        }
      });

      // 监听来自 Service Worker 的消息
      navigator.serviceWorker.addEventListener("message", (event) => {
        if (event.data && event.data.type === "CACHE_UPDATED") {
          showUpdatePrompt.value = true;
        }
      });
    } catch (error) {
      console.error("Service Worker 注册失败:", error);
    }
  }
};

const updateApp = async () => {
  if (registration?.waiting) {
    registration.waiting.postMessage({ type: "SKIP_WAITING" });

    // 监听控制权转移
    navigator.serviceWorker.addEventListener("controllerchange", () => {
      window.location.reload();
    });
  }

  showUpdatePrompt.value = false;
};

const dismissUpdatePrompt = () => {
  showUpdatePrompt.value = false;
};

// 网络状态管理
const initNetworkMonitoring = () => {
  const updateNetworkStatus = () => {
    const online = navigator.onLine;
    isOffline.value = !online;

    if (online) {
      networkStatus.value = "online";
      networkMessage.value = "网络连接正常";
      showNetworkStatusMessage("网络已连接");
    } else {
      networkStatus.value = "offline";
      networkMessage.value = "网络连接断开";
      showNetworkStatusMessage("网络连接断开，部分功能可能无法使用");
    }
  };

  window.addEventListener("online", updateNetworkStatus);
  window.addEventListener("offline", updateNetworkStatus);
};

const showNetworkStatusMessage = (message: string) => {
  showNetworkStatus.value = true;
  networkMessage.value = message;

  setTimeout(() => {
    showNetworkStatus.value = false;
  }, 3000);
};

const checkConnection = async () => {
  try {
    await fetch("/favicon.ico?t=" + Date.now(), {
      method: "HEAD",
      cache: "no-cache",
    });
    location.reload();
  } catch (error) {
    ElMessage.error("仍无法连接到网络");
  }
};

// 生命周期
onMounted(() => {
  initPWA();
  initServiceWorker();
  initNetworkMonitoring();
});

onUnmounted(() => {
  window.removeEventListener("online", () => {});
  window.removeEventListener("offline", () => {});
});
</script>

<style scoped lang="scss">
.pwa-manager {
  position: relative;
}

// 安装提示
.install-prompt {
  position: fixed;
  top: 20px;
  right: 20px;
  width: 320px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.15);
  z-index: 1000;
  animation: slideInRight 0.3s ease;

  &.mobile-prompt {
    left: 16px;
    right: 16px;
    width: auto;
    top: auto;
    bottom: 80px;
  }

  .prompt-content {
    padding: 20px;
    display: flex;
    align-items: flex-start;
    gap: 16px;

    .prompt-icon {
      color: #3b82f6;
      flex-shrink: 0;
      margin-top: 2px;
    }

    .prompt-text {
      flex: 1;

      .prompt-title {
        font-weight: 600;
        color: #111827;
        margin-bottom: 4px;
      }

      .prompt-message {
        font-size: 0.875rem;
        color: #6b7280;
        line-height: 1.4;
      }
    }

    .prompt-actions {
      display: flex;
      gap: 8px;
      margin-top: 12px;
    }
  }

  .close-button {
    position: absolute;
    top: 12px;
    right: 12px;
    background: none;
    border: none;
    color: #9ca3af;
    cursor: pointer;
    padding: 4px;
    border-radius: 4px;
    transition: all 0.2s ease;

    &:hover {
      background-color: #f3f4f6;
      color: #6b7280;
    }
  }
}

// 更新提示
.update-prompt {
  position: fixed;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  z-index: 1000;
  animation: slideInUp 0.3s ease;
  border: 1px solid #d1fae5;

  .update-content {
    padding: 16px 20px;
    display: flex;
    align-items: center;
    gap: 12px;

    .update-icon {
      flex-shrink: 0;
    }

    .update-text {
      .update-title {
        font-weight: 600;
        color: #065f46;
        margin-bottom: 2px;
      }

      .update-message {
        font-size: 0.875rem;
        color: #047857;
      }
    }

    .update-actions {
      display: flex;
      gap: 8px;
    }
  }
}

// 网络状态指示器
.network-status {
  position: fixed;
  top: 80px;
  left: 50%;
  transform: translateX(-50%);
  background: white;
  padding: 12px 16px;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  z-index: 999;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.875rem;
  font-weight: 500;

  &.status-online {
    background: #d1fae5;
    color: #065f46;
    border: 1px solid #a7f3d0;
  }

  &.status-offline {
    background: #fee2e2;
    color: #991b1b;
    border: 1px solid #fecaca;
  }

  &.status-slow {
    background: #fef3c7;
    color: #92400e;
    border: 1px solid #fde68a;
  }
}

// 离线指示器
.offline-indicator {
  position: fixed;
  bottom: 80px;
  left: 50%;
  transform: translateX(-50%);
  background: #1f2937;
  color: white;
  padding: 12px 16px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 0.875rem;
  z-index: 999;
  animation: slideInUp 0.3s ease;

  .el-button {
    color: #60a5fa;
    font-size: 0.75rem;
  }
}

// 动画
@keyframes slideInRight {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

@keyframes slideInUp {
  from {
    transform: translate(-50%, 100%);
    opacity: 0;
  }
  to {
    transform: translate(-50%, 0);
    opacity: 1;
  }
}

.slide-down-enter-active,
.slide-down-leave-active {
  transition: all 0.3s ease;
}

.slide-down-enter-from,
.slide-down-leave-to {
  transform: translate(-50%, -100%);
  opacity: 0;
}

// 响应式适配
@media (max-width: 768px) {
  .install-prompt {
    left: 12px;
    right: 12px;
    width: auto;

    .prompt-content {
      padding: 16px;
      gap: 12px;

      .prompt-actions {
        width: 100%;
        justify-content: space-between;

        .el-button {
          flex: 1;
        }
      }
    }
  }

  .update-prompt {
    left: 12px;
    right: 12px;
    transform: none;

    .update-content {
      flex-direction: column;
      align-items: flex-start;

      .update-actions {
        width: 100%;
        justify-content: space-between;
      }
    }
  }
}
</style>
