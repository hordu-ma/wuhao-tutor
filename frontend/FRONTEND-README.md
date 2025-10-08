# 五好伴学前端项目

## 📋 项目简介

基于 **Vue 3 + TypeScript + Vite** 的现代化 K12 教育前端应用，提供智能作业批改、学习问答和学情分析等功能。

---

## 🛠️ 技术栈

### 核心框架

- **Vue 3.4+** - Composition API + `<script setup>`
- **TypeScript 5.x** - 严格类型检查
- **Vite 5.x** - 快速构建工具
- **Vue Router 4.x** - 路由管理
- **Pinia** - 状态管理

### UI 组件

- **Element Plus** - 企业级 UI 库
- **Tailwind CSS** - 原子化 CSS
- **SCSS** - CSS 预处理

### 工具库

- **Axios** - HTTP 客户端
- **Day.js** - 日期处理
- **Lodash-es** - 工具函数
- **NProgress** - 进度条

---

## 📁 项目结构

```
frontend/
├── src/
│   ├── api/               # API 接口封装
│   ├── components/        # 可复用组件
│   ├── layouts/           # 布局组件
│   ├── router/            # 路由配置
│   ├── stores/            # Pinia 状态管理
│   ├── styles/            # 全局样式
│   ├── types/             # TypeScript 类型
│   ├── utils/             # 工具函数
│   ├── views/             # 页面组件
│   ├── App.vue            # 根组件
│   └── main.ts            # 应用入口
├── public/                # 静态资源
├── .env                   # 环境变量（基础配置）
├── .env.development       # 开发环境配置
├── .env.production        # 生产环境配置
├── vite.config.ts         # Vite 配置
├── tailwind.config.js     # Tailwind 配置
├── tsconfig.json          # TypeScript 配置
└── package.json           # 项目依赖

自动生成文件（不提交 Git）：
├── auto-imports.d.ts      # 自动导入类型声明
├── components.d.ts        # 组件类型声明
└── dist/                  # 构建产物
```

---

## 🚀 快速开始

### 环境要求

- Node.js >= 18.0.0
- npm >= 8.0.0

### 安装与运行

```bash
# 1. 安装依赖
npm install

# 2. 启动开发服务器（http://localhost:5173）
npm run dev

# 3. 构建生产版本
npm run build

# 4. 预览生产构建
npm run preview
```

### 常用命令

```bash
# 代码检查和格式化
npm run lint              # ESLint 检查
npm run format            # Prettier 格式化
npm run type-check        # TypeScript 类型检查

# 测试
npm run test              # 运行单元测试
npm run test:coverage     # 测试覆盖率
npm run test:ui           # 测试 UI
```

---

## 🔧 开发配置

### 环境变量

项目使用 Vite 的多环境配置：

| 文件               | 说明     | 使用场景        |
| ------------------ | -------- | --------------- |
| `.env`             | 基础配置 | 所有环境共享    |
| `.env.development` | 开发配置 | `npm run dev`   |
| `.env.production`  | 生产配置 | `npm run build` |

**关键变量：**

```bash
VITE_API_BASE_URL=/api/v1          # API 基础路径
VITE_APP_NAME=五好伴学              # 应用名称
VITE_ENABLE_DEBUG=true/false       # 调试模式
```

### API 代理

开发环境下，Vite 自动代理 API 请求到后端（`http://localhost:8000`），避免 CORS 问题。

配置在 `vite.config.ts`：

```typescript
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true,
    }
  }
}
```

---

## 📦 功能模块

| 模块        | 功能                   | 路由         |
| ----------- | ---------------------- | ------------ |
| 🏠 仪表盘   | 学习数据概览、快速入口 | `/dashboard` |
| 📝 作业批改 | AI 智能批改、历史记录  | `/homework`  |
| 💬 学习问答 | 智能对话、会话管理     | `/qa`        |
| 📊 学情分析 | 进度统计、趋势分析     | `/analytics` |
| 📁 文件管理 | 云端文件存储           | `/files`     |
| ⚙️ 设置中心 | 个人资料、安全配置     | `/settings`  |
| 🔧 系统管理 | 用户管理（管理员）     | `/admin`     |

