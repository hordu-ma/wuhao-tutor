/**
 * 响应式工具类
 * 提供移动端检测、屏幕尺寸判断等工具函数
 */

// 响应式断点配置 (与 Tailwind CSS 保持一致)
export const BREAKPOINTS = {
  xs: 0,      // 0px+
  sm: 640,    // 640px+
  md: 768,    // 768px+
  lg: 1024,   // 1024px+
  xl: 1280,   // 1280px+
  '2xl': 1536 // 1536px+
} as const

export type BreakpointKey = keyof typeof BREAKPOINTS

// 设备类型枚举
export enum DeviceType {
  MOBILE = 'mobile',
  TABLET = 'tablet',
  DESKTOP = 'desktop'
}

// 屏幕方向
export enum Orientation {
  PORTRAIT = 'portrait',
  LANDSCAPE = 'landscape'
}

/**
 * 检测是否为移动设备
 */
export const isMobile = (): boolean => {
  if (typeof window === 'undefined') return false

  // 基于用户代理检测
  const userAgent = window.navigator.userAgent
  const mobileRegex = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i

  // 基于屏幕尺寸检测 (宽度小于768px)
  const isSmallScreen = window.innerWidth < BREAKPOINTS.md

  // 基于触摸能力检测
  const isTouchDevice = 'ontouchstart' in window || navigator.maxTouchPoints > 0

  return mobileRegex.test(userAgent) || (isSmallScreen && isTouchDevice)
}

/**
 * 检测是否为平板设备
 */
export const isTablet = (): boolean => {
  if (typeof window === 'undefined') return false

  const userAgent = window.navigator.userAgent
  const tabletRegex = /iPad|Android.*(?!.*Mobile)/i
  const screenWidth = window.innerWidth

  return tabletRegex.test(userAgent) || (screenWidth >= BREAKPOINTS.md && screenWidth < BREAKPOINTS.lg)
}

/**
 * 检测是否为桌面设备
 */
export const isDesktop = (): boolean => {
  if (typeof window === 'undefined') return true
  return !isMobile() && !isTablet()
}

/**
 * 获取设备类型
 */
export const getDeviceType = (): DeviceType => {
  if (isMobile()) return DeviceType.MOBILE
  if (isTablet()) return DeviceType.TABLET
  return DeviceType.DESKTOP
}

/**
 * 获取当前屏幕断点
 */
export const getCurrentBreakpoint = (): BreakpointKey => {
  if (typeof window === 'undefined') return 'lg'

  const width = window.innerWidth

  if (width >= BREAKPOINTS['2xl']) return '2xl'
  if (width >= BREAKPOINTS.xl) return 'xl'
  if (width >= BREAKPOINTS.lg) return 'lg'
  if (width >= BREAKPOINTS.md) return 'md'
  if (width >= BREAKPOINTS.sm) return 'sm'
  return 'xs'
}

/**
 * 检查是否匹配指定断点
 */
export const matchesBreakpoint = (breakpoint: BreakpointKey): boolean => {
  if (typeof window === 'undefined') return false
  return window.innerWidth >= BREAKPOINTS[breakpoint]
}

/**
 * 获取屏幕方向
 */
export const getOrientation = (): Orientation => {
  if (typeof window === 'undefined') return Orientation.LANDSCAPE

  // 优先使用 screen.orientation API
  if ('orientation' in screen && screen.orientation) {
    return screen.orientation.angle === 0 || screen.orientation.angle === 180
      ? Orientation.PORTRAIT
      : Orientation.LANDSCAPE
  }

  // 回退到窗口尺寸判断
  return window.innerHeight > window.innerWidth
    ? Orientation.PORTRAIT
    : Orientation.LANDSCAPE
}

/**
 * 检测是否为横屏模式
 */
export const isLandscape = (): boolean => {
  return getOrientation() === Orientation.LANDSCAPE
}

/**
 * 检测是否为竖屏模式
 */
export const isPortrait = (): boolean => {
  return getOrientation() === Orientation.PORTRAIT
}

/**
 * 获取安全区域内边距 (适配刘海屏)
 */
export const getSafeAreaInsets = () => {
  const root = document.documentElement
  const computedStyle = window.getComputedStyle(root)

  return {
    top: parseInt(computedStyle.getPropertyValue('--safe-area-inset-top') || '0', 10),
    right: parseInt(computedStyle.getPropertyValue('--safe-area-inset-right') || '0', 10),
    bottom: parseInt(computedStyle.getPropertyValue('--safe-area-inset-bottom') || '0', 10),
    left: parseInt(computedStyle.getPropertyValue('--safe-area-inset-left') || '0', 10)
  }
}

/**
 * 响应式监听器类
 */
export class ResponsiveObserver {
  private listeners: Array<(deviceType: DeviceType, breakpoint: BreakpointKey) => void> = []
  private resizeObserver: ResizeObserver | null = null
  private currentDeviceType: DeviceType
  private currentBreakpoint: BreakpointKey

  constructor() {
    this.currentDeviceType = getDeviceType()
    this.currentBreakpoint = getCurrentBreakpoint()
    this.init()
  }

  private init() {
    if (typeof window === 'undefined') return

    // 使用 ResizeObserver 监听窗口大小变化
    this.resizeObserver = new ResizeObserver(() => {
      this.checkChanges()
    })

    this.resizeObserver.observe(document.body)

    // 监听屏幕方向变化
    window.addEventListener('orientationchange', () => {
      setTimeout(() => this.checkChanges(), 100) // 延迟确保获取到正确的尺寸
    })
  }

