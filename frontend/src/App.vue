<template>
    <div id="app">
        <!-- 根据路由meta.layout选择不同的布局 -->
        <component :is="currentLayout">
            <router-view v-slot="{ Component, route }">
                <transition
                    :name="transitionName"
                    mode="out-in"
                    appear
                    @before-leave="onBeforeLeave"
                    @after-enter="onAfterEnter"
                >
                    <keep-alive :include="cachedViews">
                        <component :is="Component" :key="route.path" />
                    </keep-alive>
                </transition>
            </router-view>
        </component>

        <!-- 全局加载遮罩 -->
        <div v-if="globalLoading" class="global-loading">
            <div class="loading-spinner">
                <el-icon class="is-loading">
                    <Loading />
                </el-icon>
                <p>{{ loadingText }}</p>
            </div>
        </div>

        <!-- 全局消息提示容器 -->
        <el-backtop :right="100" :bottom="100" />

        <!-- 开发环境调试信息 -->
        <div v-if="isDev" class="debug-info">
            <el-button type="primary" size="small" @click="toggleDebugPanel">
                调试面板
            </el-button>
        </div>

        <!-- 调试面板 -->
        <el-drawer
            v-if="isDev"
            v-model="showDebugPanel"
            title="调试信息"
            size="400px"
            direction="rtl"
        >
            <div class="debug-content">
                <h4>路由信息</h4>
                <pre>{{ routeDebugInfo }}</pre>

                <h4>用户状态</h4>
                <pre>{{ userDebugInfo }}</pre>

                <h4>应用配置</h4>
                <pre>{{ appDebugInfo }}</pre>
            </div>
        </el-drawer>
    </div>
</template>

<script setup lang="ts">
import { computed, watch, ref, onMounted, onUnmounted } from "vue";
import { useRoute } from "vue-router";
import { useAuthStore } from "@/stores/auth";
import { ElMessage } from "element-plus";
import { Loading } from "@element-plus/icons-vue";

// 布局组件导入
import MainLayout from "@/layouts/MainLayout.vue";
import BlankLayout from "@/layouts/BlankLayout.vue";

// 状态管理
const route = useRoute();
const authStore = useAuthStore();

// 响应式数据
const globalLoading = ref(false);
const loadingText = ref("加载中...");
const cachedViews = ref<string[]>([]);
const showDebugPanel = ref(false);
const transitionName = ref("fade");

// 计算属性
const isDev = computed(() => import.meta.env.DEV);

const currentLayout = computed(() => {
    const layoutName = route.meta?.layout as string;

    switch (layoutName) {
        case "blank":
            return BlankLayout;
        case "main":
        default:
            return MainLayout;
    }
});

const routeDebugInfo = computed(() => ({
    path: route.path,
    name: route.name,
    params: route.params,
    query: route.query,
    meta: route.meta,
}));

const userDebugInfo = computed(() => ({
    isAuthenticated: authStore.isAuthenticated,
    user: authStore.user,
    role: authStore.userRole,
    token: authStore.accessToken ? "***已设置***" : "未设置",
}));

const appDebugInfo = computed(() => ({
    version: "1.0.0",
    buildTime: new Date().toISOString(),
    env: import.meta.env.MODE,
    baseUrl: import.meta.env.BASE_URL,
    apiUrl: import.meta.env.VITE_API_BASE_URL,
}));

// 方法
const toggleDebugPanel = () => {
    showDebugPanel.value = !showDebugPanel.value;
};

const setGlobalLoading = (loading: boolean, text = "加载中...") => {
    globalLoading.value = loading;
    loadingText.value = text;
};

const onBeforeLeave = () => {
    // 路由离开前的处理
};

const onAfterEnter = () => {
    // 路由进入后的处理
};

const updateCachedViews = () => {
    // 更新需要缓存的视图
    if (route.meta?.keepAlive) {
        const componentName = route.name as string;
        if (componentName && !cachedViews.value.includes(componentName)) {
            cachedViews.value.push(componentName);
        }
    }
};

const handleNetworkChange = () => {
    // 网络状态变化处理
    if (navigator.onLine) {
        ElMessage.success("网络连接已恢复");
    } else {
        ElMessage.warning("网络连接已断开");
    }
};

const handleVisibilityChange = () => {
    // 页面可见性变化处理
    if (document.hidden) {
        // 页面隐藏时的处理
        console.log("页面已隐藏");
    } else {
        // 页面显示时的处理
        console.log("页面已显示");

        // 如果用户已登录，验证token状态
        if (authStore.isAuthenticated) {
            authStore.validateAuth();
        }
    }
};

