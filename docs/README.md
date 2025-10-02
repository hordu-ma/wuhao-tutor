# 五好伴学项目文档导航

> **📚 项目文档中心**
> 本文档提供项目所有文档的导航和快速访问

**最后更新**: 2025-10-02
**文档版本**: v2.0

---

## 🎯 快速开始

### 新手入门

1. 阅读 [项目主页](../README.md) - 了解项目概况
2. 查看 [AI助手上下文](../AI-CONTEXT.md) - AI开发助手必读
3. 参考 [开发指南](DEVELOPMENT.md) - 完整开发工作流

### 开发者

1. [MVP开发计划](../MVP-DEVELOPMENT-PLAN.md) - 当前开发计划和进度
2. [API文档](api/overview.md) - 接口规范和示例
3. [架构设计](ARCHITECTURE.md) - 系统架构详解

---

## 📁 文档结构

```
docs/
├── README.md                    # 本文档（导航）
├── api/                         # API接口文档
├── architecture/                # 架构设计文档
├── development/                 # 开发指南
│   ├── LEARNING_GUIDE.md       # 学习指南
│   └── WECHAT_MINIPROGRAM_DEVELOPMENT_GUIDE.md  # 小程序开发
├── history/                     # 历史文档
│   ├── phase1/                 # Phase 1 文档
│   └── phase2/                 # Phase 2 文档
└── [核心文档]                   # 下方列出
```

---

## 📖 核心文档

### 项目基础

- **[项目主页](../README.md)** ⭐ - 项目入口，功能特性，快速开始
- **[AI助手上下文](../AI-CONTEXT.md)** - AI开发助手上下文指南
- **[MVP开发计划](../MVP-DEVELOPMENT-PLAN.md)** - 当前开发计划和里程碑

### 架构与设计

- **[系统架构](ARCHITECTURE.md)** - 分层架构，技术栈，设计模式
- **[数据访问层](DATA-ACCESS.md)** - 数据库设计，ORM使用
- **[前端集成](FRONTEND-INTEGRATION.md)** - 前后端集成方案

### 开发指南

- **[开发工作流](DEVELOPMENT.md)** - 完整开发流程和最佳实践
- **[测试指南](TESTING.md)** - 测试策略，单元测试，集成测试
- **[数据库迁移](MIGRATION.md)** - Alembic迁移管理

### 部署运维

- **[部署指南](DEPLOYMENT.md)** - 部署策略，Docker配置
- **[可观测性](OBSERVABILITY.md)** - 监控，日志，性能指标
- **[安全策略](SECURITY.md)** - 安全基线，最佳实践

### 项目管理

- **[项目状态](STATUS.md)** - 版本规划，里程碑，技术债务
- **[术语表](GLOSSARY.md)** - 项目术语和概念定义

---

## 🔌 API 文档

完整的 REST API 文档，包含接口规范、请求响应示例、错误码说明：

- **[API概览](api/overview.md)** - API设计原则，认证方式
- **[API端点](api/endpoints.md)** - 详细端点列表和使用说明
- **[数据模型](api/models.md)** - 请求响应数据结构
- **[错误码](api/errors.md)** - 错误码定义和处理建议
- **[JavaScript SDK](api/sdk-js.md)** - 前端SDK使用
- **[Python SDK](api/sdk-python.md)** - Python客户端SDK

---

## 🏗️ 开发指南

### 通用指南

- **[学习指南](development/LEARNING_GUIDE.md)** - 通过项目学习现代Python开发
- **[小程序开发指南](development/WECHAT_MINIPROGRAM_DEVELOPMENT_GUIDE.md)** - 微信小程序完整开发流程

### 专题指南