---

## 🎨 架构特点

### 类型安全

- 全面的 TypeScript 类型定义
- 自动导入的类型支持（auto-imports.d.ts）
- 严格模式（`strict: true`）

### 性能优化

- ✅ 路由懒加载
- ✅ 组件按需加载
- ✅ Tree Shaking
- ✅ 代码分割
- ✅ 静态资源缓存

### 开发体验

- ✅ 热模块替换（HMR）
- ✅ 自动导入 Vue/Router/Pinia API
- ✅ 组件自动注册
- ✅ 开发调试面板

### 安全性

- ✅ JWT Token 认证
- ✅ 请求/响应拦截器
- ✅ CSP 安全策略

---

## 📐 代码规范

### 命名约定

| 类型 | 规则             | 示例              |
| ---- | ---------------- | ----------------- |
| 组件 | PascalCase       | `UserProfile.vue` |
| 文件 | kebab-case       | `user-profile.ts` |
| 函数 | camelCase        | `getUserInfo()`   |
| 常量 | UPPER_SNAKE_CASE | `API_BASE_URL`    |

### Git 提交规范

使用 Conventional Commits：

```
feat(component): 添加用户头像组件
fix(api): 修复登录超时问题
docs(readme): 更新开发文档
refactor(store): 重构用户状态管理
test(utils): 添加日期工具测试
chore(deps): 升级 Vue 到 3.4.21
```

---

## 🚢 部署指南

### 构建生产版本

```bash
# 构建（输出到 dist/）
npm run build

# 检查构建产物大小
ls -lh dist/
```

### 部署到生产环境

生产环境使用 Nginx 提供静态文件服务，配置已在 `/nginx/conf.d/wuhao-tutor.conf`：

```nginx
# 前端静态文件
location / {
    root /var/www/wuhao-tutor/frontend/dist;
    try_files $uri $uri/ /index.html;
}

# API 代理到后端
location /api/ {
    proxy_pass http://127.0.0.1:8000;
}
```

**部署步骤：**

```bash
# 1. 本地构建
npm run build

# 2. 同步到服务器（在项目根目录）
./scripts/deploy-to-production.sh

# 3. 验证部署
./scripts/verify_deployment.sh
```

---

## 🐛 故障排查

### 常见问题

**依赖安装失败：**

```bash
rm -rf node_modules package-lock.json
npm install
```

**类型检查错误：**

```bash
npm run type-check
# 检查 auto-imports.d.ts 和 components.d.ts 是否生成
```

**热更新不工作：**

```bash
# 重启开发服务器
npm run dev
```

**API 请求 CORS 错误：**

- 确认后端服务已启动（`http://localhost:8000`）
- 检查 `vite.config.ts` 的 proxy 配置
- 查看浏览器 Network 面板

### 调试工具

- **Vue DevTools** - 浏览器扩展，调试组件状态
- **Vite DevTools** - 内置开发面板
- **Console 日志** - `VITE_ENABLE_DEBUG=true` 启用详细日志
- **Network 面板** - 检查 API 请求和响应

---

## 📚 相关文档

- **项目主文档**: `/README.md`
- **API 文档**: `/docs/api/`
- **架构文档**: `/docs/architecture/`
- **部署文档**: `/docs/deployment/`
- **开发指南**: `/docs/development/`

---

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'feat(component): add amazing feature'`)
4. 推送分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

---

## 📝 更新日志

- **2025-10-09**: 清理临时文件，优化文档结构
- **2025-10-08**: 生产环境部署完成
- **2025-09-28**: 完成核心功能开发
- **2025-09-15**: 项目初始化

---

**最后更新**: 2025-10-09  
**维护者**: 五好伴学开发团队

🎉 欢迎使用五好伴学前端项目！如有问题，请查阅 `/docs/` 或提交 Issue。
