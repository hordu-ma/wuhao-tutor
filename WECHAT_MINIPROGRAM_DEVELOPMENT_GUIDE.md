# 五好伴学微信小程序开发指南

> **📱 微信小程序前端开发完整指南**
> 本文档提供五好伴学K12 AI学情管理平台微信小程序端的详细开发流程

**创建时间**: 2024-12-19
**项目版本**: 0.1.0 (Alpha)
**小程序版本**: 1.0.0 (规划中)

---

## 🎯 项目概述

### 小程序定位

- **名称**: 五好伴学
- **类型**: 教育类微信小程序
- **目标用户**: K12学生、家长、教师
- **核心价值**: 随时随地的AI学习辅导与学情管理

### 功能规划

1. **学生端**: 作业提交、问答互动、学习报告查看
2. **家长端**: 孩子学情监控、学习进度跟踪、成绩分析
3. **教师端**: 作业批改、班级管理、教学分析

### 技术选型

- **框架**: 微信原生小程序 + TypeScript
- **UI组件**: Vant Weapp
- **状态管理**: MobX-miniprogram
- **网络请求**: 封装wx.request + Promise
- **构建工具**: miniprogram-ci

---

## 🏗️ 开发阶段规划

## 第一阶段：项目初始化与架构搭建 (预计2-3天)

### TODO 1.1: 项目环境准备

1. 注册微信小程序账号，获取AppID
2. 安装微信开发者工具
3. 创建小程序项目，配置TypeScript支持
4. 配置代码规范工具(ESLint + Prettier)
5. 建立Git分支策略(feature/miniprogram-*)
   *小程序的AppID: wx2a8b340606664785\*

### TODO 1.2: 目录结构设计

1. 设计符合微信小程序规范的目录结构
2. 创建公共组件目录(components/)
3. 建立页面目录结构(pages/)
4. 配置工具函数目录(utils/)
5. 设置静态资源目录(assets/)

### TODO 1.3: 基础配置文件

1. 配置app.json(页面路由、tabBar、权限等)
2. 设置app.wxss(全局样式、主题色彩)
3. 配置project.config.json(项目配置)
4. 建立环境变量管理(config/)
5. 创建TypeScript配置文件

### TODO 1.4: UI组件库集成

1. 安装Vant Weapp组件库
2. 配置组件库的全局引用
3. 创建项目专用UI组件规范
4. 设计响应式布局系统
5. 建立图标字体库

### TODO 1.5: 网络层架构

1. 封装wx.request为Promise形式
2. 配置请求/响应拦截器
3. 实现API错误处理机制
4. 设置接口地址管理
5. 建立token管理机制

## 第二阶段：用户认证与角色管理 (预计3-4天)

### TODO 2.1: 微信登录流程

1. 实现微信授权登录(wx.login)
2. 获取用户信息(wx.getUserProfile)
3. 与后端API对接完成登录验证
4. 实现登录状态持久化
5. 处理登录失败场景

### TODO 2.2: 用户角色系统

1. 设计角色选择页面(学生/家长/教师)
2. 实现角色切换功能
3. 配置不同角色的权限控制
4. 建立角色相关的路由守卫
5. 设置角色专属的tabBar

### TODO 2.3: 用户信息管理

1. 创建用户信息展示页面
2. 实现用户信息编辑功能
3. 添加头像上传功能
4. 建立信息同步机制
5. 处理信息更新的异常情况

### TODO 2.4: 权限控制系统

1. 实现页面级权限控制
2. 设置功能模块权限验证
3. 建立API调用权限管理
4. 配置敏感操作二次确认
5. 添加权限不足的友好提示

### TODO 2.5: 账号安全机制

1. 实现账号绑定验证
2. 添加异常登录检测
3. 建立会话过期处理
4. 实现安全退出功能
5. 配置隐私信息保护

## 第三阶段：核心功能页面开发 (预计5-7天)

### TODO 3.1: 首页与导航

1. 设计首页布局(角色相关的功能入口)
2. 实现个性化推荐内容展示
3. 添加快捷操作面板
4. 建立消息通知中心
5. 配置页面下拉刷新

### TODO 3.2: 作业模块

1. 创建作业列表页面(待做/已完成)
2. 实现作业详情页面
3. 建立作业提交功能(拍照/文字)
4. 添加作业批改结果展示
5. 实现作业历史记录查看

### TODO 3.3: 问答互动模块

1. 设计问答对话界面
2. 实现AI问答功能对接
3. 添加问题类型分类
4. 建立历史问答记录
5. 实现问答收藏功能

### TODO 3.4: 学情分析模块

1. 创建学习报告页面
2. 实现图表数据可视化
3. 添加知识点掌握度展示
4. 建立学习建议推荐
5. 实现报告分享功能

### TODO 3.5: 个人中心

1. 设计个人中心页面布局
2. 实现设置功能页面
3. 添加帮助与反馈入口
4. 建立关于我们页面
5. 实现数据统计展示

