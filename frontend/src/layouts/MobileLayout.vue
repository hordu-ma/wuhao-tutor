<template>
  <div class="mobile-layout" :class="{ 'sidebar-open': sidebarOpen }">
    <!-- 移动端顶部导航栏 -->
    <header class="mobile-header">
      <div class="header-content">
        <button
          class="menu-button touch-optimized btn-touch"
          @click="toggleSidebar"
          :aria-label="sidebarOpen ? '关闭菜单' : '打开菜单'"
        >
          <el-icon :size="20">
            <Menu v-if="!sidebarOpen" />
            <Close v-else />
          </el-icon>
        </button>

        <div class="header-title">
          <h1 class="app-title">{{ currentPageTitle }}</h1>
        </div>

        <div class="header-actions">
          <!-- 通知按钮 -->
          <button
            class="action-button touch-optimized btn-touch"
            @click="showNotifications"
            :aria-label="`通知${unreadCount > 0 ? `(${unreadCount})` : ''}`"
          >
            <el-badge :value="unreadCount" :hidden="unreadCount === 0" :max="99">
              <el-icon :size="20">
                <Bell />
              </el-icon>
            </el-badge>
          </button>

          <!-- 用户头像 -->
          <div class="user-avatar" @click="showUserMenu">
            <el-avatar :size="32" :alt="'用户'">
              <el-icon><User /></el-icon>
            </el-avatar>
          </div>
        </div>
      </div>
    </header>

    <!-- 侧边栏遮罩 -->
    <div class="sidebar-overlay" :class="{ show: sidebarOpen }" @click="closeSidebar" />

    <!-- 侧边栏 -->
    <aside class="mobile-sidebar" :class="{ open: sidebarOpen }">
      <div class="sidebar-content">
        <!-- 用户信息区域 -->
        <div class="user-section">
          <div class="user-info">
            <el-avatar :size="48">
              <el-icon><User /></el-icon>
            </el-avatar>
            <div class="user-details">
              <div class="user-name">用户</div>
              <div class="user-role">学生</div>
            </div>
          </div>
        </div>

        <!-- 导航菜单 -->
        <nav class="sidebar-nav">
          <div class="nav-section">
            <div class="nav-section-title">主要功能</div>
            <ul class="nav-list">
              <li v-for="item in mainNavItems" :key="item.path" class="nav-item">
                <router-link
                  :to="item.path"
                  class="nav-link touch-optimized"
                  :class="{ active: route.path === item.path }"
                  @click="closeSidebar"
                >
                  <el-icon class="nav-icon" :size="20">
                    <component :is="item.icon" />
                  </el-icon>
                  <span class="nav-text">{{ item.title }}</span>
                </router-link>
              </li>
            </ul>
          </div>
        </nav>

        <!-- 底部操作 -->
        <div class="sidebar-footer">
          <button class="settings-button touch-optimized btn-touch" @click="openSettings">
            <el-icon :size="18">
              <Setting />
            </el-icon>
            <span>设置</span>
          </button>

          <button class="logout-button touch-optimized btn-touch" @click="handleLogout">
            <el-icon :size="18">
              <SwitchButton />
            </el-icon>
            <span>退出</span>
          </button>
        </div>
      </div>
    </aside>

    <!-- 主内容区域 -->
    <main class="main-content">
      <div class="content-wrapper">
        <router-view v-slot="{ Component }">
          <transition name="page" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </div>
    </main>

    <!-- 底部导航栏 -->
    <nav class="bottom-navigation">
      <router-link
        v-for="item in bottomNavItems"
        :key="item.path"
        :to="item.path"
        class="nav-item touch-optimized"
        :class="{ active: route.path === item.path }"
      >
        <div class="nav-icon">
          <el-icon :size="22">
            <component :is="item.icon" />
          </el-icon>
        </div>
        <span class="nav-text">{{ item.title }}</span>
      </router-link>
    </nav>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import { Menu, Close, Bell, User, Setting, SwitchButton } from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()

