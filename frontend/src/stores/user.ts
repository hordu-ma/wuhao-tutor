/**
 * 用户管理 Pinia Store
 * 管理用户信息、认证状态、偏好设置等
 */

import { defineStore } from "pinia";
import { ref, computed, reactive } from "vue";
import { ElMessage } from "element-plus";

// 用户信息接口
export interface UserInfo {
  id: string;
  username: string;
  real_name?: string;
  email?: string;
  phone?: string;
  avatar_url?: string;
  gender?: "male" | "female" | "other";
  grade_level?: string;
  school?: string;
  bio?: string;
  created_at: string;
  last_login_at?: string;
}

// 用户偏好设置接口
export interface UserPreferences {
  primary_subjects: string[];
  difficulty_preference: "easy" | "medium" | "hard";
  daily_study_time: number;
  enable_daily_reminder: boolean;
  enable_homework_reminder: boolean;
  enable_achievement_notification: boolean;
  reminder_time: string;
  theme: "light" | "dark" | "auto";
  language: "zh" | "en";
}

// 隐私设置接口
export interface PrivacySettings {
  allow_data_analysis: boolean;
  allow_learning_analytics: boolean;
  allow_personalization: boolean;
  data_retention_period: "1year" | "2years" | "5years" | "permanent";
}

// 认证状态接口
export interface AuthState {
  isAuthenticated: boolean;
  token?: string;
  refreshToken?: string;
  expiresAt?: number;
}