## 第四阶段：高级功能与优化 (预计4-5天)

### TODO 4.1: 数据缓存策略

1. 实现本地数据缓存机制
2. 配置缓存更新策略
3. 建立离线数据处理
4. 添加缓存清理功能
5. 优化缓存性能

### TODO 4.2: 图片与文件处理

1. 实现图片上传压缩功能
2. 添加图片预览组件
3. 建立文件上传进度显示
4. 实现图片本地缓存
5. 配置上传失败重试机制

### TODO 4.3: 消息推送系统

1. 配置模板消息推送
2. 实现订阅消息管理
3. 建立消息历史记录
4. 添加消息免打扰设置
5. 实现消息点击跳转

### TODO 4.4: 性能优化

1. 实现图片懒加载
2. 优化页面渲染性能
3. 配置代码分包加载
4. 建立性能监控埋点
5. 优化网络请求性能

### TODO 4.5: 错误处理与监控

1. 建立全局错误捕获机制
2. 实现错误上报功能
3. 配置用户行为埋点
4. 添加崩溃恢复机制
5. 建立错误日志管理

## 第五阶段：测试与发布 (预计2-3天)

### TODO 5.1: 功能测试

1. 编写核心功能测试用例
2. 进行用户操作流程测试
3. 验证API接口对接
4. 测试异常场景处理
5. 检查数据同步准确性

### TODO 5.2: 兼容性测试

1. 测试不同微信版本兼容性
2. 验证不同手机机型适配
3. 测试网络环境兼容性
4. 检查权限获取流程
5. 验证支付功能(如需要)

### TODO 5.3: 性能测试

1. 测试页面加载速度
2. 验证内存使用情况
3. 检查网络请求性能
4. 测试图片加载优化
5. 验证用户体验流畅度

### TODO 5.4: 发布准备

1. 配置生产环境参数
2. 准备小程序审核资料
3. 设置版本号和更新日志
4. 配置服务器域名白名单
5. 准备用户隐私协议

### TODO 5.5: 发布与监控

1. 提交小程序审核
2. 配置发布后监控
3. 准备用户反馈收集
4. 建立版本迭代计划
5. 设置运营数据统计

---

## 📁 推荐目录结构

```
miniprogram/
├── app.js                 # 小程序入口文件
├── app.json               # 全局配置文件
├── app.wxss               # 全局样式文件
├── components/            # 公共组件
│   ├── chat-bubble/       # 聊天气泡组件
│   ├── homework-card/     # 作业卡片组件
│   ├── chart-view/        # 图表展示组件
│   └── upload-image/      # 图片上传组件
├── pages/                 # 页面文件
│   ├── index/             # 首页
│   ├── login/             # 登录页
│   ├── homework/          # 作业模块
│   │   ├── list/          # 作业列表
│   │   ├── detail/        # 作业详情
│   │   └── submit/        # 作业提交
│   ├── chat/              # 问答模块
│   │   ├── index/         # 问答首页
│   │   └── detail/        # 对话详情
│   ├── analysis/          # 学情分析
│   │   ├── report/        # 学习报告
│   │   └── progress/      # 学习进度
│   └── profile/           # 个人中心
│       ├── index/         # 个人主页
│       ├── settings/      # 设置页面
│       └── help/          # 帮助中心
├── utils/                 # 工具函数
│   ├── api.js             # API请求封装
│   ├── auth.js            # 认证相关
│   ├── storage.js         # 本地存储
│   ├── upload.js          # 文件上传
│   └── utils.js           # 通用工具
├── config/                # 配置文件
│   ├── index.js           # 环境配置
│   └── api-config.js      # API配置
├── assets/                # 静态资源
│   ├── images/            # 图片资源
│   ├── icons/             # 图标文件
│   └── styles/            # 样式文件
└── typings/               # TypeScript类型定义
    ├── api.d.ts           # API类型
    ├── components.d.ts    # 组件类型
    └── global.d.ts        # 全局类型
```

---

## 🔧 开发规范

### 代码规范

```typescript
// 文件命名: kebab-case
// homework-detail.ts, chat-bubble.wxml

// 函数命名: camelCase
function getUserInfo(): Promise<UserInfo> {
    // 必须有类型注解和返回值类型
}

// 常量命名: UPPER_CASE
const API_BASE_URL = "https://api.wuhao-tutor.com";

// 组件命名: PascalCase
Component({
    properties: {
        homework: {
            type: Object as () => HomeworkInfo,
            required: true,
        },
    },
});
```

### API对接规范

```typescript
// 统一的响应格式处理
interface ApiResponse<T> {
    success: boolean;
    data?: T;
    error?: {
        code: string;
        message: string;
    };
}

// 错误处理
try {
    const result = await api.submitHomework(data);
    if (result.success) {
        // 处理成功逻辑
    } else {
        // 处理业务错误
        wx.showToast({
            title: result.error?.message || "操作失败",
            icon: "error",
        });
    }
} catch (error) {
    // 处理网络错误
    console.error("API调用失败:", error);
    wx.showToast({
        title: "网络异常，请稍后重试",
        icon: "error",
    });
}
```

