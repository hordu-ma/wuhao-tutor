# 五好伴学 - 项目文档中心

> **📚 Documentation Hub**  
> 最后更新: 2025-10-09  
> 文档已完成系统清理，移除过时内容，优化结构

---

## 📖 文档目录结构

```
docs/
├── api/              # 🔌 API 接口文档
├── architecture/     # 🏗️ 系统架构设计
├── deployment/       # 🚀 生产部署指南
├── development/      # 💻 开发规划文档
├── guide/            # 📖 开发使用指南
├── integration/      # 🔗 前端和小程序集成
├── miniprogram/      # 📱 微信小程序专项
├── operations/       # ⚙️ 运维和清理文档
├── reference/        # 📚 参考资料
└── reports/          # 📊 项目报告和总结
```

---

## 🚀 快速导航

### 📌 核心文档（项目根目录）

- **[README.md](../README.md)** ⭐ - 项目概览、快速开始、核心特性
- **[AI-CONTEXT.md](../AI-CONTEXT.md)** ⭐ - AI 助手必读上下文、开发约定

---

## 📂 分类文档索引

### 🏗️ 架构设计 (architecture/)

| 文档                                      | 说明                           |
| ----------------------------------------- | ------------------------------ |
| [架构概览](architecture/overview.md)      | 四层架构设计、技术栈、设计原则 |
| [数据访问层](architecture/data-access.md) | Repository 模式、数据库设计    |
| [安全策略](architecture/security.md)      | JWT 认证、多维限流、安全措施   |
| [可观测性](architecture/observability.md) | 监控指标、日志策略、性能追踪   |

### 🔌 API 文档 (api/)

| 文档                            | 说明                       |
| ------------------------------- | -------------------------- |
| [API 概览](api/overview.md)     | RESTful 设计原则、认证机制 |
| [API 端点](api/endpoints.md)    | 完整接口列表和参数说明     |
| [数据模型](api/models.md)       | 请求响应结构定义           |
| [错误码](api/errors.md)         | 错误处理和状态码           |
| [JavaScript SDK](api/sdk-js.md) | 前端 TypeScript SDK        |
| [Python SDK](api/sdk-python.md) | Python 客户端 SDK          |

### 🚀 部署指南 (deployment/)

| 文档                                                             | 说明                         |
| ---------------------------------------------------------------- | ---------------------------- |
| [生产部署标准流程](deployment/production-deployment-guide.md) ⭐ | systemd + Nginx 部署完整流程 |
| [本地代码验证](deployment/local-code-verification.md)            | 部署前代码安全检查           |
| [RDS 数据库配置](deployment/RDS_CONNECTION_GUIDE.md)             | PostgreSQL 连接和配置        |
| [Redis 缓存配置](deployment/REDIS_CONNECTION_GUIDE.md)           | Redis 连接和使用             |
| [安全密钥管理](deployment/SECURITY_KEYS_GUIDE.md)                | API Key 和密钥配置           |

### 💻 开发规划 (development/)

| 文档                                                            | 说明                             |
| --------------------------------------------------------------- | -------------------------------- |
| [全链条开发补齐计划](development/COMPREHENSIVE_TODO_PLAN.md) ⭐ | 当前开发状态、任务规划、技术债务 |

### 📖 开发指南 (guide/)

| 文档                               | 说明                         |
| ---------------------------------- | ---------------------------- |
| [开发工作流](guide/development.md) | 环境搭建、开发流程、工具使用 |
| [测试指南](guide/testing.md)       | 测试策略、规范和最佳实践     |

### 🔗 集成指南 (integration/)

| 文档                                                | 说明                    |
| --------------------------------------------------- | ----------------------- |
| [前端集成](integration/frontend.md)                 | Vue3 集成方案、API 调用 |
| [微信小程序开发](integration/wechat-miniprogram.md) | 小程序架构和开发规范    |
| [微信认证集成](integration/wechat-auth.md)          | 微信登录和用户绑定      |

### 📱 小程序专项 (miniprogram/)

| 文档                                            | 说明                    |
| ----------------------------------------------- | ----------------------- |
| [API 集成](miniprogram/api-integration.md)      | 后端 API 对接和数据交互 |
| [网络架构](miniprogram/network-architecture.md) | 请求层、缓存、错误处理  |
| [用户角色系统](miniprogram/user-role-system.md) | 权限管理和角色设计      |

### ⚙️ 运维文档 (operations/)

| 文档                                                   | 说明                        |
| ------------------------------------------------------ | --------------------------- |
| [清理执行报告](operations/cleanup-execution-report.md) | 2025-10-09 环境清理完整记录 |
| [本地清理计划](operations/local-cleanup-plan.md)       | 本地开发环境清理方案        |
| [生产清理计划](operations/production-cleanup-plan.md)  | 生产服务器优化方案          |

