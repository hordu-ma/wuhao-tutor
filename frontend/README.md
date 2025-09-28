# 五好伴学前端项目

## 项目简介

五好伴学前端是一个基于 Vue 3 + TypeScript + Vite 的现代化前端应用，提供智能作业批改、学习问答和学情分析等功能。

## 技术栈

### 核心技术
- **Vue 3.4+** - 采用 Composition API
- **TypeScript 5.x** - 类型安全的 JavaScript 超集
- **Vite 5.x** - 快速的构建工具
- **Vue Router 4.x** - 官方路由管理
- **Pinia** - Vue 3 官方状态管理

### UI 和样式
- **Element Plus** - 企业级 UI 组件库
- **Tailwind CSS** - 原子化 CSS 框架
- **SCSS** - CSS 预处理器

### 工具和插件
- **Axios** - HTTP 客户端
- **Day.js** - 日期时间处理
- **Lodash-es** - 工具函数库
- **NProgress** - 页面加载进度条

### 开发工具
- **ESLint** - 代码检查
- **Prettier** - 代码格式化
- **Vitest** - 单元测试框架
- **Vue Test Utils** - Vue 组件测试工具

## 项目结构

```
frontend/
├── public/                 # 静态资源
├── src/
│   ├── api/               # API 接口封装
│   │   ├── http.ts        # HTTP 客户端配置
│   │   └── auth.ts        # 认证相关 API
│   ├── components/        # 可复用组件
│   ├── layouts/           # 布局组件
│   │   ├── MainLayout.vue # 主布局
│   │   └── BlankLayout.vue# 空白布局
│   ├── router/            # 路由配置
│   │   └── index.ts       # 路由主配置
│   ├── stores/            # 状态管理
│   │   └── auth.ts        # 用户认证状态
│   ├── styles/            # 样式文件
│   │   ├── index.css      # 主样式文件
│   │   ├── tailwind.css   # Tailwind 配置
│   │   └── element-plus.scss # Element Plus 自定义样式
│   ├── types/             # TypeScript 类型定义
│   │   └── index.ts       # 全局类型定义
│   ├── utils/             # 工具函数
│   ├── views/             # 页面组件
│   ├── App.vue            # 根组件
│   └── main.ts            # 应用入口
├── .env                   # 环境变量（通用）
├── .env.development       # 开发环境变量
├── .gitignore             # Git 忽略文件
├── index.html             # HTML 模板
├── package.json           # 项目依赖配置
├── tailwind.config.js     # Tailwind 配置
├── tsconfig.json          # TypeScript 配置
├── vite.config.ts         # Vite 配置
└── README.md              # 项目说明文档
```

## 功能模块

### 🏠 仪表盘
- 学习数据概览
- 快速功能入口
- 最近活动展示

### 📝 作业批改
- 作业提交
- AI 智能批改
- 批改结果查看
- 作业历史记录

### 💬 学习问答
- 智能问答对话
- 问答会话管理
- 历史记录查看
- 多媒体支持

### 📊 学情分析
- 学习进度统计
- 成绩趋势分析
- 错题分析报告
- 学习建议推荐

### 📁 文件管理
- 文件上传下载
- 文件分类管理
- 云端同步

### ⚙️ 设置中心
- 个人资料管理
- 安全设置
- 偏好配置

### 🔧 系统管理（管理员）
- 用户管理
- 系统配置
- 日志查看

## 开发指南

### 环境要求
- Node.js >= 18.0.0
- npm >= 8.0.0

### 安装依赖

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install
```

### 开发模式

```bash
# 启动开发服务器
npm run dev

# 应用将在 http://localhost:3000 启动
```

### 构建部署

```bash
# 构建生产版本
npm run build

# 预览生产构建
npm run preview
```

### 代码检查

```bash
# ESLint 检查
npm run lint

# 代码格式化
npm run format

# 类型检查
npm run type-check
```

### 测试

```bash
# 运行单元测试
npm run test

# 测试覆盖率
npm run test:coverage

# 测试 UI
npm run test:ui
```

## 环境配置

### 开发环境变量

创建 `.env.development` 文件：

```bash
# API 配置
VITE_API_BASE_URL=http://localhost:8000/api/v1

# 应用配置
VITE_APP_NAME=五好伴学
VITE_APP_VERSION=1.0.0

# 功能开关
VITE_ENABLE_MOCK=false
VITE_ENABLE_DEBUG=true
```

### API 代理配置

开发环境下，API 请求会自动代理到后端服务器（默认 http://localhost:8000）。

## 架构特点

### 🎯 类型安全
- 全面的 TypeScript 类型定义
- 严格的类型检查
- 智能代码提示

### 🔒 安全性
- JWT Token 认证
- 请求拦截和响应处理
- CSP 安全策略

### 📱 响应式设计
- 移动端适配
- 断点式布局
- 触摸友好的交互

### 🚀 性能优化
- 路由懒加载
- 组件按需加载
- Tree Shaking
- 代码分割

### 🛠️ 开发体验
- 热模块替换（HMR）
- 自动导入
- 组件自动注册
- 开发调试面板

## 代码规范

### 命名约定
- 组件名：PascalCase（如 `UserProfile.vue`）
- 文件名：kebab-case（如 `user-profile.ts`）
- 函数名：camelCase（如 `getUserInfo`）
- 常量名：UPPER_SNAKE_CASE（如 `API_BASE_URL`）

### 目录结构
- 按功能模块组织代码
- 公共组件放在 `components` 目录
- 页面组件放在 `views` 目录
- 工具函数放在 `utils` 目录

### 提交规范
使用 Conventional Commits 规范：
- `feat:` 新功能
- `fix:` 问题修复
- `docs:` 文档更新
- `style:` 代码格式调整
- `refactor:` 代码重构
- `test:` 测试相关
- `chore:` 构建过程或辅助工具的变动

## 部署指南

### 构建配置
```bash
# 生产环境构建
npm run build

# 构建产物在 dist/ 目录
```

### Nginx 配置示例
```nginx
server {
    listen 80;
    server_name your-domain.com;
    root /path/to/dist;
    index index.html;

    # 处理 Vue Router 的 history 模式
    location / {
        try_files $uri $uri/ /index.html;
    }

    # 静态资源缓存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

### Docker 部署
```dockerfile
FROM nginx:alpine
COPY dist/ /usr/share/nginx/html/
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

## 故障排查

### 常见问题

1. **依赖安装失败**
   ```bash
   # 清理缓存重新安装
   rm -rf node_modules package-lock.json
   npm install
   ```

2. **类型检查错误**
   ```bash
   # 重新生成类型文件
   npm run type-check
   ```

3. **热更新不工作**
   - 检查 Vite 配置
   - 重启开发服务器

4. **API 请求失败**
   - 确认后端服务已启动
   - 检查代理配置
   - 查看网络面板

### 调试技巧

- 使用 Vue DevTools 调试组件状态
- 启用开发模式调试面板
- 查看浏览器控制台错误信息
- 使用 Network 面板检查 API 请求

## 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'feat: add amazing feature'`)
4. 推送分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 联系我们

- 项目地址：https://github.com/your-org/wuhao-tutor
- 问题反馈：https://github.com/your-org/wuhao-tutor/issues
- 邮箱：support@wuhao-tutor.com

---

🎉 感谢使用五好伴学前端项目！如有任何问题，欢迎提交 Issue 或 PR。