export const useUserStore = defineStore("user", () => {
  // ========== 状态定义 ==========

  // 用户信息
  const userInfo = ref<UserInfo | null>(null);

  // 认证状态
  const authState = reactive<AuthState>({
    isAuthenticated: false,
    token: undefined,
    refreshToken: undefined,
    expiresAt: undefined,
  });

  // 用户偏好设置
  const preferences = reactive<UserPreferences>({
    primary_subjects: [],
    difficulty_preference: "medium",
    daily_study_time: 120,
    enable_daily_reminder: true,
    enable_homework_reminder: true,
    enable_achievement_notification: true,
    reminder_time: "19:00",
    theme: "auto",
    language: "zh",
  });

  // 隐私设置
  const privacySettings = reactive<PrivacySettings>({
    allow_data_analysis: true,
    allow_learning_analytics: true,
    allow_personalization: true,
    data_retention_period: "2years",
  });

  // 加载状态
  const isLoading = ref(false);
  const isUpdating = ref(false);

  // ========== 计算属性 ==========

  const isLoggedIn = computed(() => authState.isAuthenticated && !!userInfo.value);

  const userName = computed(() => {
    if (!userInfo.value) return "";
    return userInfo.value.real_name || userInfo.value.username || "用户";
  });

  const userAvatar = computed(() => {
    return userInfo.value?.avatar_url || "";
  });

  const isTokenExpired = computed(() => {
    if (!authState.expiresAt) return false;
    return Date.now() >= authState.expiresAt;
  });

  const gradeLevel = computed(() => {
    const gradeLevelMap: Record<string, string> = {
      primary: "小学",
      junior_1: "初一",
      junior_2: "初二",
      junior_3: "初三",
      senior_1: "高一",
      senior_2: "高二",
      senior_3: "高三",
    };
    return userInfo.value?.grade_level
      ? gradeLevelMap[userInfo.value.grade_level] || userInfo.value.grade_level
      : "";
  });

  // ========== Actions ==========

  /**
   * 初始化用户状态
   */
  function initAuth() {
    try {
      // 从localStorage恢复认证状态
      const savedAuth = localStorage.getItem("auth_state");
      const savedUser = localStorage.getItem("user_info");
      const savedPreferences = localStorage.getItem("user_preferences");

      if (savedAuth) {
        const auth = JSON.parse(savedAuth);
        Object.assign(authState, auth);
      }

      if (savedUser) {
        userInfo.value = JSON.parse(savedUser);
      }

      if (savedPreferences) {
        const prefs = JSON.parse(savedPreferences);
        Object.assign(preferences, prefs);
      }

      // 检查token是否过期
      if (isTokenExpired.value) {
        logout();
      }
    } catch (error) {
      console.error("初始化用户状态失败:", error);
      logout();
    }
  }

  /**
   * 登录
   */
  async function login(credentials: { username: string; password: string }) {
    try {
      isLoading.value = true;

      // 这里应该调用登录API
      // const response = await AuthAPI.login(credentials);

      // 模拟API响应
      const mockResponse = {
        token: "mock_token_" + Date.now(),
        refresh_token: "mock_refresh_token",
        expires_in: 3600, // 1小时
        user: {
          id: "user_123",
          username: credentials.username,
          real_name: "测试用户",
          email: "test@example.com",
          created_at: new Date().toISOString(),
        }
      };

      // 更新认证状态
      authState.isAuthenticated = true;
      authState.token = mockResponse.token;
      authState.refreshToken = mockResponse.refresh_token;
      authState.expiresAt = Date.now() + mockResponse.expires_in * 1000;

      // 更新用户信息
      userInfo.value = mockResponse.user;

      // 保存到localStorage
      saveAuthState();

      ElMessage.success("登录成功");
      return mockResponse;
    } catch (error) {
      console.error("登录失败:", error);
      ElMessage.error("登录失败，请检查用户名和密码");
      throw error;
    } finally {
      isLoading.value = false;
    }
  }

  /**
   * 登出
   */
  function logout() {
    try {
      // 清除状态
      authState.isAuthenticated = false;
      authState.token = undefined;
      authState.refreshToken = undefined;
      authState.expiresAt = undefined;
      userInfo.value = null;

      // 清除localStorage
      localStorage.removeItem("auth_state");
      localStorage.removeItem("user_info");

      ElMessage.success("已退出登录");
    } catch (error) {
      console.error("登出失败:", error);
    }
  }

  /**
   * 刷新token
   */
  async function refreshToken() {
    try {
      if (!authState.refreshToken) {
        throw new Error("没有refresh token");
      }

      // 这里应该调用刷新token的API
      // const response = await AuthAPI.refreshToken(authState.refreshToken);

      // 模拟API响应
      const mockResponse = {
        token: "new_mock_token_" + Date.now(),
        expires_in: 3600,
      };

      authState.token = mockResponse.token;
      authState.expiresAt = Date.now() + mockResponse.expires_in * 1000;

      saveAuthState();

      return mockResponse.token;
    } catch (error) {
      console.error("刷新token失败:", error);
      logout();
      throw error;
    }
  }

  /**
   * 更新用户信息
   */
  async function updateUserInfo(updates: Partial<UserInfo>) {
    try {
      isUpdating.value = true;

      // 这里应该调用更新用户信息的API
      // const response = await UserAPI.updateProfile(updates);

      // 模拟更新
      if (userInfo.value) {
        Object.assign(userInfo.value, updates);
        localStorage.setItem("user_info", JSON.stringify(userInfo.value));
      }

      ElMessage.success("个人信息更新成功");
    } catch (error) {
      console.error("更新用户信息失败:", error);
      ElMessage.error("更新失败，请重试");
      throw error;
    } finally {
      isUpdating.value = false;
    }
  }

  /**
   * 更新用户偏好设置
   */
  async function updatePreferences(updates: Partial<UserPreferences>) {
    try {
      isUpdating.value = true;

      // 这里应该调用更新偏好设置的API
      // await UserAPI.updatePreferences(updates);

      Object.assign(preferences, updates);
      localStorage.setItem("user_preferences", JSON.stringify(preferences));

      ElMessage.success("偏好设置更新成功");
    } catch (error) {
      console.error("更新偏好设置失败:", error);
      ElMessage.error("更新失败，请重试");
      throw error;
    } finally {
      isUpdating.value = false;
    }
  }

  /**
   * 更新隐私设置
   */
  async function updatePrivacySettings(updates: Partial<PrivacySettings>) {
    try {
      isUpdating.value = true;

      // 这里应该调用更新隐私设置的API
      // await UserAPI.updatePrivacySettings(updates);

      Object.assign(privacySettings, updates);
      localStorage.setItem("privacy_settings", JSON.stringify(privacySettings));

      ElMessage.success("隐私设置更新成功");
    } catch (error) {
      console.error("更新隐私设置失败:", error);
      ElMessage.error("更新失败，请重试");
      throw error;
    } finally {
      isUpdating.value = false;
    }
  }

  /**
   * 上传头像
   */
  async function uploadAvatar(file: File) {
    try {
      isUpdating.value = true;

      // 这里应该调用上传头像的API
      // const response = await UserAPI.uploadAvatar(file);

      // 模拟上传
      const mockAvatarUrl = URL.createObjectURL(file);

      if (userInfo.value) {
        userInfo.value.avatar_url = mockAvatarUrl;
        localStorage.setItem("user_info", JSON.stringify(userInfo.value));
      }

      ElMessage.success("头像上传成功");
      return mockAvatarUrl;
    } catch (error) {
      console.error("上传头像失败:", error);
      ElMessage.error("上传失败，请重试");
      throw error;
    } finally {
      isUpdating.value = false;
    }
  }

  /**
   * 导出用户数据
   */
  async function exportUserData(options: string[]) {
    try {
      // 这里应该调用导出数据的API
      // await UserAPI.exportData(options);
      console.log("导出选项:", options);

      ElMessage.success("数据导出请求已提交，请稍后查收邮件");
    } catch (error) {
      console.error("导出数据失败:", error);
      ElMessage.error("导出失败，请重试");
      throw error;
    }
  }

  /**
   * 删除用户账户
   */
  async function deleteAccount() {
    try {
      // 这里应该调用删除账户的API
      // await UserAPI.deleteAccount();

      logout();
      ElMessage.success("账户已删除");
    } catch (error) {
      console.error("删除账户失败:", error);
      ElMessage.error("删除失败，请重试");
      throw error;
    }
  }

  /**
   * 保存认证状态到localStorage
   */
  function saveAuthState() {
    try {
      localStorage.setItem("auth_state", JSON.stringify({
        isAuthenticated: authState.isAuthenticated,
        token: authState.token,
        refreshToken: authState.refreshToken,
        expiresAt: authState.expiresAt,
      }));

      if (userInfo.value) {
        localStorage.setItem("user_info", JSON.stringify(userInfo.value));
      }
    } catch (error) {
      console.error("保存认证状态失败:", error);
    }
  }

  /**
   * 获取授权头
   */
  function getAuthHeader() {
    return authState.token ? `Bearer ${authState.token}` : "";
  }

  /**
   * 检查权限
   */
  function hasPermission(permission: string): boolean {
    // 这里可以根据用户角色和权限进行判断
    console.log("检查权限:", permission);
    return true;
  }

  /**
   * 重置所有状态
   */
  function resetAll() {
    logout();
    Object.assign(preferences, {
      primary_subjects: [],
      difficulty_preference: "medium",
      daily_study_time: 120,
      enable_daily_reminder: true,
      enable_homework_reminder: true,
      enable_achievement_notification: true,
      reminder_time: "19:00",
      theme: "auto",
      language: "zh",
    });
    Object.assign(privacySettings, {
      allow_data_analysis: true,
      allow_learning_analytics: true,
      allow_personalization: true,
      data_retention_period: "2years",
    });
  }

  // ========== 返回 ==========
  return {
    // 状态
    userInfo,
    authState,
    preferences,
    privacySettings,
    isLoading,
    isUpdating,

    // 计算属性
    isLoggedIn,
    userName,
    userAvatar,
    isTokenExpired,
    gradeLevel,

    // 方法
    initAuth,
    login,
    logout,
    refreshToken,
    updateUserInfo,
    updatePreferences,
    updatePrivacySettings,
    uploadAvatar,
    exportUserData,
    deleteAccount,
    saveAuthState,
    getAuthHeader,
    hasPermission,
    resetAll,
  };
});
