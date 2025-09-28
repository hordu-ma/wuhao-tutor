/**
 * 性能优化工具类
 * 提供懒加载、预加载、缓存等性能优化功能
 */

// 图片懒加载配置
export interface LazyImageOptions {
  root?: Element | null
  rootMargin?: string
  threshold?: number
  placeholder?: string
  errorImage?: string
  fadeIn?: boolean
  delay?: number
}

// 组件懒加载配置
export interface LazyComponentOptions {
  threshold?: number
  rootMargin?: string
  delay?: number
  skeleton?: boolean
}

/**
 * 图片懒加载类
 */
export class LazyImageLoader {
  private observer: IntersectionObserver | null = null
  private images: Map<Element, LazyImageOptions> = new Map()
  private defaultOptions: Required<LazyImageOptions> = {
    root: null,
    rootMargin: '50px',
    threshold: 0.1,
    placeholder: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMzAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMzAwIiBoZWlnaHQ9IjIwMCIgZmlsbD0iI2YzZjRmNiIvPjx0ZXh0IHg9IjUwJSIgeT0iNTAlIiBmb250LWZhbWlseT0iQXJpYWwiIGZvbnQtc2l6ZT0iMTQiIGZpbGw9IiM5Y2EzYWYiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGR5PSIuM2VtIj5sb2FkaW5nLi4uPC90ZXh0Pjwvc3ZnPg==',
    errorImage: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMzAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMzAwIiBoZWlnaHQ9IjIwMCIgZmlsbD0iI2ZlZjJmMiIvPjx0ZXh0IHg9IjUwJSIgeT0iNTAlIiBmb250LWZhbWlseT0iQXJpYWwiIGZvbnQtc2l6ZT0iMTQiIGZpbGw9IiNlZjQ0NDQiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGR5PSIuM2VtIj5sb2FkIGZhaWxlZDwvdGV4dD48L3N2Zz4=',
    fadeIn: true,
    delay: 0
  }

  constructor(options?: Partial<LazyImageOptions>) {
    this.defaultOptions = { ...this.defaultOptions, ...options }
    this.init()
  }

  private init() {
    if (!('IntersectionObserver' in window)) {
      console.warn('IntersectionObserver not supported, images will load immediately')
      return
    }

    this.observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            this.loadImage(entry.target as HTMLImageElement)
          }
        })
      },
      {
        root: this.defaultOptions.root,
        rootMargin: this.defaultOptions.rootMargin,
        threshold: this.defaultOptions.threshold
      }
    )
  }

  private async loadImage(img: HTMLImageElement) {
    const options = this.images.get(img) || this.defaultOptions

    if (!img.dataset.src) return

    // 添加加载延迟
    if (options.delay && options.delay > 0) {
      await new Promise(resolve => setTimeout(resolve, options.delay))
    }

    const originalSrc = img.dataset.src
    const tempImage = new Image()

    // 添加加载状态
    img.classList.add('lazy-loading')

    tempImage.onload = () => {
      img.src = originalSrc
      img.classList.remove('lazy-loading')
      img.classList.add('lazy-loaded')

      // 淡入动画
      if (options.fadeIn) {
        img.style.opacity = '0'
        img.style.transition = 'opacity 0.3s ease-in-out'
        requestAnimationFrame(() => {
          img.style.opacity = '1'
        })
      }

      this.observer?.unobserve(img)
      this.images.delete(img)
    }

    tempImage.onerror = () => {
      img.src = options.errorImage || ''
      img.classList.remove('lazy-loading')
      img.classList.add('lazy-error')
      this.observer?.unobserve(img)
      this.images.delete(img)
    }

    tempImage.src = originalSrc
  }

  /**
   * 添加图片到懒加载队列
   */
  observe(img: HTMLImageElement, options?: Partial<LazyImageOptions>) {
    if (!this.observer) {
      // 降级处理：直接加载图片
      if (img.dataset.src) {
        img.src = img.dataset.src
      }
      return
    }

    const finalOptions = { ...this.defaultOptions, ...options }
    this.images.set(img, finalOptions)

    // 设置占位符
    if (!img.src && finalOptions.placeholder) {
      img.src = finalOptions.placeholder
    }

    this.observer.observe(img)
  }

  /**
   * 停止观察指定图片
   */
  unobserve(img: HTMLImageElement) {
    if (this.observer) {
      this.observer.unobserve(img)
    }
    this.images.delete(img)
  }

  /**
   * 销毁懒加载器
   */
  destroy() {
    if (this.observer) {
      this.observer.disconnect()
      this.observer = null
    }
    this.images.clear()
  }
}

