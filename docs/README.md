# 五好伴学项目文档导航

> **📚 项目文档中心**  
> 本文档提供项目所有文档的导航和快速访问

**最后更新**: 2025-10-05  
**文档版本**: v3.1  
**项目阶段**: Phase 4 (生产部署优化)

---

## 🎯 快速开始

### 新手入门（推荐顺序）

1. 阅读 [项目主页](../README.md) - 了解项目概况和当前状态
2. 查看 [AI 助手上下文](../AI-CONTEXT.md) - AI 开发助手必读
3. 阅读 [Warp AI 指南](../WARP.md) - Warp 终端开发指导
4. 参考 [开发指南](guide/development.md) - 完整开发工作流

### 开发者快速参考

1. **架构与设计**: [系统架构](architecture/overview.md) - 了解四层设计
2. **API 文档**: [API 概览](api/overview.md) - 接口规范和示例
3. **测试指南**: [测试策略](guide/testing.md) - 测试要求和最佳实践
4. **项目状态**: [当前状态](reference/project-status.md) - 最新开发进度

---

## 📁 文档结构

```
docs/
├── README.md                      # 📚 本文档（导航中心）
│
├── PROJECT_DEVELOPMENT_STATUS.md  # ⭐ 项目开发状况深度分析
├── FRONTEND_REFACTOR_SUMMARY.md   # 🎨 前端重构总结
│
├── guide/                         # 📖 开发指南
│   ├── development.md            # 开发工作流和最佳实践
│   ├── testing.md                # 测试策略和规范
│   ├── deployment.md             # 部署指南
│   └── MATH_FORMULA_TEST.md      # 数学公式测试指南 (KaTeX)
│
├── architecture/                  # 🏗️ 架构设计
│   ├── overview.md               # 架构概览（四层设计）
│   ├── data-access.md            # 数据访问层
│   ├── security.md               # 安全策略
│   └── observability.md          # 可观测性（监控、日志）
│
├── api/                          # 🔌 API文档
│   ├── overview.md               # API设计原则和认证
│   ├── endpoints.md              # 端点列表和说明
│   ├── models.md                 # 数据模型
│   ├── errors.md                 # 错误码定义
│   ├── sdk-js.md                 # JavaScript SDK
│   └── sdk-python.md             # Python SDK
│
├── integration/                  # 🔗 集成指南
│   ├── frontend.md               # 前端集成
│   ├── wechat-miniprogram.md     # 微信小程序开发
│   └── wechat-auth.md            # 微信认证实现
│
├── miniprogram/                  # 📱 小程序专项文档
│   ├── api-integration.md        # 小程序 API 集成
│   ├── network-architecture.md   # 小程序网络架构
│   └── user-role-system.md       # 小程序用户角色系统
│
├── operations/                   # ⚙️ 运维文档
│   └── database-migration.md     # 数据库迁移管理
│
├── reference/                    # 📚 参考文档
│   ├── glossary.md               # 术语表
│   ├── learning-guide.md         # 学习指南
│   └── project-status.md         # 项目状态
│
├── history/                      # 🗄️ 历史文档
│   ├── LOGIN_DEBUG.md            # 登录调试记录
│   ├── phase1/                   # Phase 1: 核心功能打通
│   ├── phase2/                   # Phase 2: 数据持久化完善
│   └── phase3/                   # Phase 3: API集成测试
│
├── reports/                      # 📊 技术报告
│   ├── LOGIN_FIX_SUMMARY.md      # 登录修复总结
│   ├── DOCUMENTATION_REORGANIZATION_COMPLETE.md  # 文档重组报告
│   ├── DOCUMENTATION_ORGANIZATION_SUMMARY.md     # 文档整理总结
│   ├── api_alignment_report.json          # API对接报告
│   ├── backend_alignment_report.json      # 后端对接报告
│   └── miniprogram_api_alignment_report.json  # 小程序API对接报告
│
└── archived/                     # 📦 归档文档
    ├── BACKEND_ALIGNMENT_FINAL.md  # 后端对接完整性检查
    ├── phase4/                   # Phase 4 归档
    └── deprecated/               # 已废弃的文档
```