  private checkChanges() {
    const newDeviceType = getDeviceType()
    const newBreakpoint = getCurrentBreakpoint()

    if (newDeviceType !== this.currentDeviceType || newBreakpoint !== this.currentBreakpoint) {
      this.currentDeviceType = newDeviceType
      this.currentBreakpoint = newBreakpoint
      this.notifyListeners()
    }
  }

  private notifyListeners() {
    this.listeners.forEach(listener => {
      listener(this.currentDeviceType, this.currentBreakpoint)
    })
  }

  /**
   * 添加响应式变化监听器
   */
  subscribe(listener: (deviceType: DeviceType, breakpoint: BreakpointKey) => void) {
    this.listeners.push(listener)
    return () => {
      const index = this.listeners.indexOf(listener)
      if (index > -1) {
        this.listeners.splice(index, 1)
      }
    }
  }

  /**
   * 获取当前设备信息
   */
  getCurrentState() {
    return {
      deviceType: this.currentDeviceType,
      breakpoint: this.currentBreakpoint,
      isMobile: this.currentDeviceType === DeviceType.MOBILE,
      isTablet: this.currentDeviceType === DeviceType.TABLET,
      isDesktop: this.currentDeviceType === DeviceType.DESKTOP,
      orientation: getOrientation()
    }
  }

  /**
   * 销毁监听器
   */
  destroy() {
    if (this.resizeObserver) {
      this.resizeObserver.disconnect()
      this.resizeObserver = null
    }
    this.listeners = []
    window.removeEventListener('orientationchange', this.checkChanges)
  }
}

// 创建全局响应式观察者实例
let globalObserver: ResponsiveObserver | null = null

/**
 * 获取全局响应式观察者实例
 */
export const getResponsiveObserver = (): ResponsiveObserver => {
  if (!globalObserver) {
    globalObserver = new ResponsiveObserver()
  }
  return globalObserver
}

/**
 * 响应式适配工具函数
 */
export const adaptiveValue = <T>(values: Partial<Record<BreakpointKey | DeviceType, T>>, fallback: T): T => {
  const currentBreakpoint = getCurrentBreakpoint()
  const deviceType = getDeviceType()

  // 优先按设备类型匹配
  if (values[deviceType] !== undefined) {
    return values[deviceType] as T
  }

  // 按断点匹配，从大到小依次匹配
  const breakpointOrder: BreakpointKey[] = ['2xl', 'xl', 'lg', 'md', 'sm', 'xs']
  const currentIndex = breakpointOrder.indexOf(currentBreakpoint)

  for (let i = currentIndex; i < breakpointOrder.length; i++) {
    const bp = breakpointOrder[i]
    if (values[bp] !== undefined) {
      return values[bp] as T
    }
  }

  return fallback
}

/**
 * 根据设备类型获取图表配置
 */
export const getChartConfig = () => {
  const deviceType = getDeviceType()

  return {
    // 基础尺寸配置
    height: adaptiveValue({
      mobile: 200,
      tablet: 300,
      desktop: 400
    }, 300),

    // 字体大小配置
    fontSize: adaptiveValue({
      mobile: 10,
      tablet: 12,
      desktop: 14
    }, 12),

    // 图例配置
    legendItemGap: adaptiveValue({
      mobile: 10,
      tablet: 15,
      desktop: 20
    }, 15),

    // 工具提示配置
    tooltip: {
      trigger: deviceType === DeviceType.MOBILE ? 'axis' : 'item',
      confine: deviceType === DeviceType.MOBILE
    },

    // 网格配置
    grid: {
      left: adaptiveValue({
        mobile: '5%',
        tablet: '8%',
        desktop: '10%'
      }, '10%'),
      right: adaptiveValue({
        mobile: '5%',
        tablet: '8%',
        desktop: '10%'
      }, '10%'),
      top: adaptiveValue({
        mobile: '15%',
        tablet: '12%',
        desktop: '10%'
      }, '12%'),
      bottom: adaptiveValue({
        mobile: '15%',
        tablet: '12%',
        desktop: '10%'
      }, '12%')
    }
  }
}

/**
 * 获取表格配置
 */
export const getTableConfig = () => {
  const deviceType = getDeviceType()

  return {
    size: adaptiveValue({
      mobile: 'small',
      tablet: 'default',
      desktop: 'default'
    }, 'default'),

    maxHeight: adaptiveValue({
      mobile: 300,
      tablet: 400,
      desktop: 500
    }, 400),

    showHeader: deviceType !== DeviceType.MOBILE,
    stripe: true,
    border: deviceType === DeviceType.DESKTOP
  }
}

/**
 * 防抖函数 - 用于优化响应式监听性能
 */
export const debounce = <T extends (...args: any[]) => void>(
  func: T,
  wait: number
): ((...args: Parameters<T>) => void) => {
  let timeout: NodeJS.Timeout | null = null

  return (...args: Parameters<T>) => {
    if (timeout) clearTimeout(timeout)
    timeout = setTimeout(() => func(...args), wait)
  }
}

/**
 * 节流函数 - 用于优化滚动等高频事件
 */
export const throttle = <T extends (...args: any[]) => void>(
  func: T,
  limit: number
): ((...args: Parameters<T>) => void) => {
  let inThrottle: boolean = false

  return (...args: Parameters<T>) => {
    if (!inThrottle) {
      func(...args)
      inThrottle = true
      setTimeout(() => inThrottle = false, limit)
    }
  }
}