/**
 * 创建全局图片懒加载实例
 */
let globalLazyLoader: LazyImageLoader | null = null

export const getLazyImageLoader = (options?: Partial<LazyImageOptions>) => {
  if (!globalLazyLoader) {
    globalLazyLoader = new LazyImageLoader(options)
  }
  return globalLazyLoader
}

/**
 * 资源预加载器
 */
export class ResourcePreloader {
  private loadedResources: Set<string> = new Set()
  private loadingPromises: Map<string, Promise<any>> = new Map()

  /**
   * 预加载图片
   */
  preloadImage(src: string): Promise<HTMLImageElement> {
    if (this.loadedResources.has(src)) {
      return Promise.resolve(new Image())
    }

    if (this.loadingPromises.has(src)) {
      return this.loadingPromises.get(src)!
    }

    const promise = new Promise<HTMLImageElement>((resolve, reject) => {
      const img = new Image()
      img.onload = () => {
        this.loadedResources.add(src)
        this.loadingPromises.delete(src)
        resolve(img)
      }
      img.onerror = () => {
        this.loadingPromises.delete(src)
        reject(new Error(`Failed to load image: ${src}`))
      }
      img.src = src
    })

    this.loadingPromises.set(src, promise)
    return promise
  }

  /**
   * 预加载多张图片
   */
  preloadImages(srcs: string[]): Promise<HTMLImageElement[]> {
    return Promise.all(srcs.map(src => this.preloadImage(src)))
  }

  /**
   * 预加载CSS文件
   */
  preloadCSS(href: string): Promise<void> {
    if (this.loadedResources.has(href)) {
      return Promise.resolve()
    }

    if (this.loadingPromises.has(href)) {
      return this.loadingPromises.get(href)!
    }

    const promise = new Promise<void>((resolve, reject) => {
      const link = document.createElement('link')
      link.rel = 'stylesheet'
      link.href = href
      link.onload = () => {
        this.loadedResources.add(href)
        this.loadingPromises.delete(href)
        resolve()
      }
      link.onerror = () => {
        this.loadingPromises.delete(href)
        reject(new Error(`Failed to load CSS: ${href}`))
      }
      document.head.appendChild(link)
    })

    this.loadingPromises.set(href, promise)
    return promise
  }

  /**
   * 预加载JavaScript文件
   */
  preloadJS(src: string): Promise<void> {
    if (this.loadedResources.has(src)) {
      return Promise.resolve()
    }

    if (this.loadingPromises.has(src)) {
      return this.loadingPromises.get(src)!
    }

    const promise = new Promise<void>((resolve, reject) => {
      const script = document.createElement('script')
      script.src = src
      script.async = true
      script.onload = () => {
        this.loadedResources.add(src)
        this.loadingPromises.delete(src)
        resolve()
      }
      script.onerror = () => {
        this.loadingPromises.delete(src)
        reject(new Error(`Failed to load script: ${src}`))
      }
      document.head.appendChild(script)
    })

    this.loadingPromises.set(src, promise)
    return promise
  }

  /**
   * 预加载字体
   */
  preloadFont(fontFamily: string, src: string, options?: FontFaceDescriptors): Promise<void> {
    if (this.loadedResources.has(src)) {
      return Promise.resolve()
    }

    if (this.loadingPromises.has(src)) {
      return this.loadingPromises.get(src)!
    }

    const promise = new Promise<void>((resolve, reject) => {
      if (!('FontFace' in window)) {
        resolve() // 降级处理
        return
      }

      const font = new FontFace(fontFamily, `url(${src})`, options)

      font.load().then(() => {
        document.fonts.add(font)
        this.loadedResources.add(src)
        this.loadingPromises.delete(src)
        resolve()
      }).catch(() => {
        this.loadingPromises.delete(src)
        reject(new Error(`Failed to load font: ${src}`))
      })
    })

    this.loadingPromises.set(src, promise)
    return promise
  }

  /**
   * 检查资源是否已加载
   */
  isLoaded(src: string): boolean {
    return this.loadedResources.has(src)
  }

  /**
   * 清除缓存
   */
  clearCache() {
    this.loadedResources.clear()
    this.loadingPromises.clear()
  }
}

/**
 * 全局资源预加载器实例
 */