│ └── sdk-python.md # Python SDK
│
├── integration/ # 🔗 集成指南
│ ├── frontend.md # 前端集成
│ ├── wechat-miniprogram.md # 微信小程序开发
│ └── wechat-auth.md # 微信认证实现
│
├── operations/ # ⚙️ 运维文档
│ └── database-migration.md # 数据库迁移管理
│
├── reference/ # 📚 参考文档
│ ├── glossary.md # 术语表
│ ├── learning-guide.md # 学习指南
│ └── project-status.md # 项目状态
│
├── history/ # 🗄️ 历史文档
│ ├── phase1/ # Phase 1: 核心功能打通
│ ├── phase2/ # Phase 2: 数据持久化完善
│ └── phase3/ # Phase 3: API 集成测试
│
└── archived/ # 📦 归档文档
├── phase4/ # Phase 4 归档
└── deprecated/ # 已废弃的文档

````

---

## 📖 核心文档导航

### 🚀 项目基础
- **[项目主页](../README.md)** ⭐ - 项目入口，功能特性，快速开始
- **[项目开发状况深度分析](PROJECT_DEVELOPMENT_STATUS.md)** ⭐⭐⭐ - 技术审计 + 功能完整性 + 下一阶段规划
- **[前端重构总结](FRONTEND_REFACTOR_SUMMARY.md)** 🎨 - Learning.vue 通义千问风格重构
- **[AI助手上下文](../AI-CONTEXT.md)** - AI开发助手上下文指南
- **[项目状态](PROJECT_DEVELOPMENT_STATUS.md)** - 最新开发状态、关键指标、下一步计划

### 🏗️ 架构与设计
- **[系统架构](architecture/overview.md)** - 四层架构，技术栈，设计模式
- **[数据访问层](architecture/data-access.md)** - Repository模式，ORM使用
- **[安全策略](architecture/security.md)** - 多维限流，安全头配置
- **[可观测性](architecture/observability.md)** - 监控，日志，性能指标

### 📖 开发指南
- **[开发工作流](guide/development.md)** - 完整开发流程和最佳实践
- **[测试指南](guide/testing.md)** - 测试策略，单元测试，集成测试
- **[部署指南](guide/deployment.md)** - Docker部署，生产环境配置
- **[数学公式测试指南](guide/MATH_FORMULA_TEST.md)** - KaTeX 数学公式渲染测试

### 📱 小程序文档
- **[API 集成](miniprogram/api-integration.md)** - 小程序与后端 API 对接
- **[网络架构](miniprogram/network-architecture.md)** - 小程序网络层设计
- **[用户角色系统](miniprogram/user-role-system.md)** - 小程序用户权限管理

### 🔌 API文档
- **[API概览](api/overview.md)** - API设计原则，认证方式，统一响应格式
- **[API端点](api/endpoints.md)** - 详细端点列表和使用说明
- **[数据模型](api/models.md)** - 请求响应数据结构
- **[错误码](api/errors.md)** - 错误码定义和处理建议
- **[JavaScript SDK](api/sdk-js.md)** - 前端SDK使用
- **[Python SDK](api/sdk-python.md)** - Python客户端SDK

### 🔗 集成指南
- **[前端集成](integration/frontend.md)** - Vue3前端集成方案
- **[微信小程序开发](integration/wechat-miniprogram.md)** - 小程序完整开发流程
- **[微信认证实现](integration/wechat-auth.md)** - 微信登录和授权

### ⚙️ 运维文档
- **[数据库迁移](operations/database-migration.md)** - Alembic迁移管理

