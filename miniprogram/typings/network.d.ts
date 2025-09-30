/**
 * 网络层 TypeScript 类型定义
 * 五好伴学微信小程序 - 网络层架构
 */

// ==================== 基础类型 ====================

/**
 * 网络环境类型
 */
export type NetworkType = 'wifi' | '2g' | '3g' | '4g' | '5g' | 'unknown' | 'none';

/**
 * HTTP方法类型
 */
export type HttpMethod = 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH' | 'HEAD' | 'OPTIONS';

/**
 * 请求数据类型
 */
export type RequestDataType = 'json' | 'formData' | 'arrayBuffer';

/**
 * 响应数据类型
 */
export type ResponseDataType = 'json' | 'text' | 'arrayBuffer';

// ==================== 请求相关类型 ====================

/**
 * 基础请求配置接口
 */
export interface BaseRequestConfig {
  /** 请求URL */
  url: string;
  /** HTTP方法 */
  method?: HttpMethod;
  /** 请求数据 */
  data?: any;
  /** 请求头 */
  header?: Record<string, string>;
  /** 请求超时时间(毫秒) */
  timeout?: number;
  /** 数据类型 */
  dataType?: RequestDataType;
  /** 响应类型 */
  responseType?: ResponseDataType;
  /** 是否跳过认证 */
  skipAuth?: boolean;
  /** 是否启用缓存 */
  enableCache?: boolean;
  /** 缓存时间(毫秒) */
  cacheTime?: number;
  /** 是否重试 */
  enableRetry?: boolean;
  /** 重试次数 */
  retryCount?: number;
  /** 重试延迟(毫秒) */
  retryDelay?: number;
  /** 请求优先级 */
  priority?: 'high' | 'normal' | 'low';
  /** 是否启用请求去重 */
  enableDeduplication?: boolean;
  /** 自定义元数据 */
  meta?: Record<string, any>;
}

/**
 * 扩展请求配置接口
 */
export interface RequestConfig extends BaseRequestConfig {
  /** 完整请求URL */
  fullUrl?: string;
  /** 请求开始时间戳 */
  startTime?: number;
  /** 请求ID */
  requestId?: string;
  /** 重试次数计数 */
  currentRetry?: number;
  /** 是否为重试请求 */
  isRetry?: boolean;
}

/**
 * 文件上传配置接口
 */
export interface UploadConfig extends Omit<BaseRequestConfig, 'data' | 'method'> {
  /** 文件路径 */
  filePath: string;
  /** 文件字段名 */
  name?: string;
  /** 表单数据 */
  formData?: Record<string, any>;
  /** 上传进度回调 */
  onProgress?: (progress: UploadProgress) => void;
}

/**
 * 文件下载配置接口
 */
export interface DownloadConfig extends Omit<BaseRequestConfig, 'data' | 'method'> {
  /** 下载文件保存路径 */
  filePath?: string;
  /** 下载进度回调 */
  onProgress?: (progress: DownloadProgress) => void;
}

// ==================== 响应相关类型 ====================

/**
 * 基础响应接口
 */
export interface BaseResponse<T = any> {
  /** 响应数据 */
  data: T;
  /** HTTP状态码 */
  statusCode: number;
  /** 响应头 */
  header: Record<string, string>;
  /** 请求配置 */
  config: RequestConfig;
  /** 响应时间戳 */
  timestamp?: number;
  /** 响应耗时(毫秒) */
  duration?: number;
}

/**
 * API响应接口
 */
export interface ApiResponse<T = any> {
  /** 是否成功 */
  success: boolean;
  /** 响应数据 */
  data?: T;
  /** 响应消息 */
  message?: string;
  /** 错误信息 */
  error?: ApiError;
  /** 响应时间戳 */
  timestamp?: number;
  /** 请求ID */
  requestId?: string;
}

/**
 * 分页响应接口
 */
export interface PaginatedResponse<T = any> {
  /** 数据列表 */
  items: T[];
  /** 当前页码 */
  page: number;
  /** 每页数量 */
  pageSize: number;
  /** 总记录数 */
  total: number;
  /** 总页数 */
  totalPages: number;
  /** 是否有下一页 */
  hasNext: boolean;
  /** 是否有上一页 */
  hasPrev: boolean;
}

/**
 * 上传进度接口
 */