export const resourcePreloader = new ResourcePreloader()

/**
 * 内存缓存管理器
 */
export class MemoryCache<T = any> {
  private cache: Map<string, { data: T; timestamp: number; ttl: number }> = new Map()
  private maxSize: number
  private defaultTTL: number

  constructor(maxSize: number = 100, defaultTTL: number = 5 * 60 * 1000) {
    this.maxSize = maxSize
    this.defaultTTL = defaultTTL
  }

  /**
   * 设置缓存
   */
  set(key: string, data: T, ttl?: number): void {
    const finalTTL = ttl || this.defaultTTL
    const timestamp = Date.now()

    // 如果缓存已满，删除最旧的条目
    if (this.cache.size >= this.maxSize && !this.cache.has(key)) {
      const oldestKey = this.cache.keys().next().value as string
      this.cache.delete(oldestKey)
    }

    this.cache.set(key, { data, timestamp, ttl: finalTTL })
  }

  /**
   * 获取缓存
   */
  get(key: string): T | null {
    const item = this.cache.get(key)
    if (!item) return null

    const now = Date.now()
    if (now - item.timestamp > item.ttl) {
      this.cache.delete(key)
      return null
    }

    return item.data
  }

  /**
   * 删除缓存
   */
  delete(key: string): boolean {
    return this.cache.delete(key)
  }

  /**
   * 清空缓存
   */
  clear(): void {
    this.cache.clear()
  }

  /**
   * 获取缓存大小
   */
  size(): number {
    return this.cache.size
  }

  /**
   * 清理过期缓存
   */
  cleanup(): void {
    const now = Date.now()
    for (const [key, item] of this.cache.entries()) {
      if (now - item.timestamp > item.ttl) {
        this.cache.delete(key)
      }
    }
  }
}



/**
 * 请求空闲回调
 */
export function requestIdleCallback(
  callback: (deadline: { timeRemaining: () => number; didTimeout: boolean }) => void,
  options?: { timeout?: number }
): number {
  if ('requestIdleCallback' in window) {
    return window.requestIdleCallback(callback, options)
  }

  // 降级处理
  const timeout = options?.timeout || 0
  const startTime = Date.now()

  return setTimeout(() => {
    callback({
      timeRemaining: () => Math.max(0, 50 - (Date.now() - startTime)),
      didTimeout: timeout > 0 && Date.now() - startTime > timeout
    })
  }, 1) as unknown as number
}

/**
 * 取消空闲回调
 */
export function cancelIdleCallback(id: number): void {
  if ('cancelIdleCallback' in window) {
    window.cancelIdleCallback(id)
  } else {
    clearTimeout(id)
  }
}

/**
 * 虚拟滚动配置
 */
export interface VirtualScrollOptions {
  itemHeight: number
  bufferSize?: number
  containerHeight: number
}

/**
 * 虚拟滚动计算器
 */
export class VirtualScrollCalculator {
  private itemHeight: number
  private bufferSize: number
  private containerHeight: number

  constructor(options: VirtualScrollOptions) {
    this.itemHeight = options.itemHeight
    this.bufferSize = options.bufferSize || 5
    this.containerHeight = options.containerHeight
  }

  /**
   * 计算可见范围
   */
  calculateVisibleRange(scrollTop: number, totalItems: number) {
    const visibleItemCount = Math.ceil(this.containerHeight / this.itemHeight)
    const startIndex = Math.floor(scrollTop / this.itemHeight)

    const bufferedStart = Math.max(0, startIndex - this.bufferSize)
    const bufferedEnd = Math.min(totalItems - 1, startIndex + visibleItemCount + this.bufferSize)

    return {
      startIndex: bufferedStart,
      endIndex: bufferedEnd,
      visibleCount: bufferedEnd - bufferedStart + 1,
      offsetY: bufferedStart * this.itemHeight,
      totalHeight: totalItems * this.itemHeight
    }
  }

  /**
   * 更新配置
   */
  updateOptions(options: Partial<VirtualScrollOptions>) {
    if (options.itemHeight !== undefined) this.itemHeight = options.itemHeight
    if (options.bufferSize !== undefined) this.bufferSize = options.bufferSize
    if (options.containerHeight !== undefined) this.containerHeight = options.containerHeight
  }
}

/**
 * 性能监控器
 */
export class PerformanceMonitor {
  private metrics: Map<string, number[]> = new Map()
  private observers: PerformanceObserver[] = []

  constructor() {
    this.initObservers()
  }