// 响应式数据
const sidebarOpen = ref(false)
const unreadCount = ref(0)

// 导航菜单配置
const mainNavItems = [
  {
    path: '/',
    title: '首页',
    icon: 'House',
  },
  {
    path: '/homework',
    title: '作业批改',
    icon: 'Document',
  },
  {
    path: '/learning',
    title: '学习问答',
    icon: 'ChatSquare',
  },
  {
    path: '/analytics',
    title: '学习进度',
    icon: 'DataAnalysis',
  },
]

const bottomNavItems = [
  {
    path: '/',
    title: '首页',
    icon: 'House',
  },
  {
    path: '/homework',
    title: '批改',
    icon: 'Document',
  },
  {
    path: '/learning',
    title: '问答',
    icon: 'ChatSquare',
  },
  {
    path: '/analytics',
    title: '分析',
    icon: 'DataAnalysis',
  },
]

// 计算属性
const currentPageTitle = computed(() => {
  const currentPath = route.path
  const navItem = mainNavItems.find((item) => item.path === currentPath)
  return navItem?.title || '五好伴学'
})

// 方法
const toggleSidebar = () => {
  sidebarOpen.value = !sidebarOpen.value
}

const closeSidebar = () => {
  sidebarOpen.value = false
}

const showNotifications = () => {
  // 显示通知
  console.log('显示通知')
}

const showUserMenu = () => {
  // 显示用户菜单
  console.log('显示用户菜单')
}

const openSettings = () => {
  closeSidebar()
  router.push('/settings')
}

const handleLogout = async () => {
  try {
    const result = await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })

    if (result === 'confirm') {
      router.push('/login')
    }
  } catch (error) {
    // 用户取消
  }
}
</script>

<style scoped lang="scss">
@import '@/styles/responsive.scss';

