<template>
  <div class="main-layout">
    <!-- 顶部导航栏 -->
    <header class="main-header">
      <div class="header-left">
        <div class="logo">
          <h1>五好伴学</h1>
        </div>
      </div>

      <div class="header-right">
        <!-- 用户信息 -->
        <el-dropdown @command="handleUserCommand">
          <div class="user-info">
            <el-avatar :size="32" :src="userAvatar">
              {{ userInitial }}
            </el-avatar>
            <span class="username">{{ userNickname }}</span>
            <el-icon><ArrowDown /></el-icon>
          </div>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="profile">个人中心</el-dropdown-item>
              <el-dropdown-item command="settings">设置</el-dropdown-item>
              <el-dropdown-item divided command="logout"
                >退出登录</el-dropdown-item
              >
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </header>

    <!-- 主内容区域 -->
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "@/stores/auth";
import { ElMessageBox } from "element-plus";
import { ArrowDown } from "@element-plus/icons-vue";

const router = useRouter();
const authStore = useAuthStore();

// 计算属性
const userNickname = computed(() => authStore.userNickname);
const userAvatar = computed(() => authStore.userAvatar);
const userInitial = computed(() => {
  return userNickname.value.charAt(0).toUpperCase();
});

// 处理用户下拉菜单命令
const handleUserCommand = async (command: string) => {
  switch (command) {
    case "profile":
      router.push("/profile");
      break;
    case "settings":
      router.push("/settings");
      break;
    case "logout":
      try {
        await ElMessageBox.confirm("确定要退出登录吗？", "提示", {
          confirmButtonText: "确定",
          cancelButtonText: "取消",
          type: "warning",
        });

        await authStore.logout();
        router.push("/login");
      } catch {
        // 用户取消操作
      }
      break;
  }
};
</script>

<style lang="scss" scoped>
.main-layout {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: var(--el-bg-color-page);
}

.main-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 64px;
  padding: 0 24px;
  background: white;
  border-bottom: 1px solid var(--el-border-color-light);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);

  .header-left {
    .logo h1 {
      margin: 0;
      font-size: 24px;
      font-weight: 700;
      color: var(--el-color-primary);
    }
  }

  .header-right {
    .user-info {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 8px 12px;
      border-radius: 6px;
      cursor: pointer;
      transition: background-color 0.3s;

      &:hover {
        background-color: var(--el-fill-color-light);
      }

      .username {
        font-size: 14px;
        color: var(--el-text -color-primary);
      }

      .el-icon {
        font-size: 12px;
        color: var(--el-text-color-secondary);
        transition: transform 0.3s;
      }

      &:hover .el-icon {
        transform: rotate(180deg);
      }
    }
  }
}

.main-content {
  flex: 1;
  overflow: auto;
  background-color: var(--el-bg-color-page);
}

// 响应式设计
@media (max-width: 768px) {
  .main-header {
    padding: 0 16px;

    .logo h1 {
      font-size: 20px;
    }

    .user-info .username {
      display: none;
    }
  }
}
</style>