  private initObservers() {
    // 监控导航性能
    if ('PerformanceObserver' in window) {
      try {
        const navigationObserver = new PerformanceObserver((list) => {
          const entries = list.getEntries()
          entries.forEach((entry) => {
            this.recordMetric('navigation', entry.duration)
          })
        })
        navigationObserver.observe({ entryTypes: ['navigation'] })
        this.observers.push(navigationObserver)
      } catch (e) {
        console.warn('Navigation performance observer not supported')
      }
    }
  }

  /**
   * 记录指标
   */
  recordMetric(name: string, value: number) {
    if (!this.metrics.has(name)) {
      this.metrics.set(name, [])
    }

    const values = this.metrics.get(name)!
    values.push(value)

    // 保持最近100条记录
    if (values.length > 100) {
      values.shift()
    }
  }

  /**
   * 获取指标统计
   */
  getMetricStats(name: string) {
    const values = this.metrics.get(name) || []
    if (values.length === 0) return null

    const sorted = [...values].sort((a, b) => a - b)
    const sum = values.reduce((acc, val) => acc + val, 0)

    return {
      count: values.length,
      min: sorted[0],
      max: sorted[sorted.length - 1],
      avg: sum / values.length,
      median: sorted[Math.floor(sorted.length / 2)],
      p95: sorted[Math.floor(sorted.length * 0.95)],
      p99: sorted[Math.floor(sorted.length * 0.99)]
    }
  }

  /**
   * 测量函数执行时间
   */
  measureFunction<T>(name: string, fn: () => T): T {
    const start = performance.now()
    const result = fn()
    const duration = performance.now() - start
    this.recordMetric(name, duration)
    return result
  }

  /**
   * 测量异步函数执行时间
   */
  async measureAsyncFunction<T>(name: string, fn: () => Promise<T>): Promise<T> {
    const start = performance.now()
    const result = await fn()
    const duration = performance.now() - start
    this.recordMetric(name, duration)
    return result
  }

  /**
   * 清除指标
   */
  clearMetrics() {
    this.metrics.clear()
  }

  /**
   * 销毁监控器
   */
  destroy() {
    this.observers.forEach(observer => observer.disconnect())
    this.observers = []
    this.metrics.clear()
  }
}

/**
 * 全局性能监控器实例
 */
export const performanceMonitor = new PerformanceMonitor()

/**
 * Web Workers 工具
 */
export class WebWorkerManager {
  private workers: Map<string, Worker> = new Map()

  /**
   * 创建或获取 Worker
   */
  getWorker(name: string, scriptPath: string): Worker {
    if (this.workers.has(name)) {
      return this.workers.get(name)!
    }

    const worker = new Worker(scriptPath)
    this.workers.set(name, worker)
    return worker
  }

  /**
   * 执行 Worker 任务
   */
  executeTask<T = any>(
    workerName: string,
    scriptPath: string,
    data: any,
    timeout?: number
  ): Promise<T> {
    const worker = this.getWorker(workerName, scriptPath)

    return new Promise((resolve, reject) => {
      let timeoutId: NodeJS.Timeout | null = null

      const handleMessage = (event: MessageEvent) => {
        if (timeoutId) clearTimeout(timeoutId)
        worker.removeEventListener('message', handleMessage)
        worker.removeEventListener('error', handleError)
        resolve(event.data)
      }

      const handleError = (error: ErrorEvent) => {
        if (timeoutId) clearTimeout(timeoutId)
        worker.removeEventListener('message', handleMessage)
        worker.removeEventListener('error', handleError)
        reject(error)
      }

      worker.addEventListener('message', handleMessage)
      worker.addEventListener('error', handleError)

      if (timeout) {
        timeoutId = setTimeout(() => {
          worker.removeEventListener('message', handleMessage)
          worker.removeEventListener('error', handleError)
          reject(new Error('Worker task timeout'))
        }, timeout)
      }

      worker.postMessage(data)
    })
  }

  /**
   * 终止指定 Worker
   */
  terminateWorker(name: string) {
    const worker = this.workers.get(name)
    if (worker) {
      worker.terminate()
      this.workers.delete(name)
    }
  }

  /**
   * 终止所有 Worker
   */
  terminateAll() {
    this.workers.forEach(worker => worker.terminate())
    this.workers.clear()
  }
}

/**
 * 全局 WebWorker 管理器实例
 */
export const webWorkerManager = new WebWorkerManager()
