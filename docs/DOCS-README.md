# 五好伴学 - 项目文档中心# 五好伴学 - 项目文档中心

> **Documentation Hub** > **📚 Documentation Hub**

> 最后更新: 2025-10-12 > 最后更新: 2025-10-09

> 文档已完成全面重组,反映当前项目实际状态> 文档已完成系统清理，移除过时内容，优化结构

---

## 📖 文档目录结构## 📖 文档目录结构

````

docs/docs/

├── api/              # 🔌 API 接口文档├── api/              # 🔌 API 接口文档

├── architecture/     # 🏗️ 系统架构设计├── architecture/     # 🏗️ 系统架构设计

├── deployment/       # 🚀 生产部署指南├── deployment/       # 🚀 生产部署指南

├── fixes/            # 🔧 Bug 修复记录├── development/      # 💻 开发规划文档

├── frontend/         # 🎨 前端开发文档├── guide/            # 📖 开发使用指南

├── guide/            # 📖 开发使用指南├── integration/      # 🔗 前端和小程序集成

├── integration/      # 🔗 前端和小程序集成├── miniprogram/      # 📱 微信小程序专项

├── miniprogram/      # 📱 微信小程序专项├── operations/       # ⚙️ 运维和清理文档

├── operations/       # ⚙️ 运维和清理文档├── reference/        # 📚 参考资料

├── reference/        # 📚 参考资料└── reports/          # 📊 项目报告和总结

└── reports/          # 📊 项目报告和总结```