- [开发环境搭建](DEVELOPMENT.md#环境搭建)
- [代码规范](DEVELOPMENT.md#代码规范)
- [Git工作流](DEVELOPMENT.md#git工作流)
- [性能优化](OBSERVABILITY.md#性能优化)

---

## 📚 历史文档

项目各个开发阶段的完整文档和总结报告：

### Phase 1: 核心功能打通 ✅

**完成时间**: 2025-10-02
**主要成果**: 作业批改功能完整实现

- [Phase 1 目录](history/phase1/README.md)
- [完成总结](history/phase1/PHASE1_COMPLETION_SUMMARY.md)
- [作业批改模块修复报告](history/phase1/HOMEWORK_REPAIR_REPORT.md)

### Phase 2: 数据持久化完善 ✅

**完成时间**: 2025-10-02
**主要成果**: Analytics后端实现，数据库迁移完成

- [Phase 2 目录](history/phase2/README.md) ⭐ 推荐阅读
- [最终总结](history/phase2/PHASE2_FINAL_SUMMARY.md) - 完整总结
- [测试结果](history/phase2/PHASE2_TEST_RESULTS.md) - 详细测试报告
- [其他文档](history/phase2/) - 共8个专题文档

---

## 🎓 按场景查找文档

### 我想了解项目

1. 阅读 [README.md](../README.md) - 项目概览
2. 查看 [ARCHITECTURE.md](ARCHITECTURE.md) - 技术架构
3. 参考 [STATUS.md](STATUS.md) - 项目状态

### 我想开始开发

1. [开发指南](DEVELOPMENT.md) - 环境搭建和工作流
2. [API文档](api/overview.md) - 接口规范
3. [测试指南](TESTING.md) - 测试要求

### 我想部署项目

1. [部署指南](DEPLOYMENT.md) - 部署流程
2. [安全策略](SECURITY.md) - 安全配置
3. [可观测性](OBSERVABILITY.md) - 监控配置

### 我遇到了问题

1. [开发指南](DEVELOPMENT.md#故障排查) - 常见问题
2. [历史文档](history/) - 查看历史问题解决方案
3. [GitHub Issues](../../issues) - 提交问题

### 我想学习技术

1. [学习指南](development/LEARNING_GUIDE.md) - 系统学习路径
2. [架构设计](ARCHITECTURE.md) - 设计模式和最佳实践
3. [历史文档](history/) - 实际问题解决案例

---

## 🔍 按主题查找

### 后端开发

- [系统架构](ARCHITECTURE.md)
- [API设计](api/overview.md)
- [数据访问](DATA-ACCESS.md)
- [安全策略](SECURITY.md)

### 前端开发

- [前端集成](FRONTEND-INTEGRATION.md)
- [小程序开发](development/WECHAT_MINIPROGRAM_DEVELOPMENT_GUIDE.md)
- [API文档](api/endpoints.md)

### 数据库

- [数据访问层](DATA-ACCESS.md)
- [数据库迁移](MIGRATION.md)
- [Phase 2 总结](history/phase2/PHASE2_FINAL_SUMMARY.md#数据库表结构)

### 测试

- [测试指南](TESTING.md)
- [Phase 2 测试报告](history/phase2/PHASE2_TEST_RESULTS.md)

### 运维

- [部署指南](DEPLOYMENT.md)
- [可观测性](OBSERVABILITY.md)
- [安全策略](SECURITY.md)

---

## 📝 文档规范

### 文档命名

- 核心文档: `UPPERCASE.md` (如 `README.md`)
- 专题文档: `lowercase-with-dash.md` (如 `quick-start.md`)
- Phase文档: `PHASE{N}_DESCRIPTION.md` (如 `PHASE1_COMPLETION_SUMMARY.md`)

### 文档结构

```markdown
# 文档标题

> 简短描述

**元信息**: 创建时间、状态等

## 主要内容

...

## 相关文档

...
```

### 文档更新

- 重要文档应包含"最后更新"时间
- Phase完成后文档移至 `history/` 目录
- 文档链接使用相对路径

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

---

## 📞 获取帮助

### 文档相关问题

- **GitHub Issues**: [提交Issue](../../issues)
- **维护者**: Liguo Ma <maliguo@outlook.com>

### 技术支持

- **API文档**: http://localhost:8000/docs (开发环境)
- **项目Wiki**: [GitHub Wiki](../../wiki)

---

## 🔗 外部资源

### 技术文档

- [FastAPI官方文档](https://fastapi.tiangolo.com/)
- [SQLAlchemy 2.0文档](https://docs.sqlalchemy.org/en/20/)
- [Vue 3文档](https://cn.vuejs.org/)
- [微信小程序文档](https://developers.weixin.qq.com/miniprogram/dev/framework/)

### 学习资源

- [Python最佳实践](https://docs.python-guide.org/)
- [TypeScript手册](https://www.typescriptlang.org/docs/)
- [阿里云百炼文档](https://help.aliyun.com/zh/model-studio/)

---

## 📈 文档统计

- **总文档数**: 30+
- **API文档**: 6个
- **开发指南**: 10+
- **历史文档**: 10+ (Phase 1 & Phase 2)
- **最后更新**: 2025-10-02

---

**💡 提示**:

- 从 [README.md](../README.md) 开始
- AI开发必读 [AI-CONTEXT.md](../AI-CONTEXT.md)
- 当前计划 [MVP-DEVELOPMENT-PLAN.md](../MVP-DEVELOPMENT-PLAN.md)

---

**文档维护**: 项目团队
**问题反馈**: [GitHub Issues](../../issues)
**最后更新**: 2025-10-02