### 📚 参考文档
- **[术语表](reference/glossary.md)** - 项目术语和概念定义
- **[学习指南](reference/learning-guide.md)** - 通过项目学习现代Python开发

### 📊 技术报告
- **[登录修复总结](reports/LOGIN_FIX_SUMMARY.md)** - refresh_token 机制修复
- **[文档整理总结](reports/DOCUMENTATION_ORGANIZATION_SUMMARY.md)** - 文档重组记录
- **[API 对接报告](reports/)** - 后端、前端、小程序 API 对接检查报告 (JSON)

### 🗄️ 历史记录
- **[登录调试记录](history/LOGIN_DEBUG.md)** - 登录重复问题诊断过程

---

## 🎓 按场景查找文档

### 我想了解项目
1. 阅读 [项目主页](../README.md) - ⭐ 项目概览和当前状态
2. 查看 [项目开发状况深度分析](PROJECT_DEVELOPMENT_STATUS.md) - ⭐⭐⭐ 完整技术审计
3. 查看 [项目状态](reference/project-status.md) - 最新开发进度
4. 了解 [架构设计](architecture/overview.md) - 技术架构详解

### 我想开始开发
1. [开发指南](guide/development.md) - 环境搭建和工作流
2. [API文档](api/overview.md) - 接口规范
3. [测试指南](guide/testing.md) - 测试要求

### 我想集成前端
1. [前端集成](integration/frontend.md) - Vue3集成方案
2. [微信小程序](integration/wechat-miniprogram.md) - 小程序开发
3. [API端点](api/endpoints.md) - 接口调用

### 我想部署项目
1. [部署指南](guide/deployment.md) - 部署流程
2. [安全策略](architecture/security.md) - 安全配置
3. [可观测性](architecture/observability.md) - 监控配置

