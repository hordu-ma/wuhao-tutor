# 五好伴学 - 项目文档

> **📚 文档中心**  
> 最后更新: 2025-10-05

---

## 📖 文档结构

```
docs/
├── api/              # 🔌 API 文档
├── architecture/     # 🏗️ 架构设计
├── guide/            # 📖 开发指南
├── integration/      # 🔗 集成指南
├── miniprogram/      # 📱 小程序文档
├── operations/       # ⚙️ 运维文档
└── reference/        # 📚 参考资料
```

---

## 🚀 快速导航

### 核心文档（项目根目录）
- **[README.md](../README.md)** ⭐ - 项目概览和快速开始
- **[AI-CONTEXT.md](../AI-CONTEXT.md)** ⭐ - AI 助手必读上下文
- **[NEXT_STEPS.md](../NEXT_STEPS.md)** - 下一步开发任务

### 架构设计
- [架构概览](architecture/overview.md) - 四层架构设计
- [数据访问层](architecture/data-access.md) - Repository 模式
- [安全策略](architecture/security.md) - 限流和安全措施
- [可观测性](architecture/observability.md) - 监控和日志

### 开发指南
- [开发工作流](guide/development.md) - 环境搭建和开发流程
- [测试指南](guide/testing.md) - 测试策略和规范
- [部署指南](guide/deployment.md) - Docker 部署流程

### API 文档
- [API 概览](api/overview.md) - 设计原则和认证
- [API 端点](api/endpoints.md) - 接口列表
- [数据模型](api/models.md) - 请求响应结构
- [错误码](api/errors.md) - 错误处理
- [JavaScript SDK](api/sdk-js.md) - 前端 SDK
- [Python SDK](api/sdk-python.md) - Python SDK

### 集成指南
- [前端集成](integration/frontend.md) - Vue3 集成方案
- [微信小程序](integration/wechat-miniprogram.md) - 小程序开发
- [微信认证](integration/wechat-auth.md) - 微信登录

### 小程序文档
- [API 集成](miniprogram/api-integration.md) - 后端 API 对接
- [网络架构](miniprogram/network-architecture.md) - 网络层设计
- [用户角色系统](miniprogram/user-role-system.md) - 权限管理
- [问题修复记录](miniprogram/MINIPROGRAM_FIXES.md) - 已修复问题

### 运维文档
- [数据库迁移](operations/database-migration.md) - Alembic 迁移管理

### 参考资料
- [术语表](reference/glossary.md) - 项目术语定义
- [学习指南](reference/learning-guide.md) - 技术学习资源
- [项目状态](reference/project-status.md) - 开发进度追踪

---

## 🎓 按场景查找

### 我是新手，想了解项目
1. [项目主页](../README.md) - 项目概览
2. [AI 助手上下文](../AI-CONTEXT.md) - 项目核心信息
3. [架构概览](architecture/overview.md) - 技术架构

### 我要开始开发
1. [开发工作流](guide/development.md) - 环境搭建
2. [API 概览](api/overview.md) - 接口规范
3. [测试指南](guide/testing.md) - 测试要求

### 我要集成前端
1. [前端集成](integration/frontend.md) - Vue3 方案
2. [API 端点](api/endpoints.md) - 接口列表
3. [微信小程序](integration/wechat-miniprogram.md) - 小程序开发

### 我要部署项目
1. [部署指南](guide/deployment.md) - 部署流程
2. [数据库迁移](operations/database-migration.md) - 数据库管理

---

**维护**: 保持文档简洁实用，过时文档及时归档或删除