```

---

---

## 🚀 快速导航

## 🚀 快速导航

### 📌 核心文档（项目根目录）

### 📌 核心文档 (项目根目录)

- **[README.md](../README.md)** ⭐ - 项目概览、快速开始、核心特性

- **[README.md](../README.md)** ⭐ - 项目概览、快速开始、核心特性- **[AI-CONTEXT.md](../AI-CONTEXT.md)** ⭐ - AI 助手必读上下文、开发约定

- **[DEVELOPMENT_ROADMAP.md](../DEVELOPMENT_ROADMAP.md)** ⭐ - 开发路线图和未来规划

- **[AI-CONTEXT.md](../AI-CONTEXT.md)** - AI 助手必读上下文、开发约定---

- **[.github/copilot-instructions.md](../.github/copilot-instructions.md)** - GitHub Copilot 使用规范

## 📂 分类文档索引

---

### 🏗️ 架构设计 (architecture/)

## 📂 分类文档索引

| 文档                                      | 说明                           |

### 🏗️ 架构设计 (architecture/)| ----------------------------------------- | ------------------------------ |

| [架构概览](architecture/overview.md)      | 四层架构设计、技术栈、设计原则 |

| 文档 | 说明 | 更新时间 || [数据访问层](architecture/data-access.md) | Repository 模式、数据库设计    |

|------|------|----------|| [安全策略](architecture/security.md)      | JWT 认证、多维限流、安全措施   |

| [架构概览](architecture/overview.md) | 四层架构设计、技术栈、设计原则 | 2025-09 || [可观测性](architecture/observability.md) | 监控指标、日志策略、性能追踪   |

| [数据访问层](architecture/data-access.md) | Repository 模式、数据库设计 | 2025-09 |

| [安全策略](architecture/security.md) | JWT 认证、多维限流、安全措施 | 2025-09 |### 🔌 API 文档 (api/)

| [可观测性](architecture/observability.md) | 监控指标、日志策略、性能追踪 | 2025-09 |

| 文档                            | 说明                       |

**状态**: ✅ 核心架构文档完整,需要定期更新以反映最新实现| ------------------------------- | -------------------------- |

| [API 概览](api/overview.md)     | RESTful 设计原则、认证机制 |

### 🔌 API 文档 (api/)| [API 端点](api/endpoints.md)    | 完整接口列表和参数说明     |

| [数据模型](api/models.md)       | 请求响应结构定义           |

| 文档 | 说明 | 状态 || [错误码](api/errors.md)         | 错误处理和状态码           |

|------|------|------|| [JavaScript SDK](api/sdk-js.md) | 前端 TypeScript SDK        |

| [API 概览](api/overview.md) | RESTful 设计原则、认证机制 | ✅ 有效 || [Python SDK](api/sdk-python.md) | Python 客户端 SDK          |

| [API 端点](api/endpoints.md) | 完整接口列表和参数说明 | ⚠️ 需要更新为当前实现 |

| [数据模型](api/models.md) | 请求响应结构定义 | ✅ 有效 |### 🚀 部署指南 (deployment/)

| [错误码](api/errors.md) | 错误处理和状态码 | ✅ 有效 |

| [JavaScript SDK](api/sdk-js.md) | 前端 TypeScript SDK | ⚠️ 需要验证 || 文档                                                             | 说明                         |

| [Python SDK](api/sdk-python.md) | Python 客户端 SDK | ⚠️ 需要验证 || ---------------------------------------------------------------- | ---------------------------- |

| [生产部署标准流程](deployment/production-deployment-guide.md) ⭐ | systemd + Nginx 部署完整流程 |

**待更新**: `endpoints.md` 需要反映当前已实现的 API (Learning, Mistakes, Analytics, Goals)| [本地代码验证](deployment/local-code-verification.md)            | 部署前代码安全检查           |

| [RDS 数据库配置](deployment/RDS_CONNECTION_GUIDE.md)             | PostgreSQL 连接和配置        |

### 🚀 部署指南 (deployment/)| [Redis 缓存配置](deployment/REDIS_CONNECTION_GUIDE.md)           | Redis 连接和使用             |

| [安全密钥管理](deployment/SECURITY_KEYS_GUIDE.md)                | API Key 和密钥配置           |

| 文档 | 说明 | 状态 |

|------|------|------|### 💻 开发规划 (development/)

| [生产部署标准流程](deployment/production-deployment-guide.md) ⭐ | systemd + Nginx 部署完整流程 | ✅ 已更新 |

| [本地代码验证](deployment/local-code-verification.md) | 部署前代码安全检查 | ✅ 有效 || 文档                                                            | 说明                             |

| [RDS 数据库配置](deployment/RDS_CONNECTION_GUIDE.md) | PostgreSQL 连接和配置 | ✅ 有效 || --------------------------------------------------------------- | -------------------------------- |

| [Redis 缓存配置](deployment/REDIS_CONNECTION_GUIDE.md) | Redis 连接和使用 | ✅ 有效 || [全链条开发补齐计划](development/COMPREHENSIVE_TODO_PLAN.md) ⭐ | 当前开发状态、任务规划、技术债务 |

| [安全密钥管理](deployment/SECURITY_KEYS_GUIDE.md) | API Key 和密钥配置 | ✅ 有效 |

### 📖 开发指南 (guide/)

**状态**: ✅ 部署文档完整且最新,已验证生产环境可用

| 文档                               | 说明                         |

### 📖 开发指南 (guide/)| ---------------------------------- | ---------------------------- |

| [开发工作流](guide/development.md) | 环境搭建、开发流程、工具使用 |

| 文档 | 说明 | 状态 || [测试指南](guide/testing.md)       | 测试策略、规范和最佳实践     |

|------|------|------|

| [开发工作流](guide/development.md) | 环境搭建、开发流程、工具使用 | ⚠️ 需要更新 uv 使用说明 |### 🔗 集成指南 (integration/)

| [测试指南](guide/testing.md) | 测试策略、规范和最佳实践 | ✅ 有效 |

| 文档                                                | 说明                    |

**待补充**: 添加错题手册、RAG 等新功能的开发指南| --------------------------------------------------- | ----------------------- |

| [前端集成](integration/frontend.md)                 | Vue3 集成方案、API 调用 |

### 🔗 集成指南 (integration/)| [微信小程序开发](integration/wechat-miniprogram.md) | 小程序架构和开发规范    |

| [微信认证集成](integration/wechat-auth.md)          | 微信登录和用户绑定      |

| 文档 | 说明 | 状态 |

|------|------|------|### 📱 小程序专项 (miniprogram/)

| [前端集成](integration/frontend.md) | Vue3 集成方案、API 调用 | ⚠️ 需要更新为 Pinia 模式 |

| [微信小程序开发](integration/wechat-miniprogram.md) | 小程序架构和开发规范 | 🔜 规划中 || 文档                                            | 说明                    |

| [微信认证集成](integration/wechat-auth.md) | 微信登录和用户绑定 | 🔜 规划中 || ----------------------------------------------- | ----------------------- |

| [API 集成](miniprogram/api-integration.md)      | 后端 API 对接和数据交互 |

**状态**: 前端集成文档需要更新,小程序文档待后续开发时补充| [网络架构](miniprogram/network-architecture.md) | 请求层、缓存、错误处理  |

| [用户角色系统](miniprogram/user-role-system.md) | 权限管理和角色设计      |

### 🎨 前端开发 (frontend/)

### ⚙️ 运维文档 (operations/)

| 文档 | 说明 | 状态 |

|------|------|------|| 文档                                                   | 说明                        |

| [前端 README](../frontend/FRONTEND-README.md) | 前端项目说明 | ✅ 有效 || ------------------------------------------------------ | --------------------------- |

| [Pinia 状态管理](../frontend/src/stores/) | 状态管理实现 | ✅ 代码即文档 || [清理执行报告](operations/cleanup-execution-report.md) | 2025-10-09 环境清理完整记录 |

| [组件库](../frontend/src/components/) | 可复用组件 | ✅ 代码即文档 || [本地清理计划](operations/local-cleanup-plan.md)       | 本地开发环境清理方案        |

| [生产清理计划](operations/production-cleanup-plan.md)  | 生产服务器优化方案          |

**状态**: 前端项目结构清晰,代码注释完善,暂不需要额外文档

### 📚 参考资料 (reference/)

### 📱 小程序专项 (miniprogram/)

| 文档                                    | 说明             |

| 文档 | 说明 | 状态 || --------------------------------------- | ---------------- |

|------|------|------|| [术语表](reference/glossary.md)         | 项目专业术语定义 |

| [API 集成](miniprogram/api-integration.md) | 后端 API 对接和数据交互 | 🔜 Phase 4 规划 || [学习指南](reference/learning-guide.md) | 技术栈学习资源   |

| [网络架构](miniprogram/network-architecture.md) | 请求层、缓存、错误处理 | 🔜 Phase 4 规划 |

| [用户角色系统](miniprogram/user-role-system.md) | 权限管理和角色设计 | 🔜 Phase 4 规划 |### 📊 项目报告 (reports/)



**状态**: 小程序开发计划在 Phase 4 (2026 Q1-Q2),文档待开发时补充| 文档                                                                | 说明                        |

| ------------------------------------------------------------------- | --------------------------- |

### ⚙️ 运维文档 (operations/)| [部署后总结](reports/post-deployment-summary.md) ⭐                 | 2025-10-08 生产部署完整总结 |

| [作业 API 兼容性报告](reports/homework-api-compatibility-report.md) | API 重构兼容性分析          |

| 文档 | 说明 | 状态 || [作业 API 重构总结](reports/homework-api-refactor-summary.md)       | 从硬编码到生产就绪          |

|------|------|------|

| [数据库清理计划](operations/database-cleanup-plan.md) | 数据归档和清理策略 | ✅ 有效 |---

| [日志管理](operations/logging.md) | 日志收集和分析 | ⚠️ 需要补充 ELK 集成 |

| [监控告警](operations/monitoring.md) | Prometheus + Grafana 配置 | ⚠️ 需要补充实际部署步骤 |## � 场景化快速查找



**待完善**: 生产环境监控和告警系统配置文档### 🆕 新手入门路径



### 🔧 Bug 修复记录 (fixes/)1. **[项目主页](../README.md)** - 了解项目概览和核心功能

2. **[架构概览](architecture/overview.md)** - 理解技术架构

| 文档 | 说明 | 日期 |3. **[开发工作流](guide/development.md)** - 搭建开发环境

|------|------|------|4. **[API 概览](api/overview.md)** - 熟悉接口规范

| [Enum 字符串修复](fixes/2025-10-11-enum-string-fix.md) | 修复枚举类型序列化问题 | 2025-10-11 |

| [头像上传修复](fixes/2025-10-12-avatar-upload-fix.md) | Pinia 响应式 + Nginx 配置 | 2025-10-12 |### 💻 开发者工作流



**用途**: 记录重要 Bug 修复过程,便于后续查阅和学习1. **[开发工作流](guide/development.md)** - 环境配置和启动

2. **[API 端点](api/endpoints.md)** - 查看可用接口

### 📊 项目报告 (reports/)3. **[测试指南](guide/testing.md)** - 编写和运行测试

4. **[AI-CONTEXT.md](../AI-CONTEXT.md)** - 了解开发约定

| 文档 | 说明 | 状态 |

|------|------|------|### 🎨 前端集成路径

| [Learning 500 错误修复](reports/FIX_LEARNING_500_ERROR_2025-10-11.md) | MCP 集成错误排查 | ✅ 已归档 |

| [UI 增强报告](reports/UI_ENHANCEMENT_INPUT_AREA_2025-10-11.md) | 输入区域优化 | ✅ 已归档 |1. **[前端集成](integration/frontend.md)** - Vue3 项目集成

| [Homework API 兼容性](reports/homework-api-compatibility-report.md) | API 重构兼容性分析 | ✅ 已归档 |2. **[API 端点](api/endpoints.md)** - 接口清单

| [Homework API 重构总结](reports/homework-api-refactor-summary.md) | 重构成果总结 | ✅ 已归档 |3. **[JavaScript SDK](api/sdk-js.md)** - 使用前端 SDK

| [错题手册实现报告](reports/mistake-notebook-implementation.md) | 前端组件实现记录 | ✅ 已归档 |4. **[错误码](api/errors.md)** - 错误处理

| [部署后总结](reports/post-deployment-summary.md) | 生产部署经验总结 | ✅ 已归档 |

| [VL 模型修复](reports/vl-model-fix-report.md) | 视觉语言模型问题修复 | ✅ 已归档 |### 📱 小程序开发路径



**用途**: 历史记录和经验总结,供后续参考1. **[微信小程序开发](integration/wechat-miniprogram.md)** - 开发规范

2. **[API 集成](miniprogram/api-integration.md)** - 后端对接

### 📚 参考资料 (reference/)3. **[网络架构](miniprogram/network-architecture.md)** - 网络层设计

4. **[用户角色系统](miniprogram/user-role-system.md)** - 权限管理

| 文档 | 说明 | 状态 |

|------|------|------|### 🚀 部署和运维路径

| [知识图谱设计](reference/knowledge-graph.md) | 知识图谱结构和关系定义 | ⚠️ 需要扩展 |

| [AI Prompt 模板](reference/prompt-templates.md) | 常用 Prompt 设计模式 | ⚠️ 需要补充 |1. **[生产部署标准流程](deployment/production-deployment-guide.md)** ⭐ - 完整部署指南

| [数据库 Schema](reference/database-schema.md) | 完整数据库表结构 | ⚠️ 需要更新 |2. **[RDS 数据库配置](deployment/RDS_CONNECTION_GUIDE.md)** - 数据库设置

3. **[安全密钥管理](deployment/SECURITY_KEYS_GUIDE.md)** - 密钥配置

**待补充**: 随着项目发展持续补充参考资料4. **[生产清理计划](operations/production-cleanup-plan.md)** - 环境优化



------



## 🎯 文档维护指南## 📝 文档维护原则



### 文档更新原则### ✅ 保留标准



1. **及时性**: 代码变更后立即更新相关文档- **有价值**: 内容对开发、部署、运维有实际帮助

2. **准确性**: 文档内容必须与实际代码一致- **准确性**: 反映当前系统实际状态（systemd 部署，非 Docker）

3. **完整性**: 重要功能必须有完整的文档说明- **时效性**: 信息是最新的，技术方案是当前使用的

4. **可读性**: 使用清晰的语言和示例代码

### 🗑️ 清理标准

### 文档分类标准

- **临时性**: 一次性任务文档（如问题修复记录）

- **✅ 有效**: 内容准确,无需更新- **过时性**: 引用已废弃技术（Docker Compose、Alembic）

- **⚠️ 需要更新**: 内容部分过时,需要修订- **重复性**: 内容已在其他文档中覆盖

- **🔜 规划中**: 功能未实现,文档待补充

- **🗑️ 已废弃**: 内容完全过时,可以删除### 📅 最近更新 (2025-10-09)



### 文档审查周期- ✅ 删除 `.dockerignore`（项目已不使用 Docker）

- ✅ 移动 6 个根目录文档到 docs 对应子目录

- **核心文档** (README, ROADMAP): 每月审查- ✅ 删除 8 个过时/临时文档：

- **API 文档**: 每次 API 变更后更新  - `deployment/SSH_PASSPHRASE_HELP.md`

- **部署文档**: 每次部署流程变更后更新  - `deployment/DEPLOYMENT_INFO_FORM.md`

- **开发指南**: 每季度审查  - `deployment/SSH_KEY_SETUP.md`

  - `deployment/TEST_ACCOUNTS.md`

---  - `guide/deployment.md` (过时的 Docker 部署)

  - `operations/database-migration.md` (过时的 Alembic 迁移)

## 📝 文档贡献  - `miniprogram/MINIPROGRAM_FIXES.md` (临时修复记录)

  - `reports/README.md` (空目录说明)

### 新增文档流程- ✅ 优化文档目录结构，清晰分类



1. 在对应目录创建 Markdown 文件---

2. 遵循项目文档模板格式

3. 在本文件中添加索引链接## 🤝 贡献指南

4. 提交 PR 并 @文档维护者

### 新增文档时

### 文档模板

1. 选择合适的目录（api/architecture/deployment 等）

```markdown2. 使用清晰的文件名（kebab-case）

