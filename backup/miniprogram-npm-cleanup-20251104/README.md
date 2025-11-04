# 五好伴学微信小程序

> 📱 K12 AI学情管理平台微信小程序端

## 🎯 项目概述

五好伴学微信小程序是为K12学生、家长和教师提供AI学习辅导服务的移动端应用。支持智能作业批改、学习问答互动、学情分析反馈等核心功能。

### 核心功能

- **学生端**: 作业提交、AI问答、学习报告查看
- **家长端**: 孩子学情监控、学习进度跟踪、成绩分析
- **教师端**: 作业批改、班级管理、教学分析

### 技术栈

- **框架**: 微信原生小程序 + TypeScript
- **UI组件**: Vant Weapp
- **状态管理**: MobX-miniprogram
- **网络请求**: 封装wx.request + Promise
- **构建工具**: miniprogram-ci

## 🚀 快速开始

### 环境要求

- Node.js >= 16.0.0
- npm >= 8.0.0
- 微信开发者工具 (最新稳定版)

### 安装步骤

1. **克隆项目**

```bash
cd ~/my-devs/python/wuhao-tutor/miniprogram
```

2. **安装依赖**

```bash
npm install
```

3. **配置环境**

```bash
# 复制配置文件模板
cp config/index.example.js config/index.js

# 编辑配置文件，填入正确的 AppID 和 API 地址
```

4. **开启开发模式**

```bash
npm run dev
```

5. **使用微信开发者工具**
   - 打开微信开发者工具
   - 导入项目（选择当前目录）
   - 填入小程序 AppID
   - 开始开发调试

## 📁 目录结构

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
│   ├── chat/              # 问答模块
│   ├── analysis/          # 学情分析
│   └── profile/           # 个人中心
├── utils/                 # 工具函数
│   ├── api.js             # API请求封装
│   ├── auth.js            # 认证相关
│   ├── storage.js         # 本地存储
│   └── utils.js           # 通用工具
├── config/                # 配置文件
│   ├── index.js           # 环境配置
│   └── api-config.js      # API配置
├── assets/                # 静态资源
│   ├── images/            # 图片资源
│   └── icons/             # 图标文件
└── typings/               # TypeScript类型定义
```

## 🛠️ 开发规范

### 代码规范

我们使用 ESLint + Prettier 确保代码质量和风格一致性：

```bash
# 代码检查
npm run lint

# 代码格式化
npm run format

# TypeScript 类型检查
npm run type-check

# 提交前完整检查
npm run pre-commit
```

### 命名规范

- **文件命名**: kebab-case (例: `homework-detail.js`)
- **函数命名**: camelCase (例: `getUserInfo`)
- **常量命名**: UPPER_CASE (例: `API_BASE_URL`)
- **组件命名**: PascalCase (例: `HomeworkCard`)

### Git 提交规范

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

## 📋 可用脚本

| 命令                 | 描述               |
| -------------------- | ------------------ |
| `npm run dev`        | 开发模式构建       |
| `npm run build`      | 生产模式构建       |
| `npm run lint`       | 代码检查并自动修复 |
| `npm run format`     | 代码格式化         |
| `npm run type-check` | TypeScript类型检查 |
| `npm run pre-commit` | 提交前完整检查     |
| `npm run clean`      | 清理构建文件       |

## 🔧 配置说明

### 环境配置

主要配置文件在 `config/index.js` 中：

```javascript
const config = {
  environment: 'development',
  api: {
    baseUrl: 'https://localhost:8000',
    version: 'v1',
    timeout: 10000,
  },
  miniprogram: {
    appId: 'wxYOUR_APPID_HERE', // 需要替换
  },
  // ... 更多配置
};
```

### 重要配置项

- **appId**: 小程序 AppID (必须配置)
- **api.baseUrl**: 后端 API 地址
- **upload.ossBaseUrl**: 文件上传服务地址
- **theme**: UI 主题色彩配置

## 🔐 安全注意事项

1. **不要提交敏感信息**
   - AppID 等配置信息使用模板文件
   - 不要在代码中硬编码密钥

2. **权限控制**
   - 按需申请微信权限
   - 实现页面级权限验证
   - 保护用户隐私数据

3. **数据安全**
   - 使用 HTTPS 进行 API 通信
   - 敏感信息不存储在本地
   - 实现请求签名验证

## 📱 兼容性

- **微信版本**: >= 7.0.0
- **基础库版本**: >= 2.10.0
- **支持系统**: iOS 10.0+, Android 5.0+

## 🐛 调试技巧

### 常见问题

1. **页面空白**
   - 检查 app.json 中的页面路径配置
   - 查看控制台错误信息

2. **API 请求失败**
   - 确认服务器域名已在小程序后台配置
   - 检查 config/index.js 中的 API 地址

3. **组件不显示**
   - 确认组件路径在 app.json 中正确配置
   - 检查组件的 js/json/wxml/wxss 文件完整性

### 调试工具

```bash
# 查看编译输出
npm run compile

# 检查依赖
npm list

# 清理重装
npm run reinstall
```

## 📊 性能优化

### 优化策略

1. **代码分包**: 按功能模块分包加载
2. **图片优化**: 使用 WebP 格式，实现懒加载
3. **缓存策略**: 合理设置接口和静态资源缓存
4. **包大小**: 主包 < 500KB，总包 < 2MB

### 性能监控

项目集成了性能监控，可通过配置启用：

```javascript
// config/index.js
performance: {
  enabled: true,
  sampleRate: 0.1,
  metrics: {
    pageLoadTime: true,
    apiRequestTime: true,
  }
}
```

## 🤝 贡献指南

### 开发流程

1. **创建功能分支**

```bash
git checkout -b feature/your-feature-name
```

2. **开发并测试**

```bash
npm run pre-commit  # 确保代码质量
```

3. **提交代码**

```bash
git commit -m "feat: 添加新功能描述"
git push origin feature/your-feature-name
```

4. **创建 Pull Request**

### 代码审查

- 确保所有测试通过
- 遵循项目编码规范
- 提供清晰的变更说明
- 考虑向后兼容性

## 📞 技术支持

### 开发资源

- [微信小程序官方文档](https://developers.weixin.qq.com/miniprogram/dev/)
- [Vant Weapp 组件库](https://youzan.github.io/vant-weapp/)
- [TypeScript 官方文档](https://www.typescriptlang.org/)

### 联系方式

- **项目负责人**: Liguo Ma <maliguo@outlook.com>
- **技术文档**: [../docs](../docs/) 目录
- **问题反馈**: GitHub Issues

## 📄 许可证

MIT License - 详见 [LICENSE](../LICENSE) 文件

---

**🎯 让我们一起打造高质量的教育类微信小程序！**
