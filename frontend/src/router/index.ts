/**
 * Vue Router 路由配置
 * 定义前端应用的路由结构和导航守卫
 */

import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'
import NProgress from 'nprogress'
import 'nprogress/nprogress.css'

// 配置NProgress
NProgress.configure({ showSpinner: false })

// 路由配置
const routes: RouteRecordRaw[] = [
  // 登录页
  {
    path: '/login',
    name: 'Login',
    component: () => import(/* webpackChunkName: "auth" */ '@/views/auth/LoginView.vue'),
    meta: {
      title: '用户登录',
      requiresAuth: false,
      hideInMenu: true,
      layout: 'blank',
    },
  },

  // 注册页
  {
    path: '/register',
    name: 'Register',
    component: () => import(/* webpackChunkName: "auth" */ '@/views/auth/RegisterView.vue'),
    meta: {
      title: '用户注册',
      requiresAuth: false,
      hideInMenu: true,
      layout: 'blank',
    },
  },

  // 主应用布局
  {
    path: '/',
    children: [
      // 根路径重定向到仪表板
      {
        path: '',
        redirect: '/dashboard',
      },
      // 仪表板
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () =>
          import(/* webpackChunkName: "dashboard" */ '@/views/dashboard/DashboardView.vue'),
        meta: {
          title: '仪表板',
          requiresAuth: true,
          icon: 'House',
          keepAlive: true,
          layout: 'main',
        },
      },
    ],
  },

  // 移动端布局
  {
    path: '/mobile',
    component: () => import(/* webpackChunkName: "mobile-layout" */ '@/layouts/MobileLayout.vue'),
    children: [
      {
        path: '',
        redirect: '/mobile/dashboard',
      },
      {
        path: 'dashboard',
        component: () =>
          import(/* webpackChunkName: "dashboard" */ '@/views/dashboard/DashboardView.vue'),
        meta: {
          title: '首页',
          requiresAuth: true,
        },
      },
      {
        path: 'homework',
        component: () =>
          import(/* webpackChunkName: "homework" */ '@/views/homework/HomeworkList.vue'),
        meta: {
          title: '作业批改',
          requiresAuth: true,
        },
      },
      {
        path: 'learning',
        component: () => import(/* webpackChunkName: "learning" */ '@/views/Learning.vue'),
        meta: {
          title: '学习问答',
          requiresAuth: true,
        },
      },
      {
        path: 'analytics',
        component: () => import(/* webpackChunkName: "analytics" */ '@/views/Analytics.vue'),
        meta: {
          title: '学习进度',
          requiresAuth: true,
        },
      },
    ],
  },

  // 作业管理
  {
    path: '/homework',
    children: [
      {
        path: '',
        name: 'HomeworkList',
        component: () =>
          import(/* webpackChunkName: "homework" */ '@/views/homework/HomeworkList.vue'),
        meta: {
          title: '我的作业',
          requiresAuth: true,
          icon: 'Notebook',
          keepAlive: true,
          layout: 'main',
        },
      },
      {
        path: 'upload',
        name: 'HomeworkUpload',
        component: () =>
          import(/* webpackChunkName: "homework" */ '@/views/homework/HomeworkUpload.vue'),
        meta: {
          title: '上传作业',
          requiresAuth: true,
          hideInMenu: true,
          layout: 'main',
        },
      },
      {
        path: ':id',
        name: 'HomeworkDetail',
        component: () =>
          import(/* webpackChunkName: "homework" */ '@/views/homework/HomeworkDetail.vue'),
        meta: {
          title: '作业详情',
          requiresAuth: true,
          hideInMenu: true,
          layout: 'main',
        },
      },
    ],
  },

  // 学习问答
  {
    path: '/learning',
    children: [
      {
        path: '',
        name: 'Learning',
        component: () => import(/* webpackChunkName: "learning" */ '@/views/Learning.vue'),
        meta: {
          title: 'AI学习助手',
          requiresAuth: true,
          icon: 'ChatDotRound',
          keepAlive: true,
          layout: 'main',
        },
      },
    ],
  },

  // 学习进度
  {
    path: '/analytics',
    children: [
      {
        path: '',
        name: 'Analytics',
        component: () => import(/* webpackChunkName: "analytics" */ '@/views/Analytics.vue'),
        meta: {
          title: '学习进度',
          requiresAuth: true,
          icon: 'DataAnalysis',
          keepAlive: true,
          layout: 'main',
        },
      },
    ],
  },

  // 学习进度（重定向到学习进度分析页面）
  {
    path: '/progress',
    redirect: '/analytics',
  },

  // 个人中心
  {
    path: '/profile',
    children: [
      {
        path: '',
        name: 'Profile',
        component: () => import(/* webpackChunkName: "profile" */ '@/views/Profile.vue'),
        meta: {
          title: '个人中心',
          requiresAuth: true,
          icon: 'User',
          keepAlive: true,
          layout: 'main',
        },
      },
    ],
  },

  // 404页面
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import(/* webpackChunkName: "error" */ '@/views/error/NotFoundView.vue'),
    meta: {
      title: '页面不存在',
      requiresAuth: false,
      hideInMenu: true,
      layout: 'blank',
    },
  },
]