export interface UploadProgress {
  /** 已上传大小(字节) */
  loaded: number;
  /** 总大小(字节) */
  total: number;
  /** 进度百分比(0-100) */
  progress: number;
  /** 上传速度(字节/秒) */
  speed?: number;
  /** 预计剩余时间(毫秒) */
  timeRemaining?: number;
}

/**
 * 下载进度接口
 */
export interface DownloadProgress {
  /** 已下载大小(字节) */
  loaded: number;
  /** 总大小(字节) */
  total: number;
  /** 进度百分比(0-100) */
  progress: number;
  /** 下载速度(字节/秒) */
  speed?: number;
  /** 预计剩余时间(毫秒) */
  timeRemaining?: number;
}

// ==================== 错误相关类型 ====================

/**
 * 错误类型枚举
 */
export enum ErrorType {
  /** 网络错误 */
  NETWORK_ERROR = 'NETWORK_ERROR',
  /** 请求超时 */
  TIMEOUT_ERROR = 'TIMEOUT_ERROR',
  /** 认证错误 */
  AUTH_ERROR = 'AUTH_ERROR',
  /** 权限错误 */
  PERMISSION_ERROR = 'PERMISSION_ERROR',
  /** 参数错误 */
  VALIDATION_ERROR = 'VALIDATION_ERROR',
  /** 业务错误 */
  BUSINESS_ERROR = 'BUSINESS_ERROR',
  /** 服务器错误 */
  SERVER_ERROR = 'SERVER_ERROR',
  /** 未知错误 */
  UNKNOWN_ERROR = 'UNKNOWN_ERROR'
}

/**
 * API错误接口
 */
export interface ApiError {
  /** 错误代码 */
  code: string;
  /** 错误消息 */
  message: string;
  /** 错误类型 */
  type: ErrorType;
  /** 错误详情 */
  details?: any;
  /** 错误堆栈 */
  stack?: string;
  /** 时间戳 */
  timestamp?: number;
  /** 请求ID */
  requestId?: string;
}

/**
 * 网络错误接口
 */
export interface NetworkError extends Error {
  /** 错误代码 */
  code?: string;
  /** HTTP状态码 */
  statusCode?: number;
  /** 响应数据 */
  data?: any;
  /** 请求配置 */
  config?: RequestConfig;
  /** 错误类型 */
  type: ErrorType;
  /** 是否可重试 */
  retryable?: boolean;
}

// ==================== 拦截器相关类型 ====================

/**
 * 请求拦截器函数类型
 */
export type RequestInterceptor = (config: RequestConfig) => RequestConfig | Promise<RequestConfig>;

/**
 * 请求错误拦截器函数类型
 */
export type RequestErrorInterceptor = (error: NetworkError) => NetworkError | Promise<NetworkError>;

/**
 * 响应拦截器函数类型
 */
export type ResponseInterceptor<T = any> = (response: BaseResponse<T>) => BaseResponse<T> | Promise<BaseResponse<T>>;

/**
 * 响应错误拦截器函数类型
 */
export type ResponseErrorInterceptor = (error: NetworkError) => NetworkError | Promise<NetworkError>;

/**
 * 拦截器配置接口
 */
export interface InterceptorConfig {
  /** 拦截器ID */
  id?: string;
  /** 拦截器优先级 */
  priority?: number;
  /** 是否启用 */
  enabled?: boolean;
}

/**
 * 拦截器接口
 */
export interface Interceptor {
  /** 请求成功拦截器 */
  fulfilled?: RequestInterceptor | ResponseInterceptor;
  /** 请求失败拦截器 */
  rejected?: RequestErrorInterceptor | ResponseErrorInterceptor;
  /** 拦截器配置 */
  config?: InterceptorConfig;
}

// ==================== 缓存相关类型 ====================

/**
 * 缓存策略枚举
 */
export enum CacheStrategy {
  /** 不缓存 */
  NO_CACHE = 'NO_CACHE',
  /** 内存缓存 */
  MEMORY_CACHE = 'MEMORY_CACHE',
  /** 存储缓存 */
  STORAGE_CACHE = 'STORAGE_CACHE',
  /** 网络优先 */
  NETWORK_FIRST = 'NETWORK_FIRST',
  /** 缓存优先 */
  CACHE_FIRST = 'CACHE_FIRST',
  /** 仅缓存 */
  CACHE_ONLY = 'CACHE_ONLY',
  /** 仅网络 */
  NETWORK_ONLY = 'NETWORK_ONLY'
}

