/**
 * 响应式 Vue Composition Hook
 * 提供响应式状态管理和设备检测功能
 */

import { ref, reactive, onMounted, onUnmounted, computed } from 'vue'
import {
  getDeviceType,
  getCurrentBreakpoint,
  getOrientation,
  getResponsiveObserver,
  getChartConfig,
  getTableConfig,
  adaptiveValue,
  debounce,
  throttle,
  DeviceType,
  type BreakpointKey
} from '../utils/responsive'

/**
 * 响应式状态管理 Hook
 */
export const useResponsive = () => {
  // 响应式状态
  const deviceType = ref<DeviceType>(DeviceType.DESKTOP)
  const breakpoint = ref<BreakpointKey>('lg')
  const orientation = ref(getOrientation())

  // 设备类型判断
  const isMobileDevice = computed(() => deviceType.value === DeviceType.MOBILE)
  const isTabletDevice = computed(() => deviceType.value === DeviceType.TABLET)
  const isDesktopDevice = computed(() => deviceType.value === DeviceType.DESKTOP)

  // 断点判断
  const isXs = computed(() => breakpoint.value === 'xs')
  const isSm = computed(() => breakpoint.value === 'sm')
  const isMd = computed(() => breakpoint.value === 'md')
  const isLg = computed(() => breakpoint.value === 'lg')
  const isXl = computed(() => breakpoint.value === 'xl')
  const is2xl = computed(() => breakpoint.value === '2xl')

  // 屏幕方向
  const isLandscape = computed(() => orientation.value === 'landscape')
  const isPortrait = computed(() => orientation.value === 'portrait')

  // 屏幕尺寸
  const screenSize = reactive({
    width: 0,
    height: 0
  })

  // 更新状态函数
  const updateState = () => {
    deviceType.value = getDeviceType()
    breakpoint.value = getCurrentBreakpoint()
    orientation.value = getOrientation()
    screenSize.width = window.innerWidth
    screenSize.height = window.innerHeight
  }

  // 防抖更新函数
  const debouncedUpdate = debounce(updateState, 150)

  let unsubscribe: (() => void) | null = null

  onMounted(() => {
    // 初始化状态
    updateState()

    // 订阅响应式变化
    const observer = getResponsiveObserver()
    unsubscribe = observer.subscribe((newDeviceType, newBreakpoint) => {
      deviceType.value = newDeviceType
      breakpoint.value = newBreakpoint
      orientation.value = getOrientation()
    })

    // 监听窗口大小变化
    window.addEventListener('resize', debouncedUpdate)
    window.addEventListener('orientationchange', () => {
      setTimeout(updateState, 100) // 延迟确保获取正确的方向
    })
  })

  onUnmounted(() => {
    // 清理监听器
    if (unsubscribe) {
      unsubscribe()
    }
    window.removeEventListener('resize', debouncedUpdate)
  })

  return {
    // 响应式状态
    deviceType: readonly(deviceType),
    breakpoint: readonly(breakpoint),
    orientation: readonly(orientation),
    screenSize: readonly(screenSize),

    // 设备类型判断
    isMobileDevice,
    isTabletDevice,
    isDesktopDevice,

    // 断点判断
    isXs,
    isSm,
    isMd,
    isLg,
    isXl,
    is2xl,

    // 屏幕方向
    isLandscape,
    isPortrait,

    // 工具函数
    adaptiveValue: <T>(values: Partial<Record<BreakpointKey | DeviceType, T>>, fallback: T): T => {
      return adaptiveValue(values, fallback)
    }
  }
}

/**
 * 图表响应式配置 Hook
 */
export const useChartResponsive = () => {
  const { isMobileDevice } = useResponsive()

  // 图表基础配置
  const chartConfig = computed(() => getChartConfig())

  // 图表高度配置
  const getChartHeight = (baseHeight: number = 400) => {
    return adaptiveValue({
      mobile: Math.min(baseHeight * 0.6, 250),
      tablet: Math.min(baseHeight * 0.8, 350),
      desktop: baseHeight
    }, baseHeight)
  }

  // 图表字体大小
  const getChartFontSize = (baseSize: number = 12) => {
    return adaptiveValue({
      mobile: Math.max(baseSize * 0.8, 10),
      tablet: Math.max(baseSize * 0.9, 11),
      desktop: baseSize
    }, baseSize)
  }

  // 图表边距配置
  const getChartPadding = () => {
    return {
      top: adaptiveValue({ mobile: 10, tablet: 15, desktop: 20 }, 20),
      right: adaptiveValue({ mobile: 10, tablet: 15, desktop: 20 }, 20),
      bottom: adaptiveValue({ mobile: 10, tablet: 15, desktop: 20 }, 20),
      left: adaptiveValue({ mobile: 10, tablet: 15, desktop: 20 }, 20)
    }
  }

  // 响应式图例配置
  const getLegendConfig = () => {
    return {
      orient: isMobileDevice.value ? 'horizontal' : 'vertical',
      top: isMobileDevice.value ? 'bottom' : 'middle',
      right: isMobileDevice.value ? 'center' : 10,
      itemGap: adaptiveValue({ mobile: 8, tablet: 12, desktop: 16 }, 12),
      textStyle: {
        fontSize: getChartFontSize(11)
      }
    }
  }

  return {
    chartConfig,
    getChartHeight,
    getChartFontSize,
    getChartPadding,
    getLegendConfig
  }
}

