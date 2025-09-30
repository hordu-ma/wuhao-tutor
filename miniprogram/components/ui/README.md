# UI组件使用规范

## 概述

本文档定义了五好伴学小程序的UI组件使用规范，基于Vant Weapp组件库，结合项目特色进行定制。

## 设计原则

### 1. 一致性 (Consistency)
- 统一的视觉语言和交互模式
- 保持组件在不同页面中的表现一致
- 遵循微信小程序设计规范

### 2. 易用性 (Usability)
- 简洁明了的界面布局
- 符合用户直觉的交互方式
- 适配不同屏幕尺寸和设备

### 3. 可访问性 (Accessibility)
- 支持无障碍访问
- 合理的色彩对比度
- 清晰的文字层级

## 组件分类

### 基础组件 (Basic Components)
基于Vant Weapp的基础组件，用于构建界面的基本元素。

#### 按钮 (Button)
```wxml
<!-- 主要按钮 -->
<van-button type="primary" size="large">确认提交</van-button>

<!-- 次要按钮 -->
<van-button type="default" size="medium">取消</van-button>

<!-- 文本按钮 -->
<van-button type="primary" plain>查看详情</van-button>
```

**使用规范：**
- 主要按钮用于关键操作（提交、确认等）
- 次要按钮用于辅助操作（取消、返回等）
- 一个页面中主要按钮不超过2个

#### 输入框 (Field)
```wxml
<van-field
  value="{{ value }}"
  placeholder="请输入内容"
  border="{{ false }}"
  bind:change="onChange"
/>
```

#### 单元格 (Cell)
```wxml
<van-cell-group>
  <van-cell title="标题" value="内容" is-link />
  <van-cell title="设置项" is-link url="/pages/settings/index" />
</van-cell-group>
```

### 导航组件 (Navigation Components)

#### 标签页 (Tabs)
```wxml
<van-tabs active="{{ active }}" bind:change="onTabChange">
  <van-tab title="待完成">内容1</van-tab>
  <van-tab title="已完成">内容2</van-tab>
</van-tabs>
```

#### 导航栏 (NavBar)
```wxml
<van-nav-bar
  title="页面标题"
  left-text="返回"
  left-arrow
  bind:click-left="onClickLeft"
/>
```

### 反馈组件 (Feedback Components)

#### 消息提示 (Toast)
```javascript
// 成功提示
wx.showToast({
  title: '操作成功',
  icon: 'success'
});

// 错误提示
wx.showToast({
  title: '操作失败',
  icon: 'error'
});
```

#### 对话框 (Dialog)
```javascript
import Dialog from '@vant/weapp/dialog/dialog';

Dialog.confirm({
  title: '确认删除',
  message: '删除后无法恢复，是否确认？'
}).then(() => {
  // 确认逻辑
}).catch(() => {
  // 取消逻辑
});
```

### 展示组件 (Display Components)

#### 卡片 (Card)
```wxml
<van-card
  num="2"
  price="10.00"
  title="商品标题"
  desc="商品描述"
  thumb="{{ imageURL }}"
/>
```

#### 空状态 (Empty)
```wxml
<van-empty
  image="search"
  description="暂无搜索结果"
>
  <van-button round type="primary" class="bottom-button">
    重新搜索
  </van-button>
</van-empty>
```

## 自定义组件

### 1. 学习卡片 (Study Card)
用于展示作业、课程等学习内容。

```wxml
<!-- 使用示例 -->
<study-card
  title="数学作业"
  subtitle="第三章练习题"
  status="pending"
  deadline="2024-01-15"
  bind:tap="onCardTap"
/>
```

### 2. 角色标识 (Role Badge)
用于标识用户角色（学生、家长、老师）。

```wxml
<role-badge role="student" size="small" />
```

### 3. 学习进度 (Study Progress)
展示学习进度和统计信息。

```wxml
<study-progress
  progress="{{ 75 }}"
  total="{{ 100 }}"
  label="本周完成度"
/>
```

## 样式规范

### 颜色规范
- 主色调：`#1890ff` (蓝色)
- 辅助色：`#52c41a` (绿色), `#faad14` (橙色), `#f5222d` (红色)
- 中性色：`#000000`, `#333333`, `#666666`, `#999999`, `#cccccc`, `#f5f5f5`

### 字体规范
- 标题：16px, 18px, 20px
- 正文：14px
- 辅助文字：12px

### 间距规范
- 页面边距：16px
- 组件间距：12px, 16px, 24px
- 内容间距：8px, 12px

### 圆角规范
- 按钮圆角：4px
- 卡片圆角：8px
- 弹窗圆角：12px

## 响应式布局

### 栅格系统
使用Vant的栅格系统进行布局：

```wxml
<van-row gutter="20">
  <van-col span="12">左侧内容</van-col>
  <van-col span="12">右侧内容</van-col>
</van-row>
```

### 屏幕适配
- 支持iPhone、Android各种屏幕尺寸
- 使用rpx单位进行适配
- 关键内容在安全区域内显示

## 最佳实践

### 1. 性能优化
- 按需引入组件，避免全量引入
- 合理使用列表组件的虚拟滚动
- 图片懒加载和压缩

### 2. 用户体验
- 提供加载状态反馈
- 合理使用骨架屏
- 避免误触操作

### 3. 开发规范
- 组件封装遵循单一职责原则
- 统一的事件命名规范
- 完善的属性类型定义

## 组件开发模板

创建新组件时，请遵循以下目录结构：

```
components/
├── ui/
│   └── component-name/
│       ├── index.js
│       ├── index.json
│       ├── index.wxml
│       ├── index.wxss
│       └── README.md
```

### 组件配置 (index.json)
```json
{
  "component": true,
  "usingComponents": {}
}
```

### 组件逻辑 (index.js)
```javascript
Component({
  properties: {
    // 属性定义
  },
  data: {
    // 内部数据
  },
  methods: {
    // 方法定义
  },
  lifetimes: {
    // 生命周期
  }
});
```

## 更新日志

### v1.0.0 (2024-01-01)
- 初始版本
- 建立基础组件规范
- 定义设计原则和样式规范