# 文档标题3. 添加到本文档的对应索引中

4. 确保内容准确反映当前系统状态

> **最后更新**: YYYY-MM-DD

> **维护者**: @username### 更新文档时



## 概述1. 修改后更新"最后更新"日期

2. 如果涉及重大变更，在变更日志中记录

[简要说明文档目的和适用场景]3. 确保引用的技术栈是当前使用的



## 详细内容### 删除文档时



[具体内容]1. 确认内容确实过时或无价值

2. 检查是否有其他文档引用

## 参考链接3. 在本文档中移除对应索引



- [相关文档链接]---



---**维护者**: Liguo Ma <maliguo@outlook.com>

**最后清理**: 2025-10-09

最后更新: YYYY-MM-DD**文档总数**: 33 个（清理前 41 个，删除 8 个）

```**原则**: 保持简洁实用，及时更新，定期清理


---

## 🔍 快速查找

### 我想了解...

- **项目整体情况** → [README.md](../README.md)
- **如何部署到生产环境** → [生产部署指南](deployment/production-deployment-guide.md)
- **如何配置开发环境** → [开发工作流](guide/development.md)
- **API 接口如何调用** → [API 端点](api/endpoints.md)
- **系统架构设计** → [架构概览](architecture/overview.md)
- **下一步开发什么** → [开发路线图](../DEVELOPMENT_ROADMAP.md)
- **如何贡献代码** → [README.md - 贡献指南](../README.md#🤝-贡献指南)

### 我遇到问题...

- **部署失败** → [本地代码验证](deployment/local-code-verification.md)
- **API 错误** → [错误码文档](api/errors.md)
- **性能问题** → [可观测性文档](architecture/observability.md)
- **数据库问题** → [数据访问层文档](architecture/data-access.md)

---

## 📞 联系方式

- **问题反馈**: [GitHub Issues](https://github.com/hordu-ma/wuhao-tutor/issues)
- **文档建议**: 在对应文档下提 Issue
- **紧急问题**: 联系项目维护者

---

<div align="center">

**文档即代码,让项目更易维护**

最后更新: 2025-10-12 by hordu-ma

</div>
````