### 我遇到了问题
1. [开发指南](guide/development.md#故障排查) - 常见问题
2. [历史文档](history/) - 查看历史问题解决方案
3. [GitHub Issues](../../issues) - 提交问题

---

## 🔍 按主题查找

### 后端开发
- [系统架构](architecture/overview.md) - 四层设计模式
- [数据访问](architecture/data-access.md) - Repository模式
- [API设计](api/overview.md) - RESTful API规范
- [安全策略](architecture/security.md) - 限流和安全头

### 前端开发
- [前端集成](integration/frontend.md) - Vue3 + TypeScript
- [小程序开发](integration/wechat-miniprogram.md) - 微信小程序
- [API文档](api/endpoints.md) - 接口调用

### 数据库
- [数据访问层](architecture/data-access.md) - ORM和查询优化
- [数据库迁移](operations/database-migration.md) - Alembic管理

### 测试
- [测试指南](guide/testing.md) - 单元测试、集成测试、性能测试

### 运维
- [部署指南](guide/deployment.md) - Docker部署
- [可观测性](architecture/observability.md) - 监控和日志
- [安全策略](architecture/security.md) - 安全配置

---

## 📚 历史文档

项目各个开发阶段的完整文档和总结报告：

### Phase 1: 核心功能打通 ✅
**完成时间**: 2025-10-02
**主要成果**: 作业批改功能完整实现

- [Phase 1 目录](history/phase1/README.md)
- [完成总结](history/phase1/PHASE1_COMPLETION_SUMMARY.md)

### Phase 2: 数据持久化完善 ✅
**完成时间**: 2025-10-02
**主要成果**: Analytics后端实现，数据库迁移完成

- [Phase 2 目录](history/phase2/README.md)
- [最终总结](history/phase2/PHASE2_FINAL_SUMMARY.md) - 完整总结 ⭐

### Phase 3: API集成测试与优化 ✅
**完成时间**: 2025-10-03
**主要成果**: 100%测试通过率，API路径全面对齐

- [Phase 3 目录](history/phase3/README.md)
- [完成报告](history/phase3/TASK-1.5-COMPLETION-REPORT.md) - 详细总结 ⭐

### Phase 4: 生产部署优化 🔄
**当前阶段**: 2025-10-04
**预计完成**: 2025-10-15
**主要目标**: 前端用户体验完善，生产环境部署

- [归档文档](archived/phase4/) - Phase 4 相关文档

---

## 📝 文档规范

### 文档命名
- **指南类**: `development.md`, `testing.md`, `deployment.md`
- **架构类**: `overview.md`, `security.md`, `observability.md`
- **参考类**: `glossary.md`, `learning-guide.md`, `project-status.md`

### 文档结构
```markdown
# 文档标题

**最后更新**: YYYY-MM-DD
**状态**: 草稿/审核中/已发布

## 概述
简短描述...

## 主要内容
...

## 相关文档
- [相关文档1](path/to/doc1.md)
- [相关文档2](path/to/doc2.md)
````

### 文档更新

- 重要文档应包含"最后更新"时间
- 归档已完成阶段的文档到 `history/` 或 `archived/`
- 文档链接使用相对路径
- 及时更新文档导航（本文档）

---

## 🤝 贡献文档

### 如何贡献

1. 发现文档问题或缺失
2. 创建 Issue 说明问题
3. 提交 Pull Request 修复

### 文档审核标准

- ✅ 内容准确完整
- ✅ 格式规范统一
- ✅ 链接有效可用
- ✅ 示例代码可运行
- ✅ 及时更新导航

---

## 📞 获取帮助

### 文档相关问题

- **GitHub Issues**: [提交 Issue](../../issues)
- **维护者**: Liguo Ma <maliguo@outlook.com>

### 技术支持

- **API 文档**: http://localhost:8000/docs (开发环境)
- **项目 Wiki**: [GitHub Wiki](../../wiki)

---

## 🔗 外部资源

### 技术文档

- [FastAPI 官方文档](https://fastapi.tiangolo.com/)
- [SQLAlchemy 2.0 文档](https://docs.sqlalchemy.org/en/20/)
- [Vue 3 文档](https://cn.vuejs.org/)
- [微信小程序文档](https://developers.weixin.qq.com/miniprogram/dev/framework/)

### 学习资源

- [Python 最佳实践](https://docs.python-guide.org/)
- [TypeScript 手册](https://www.typescriptlang.org/docs/)
- [阿里云百炼文档](https://help.aliyun.com/zh/model-studio/)

---

## 📈 文档统计

- **总文档数**: 50+ 个 (2025-10-05 更新)
- **核心指南**: 4 个 (development, testing, deployment, math-formula-test)
- **架构文档**: 4 个 (overview, data-access, security, observability)
- **API 文档**: 6 个 (overview, endpoints, models, errors, sdk-js, sdk-python)
- **集成文档**: 3 个 (frontend, wechat-miniprogram, wechat-auth)
- **小程序文档**: 3 个 (api-integration, network-architecture, user-role-system)
- **技术报告**: 6 个 (修复总结、对接报告等)
- **历史文档**: Phase 1, 2, 3 归档
- **当前阶段**: Phase 4 (生产部署优化)
- **最后更新**: 2025-10-05

---

**💡 提示**:

- ⭐ 新手推荐从 [项目主页](../README.md) 开始
- ⭐⭐⭐ 深入了解项目请阅读 [项目开发状况深度分析](PROJECT_DEVELOPMENT_STATUS.md)
- 🤖 AI 开发必读 [AI-CONTEXT.md](../AI-CONTEXT.md)
- 📊 查看最新进度 [项目状态](reference/project-status.md)
- 🏗️ 了解架构 [系统架构](architecture/overview.md)
- 🎨 前端重构成果 [前端重构总结](FRONTEND_REFACTOR_SUMMARY.md)

---

**文档维护**: 项目团队  
**问题反馈**: [GitHub Issues](../../issues)  
**最后更新**: 2025-10-05  
**版本**: v3.1