### 📚 参考资料 (reference/)

| 文档                                    | 说明             |
| --------------------------------------- | ---------------- |
| [术语表](reference/glossary.md)         | 项目专业术语定义 |
| [学习指南](reference/learning-guide.md) | 技术栈学习资源   |

### 📊 项目报告 (reports/)

| 文档                                                                | 说明                        |
| ------------------------------------------------------------------- | --------------------------- |
| [部署后总结](reports/post-deployment-summary.md) ⭐                 | 2025-10-08 生产部署完整总结 |
| [作业 API 兼容性报告](reports/homework-api-compatibility-report.md) | API 重构兼容性分析          |
| [作业 API 重构总结](reports/homework-api-refactor-summary.md)       | 从硬编码到生产就绪          |

---

## � 场景化快速查找

### 🆕 新手入门路径

1. **[项目主页](../README.md)** - 了解项目概览和核心功能
2. **[架构概览](architecture/overview.md)** - 理解技术架构
3. **[开发工作流](guide/development.md)** - 搭建开发环境
4. **[API 概览](api/overview.md)** - 熟悉接口规范

### 💻 开发者工作流

1. **[开发工作流](guide/development.md)** - 环境配置和启动
2. **[API 端点](api/endpoints.md)** - 查看可用接口
3. **[测试指南](guide/testing.md)** - 编写和运行测试
4. **[AI-CONTEXT.md](../AI-CONTEXT.md)** - 了解开发约定

### 🎨 前端集成路径

1. **[前端集成](integration/frontend.md)** - Vue3 项目集成
2. **[API 端点](api/endpoints.md)** - 接口清单
3. **[JavaScript SDK](api/sdk-js.md)** - 使用前端 SDK
4. **[错误码](api/errors.md)** - 错误处理

### 📱 小程序开发路径

1. **[微信小程序开发](integration/wechat-miniprogram.md)** - 开发规范
2. **[API 集成](miniprogram/api-integration.md)** - 后端对接
3. **[网络架构](miniprogram/network-architecture.md)** - 网络层设计
4. **[用户角色系统](miniprogram/user-role-system.md)** - 权限管理

### 🚀 部署和运维路径

1. **[生产部署标准流程](deployment/production-deployment-guide.md)** ⭐ - 完整部署指南
2. **[RDS 数据库配置](deployment/RDS_CONNECTION_GUIDE.md)** - 数据库设置
3. **[安全密钥管理](deployment/SECURITY_KEYS_GUIDE.md)** - 密钥配置
4. **[生产清理计划](operations/production-cleanup-plan.md)** - 环境优化

---

## 📝 文档维护原则

### ✅ 保留标准

- **有价值**: 内容对开发、部署、运维有实际帮助
- **准确性**: 反映当前系统实际状态（systemd 部署，非 Docker）
- **时效性**: 信息是最新的，技术方案是当前使用的

### 🗑️ 清理标准

- **临时性**: 一次性任务文档（如问题修复记录）
- **过时性**: 引用已废弃技术（Docker Compose、Alembic）
- **重复性**: 内容已在其他文档中覆盖

### 📅 最近更新 (2025-10-09)

- ✅ 删除 `.dockerignore`（项目已不使用 Docker）
- ✅ 移动 6 个根目录文档到 docs 对应子目录
- ✅ 删除 8 个过时/临时文档：
  - `deployment/SSH_PASSPHRASE_HELP.md`
  - `deployment/DEPLOYMENT_INFO_FORM.md`
  - `deployment/SSH_KEY_SETUP.md`
  - `deployment/TEST_ACCOUNTS.md`
  - `guide/deployment.md` (过时的 Docker 部署)
  - `operations/database-migration.md` (过时的 Alembic 迁移)
  - `miniprogram/MINIPROGRAM_FIXES.md` (临时修复记录)
  - `reports/README.md` (空目录说明)
- ✅ 优化文档目录结构，清晰分类

---

## 🤝 贡献指南

### 新增文档时

1. 选择合适的目录（api/architecture/deployment 等）
2. 使用清晰的文件名（kebab-case）
3. 添加到本文档的对应索引中
4. 确保内容准确反映当前系统状态

### 更新文档时

1. 修改后更新"最后更新"日期
2. 如果涉及重大变更，在变更日志中记录
3. 确保引用的技术栈是当前使用的

### 删除文档时

1. 确认内容确实过时或无价值
2. 检查是否有其他文档引用
3. 在本文档中移除对应索引

---

**维护者**: Liguo Ma <maliguo@outlook.com>  
**最后清理**: 2025-10-09  
**文档总数**: 33 个（清理前 41 个，删除 8 个）  
**原则**: 保持简洁实用，及时更新，定期清理