.mobile-layout {
  min-height: 100vh;
  background-color: #f8fafc;
  position: relative;

  // 移动端顶部导航栏
  .mobile-header {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    height: 60px;
    background: white;
    border-bottom: 1px solid #e5e7eb;
    z-index: 100;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.08);

    .header-content {
      display: flex;
      align-items: center;
      justify-content: space-between;
      height: 100%;
      padding: 0 16px;
    }

    .menu-button {
      background: none;
      border: none;
      color: #374151;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: color 0.2s ease;

      &:hover {
        color: #3b82f6;
      }
    }

    .header-title {
      flex: 1;
      text-align: center;
      margin: 0 16px;

      .app-title {
        font-size: 1.125rem;
        font-weight: 600;
        color: #111827;
        margin: 0;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
      }
    }

    .header-actions {
      display: flex;
      align-items: center;
      gap: 12px;

      .action-button {
        background: none;
        border: none;
        color: #6b7280;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: color 0.2s ease;

        &:hover {
          color: #3b82f6;
        }
      }

      .user-avatar {
        cursor: pointer;
        transition: transform 0.2s ease;

        &:hover {
          transform: scale(1.05);
        }
      }
    }
  }

  // 侧边栏遮罩
  .sidebar-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    background: rgba(0, 0, 0, 0.5);
    z-index: 200;
    opacity: 0;
    visibility: hidden;
    transition: all 0.3s ease;

    &.show {
      opacity: 1;
      visibility: visible;
    }
  }

  // 侧边栏
  .mobile-sidebar {
    position: fixed;
    top: 0;
    left: -320px;
    width: 320px;
    height: 100vh;
    background: white;
    z-index: 300;
    transition: left 0.3s ease;
    box-shadow: 2px 0 8px rgba(0, 0, 0, 0.15);
    overflow-y: auto;

    &.open {
      left: 0;
    }

    .sidebar-content {
      display: flex;
      flex-direction: column;
      height: 100%;
      padding: 16px 0;
    }

    .user-section {
      padding: 0 20px 20px;
      border-bottom: 1px solid #f3f4f6;

      .user-info {
        display: flex;
        align-items: center;
        gap: 12px;

        .user-details {
          flex: 1;

          .user-name {
            font-weight: 600;
            color: #111827;
            margin-bottom: 2px;
          }

          .user-role {
            font-size: 0.875rem;
            color: #6b7280;
          }
        }
      }
    }

    .sidebar-nav {
      flex: 1;
      padding: 16px 0;

      .nav-section {
        margin-bottom: 24px;

        .nav-section-title {
          font-size: 0.75rem;
          font-weight: 600;
          color: #9ca3af;
          text-transform: uppercase;
          letter-spacing: 0.05em;
          margin-bottom: 8px;
          padding: 0 20px;
        }

        .nav-list {
          list-style: none;
          margin: 0;
          padding: 0;

          .nav-item {
            .nav-link {
              display: flex;
              align-items: center;
              padding: 12px 20px;
              color: #6b7280;
              text-decoration: none;
              transition: all 0.2s ease;
              position: relative;

              &:hover {
                background-color: #f9fafb;
                color: #3b82f6;
              }

              &.active {
                background-color: #eff6ff;
                color: #3b82f6;

                &::before {
                  content: '';
                  position: absolute;
                  left: 0;
                  top: 0;
                  bottom: 0;
                  width: 3px;
                  background-color: #3b82f6;
                }
              }

              .nav-icon {
                margin-right: 12px;
                flex-shrink: 0;
              }

              .nav-text {
                flex: 1;
                font-weight: 500;
              }
            }
          }
        }
      }
    }

    .sidebar-footer {
      padding: 16px 20px;
      border-top: 1px solid #f3f4f6;
      display: flex;
      flex-direction: column;
      gap: 8px;

      .settings-button,
      .logout-button {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 12px;
        background: none;
        border: none;
        color: #6b7280;
        text-align: left;
        border-radius: 8px;
        transition: all 0.2s ease;
        font-size: 0.875rem;

        &:hover {
          background-color: #f9fafb;
          color: #3b82f6;
        }
      }

      .logout-button:hover {
        color: #ef4444;
      }
    }
  }

  // 主内容区域
  .main-content {
    margin-top: 60px;
    margin-bottom: 60px;
    min-height: calc(100vh - 120px);

    .content-wrapper {
      padding: 16px;
    }
  }

  // 底部导航栏
  .bottom-navigation {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    height: 60px;
    background: white;
    border-top: 1px solid #e5e7eb;
    display: flex;
    z-index: 100;
    box-shadow: 0 -2px 4px rgba(0, 0, 0, 0.08);

    .nav-item {
      flex: 1;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      text-decoration: none;
      color: #9ca3af;
      font-size: 0.75rem;
      transition: color 0.2s ease;
      position: relative;
      overflow: hidden;

      .nav-icon {
        margin-bottom: 2px;
        position: relative;
      }

      .nav-text {
        font-weight: 500;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
      }

      &.active {
        color: #3b82f6;

        &::before {
          content: '';
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          height: 2px;
          background-color: #3b82f6;
        }
      }

      &:hover {
        color: #3b82f6;
        background-color: #f8fafc;
      }
    }
  }

  // 页面过渡动画
  .page-enter-active,
  .page-leave-active {
    transition: all 0.3s ease;
  }

  .page-enter-from,
  .page-leave-to {
    opacity: 0;
    transform: translateX(10px);
  }
}

.touch-optimized {
  -webkit-tap-highlight-color: transparent;
  -webkit-touch-callout: none;
  -webkit-user-select: none;
  -moz-user-select: none;
  -ms-user-select: none;
  user-select: none;

  &.btn-touch {
    min-height: 44px;
    min-width: 44px;
    padding: 12px 16px;

    @include respond-below('sm') {
      min-height: 48px;
      padding: 14px 18px;
    }
  }
}
</style>
