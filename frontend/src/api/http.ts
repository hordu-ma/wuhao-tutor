/**
 * HTTP客户端配置
 * 基于Axios封装，提供统一的请求和响应处理
 */

import axios, {
  AxiosInstance,
  AxiosRequestConfig,
  AxiosResponse,
  AxiosError,
  InternalAxiosRequestConfig
} from 'axios'
import { ElMessage, ElMessageBox, ElLoading } from 'element-plus'
import type { ApiResponse } from '@/types'

// 请求配置接口
interface RequestConfig extends AxiosRequestConfig {
  skipAuth?: boolean
  skipErrorHandler?: boolean
  showLoading?: boolean
  loadingText?: string
}

// 响应拦截器配置
interface ResponseConfig {
  showSuccessMessage?: boolean
  successMessage?: string
  skipGlobalErrorHandler?: boolean
}

class HttpClient {
  private instance: AxiosInstance
  private loading: any = null
  private loadingCount = 0

  constructor(baseURL?: string) {
    // 创建axios实例
    this.instance = axios.create({
      baseURL: baseURL || import.meta.env.VITE_API_BASE_URL || '/api/v1',
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    // 设置请求拦截器
    this.setupRequestInterceptors()
    // 设置响应拦截器
    this.setupResponseInterceptors()
  }

  /**
   * 设置请求拦截器
   */
  private setupRequestInterceptors(): void {
    this.instance.interceptors.request.use(
      (config: InternalAxiosRequestConfig & RequestConfig) => {
        // 添加认证token
        if (!config.skipAuth) {
          const token = this.getAuthToken()
          if (token) {
            config.headers.Authorization = `Bearer ${token}`
          }
        }

        // 显示loading
        if (config.showLoading) {
          this.showLoading(config.loadingText)
        }

        // 请求日志
        if (import.meta.env.DEV) {
          console.log(
            `🚀 [${config.method?.toUpperCase()}] ${config.url}`,
            config.data || config.params
          )
        }

        return config
      },
      (error: AxiosError) => {
        this.hideLoading()
        return Promise.reject(error)
      }
    )
  }

  /**
   * 设置响应拦截器
   */
  private setupResponseInterceptors(): void {
    this.instance.interceptors.response.use(
      (response: AxiosResponse<ApiResponse> & ResponseConfig) => {
        this.hideLoading()

        // 响应日志
        if (import.meta.env.DEV) {
          console.log(
            `✅ [${response.config.method?.toUpperCase()}] ${response.config.url}`,
            response.data
          )
        }

        // 显示成功消息
        if (response.showSuccessMessage && response.successMessage) {
          ElMessage.success(response.successMessage)
        }

        // 统一响应格式处理
        const { data } = response
        if (data && typeof data === 'object' && 'success' in data) {
          if (!data.success) {
            // API返回业务错误
            const errorMessage = data.message || '请求失败'
            if (!response.skipGlobalErrorHandler) {
              ElMessage.error(errorMessage)
            }
            return Promise.reject(new Error(errorMessage))
          }
          return data.data || data
        }

        return data
      },
      (error: AxiosError<ApiResponse>) => {
        this.hideLoading()
        return this.handleError(error)
      }
    )
  }

  /**
   * 错误处理
   */
  private handleError(error: AxiosError<ApiResponse>): Promise<never> {
    let message = '请求失败，请稍后重试'

    if (error.response) {
      const { status, data } = error.response

      // 根据HTTP状态码处理
      switch (status) {
        case 400:
          message = data?.message || '请求参数错误'
          break
        case 401:
          message = '登录已过期，请重新登录'
          this.handleUnauthorized()
          break
        case 403:
          message = '没有权限访问该资源'
          break
        case 404:
          message = '请求的资源不存在'
          break
        case 422:
          message = data?.message || '数据验证失败'
          break
        case 429:
          message = '请求过于频繁，请稍后再试'
          break
        case 500:
          message = '服务器内部错误'
          break
        case 502:
          message = '网关错误'
          break
        case 503:
          message = '服务暂时不可用'
          break
        case 504:
          message = '网关超时'
          break
        default:
          message = `请求失败 (${status})`
      }
    } else if (error.request) {
      // 网络错误
      if (error.code === 'ECONNABORTED') {
        message = '请求超时，请检查网络连接'
      } else {
        message = '网络连接失败，请检查网络设置'
      }
    } else {
      message = error.message || '未知错误'
    }

    // 错误日志
    if (import.meta.env.DEV) {
      console.error('❌ HTTP Error:', {
        url: error.config?.url,
        method: error.config?.method,
        status: error.response?.status,
        message,
        error,
      })
    }

    // 显示错误消息
    if (!(error.config as RequestConfig)?.skipErrorHandler) {
      ElMessage.error(message)
    }

    return Promise.reject(error)
  }

  /**
   * 处理未授权
   */
  private handleUnauthorized(): void {
    // 清除本地存储的认证信息
    this.clearAuthToken()

    // 重定向到登录页
    ElMessageBox.confirm(
      '登录状态已过期，您可以继续留在该页面，或者重新登录',
      '系统提示',
      {
        confirmButtonText: '重新登录',
        cancelButtonText: '取消',
        type: 'warning',
      }
    ).then(() => {
      // 跳转到登录页
      window.location.href = '/login'
    })
  }

  /**
   * 显示loading
   */
  private showLoading(text?: string): void {
    if (this.loadingCount === 0) {
      this.loading = ElLoading.service({
        text: text || '加载中...',
        background: 'rgba(0, 0, 0, 0.7)',
      })
    }
    this.loadingCount++
  }

  /**
   * 隐藏loading
   */
  private hideLoading(): void {
    this.loadingCount--
    if (this.loadingCount <= 0) {
      this.loadingCount = 0
      if (this.loading) {
        this.loading.close()
        this.loading = null
      }
    }
  }

  /**
   * 获取认证token
   */
  private getAuthToken(): string | null {
    return localStorage.getItem('access_token') || sessionStorage.getItem('access_token')
  }

  /**
   * 清除认证token
   */
  private clearAuthToken(): void {
    localStorage.removeItem('access_token')
    sessionStorage.removeItem('access_token')
    localStorage.removeItem('user_info')
    sessionStorage.removeItem('user_info')
  }

  /**
   * GET请求
   */
  get<T = any>(
    url: string,
    config?: RequestConfig & ResponseConfig
  ): Promise<T> {
    return this.instance.get(url, config)
  }

  /**
   * POST请求
   */
  post<T = any>(
    url: string,
    data?: any,
    config?: RequestConfig & ResponseConfig
  ): Promise<T> {
    return this.instance.post(url, data, config)
  }

  /**
   * PUT请求
   */
  put<T = any>(
    url: string,
    data?: any,
    config?: RequestConfig & ResponseConfig
  ): Promise<T> {
    return this.instance.put(url, data, config)
  }

  /**
   * DELETE请求
   */
  delete<T = any>(
    url: string,
    config?: RequestConfig & ResponseConfig
  ): Promise<T> {
    return this.instance.delete(url, config)
  }

  /**
   * PATCH请求
   */
  patch<T = any>(
    url: string,
    data?: any,
    config?: RequestConfig & ResponseConfig
  ): Promise<T> {
    return this.instance.patch(url, data, config)
  }

  /**
   * 上传文件
   */
  upload<T = any>(
    url: string,
    formData: FormData,
    config?: RequestConfig & ResponseConfig & {
      onUploadProgress?: (progressEvent: any) => void
    }
  ): Promise<T> {
    return this.instance.post(url, formData, {
      ...config,
      headers: {
        'Content-Type': 'multipart/form-data',
        ...config?.headers,
      },
    })
  }

  /**
   * 下载文件
   */
  download(
    url: string,
    filename?: string,
    config?: RequestConfig
  ): Promise<void> {
    return this.instance.get(url, {
      ...config,
      responseType: 'blob',
    }).then((response) => {
      const blob = new Blob([response.data])
      const downloadUrl = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = downloadUrl
      link.download = filename || 'download'
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(downloadUrl)
    })
  }

  /**
   * 取消请求
   */
  cancelRequest(source: any): void {
    if (source && source.cancel) {
      source.cancel('Request canceled by user')
    }
  }

  /**
   * 创建取消token
   */
  createCancelToken(): any {
    return axios.CancelToken.source()
  }
}

// 创建默认实例
const http = new HttpClient()

export default http
export { HttpClient }
export type { RequestConfig, ResponseConfig }