/**
 * 缓存配置接口
 */
export interface CacheConfig {
  /** 缓存策略 */
  strategy: CacheStrategy;
  /** 缓存时间(毫秒) */
  ttl?: number;
  /** 缓存键 */
  key?: string;
  /** 缓存标签 */
  tags?: string[];
  /** 是否加密缓存 */
  encrypt?: boolean;
  /** 缓存大小限制(字节) */
  maxSize?: number;
}

/**
 * 缓存项接口
 */
export interface CacheItem<T = any> {
  /** 缓存键 */
  key: string;
  /** 缓存值 */
  value: T;
  /** 过期时间戳 */
  expireTime: number;
  /** 创建时间戳 */
  createTime: number;
  /** 访问次数 */
  accessCount: number;
  /** 最后访问时间戳 */
  lastAccessTime: number;
  /** 缓存标签 */
  tags?: string[];
  /** 数据大小(字节) */
  size?: number;
}

// ==================== 网络状态相关类型 ====================

/**
 * 网络状态接口
 */
export interface NetworkStatus {
  /** 是否连接到网络 */
  isConnected: boolean;
  /** 网络类型 */
  networkType: NetworkType;
  /** 信号强度(0-100) */
  signalStrength?: number;
  /** 网络延迟(毫秒) */
  latency?: number;
  /** 网络带宽(Mbps) */
  bandwidth?: number;
  /** 是否为计费网络 */
  isMetered?: boolean;
}

/**
 * 网络状态变化回调函数类型
 */
export type NetworkStatusChangeCallback = (status: NetworkStatus) => void;

// ==================== 性能监控相关类型 ====================

/**
 * 请求性能指标接口
 */
export interface RequestMetrics {
  /** 请求ID */
  requestId: string;
  /** 请求URL */
  url: string;
  /** HTTP方法 */
  method: HttpMethod;
  /** 请求开始时间 */
  startTime: number;
  /** 请求结束时间 */
  endTime: number;
  /** 请求耗时(毫秒) */
  duration: number;
  /** 请求大小(字节) */
  requestSize?: number;
  /** 响应大小(字节) */
  responseSize?: number;
  /** HTTP状态码 */
  statusCode?: number;
  /** 是否成功 */
  success: boolean;
  /** 错误类型 */
  errorType?: ErrorType;
  /** 重试次数 */
  retryCount?: number;
  /** 缓存命中 */
  cacheHit?: boolean;
  /** 网络类型 */
  networkType?: NetworkType;
}

/**
 * 性能监控配置接口
 */
export interface PerformanceConfig {
  /** 是否启用性能监控 */
  enabled: boolean;
  /** 采样率(0-1) */
  sampleRate: number;
  /** 上报阈值(毫秒) */
  reportThreshold: number;
  /** 最大缓存数量 */
  maxCacheSize: number;
  /** 上报间隔(毫秒) */
  reportInterval: number;
}

// ==================== 重试相关类型 ====================

/**
 * 重试策略枚举
 */
export enum RetryStrategy {
  /** 固定延迟 */
  FIXED_DELAY = 'FIXED_DELAY',
  /** 线性延迟 */
  LINEAR_DELAY = 'LINEAR_DELAY',
  /** 指数退避 */
  EXPONENTIAL_BACKOFF = 'EXPONENTIAL_BACKOFF',
  /** 随机延迟 */
  RANDOM_DELAY = 'RANDOM_DELAY'
}

/**
 * 重试配置接口
 */
export interface RetryConfig {
  /** 重试策略 */
  strategy: RetryStrategy;
  /** 最大重试次数 */
  maxRetries: number;
  /** 基础延迟时间(毫秒) */
  baseDelay: number;
  /** 最大延迟时间(毫秒) */
  maxDelay: number;
  /** 延迟倍数 */
  multiplier: number;
  /** 随机因子 */
  jitter: number;
  /** 重试条件判断函数 */
  shouldRetry?: (error: NetworkError) => boolean;
}

// ==================== 队列相关类型 ====================

/**
 * 请求优先级枚举
 */
export enum RequestPriority {
  HIGH = 3,
  NORMAL = 2,
  LOW = 1
}

/**
 * 队列项接口
 */
