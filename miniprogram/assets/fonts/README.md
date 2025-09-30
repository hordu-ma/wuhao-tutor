# 图标字体库使用指南

## 概述

五好伴学小程序图标字体库提供了丰富的图标资源，涵盖教育、功能、状态等多个类别。所有图标都经过优化，支持多种尺寸和颜色主题。

## 快速开始

### 1. 引入图标样式

在 `app.wxss` 中引入图标样式文件：

```css
@import "assets/fonts/icons.wxss";
```

### 2. 基本使用

```html
<!-- 基础图标 -->
<text class="icon icon-home"></text>

<!-- 带尺寸的图标 -->
<text class="icon icon-home icon-lg"></text>

<!-- 带颜色的图标 -->
<text class="icon icon-home icon-primary"></text>

<!-- 组合使用 -->
<text class="icon icon-home icon-lg icon-primary"></text>
```

## 图标分类

### 通用图标
- `icon-home` - 首页
- `icon-user` - 用户
- `icon-setting` - 设置
- `icon-search` - 搜索
- `icon-add` - 添加
- `icon-delete` - 删除
- `icon-edit` - 编辑
- `icon-save` - 保存
- `icon-close` - 关闭
- `icon-check` - 确认
- `icon-arrow-left` - 左箭头
- `icon-arrow-right` - 右箭头
- `icon-arrow-up` - 上箭头
- `icon-arrow-down` - 下箭头
- `icon-more` - 更多
- `icon-share` - 分享
- `icon-download` - 下载
- `icon-upload` - 上传
- `icon-refresh` - 刷新
- `icon-loading` - 加载中

### 教育相关图标
- `icon-book` - 书本
- `icon-homework` - 作业
- `icon-test` - 测试
- `icon-grade` - 成绩
- `icon-certificate` - 证书
- `icon-teacher` - 老师
- `icon-student` - 学生
- `icon-parent` - 家长
- `icon-class` - 班级
- `icon-school` - 学校
- `icon-subject` - 学科
- `icon-lesson` - 课程
- `icon-exam` - 考试
- `icon-practice` - 练习
- `icon-knowledge` - 知识点

### 学科图标
- `icon-math` - 数学
- `icon-chinese` - 语文
- `icon-english` - 英语
- `icon-physics` - 物理
- `icon-chemistry` - 化学
- `icon-biology` - 生物
- `icon-history` - 历史
- `icon-geography` - 地理
- `icon-politics` - 政治
- `icon-art` - 美术
- `icon-music` - 音乐
- `icon-pe` - 体育

### 功能图标
- `icon-chat` - 聊天
- `icon-message` - 消息
- `icon-notification` - 通知
- `icon-calendar` - 日历
- `icon-clock` - 时钟
- `icon-timer` - 计时器
- `icon-camera` - 相机
- `icon-image` - 图片
- `icon-video` - 视频
- `icon-audio` - 音频
- `icon-file` - 文件
- `icon-folder` - 文件夹
- `icon-report` - 报告
- `icon-chart` - 图表
- `icon-statistics` - 统计
- `icon-progress` - 进度
- `icon-achievement` - 成就
- `icon-medal` - 奖牌
- `icon-star` - 星星
- `icon-heart` - 心形
- `icon-like` - 点赞
- `icon-dislike` - 点踩
- `icon-favorite` - 收藏
- `icon-bookmark` - 书签
- `icon-tag` - 标签
- `icon-flag` - 标记

### 状态图标
- `icon-success` - 成功
- `icon-error` - 错误
- `icon-warning` - 警告
- `icon-info` - 信息
- `icon-question` - 问题
- `icon-help` - 帮助
- `icon-tips` - 提示
- `icon-lock` - 锁定
- `icon-unlock` - 解锁
- `icon-visible` - 可见
- `icon-invisible` - 不可见
- `icon-online` - 在线
- `icon-offline` - 离线
- `icon-new` - 新的
- `icon-hot` - 热门
- `icon-recommend` - 推荐

### AI相关图标
- `icon-ai` - AI
- `icon-robot` - 机器人
- `icon-brain` - 大脑
- `icon-smart` - 智能
- `icon-analysis` - 分析
- `icon-prediction` - 预测
- `icon-insight` - 洞察
- `icon-recommendation` - 推荐

## 图标尺寸

```html
<!-- 超小图标 (24rpx) -->
<text class="icon icon-home icon-xs"></text>

<!-- 小图标 (32rpx) -->
<text class="icon icon-home icon-sm"></text>

<!-- 中等图标 (40rpx) -->
<text class="icon icon-home icon-md"></text>

<!-- 大图标 (48rpx) -->
<text class="icon icon-home icon-lg"></text>

<!-- 超大图标 (64rpx) -->
<text class="icon icon-home icon-xl"></text>

<!-- 特大图标 (96rpx) -->
<text class="icon icon-home icon-xxl"></text>
```

## 图标颜色

### 功能颜色
```html
<!-- 主色 -->
<text class="icon icon-home icon-primary"></text>

<!-- 成功色 -->
<text class="icon icon-check icon-success"></text>

<!-- 警告色 -->
<text class="icon icon-warning icon-warning"></text>

<!-- 错误色 -->
<text class="icon icon-error icon-error"></text>

<!-- 信息色 -->
<text class="icon icon-info icon-info"></text>

<!-- 禁用色 -->
<text class="icon icon-home icon-disabled"></text>

<!-- 次要色 -->
<text class="icon icon-home icon-secondary"></text>
```

