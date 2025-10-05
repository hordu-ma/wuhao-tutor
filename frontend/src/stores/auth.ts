/**
 * 用户认证状态管理
 * 使用Pinia管理用户登录状态、用户信息等
 */

import { defineStore } from 'pinia'
import { ElMessage } from 'element-plus'
import AuthAPI from '@/api/auth'
import type { User, LoginRequest, RegisterRequest, LoginResponse } from '@/types'

interface AuthState {
  // 用户信息
  user: User | null
  // 访问令牌
  accessToken: string | null
  // 刷新令牌
  refreshToken: string | null
  // 是否已登录
  isAuthenticated: boolean
  // 是否记住我
  rememberMe: boolean
  // 登录加载状态
  loginLoading: boolean
  // 用户信息加载状态
  userLoading: boolean
  // 登录重试次数
  retryCount: number
  // 最大重试次数
  maxRetries: number
}

export const useAuthStore = defineStore('auth', {
  state: (): AuthState => ({
    user: null,
    accessToken: null,
    refreshToken: null,
    isAuthenticated: false,
    rememberMe: false,
    loginLoading: false,
    userLoading: false,
    retryCount: 0,
    maxRetries: 3,
  }),

  getters: {
    /**
     * 获取用户角色
     */
    userRole: (state): string => state.user?.role || 'guest',

    /**
     * 获取用户头像
     */
    userAvatar: (state): string => state.user?.avatar || '/default-avatar.png',

    /**
     * 获取用户昵称
     */
    userNickname: (state): string => state.user?.nickname || state.user?.name || '未知用户',

    /**
     * 检查是否有特定权限
     */
    hasRole:
      (state) =>
      (role: string): boolean => {
        if (!state.user) return false
        return state.user.role === role || state.user.role === 'admin'
      },

    /**
     * 检查是否为管理员
     */
    isAdmin: (state): boolean => state.user?.role === 'admin',

    /**
     * 检查是否为教师
     */
    isTeacher: (state): boolean => state.user?.role === 'teacher' || state.user?.role === 'admin',

    /**
     * 检查是否为学生
     */
    isStudent: (state): boolean => state.user?.role === 'student',
  },

  actions: {
    /**
     * 用户登录
     */
    async login(loginData: LoginRequest): Promise<boolean> {
      this.loginLoading = true
      try {
        const response: LoginResponse = await AuthAPI.login(loginData)

        // 保存认证信息
        this.setAuth(response, loginData.remember_me)

        // 获取用户详细信息
        await this.fetchUserInfo()

        ElMessage.success('登录成功！')
        return true
      } catch (error) {
        console.error('Login failed:', error)
        return false
      } finally {
        this.loginLoading = false
      }
    },

    /**
     * 用户注册
     */
    async register(registerData: RegisterRequest): Promise<boolean> {
      try {
        await AuthAPI.register(registerData)
        ElMessage.success('注册成功，请登录！')
        return true
      } catch (error) {
        console.error('Registration failed:', error)
        return false
      }
    },

    /**
     * 用户登出
     */
    async logout(): Promise<void> {
      try {
        // 调用后端登出接口
        await AuthAPI.logout()
      } catch (error) {
        console.error('Logout API failed:', error)
      } finally {
        // 无论API调用成功与否都清除本地状态
        this.clearAuth()
        ElMessage.success('已退出登录')
      }
    },

    /**
     * 设置认证信息
     */
    setAuth(response: LoginResponse, rememberMe: boolean = false): void {
      const { access_token, refresh_token, user, expires_in } = response

      // 更新状态
      this.accessToken = access_token
      this.refreshToken = refresh_token || null // 保存 refresh_token
      this.user = user
      this.isAuthenticated = true
      this.rememberMe = rememberMe

      // 选择存储方式
      const storage = rememberMe ? localStorage : sessionStorage

      // 保存到本地存储
      storage.setItem('access_token', access_token)

      // 保存 refresh_token
      if (refresh_token) {
        storage.setItem('refresh_token', refresh_token)
      }

      storage.setItem('user_info', JSON.stringify(user))
      storage.setItem('remember_me', rememberMe.toString())

      // 保存过期时间
      if (expires_in) {
        const expiryTime = Date.now() + expires_in * 1000
        storage.setItem('token_expiry', expiryTime.toString())
      }
    },

    /**
     * 清除认证信息
     */
    clearAuth(): void {
      // 清除状态
      this.accessToken = null
      this.refreshToken = null
      this.user = null
      this.isAuthenticated = false
      this.rememberMe = false
      this.retryCount = 0

      // 清除本地存储
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('user_info')
      localStorage.removeItem('remember_me')
      localStorage.removeItem('token_expiry')

      sessionStorage.removeItem('access_token')
      sessionStorage.removeItem('refresh_token')
      sessionStorage.removeItem('user_info')
      sessionStorage.removeItem('remember_me')
      sessionStorage.removeItem('token_expiry')
    },

    /**
     * 从本地存储恢复认证状态
     */
    restoreAuth(): boolean {
      try {
        // 优先从localStorage读取
        let token = localStorage.getItem('access_token')
        let refreshToken = localStorage.getItem('refresh_token')
        let userInfo = localStorage.getItem('user_info')
        let rememberMe = localStorage.getItem('remember_me') === 'true'

        // 如果localStorage没有，从sessionStorage读取
        if (!token) {
          token = sessionStorage.getItem('access_token')
          refreshToken = sessionStorage.getItem('refresh_token')
          userInfo = sessionStorage.getItem('user_info')
          rememberMe = sessionStorage.getItem('remember_me') === 'true'
        }

        if (token && userInfo) {
          // 检查token是否过期
          if (this.isTokenExpired(token)) {
            this.clearAuth()
            return false
          }

          // 恢复状态
          this.accessToken = token
          this.refreshToken = refreshToken || null
          this.user = JSON.parse(userInfo)
          this.isAuthenticated = true
          this.rememberMe = rememberMe

          return true
        }
      } catch (error) {
        console.error('Failed to restore auth state:', error)
        this.clearAuth()
      }

      return false
    },

    /**
     * 刷新token
     */
    async refreshAccessToken(): Promise<boolean> {
      try {
        if (this.retryCount >= this.maxRetries) {
          this.clearAuth()
          return false
        }

        this.retryCount++
        const response = await AuthAPI.refreshToken()

        // 更新token信息
        this.setAuth(response, this.rememberMe)
        this.retryCount = 0

        return true
      } catch (error) {
        console.error('Token refresh failed:', error)

        // 如果刷新失败且达到最大重试次数，清除认证状态
        if (this.retryCount >= this.maxRetries) {
          this.clearAuth()
          ElMessage.error('登录已过期，请重新登录')
        }

        return false
      }
    },

    /**
     * 获取用户信息
     */
    async fetchUserInfo(): Promise<void> {
      if (!this.isAuthenticated) return

      this.userLoading = true
      try {
        const user = await AuthAPI.getCurrentUser()
        this.user = user

        // 更新本地存储
        const storage = this.rememberMe ? localStorage : sessionStorage
        storage.setItem('user_info', JSON.stringify(user))
      } catch (error) {
        console.error('Failed to fetch user info:', error)

        // 如果获取用户信息失败，可能是token无效
        const tokenExpiry = this.getTokenExpiry()
        const isExpiringSoon = tokenExpiry ? Date.now() > tokenExpiry - 5 * 60 * 1000 : true

        if (isExpiringSoon) {
          await this.refreshAccessToken()
        }
      } finally {
        this.userLoading = false
      }
    },

    /**
     * 更新用户资料
     */
    async updateProfile(data: {
      nickname?: string
      email?: string
      avatar?: string
    }): Promise<boolean> {
      try {
        const updatedUser = await AuthAPI.updateProfile(data)
        this.user = updatedUser

        // 更新本地存储
        const storage = this.rememberMe ? localStorage : sessionStorage
        storage.setItem('user_info', JSON.stringify(updatedUser))

        return true
      } catch (error) {
        console.error('Failed to update profile:', error)
        return false
      }
    },

    /**
     * 修改密码
     */
    async changePassword(data: {
      old_password: string
      new_password: string
      confirm_password: string
    }): Promise<boolean> {
      try {
        await AuthAPI.changePassword(data)
        return true
      } catch (error) {
        console.error('Failed to change password:', error)
        return false
      }
    },

    /**
     * 检查token是否过期
     */
    isTokenExpired(token?: string): boolean {
      try {
        const actualToken = token || this.accessToken
        if (!actualToken) return true

        const payload = JSON.parse(atob(actualToken.split('.')[1]))
        const exp = payload.exp * 1000 // 转换为毫秒

        return Date.now() >= exp
      } catch {
        return true
      }
    },

    /**
     * 获取token过期时间
     */
    getTokenExpiry(): number | null {
      try {
        const token = localStorage.getItem('access_token') || sessionStorage.getItem('access_token')
        if (!token) return null

        const payload = JSON.parse(atob(token.split('.')[1]))
        return payload.exp * 1000 // 转换为毫秒
      } catch {
        return null
      }
    },

    /**
     * 自动刷新token（定时器）
     */
    startTokenRefreshTimer(): void {
      // 每5分钟检查一次token状态
      setInterval(
        () => {
          if (this.isAuthenticated) {
            const tokenExpiry = this.getTokenExpiry()
            const isExpiringSoon = tokenExpiry ? Date.now() > tokenExpiry - 5 * 60 * 1000 : true

            if (isExpiringSoon) {
              this.refreshAccessToken()
            }
          }
        },
        5 * 60 * 1000
      ) // 5分钟
    },

    /**
     * 检查权限
     */
    checkPermission(): boolean {
      if (!this.user) return false

      // 管理员拥有所有权限
      if (this.user.role === 'admin') return true

      // 这里可以根据实际需求扩展权限检查逻辑
      // 比如从后端获取用户的详细权限列表
      return true
    },

    /**
     * 验证当前登录状态
     */
    async validateAuth(): Promise<boolean> {
      if (!this.isAuthenticated || !this.accessToken) {
        return false
      }

      // 如果token过期，尝试刷新
      if (this.isTokenExpired()) {
        return await this.refreshAccessToken()
      }

      // 验证用户信息是否完整
      if (!this.user) {
        await this.fetchUserInfo()
      }

      return this.isAuthenticated
    },
  },
})

export default useAuthStore