const handleBeforeUnload = (event: BeforeUnloadEvent) => {
    // 页面卸载前的警告
    const hasUnsavedChanges = false; // 这里可以检查是否有未保存的更改

    if (hasUnsavedChanges) {
        const message = "您有未保存的更改，确定要离开吗？";
        event.returnValue = message;
        return message;
    }
};

// 监听器
watch(
    () => route.path,
    () => {
        updateCachedViews();

        // 设置路由过渡动画
        const depth = route.path.split("/").length;
        transitionName.value = depth > 3 ? "slide-left" : "fade";
    },
    { immediate: true },
);

// 生命周期
onMounted(() => {
    // 监听网络状态变化
    window.addEventListener("online", handleNetworkChange);
    window.addEventListener("offline", handleNetworkChange);

    // 监听页面可见性变化
    document.addEventListener("visibilitychange", handleVisibilityChange);

    // 监听页面卸载前事件
    window.addEventListener("beforeunload", handleBeforeUnload);

    // 应用启动完成日志
    console.log("🎉 五好伴学前端应用已启动");

    // 检查浏览器兼容性
    if (!window.fetch) {
        ElMessage.error("您的浏览器版本过低，请升级浏览器以获得最佳体验");
    }
});

onUnmounted(() => {
    // 清理事件监听器
    window.removeEventListener("online", handleNetworkChange);
    window.removeEventListener("offline", handleNetworkChange);
    document.removeEventListener("visibilitychange", handleVisibilityChange);
    window.removeEventListener("beforeunload", handleBeforeUnload);
});

// 全局方法暴露（用于调试）
if (isDev.value) {
    (window as any).__APP_DEBUG__ = {
        setGlobalLoading,
        authStore,
        route,
        toggleDebugPanel,
    };
}
</script>

<style lang="scss" scoped>
#app {
    width: 100%;
    height: 100%;
    min-height: 100vh;
    font-family:
        "PingFang SC", "Helvetica Neue", Helvetica, "Microsoft YaHei", "微软雅黑",
        Arial, sans-serif;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
    color: var(--el-text-color-primary);
    background-color: var(--el-bg-color);
}

// 全局加载遮罩
.global-loading {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    z-index: 9999;
    display: flex;
    align-items: center;
    justify-content: center;
    background-color: rgba(255, 255, 255, 0.9);
    backdrop-filter: blur(4px);

    .loading-spinner {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 16px;

        .el-icon {
            font-size: 32px;
            color: var(--el-color-primary);
        }

        p {
            margin: 0;
            font-size: 14px;
            color: var(--el-text-color-regular);
        }
    }
}

// 调试信息
.debug-info {
    position: fixed;
    top: 20px;
    right: 20px;
    z-index: 9998;
}

.debug-content {
    h4 {
        margin: 16px 0 8px;
        color: var(--el-color-primary);
        font-size: 14px;
        font-weight: 600;
    }

    pre {
        background-color: var(--el-fill-color-light);
        padding: 8px;
        border-radius: 4px;
        font-size: 12px;
        line-height: 1.4;
        overflow-x: auto;
        white-space: pre-wrap;
        word-break: break-all;
    }
}

// 路由过渡动画
.fade-enter-active,
.fade-leave-active {
    transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
    opacity: 0;
}

.slide-left-enter-active,
.slide-left-leave-active {
    transition:
        transform 0.3s ease,
        opacity 0.3s ease;
}

.slide-left-enter-from {
    transform: translateX(30px);
    opacity: 0;
}

.slide-left-leave-to {
    transform: translateX(-30px);
    opacity: 0;
}

// 响应式设计
@media (max-width: 768px) {
    .debug-info {
        top: 10px;
        right: 10px;
    }
}
</style>

<style>
/* 全局样式重写 */
html,
body {
    margin: 0;
    padding: 0;
    width: 100%;
    height: 100%;
}

#app {
    height: 100%;
}

/* Element Plus 组件样式调整 */
.el-message-box {
    border-radius: 8px;
}

.el-button {
    border-radius: 6px;
}

.el-input__wrapper {
    border-radius: 6px;
}

/* 滚动条样式 */
::-webkit-scrollbar {
    width: 6px;
    height: 6px;
}

::-webkit-scrollbar-track {
    background: var(--el-fill-color-light);
    border-radius: 3px;
}

::-webkit-scrollbar-thumb {
    background: var(--el-border-color);
    border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
    background: var(--el-border-color-dark);
}
</style>