/**
 * 表格响应式配置 Hook
 */
export const useTableResponsive = () => {
  const { isMobileDevice } = useResponsive()

  // 表格基础配置
  const tableConfig = computed(() => getTableConfig())

  // 表格列配置
  const getColumnConfig = (columns: any[], mobileColumns?: string[]) => {
    if (isMobileDevice.value && mobileColumns) {
      return columns.filter(col => mobileColumns.includes(col.prop))
    }
    return columns
  }

  // 表格分页配置
  const getPaginationConfig = () => {
    return {
      small: isMobileDevice.value,
      layout: isMobileDevice.value
        ? 'prev, pager, next'
        : 'total, sizes, prev, pager, next, jumper',
      pageSizes: isMobileDevice.value ? [10, 20] : [10, 20, 50, 100],
      pageSize: isMobileDevice.value ? 10 : 20
    }
  }

  return {
    tableConfig,
    getColumnConfig,
    getPaginationConfig
  }
}

/**
 * 布局响应式 Hook
 */
export const useLayoutResponsive = () => {
  const { isMobileDevice } = useResponsive()

  // 侧边栏配置
  const sidebarConfig = computed(() => ({
    collapse: isMobileDevice.value,
    width: adaptiveValue({
      mobile: '100%',
      tablet: '240px',
      desktop: '260px'
    }, '260px'),
    collapsedWidth: '64px'
  }))

  // 容器配置
  const containerConfig = computed(() => ({
    padding: adaptiveValue({
      mobile: '12px',
      tablet: '16px',
      desktop: '24px'
    }, '24px'),
    maxWidth: adaptiveValue({
      mobile: '100%',
      tablet: '100%',
      desktop: '1200px'
    }, '1200px')
  }))

  // 卡片配置
  const cardConfig = computed(() => ({
    shadow: adaptiveValue({
      mobile: 'never',
      tablet: 'hover',
      desktop: 'hover'
    }, 'hover'),
    bodyPadding: adaptiveValue({
      mobile: '12px',
      tablet: '16px',
      desktop: '20px'
    }, '20px')
  }))

  // 网格配置
  const getGridConfig = (cols: { xs?: number, sm?: number, md?: number, lg?: number, xl?: number }) => {
    return {
      xs: cols.xs || 1,
      sm: cols.sm || 2,
      md: cols.md || 3,
      lg: cols.lg || 4,
      xl: cols.xl || 5
    }
  }

  return {
    sidebarConfig,
    containerConfig,
    cardConfig,
    getGridConfig
  }
}

/**
 * 触摸事件 Hook
 */
export const useTouchEvents = () => {
  const { isMobileDevice } = useResponsive()

  // 触摸状态
  const touchState = reactive({
    startX: 0,
    startY: 0,
    endX: 0,
    endY: 0,
    deltaX: 0,
    deltaY: 0,
    isScrolling: false
  })

  // 处理触摸开始
  const handleTouchStart = (event: TouchEvent) => {
    if (!isMobileDevice.value) return

    const touch = event.touches[0]
    touchState.startX = touch.clientX
    touchState.startY = touch.clientY
    touchState.isScrolling = false
  }

  // 处理触摸移动
  const handleTouchMove = throttle((event: TouchEvent) => {
    if (!isMobileDevice.value) return

    const touch = event.touches[0]
    touchState.endX = touch.clientX
    touchState.endY = touch.clientY
    touchState.deltaX = touchState.endX - touchState.startX
    touchState.deltaY = touchState.endY - touchState.startY

    // 判断是否为滚动
    if (Math.abs(touchState.deltaY) > Math.abs(touchState.deltaX)) {
      touchState.isScrolling = true
    }
  }, 16)

  // 处理触摸结束
  const handleTouchEnd = (callback?: (deltaX: number, deltaY: number) => void) => {
    return () => {
      if (!isMobileDevice.value || touchState.isScrolling) return

      if (callback) {
        callback(touchState.deltaX, touchState.deltaY)
      }

      // 重置状态
      Object.assign(touchState, {
        startX: 0,
        startY: 0,
        endX: 0,
        endY: 0,
        deltaX: 0,
        deltaY: 0,
        isScrolling: false
      })
    }
  }

  return {
    touchState: readonly(touchState),
    handleTouchStart,
    handleTouchMove,
    handleTouchEnd
  }
}