### 学科颜色
```html
<!-- 数学红色 -->
<text class="icon icon-math icon-math-color"></text>

<!-- 语文青色 -->
<text class="icon icon-chinese icon-chinese-color"></text>

<!-- 英语蓝色 -->
<text class="icon icon-english icon-english-color"></text>

<!-- 物理绿色 -->
<text class="icon icon-physics icon-physics-color"></text>

<!-- 化学黄色 -->
<text class="icon icon-chemistry icon-chemistry-color"></text>
```

## 图标动画

```html
<!-- 旋转动画 -->
<text class="icon icon-loading icon-spin"></text>

<!-- 脉冲动画 -->
<text class="icon icon-heart icon-pulse"></text>

<!-- 弹跳动画 -->
<text class="icon icon-star icon-bounce"></text>

<!-- 摇摆动画 -->
<text class="icon icon-notification icon-shake"></text>
```

## 图标组合

### 图标与文字组合
```html
<view class="icon-with-text">
  <text class="icon icon-book"></text>
  <text>作业本</text>
</view>
```

### 图标叠加
```html
<view class="icon-stack">
  <text class="icon icon-user icon-lg"></text>
  <text class="icon icon-check icon-sm icon-success"></text>
</view>
```

## 图标背景

```html
<!-- 圆形背景 -->
<text class="icon icon-home icon-bg-circle"></text>

<!-- 方形背景 -->
<text class="icon icon-home icon-bg-square"></text>

<!-- 主色背景 -->
<text class="icon icon-home icon-bg-primary"></text>

<!-- 成功色背景 -->
<text class="icon icon-check icon-bg-success"></text>

<!-- 警告色背景 -->
<text class="icon icon-warning icon-bg-warning"></text>

<!-- 错误色背景 -->
<text class="icon icon-error icon-bg-error"></text>
```

## 使用示例

### 导航栏图标
```html
<van-nav-bar
  title="作业详情"
  left-arrow
  bind:click-left="onClickLeft"
>
  <view slot="right" class="nav-right">
    <text class="icon icon-share icon-lg" bind:tap="onShare"></text>
    <text class="icon icon-more icon-lg ml-md" bind:tap="onMore"></text>
  </view>
</van-nav-bar>
```

### 功能卡片
```html
<view class="function-card">
  <view class="card-icon">
    <text class="icon icon-homework icon-xl icon-primary"></text>
  </view>
  <view class="card-content">
    <text class="card-title">今日作业</text>
    <text class="card-desc">3项待完成</text>
  </view>
  <view class="card-action">
    <text class="icon icon-arrow-right icon-secondary"></text>
  </view>
</view>
```

### 状态提示
```html
<view class="status-item">
  <text class="icon icon-success icon-success"></text>
  <text class="status-text">作业已提交</text>
</view>

<view class="status-item">
  <text class="icon icon-warning icon-warning"></text>
  <text class="status-text">即将到期</text>
</view>

<view class="status-item">
  <text class="icon icon-error icon-error"></text>
  <text class="status-text">提交失败</text>
</view>
```

### 学科标识
```html
<view class="subject-list">
  <view class="subject-item">
    <text class="icon icon-math icon-lg icon-math-color"></text>
    <text>数学</text>
  </view>
  <view class="subject-item">
    <text class="icon icon-chinese icon-lg icon-chinese-color"></text>
    <text>语文</text>
  </view>
  <view class="subject-item">
    <text class="icon icon-english icon-lg icon-english-color"></text>
    <text>英语</text>
  </view>
</view>
```

## 自定义图标

如需添加新图标，请按以下步骤操作：

1. 设计符合规范的图标（24x24px）
2. 转换为字体格式
3. 在 `icons.wxss` 中添加对应的 CSS 类
4. 更新本文档

## 最佳实践

### 1. 语义化使用
- 选择意义明确的图标
- 保持图标与功能的对应关系
- 避免装饰性使用图标

### 2. 尺寸规范
- 导航栏：使用 `icon-lg` (48rpx)
- 按钮：使用 `icon-md` (40rpx) 或 `icon-sm` (32rpx)
- 列表项：使用 `icon-md` (40rpx)
- 状态提示：使用 `icon-sm` (32rpx)

### 3. 颜色搭配
- 主要功能使用 `icon-primary`
- 状态提示使用对应的状态色
- 次要信息使用 `icon-secondary`
- 禁用状态使用 `icon-disabled`

### 4. 性能优化
- 优先使用字体图标而非图片
- 避免过度使用动画效果
- 合理控制图标数量

## 注意事项

1. 图标字体文件较大时，建议按需加载
2. 在不同设备上测试图标显示效果
3. 确保图标在深色模式下的可读性
4. 保持图标风格的一致性
5. 定期清理未使用的图标类

## 更新日志

### v1.0.0 (2024-01-01)
- 初始版本发布
- 包含150+图标
- 支持多种尺寸和颜色
- 提供动画效果