export interface QueueItem {
  /** 请求配置 */
  config: RequestConfig;
  /** 优先级 */
  priority: RequestPriority;
  /** 创建时间戳 */
  createTime: number;
  /** Promise resolve */
  resolve: (value: any) => void;
  /** Promise reject */
  reject: (reason: any) => void;
}

/**
 * 队列配置接口
 */
export interface QueueConfig {
  /** 最大并发数 */
  maxConcurrency: number;
  /** 队列最大长度 */
  maxQueueSize: number;
  /** 请求超时时间(毫秒) */
  timeout: number;
  /** 是否启用优先级队列 */
  enablePriority: boolean;
}

// ==================== API客户端相关类型 ====================

/**
 * API客户端配置接口
 */
export interface ApiClientConfig {
  /** 基础URL */
  baseURL: string;
  /** API版本 */
  version: string;
  /** 默认超时时间(毫秒) */
  timeout: number;
  /** 默认请求头 */
  headers: Record<string, string>;
  /** 重试配置 */
  retry: RetryConfig;
  /** 缓存配置 */
  cache: CacheConfig;
  /** 队列配置 */
  queue: QueueConfig;
  /** 性能监控配置 */
  performance: PerformanceConfig;
  /** 是否启用请求去重 */
  enableDeduplication: boolean;
  /** 是否启用网络状态监控 */
  enableNetworkMonitoring: boolean;
}

/**
 * API端点配置接口
 */
export interface ApiEndpointConfig {
  /** 端点路径 */
  path: string;
  /** HTTP方法 */
  method: HttpMethod;
  /** 缓存配置 */
  cache?: Partial<CacheConfig>;
  /** 重试配置 */
  retry?: Partial<RetryConfig>;
  /** 是否需要认证 */
  requireAuth?: boolean;
  /** 请求优先级 */
  priority?: RequestPriority;
  /** 超时时间(毫秒) */
  timeout?: number;
  /** 描述 */
  description?: string;
}

// ==================== 事件相关类型 ====================

/**
 * 网络事件类型枚举
 */
export enum NetworkEventType {
  REQUEST_START = 'REQUEST_START',
  REQUEST_SUCCESS = 'REQUEST_SUCCESS',
  REQUEST_ERROR = 'REQUEST_ERROR',
  REQUEST_RETRY = 'REQUEST_RETRY',
  CACHE_HIT = 'CACHE_HIT',
  CACHE_MISS = 'CACHE_MISS',
  NETWORK_STATUS_CHANGE = 'NETWORK_STATUS_CHANGE',
  AUTH_TOKEN_REFRESH = 'AUTH_TOKEN_REFRESH',
  AUTH_TOKEN_EXPIRED = 'AUTH_TOKEN_EXPIRED'
}

/**
 * 网络事件接口
 */
export interface NetworkEvent {
  /** 事件类型 */
  type: NetworkEventType;
  /** 事件数据 */
  data?: any;
  /** 时间戳 */
  timestamp: number;
  /** 请求ID */
  requestId?: string;
}

/**
 * 事件监听器函数类型
 */
export type NetworkEventListener = (event: NetworkEvent) => void;

// ==================== 导出所有类型 ====================

export {
  // 基础类型
  NetworkType,
  HttpMethod,
  RequestDataType,
  ResponseDataType,

  // 请求相关
  BaseRequestConfig,
  RequestConfig,
  UploadConfig,
  DownloadConfig,

  // 响应相关
  BaseResponse,
  ApiResponse,
  PaginatedResponse,
  UploadProgress,
  DownloadProgress,

  // 错误相关
  ErrorType,
  ApiError,
  NetworkError,

  // 拦截器相关
  RequestInterceptor,
  RequestErrorInterceptor,
  ResponseInterceptor,
  ResponseErrorInterceptor,
  InterceptorConfig,
  Interceptor,

  // 缓存相关
  CacheStrategy,
  CacheConfig,
  CacheItem,

  // 网络状态相关
  NetworkStatus,
  NetworkStatusChangeCallback,

  // 性能监控相关
  RequestMetrics,
  PerformanceConfig,

  // 重试相关
  RetryStrategy,
  RetryConfig,

  // 队列相关
  RequestPriority,
  QueueItem,
  QueueConfig,

  // API客户端相关
  ApiClientConfig,
  ApiEndpointConfig,

  // 事件相关
  NetworkEventType,
  NetworkEvent,
  NetworkEventListener
};
