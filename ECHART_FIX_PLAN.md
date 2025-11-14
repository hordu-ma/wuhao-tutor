# ECharts 图谱显示问题 - 完整诊断与解决方案

## 问题诊断

### 1. 根本原因

- ec-canvas 组件的 `lazyLoad: true` 需要手动调用 `component.init()` 才会触发 `onInit`
- 当前代码在 `initGraphView()` 中先设置 option,但没有正确初始化组件
- `onInit` 中尝试访问 `currentPage.data.graphOption` 导致时序问题

### 2. 错误演化

1. **初始错误**: 组件未初始化 → chart 实例不存在
2. **第二次错误**: 试图将 chart 存入 data.chart → 循环引用 JSON 序列化错误
3. **第三次错误**: 试图直接赋值 currentPage.data.chart → 仍然循环引用

## 正确解决方案

### 关键点

1. **使用 lazyLoad + 手动 init()**
2. **在 init() 回调中创建图表并设置 option**
3. **chart 实例保存为页面普通属性 (this.chartInstance)**
4. **不要依赖 data.graphOption 的时序**

### 实现步骤

1. 保持 `ec: { lazyLoad: true }` (不需要 onInit)
2. 在 `initGraphView()` 中:
   - 构建 option
   - 获取 ec-canvas 组件
   - 调用 `component.init(callback)`
   - 在 callback 中初始化 echarts 并设置 option
3. 将 chart 保存为 `this.chartInstance`
