// 全局类型定义文件

/// <reference path="./app.d.ts" />

// 扩展全局声明
declare global {
  const __DEV__: boolean
  const __VERSION__: string

  interface Wx {
    utils?: Utils
  }
}

// 导出模块
export { }