### 样式规范

```wxss
/* 使用BEM命名规范 */
.homework-card {
    /* 块级元素 */
}

.homework-card__title {
    /* 元素 */
}

.homework-card--pending {
    /* 修饰符 */
}

/* 响应式设计 */
.container {
    padding: 32rpx;
    box-sizing: border-box;
}

/* 主题色彩变量 */
:root {
    --primary-color: #1890ff;
    --success-color: #52c41a;
    --warning-color: #faad14;
    --error-color: #f5222d;
}
```

---

## 🚀 快速开始

### 环境准备

```bash
# 1. 克隆项目到小程序目录
cd ~/my-devs/python/wuhao-tutor
mkdir miniprogram
cd miniprogram

# 2. 初始化小程序项目
# 使用微信开发者工具创建项目

# 3. 安装依赖(如使用npm)
npm install @vant/weapp mobx-miniprogram

# 4. 配置开发环境
cp config/index.example.js config/index.js
```

### 开发流程

```bash
# 1. 创建功能分支
git checkout -b feature/miniprogram-auth

# 2. 开发调试
# 使用微信开发者工具进行开发

# 3. 代码检查
npm run lint
npm run type-check

# 4. 提交代码
git add .
git commit -m "feat: 实现微信登录功能"
git push origin feature/miniprogram-auth
```

---

## 🔐 安全注意事项

### 数据安全

- 敏感信息不存储在小程序本地
- 使用HTTPS协议进行API通信
- 实现请求签名验证
- 用户隐私信息加密传输

### 小程序特殊约束

- 遵循微信小程序内容规范
- 不得绕过微信支付进行交易
- 保护用户隐私，合理获取权限
- 避免诱导分享和关注

---

## 📊 性能指标

### 性能目标

- 首屏加载时间: < 3秒
- 页面切换响应: < 500ms
- 图片加载优化: 懒加载 + 压缩
- 代码包大小: < 2MB (主包 < 500KB)

### 监控指标

- 页面访问量(PV)
- 用户活跃度(DAU/MAU)
- 功能使用率
- 错误率和崩溃率
- 网络请求成功率

---

## 🤝 团队协作

### Git分支策略

```
main                 # 主分支(发布版本)
├── develop          # 开发分支
├── feature/miniprogram-*  # 功能分支
├── fix/miniprogram-*      # 修复分支
└── release/v1.0.0   # 发布分支
```

### 提交信息规范

```bash
# 功能开发
feat: 添加作业提交功能
feat(chat): 实现AI问答界面

# 问题修复
fix: 修复图片上传失败问题
fix(auth): 解决登录状态丢失

# 文档和样式
docs: 更新小程序开发指南
style: 调整首页布局样式
```

---

## 📝 注意事项

### 开发提醒

1. **权限申请**: 按需申请，避免过度索要权限
2. **用户体验**: 保持页面响应速度，避免长时间加载
3. **错误处理**: 提供友好的错误提示和重试机制
4. **数据同步**: 确保本地缓存与服务器数据一致性
5. **版本兼容**: 考虑不同微信版本的功能支持

### 审核要点

1. **内容合规**: 确保教育内容健康积极
2. **功能完整**: 确保所有功能正常可用
3. **隐私保护**: 明确隐私政策和数据使用说明
4. **用户协议**: 完善用户服务协议
5. **客服支持**: 提供用户反馈和客服入口

---

## 🔄 迭代计划

### V1.0.0 (MVP版本)

- [ ] 基础用户认证
- [ ] 作业提交与查看
- [ ] 简单问答功能
- [ ] 基础学情报告

### V1.1.0 (功能增强)

- [ ] 消息推送
- [ ] 离线缓存
- [ ] 家长监控功能
- [ ] 教师管理面板

### V1.2.0 (体验优化)

- [ ] 界面美化
- [ ] 性能优化
- [ ] 高级图表
- [ ] 社交分享

---

## 📞 技术支持

### 开发资源

- **微信小程序官方文档**: https://developers.weixin.qq.com/miniprogram/dev/
- **Vant Weapp组件库**: https://youzan.github.io/vant-weapp/
- **TypeScript官方文档**: https://www.typescriptlang.org/

### 联系方式

- **项目负责人**: Liguo Ma <maliguo@outlook.com>
- **技术文档**: `/docs` 目录
- **问题反馈**: GitHub Issues

---

**🎯 开发目标**: 打造一个高质量、用户体验优秀的教育类微信小程序，为K12学生提供便捷的AI学习辅导服务。

---

_本文档将随着开发进度持续更新，确保团队协作的一致性和开发质量。_