// 创建路由实例
const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
  scrollBehavior(_to, _from, savedPosition) {
    if (savedPosition) {
      return savedPosition
    } else {
      return { top: 0 }
    }
  },
})

// 全局前置守卫
router.beforeEach(async (to, _from, next) => {
  // 开始加载进度条
  NProgress.start()

  // 设置页面标题
  const title = to.meta?.title
  if (title) {
    document.title = `${title} - 五好伴学`
  }

  // 获取认证状态
  const authStore = useAuthStore()

  // 检查路由是否需要认证
  const requiresAuth = to.meta?.requiresAuth

  // 如果明确设置为需要认证
  if (requiresAuth === true) {
    // 需要认证的页面
    if (!authStore.isAuthenticated) {
      // 未登录，重定向到登录页
      ElMessage.warning('请先登录')
      next({
        path: '/login',
        query: { redirect: to.fullPath },
      })
      return
    }

    // 验证token有效性
    const isValid = await authStore.validateAuth()
    if (!isValid) {
      ElMessage.error('登录已过期，请重新登录')
      next({
        path: '/login',
        query: { redirect: to.fullPath },
      })
      return
    }
  }
  // 如果明确设置为不需要认证
  else if (requiresAuth === false) {
    // 不需要认证的页面
    if (authStore.isAuthenticated && (to.path === '/login' || to.path === '/register')) {
      // 已登录用户访问登录/注册页，重定向到仪表板
      next('/dashboard')
      return
    }
  }
  // 如果未明确设置，默认需要认证（除了特定的公开页面）
  else {
    const publicPaths = ['/login', '/register', '/404']
    const isPublicPath = publicPaths.includes(to.path)

    if (!isPublicPath) {
      // 默认需要认证
      if (!authStore.isAuthenticated) {
        ElMessage.warning('请先登录')
        next({
          path: '/login',
          query: { redirect: to.fullPath },
        })
        return
      }

      // 验证token有效性
      const isValid = await authStore.validateAuth()
      if (!isValid) {
        ElMessage.error('登录已过期，请重新登录')
        next({
          path: '/login',
          query: { redirect: to.fullPath },
        })
        return
      }
    }
  }

  // 权限检查
  const requiredRole = to.meta.role as string
  if (requiredRole && authStore.user) {
    if (!authStore.hasRole(requiredRole)) {
      ElMessage.error('权限不足')
      next('/dashboard')
      return
    }
  }

  next()
})

// 全局后置守卫
router.afterEach((_to, _from) => {
  // 完成加载进度条
  NProgress.done()

  // 页面访问统计（可选）
  if (import.meta.env.PROD) {
    // TODO: 发送页面访问统计
    // analytics.track('page_view', { path: to.path, title: to.meta.title })
  }
})

// 路由错误处理
router.onError((error) => {
  console.error('Router error:', error)
  NProgress.done()
  ElMessage.error('页面加载失败，请刷新重试')
})

export default router

// 导出路由配置用于其他地方使用
export { routes }

// 路由元信息类型扩展
declare module 'vue-router' {
  interface RouteMeta {
    // 页面标题
    title?: string
    // 是否需要认证
    requiresAuth?: boolean
    // 所需角色
    role?: string
    // 是否在菜单中隐藏
    hideInMenu?: boolean
    // 菜单图标
    icon?: string
    // 布局类型
    layout?: 'main' | 'blank'
    // 是否缓存
    keepAlive?: boolean
    // 面包屑
    breadcrumb?: Array<{ title: string; path?: string }>
    // 页面描述
    description?: string
  }
}
