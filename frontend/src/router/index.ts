/**
 * Vue Router 路由配置
 * 定义前端应用的路由结构和导航守卫
 */

import { createRouter, createWebHistory } from "vue-router";
import type { RouteRecordRaw } from "vue-router";
import { useAuthStore } from "@/stores/auth";
import { ElMessage } from "element-plus";
import NProgress from "nprogress";
import "nprogress/nprogress.css";

// 配置NProgress
NProgress.configure({ showSpinner: false });

// 路由配置
const routes: RouteRecordRaw[] = [
  // 根路径重定向
  {
    path: "/",
    redirect: "/dashboard",
  },

  // 登录页
  {
    path: "/login",
    name: "Login",
    component: () => import("@/views/auth/LoginView.vue"),
    meta: {
      title: "用户登录",
      requiresAuth: false,
      hideInMenu: true,
      layout: "blank",
    },
  },

  // 注册页
  {
    path: "/register",
    name: "Register",
    component: () => import("@/views/auth/RegisterView.vue"),
    meta: {
      title: "用户注册",
      requiresAuth: false,
      hideInMenu: true,
      layout: "blank",
    },
  },

  // 作业管理
  {
    path: "/homework",
    name: "HomeworkList",
    component: () => import("@/views/homework/HomeworkList.vue"),
    meta: {
      title: "我的作业",
      requiresAuth: true,
      layout: "main",
      icon: "Notebook",
    },
  },

  {
    path: "/homework/upload",
    name: "HomeworkUpload",
    component: () => import("@/views/homework/HomeworkUpload.vue"),
    meta: {
      title: "上传作业",
      requiresAuth: true,
      layout: "main",
      hideInMenu: true,
    },
  },

  {
    path: "/homework/:id",
    name: "HomeworkDetail",
    component: () => import("@/views/homework/HomeworkDetail.vue"),
    meta: {
      title: "作业详情",
      requiresAuth: true,
      layout: "main",
      hideInMenu: true,
    },
  },

  // 学习问答
  {
    path: "/learning",
    name: "Learning",
    component: () => import("@/views/Learning.vue"),
    meta: {
      title: "AI学习助手",
      requiresAuth: true,
      layout: "main",
      icon: "ChatDotRound",
    },
  },

  // 仪表板
  {
    path: "/dashboard",
    name: "Dashboard",
    component: () => import("@/views/dashboard/DashboardView.vue"),
    meta: {
      title: "仪表板",
      requiresAuth: true,
      layout: "main",
      icon: "House",
    },
  },

  // 404页面
  {
    path: "/:pathMatch(.*)*",
    name: "NotFound",
    component: () => import("@/views/error/NotFoundView.vue"),
    meta: {
      title: "页面不存在",
      requiresAuth: false,
      hideInMenu: true,
      layout: "blank",
    },
  },
];

// 创建路由实例
const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
  scrollBehavior(_to, _from, savedPosition) {
    if (savedPosition) {
      return savedPosition;
    } else {
      return { top: 0 };
    }
  },
});

// 全局前置守卫
router.beforeEach(async (to, _from, next) => {
  // 开始加载进度条
  NProgress.start();

  // 设置页面标题
  const title = to.meta?.title;
  if (title) {
    document.title = `${title} - 五好伴学`;
  }

  // 获取认证状态
  const authStore = useAuthStore();

  // 检查路由是否需要认证
  const requiresAuth = to.meta.requiresAuth !== false;

  if (requiresAuth) {
    // 需要认证的页面
    if (!authStore.isAuthenticated) {
      // 未登录，重定向到登录页
      ElMessage.warning("请先登录");
      next({
        path: "/login",
        query: { redirect: to.fullPath },
      });
      return;
    }

    // 验证token有效性
    const isValid = await authStore.validateAuth();
    if (!isValid) {
      ElMessage.error("登录已过期，请重新登录");
      next({
        path: "/login",
        query: { redirect: to.fullPath },
      });
      return;
    }
  } else {
    // 不需要认证的页面
    if (
      authStore.isAuthenticated &&
      (to.path === "/login" || to.path === "/register")
    ) {
      // 已登录用户访问登录/注册页，重定向到仪表板
      next("/dashboard");
      return;
    }
  }

  // 权限检查
  const requiredRole = to.meta.role as string;
  if (requiredRole && authStore.user) {
    if (!authStore.hasRole(requiredRole)) {
      ElMessage.error("权限不足");
      next("/dashboard");
      return;
    }
  }

  next();
});

// 全局后置守卫
router.afterEach((_to, _from) => {
  // 完成加载进度条
  NProgress.done();

  // 页面访问统计（可选）
  if (import.meta.env.PROD) {
    // TODO: 发送页面访问统计
    // analytics.track('page_view', { path: to.path, title: to.meta.title })
  }
});

// 路由错误处理
router.onError((error) => {
  console.error("Router error:", error);
  NProgress.done();
  ElMessage.error("页面加载失败，请刷新重试");
});

export default router;

// 导出路由配置用于其他地方使用
export { routes };

// 路由元信息类型扩展
declare module "vue-router" {
  interface RouteMeta {
    // 页面标题
    title?: string;
    // 是否需要认证
    requiresAuth?: boolean;
    // 所需角色
    role?: string;
    // 是否在菜单中隐藏
    hideInMenu?: boolean;
    // 菜单图标
    icon?: string;
    // 布局类型
    layout?: "main" | "blank";
    // 是否缓存
    keepAlive?: boolean;
    // 面包屑
    breadcrumb?: Array<{ title: string; path?: string }>;
    // 页面描述
    description?: string;
  }
}
