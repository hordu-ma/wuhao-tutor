# 五好伴学 - 项目文档中心

> **📚 Documentation Hub**
>
> 最后更新: 2025-10-12
>
> 文档已完成全面重组，反映当前项目实际状态

---

## 📖 文档目录结构

```
docs/
├── api/              # 🔌 API 接口文档
├── architecture/     # 🏗️ 系统架构设计
├── database/         # 🗄️ 数据库设计与迁移
├── deployment/       # 🚀 生产部署指南
├── frontend/         # 🎨 前端开发文档
├── guide/            # 📖 开发使用指南
├── integration/      # 🔗 前端和小程序集成
├── miniprogram/      # 📱 微信小程序专项
├── operations/       # ⚙️ 运维和清理文档
├── reference/        # 📚 参考资料
├── solutions/        # 💡 问题解决方案
└── archive/          # 📦 历史文档归档
```

---

## 🚀 快速导航

### 📌 核心文档（项目根目录）

- **[README.md](../README.md)** ⭐ - 项目概览、快速开始、核心特性
- **[DEVELOPMENT_STATUS.md](../DEVELOPMENT_STATUS.md)** ⭐ - 当前开发状态、已完成功能、下阶段计划
- **[DEVELOPMENT_ROADMAP.md](../DEVELOPMENT_ROADMAP.md)** - 长期开发路线图（12 个月规划）
- **[CHANGELOG.md](../CHANGELOG.md)** - 版本更新日志和修复记录
- **[.github/copilot-instructions.md](../.github/copilot-instructions.md)** - GitHub Copilot 开发规范

---

## 📂 分类文档索引

### 🏗️ 架构设计 (architecture/)

| 文档                                      | 说明                           | 状态      |
| ----------------------------------------- | ------------------------------ | --------- |
| [架构概览](architecture/overview.md)      | 四层架构设计、技术栈、设计原则 | ✅ 已更新 |
| [数据访问层](architecture/data-access.md) | Repository 模式、数据库设计    | ✅ 已更新 |
| [安全策略](architecture/security.md)      | JWT 认证、多维限流、安全措施   | ✅ 已更新 |
| [可观测性](architecture/observability.md) | 监控指标、日志策略、性能追踪   | ✅ 已更新 |

**状态**: ✅ 核心架构文档完整，需要定期更新以反映最新实现

---

### 🔌 API 文档 (api/)

| 文档                         | 说明                                 | 状态      |
| ---------------------------- | ------------------------------------ | --------- |
| [API 概览](api/overview.md)  | RESTful 设计原则、认证机制           | ✅ 已更新 |
| [API 端点](api/endpoints.md) | 完整接口列表和参数说明（~94 个端点） | ✅ 已更新 |
| [数据模型](api/models.md)    | 请求响应结构定义                     | ⚠️ 待更新 |
| [错误码](api/errors.md)      | 错误处理和状态码                     | ⚠️ 待更新 |

**待完成**:

- [ ] `models.md` 需要根据当前 Pydantic 模型自动生成
- [ ] `errors.md` 需要同步 `src/core/exceptions.py` 的异常类型

---

### 🗄️ 数据库设计 (database/)

| 文档                                          | 说明                       | 状态      |
| --------------------------------------------- | -------------------------- | --------- |
| [数据库设计文档](database/database-design.md) | 表结构、关系图、索引设计   | 🔜 待创建 |
| [迁移指南](database/migration-guide.md)       | Alembic 迁移流程和最佳实践 | 🔜 待创建 |

**已实现的表**:

- `users` - 用户信息
- `mistakes` - 错题记录
- `mistake_reviews` - 复习记录（艾宾浩斯曲线）
- `learning_records` - 学习记录
- `homework_submissions` - 作业提交
- `learning_goals` - 学习目标

---

### 🚀 部署指南 (deployment/)

| 文档                                                             | 说明                         | 状态      |
| ---------------------------------------------------------------- | ---------------------------- | --------- |
| [生产部署标准流程](deployment/production-deployment-guide.md) ⭐ | systemd + Nginx 部署完整流程 | ✅ 已验证 |
| [本地代码验证](deployment/local-code-verification.md)            | 部署前代码安全检查           | ✅ 已更新 |
| [RDS 数据库配置](deployment/RDS_CONNECTION_GUIDE.md)             | PostgreSQL 连接和配置        | ✅ 已更新 |
| [Redis 缓存配置](deployment/REDIS_CONNECTION_GUIDE.md)           | Redis 连接和使用             | ✅ 已更新 |
| [安全密钥管理](deployment/SECURITY_KEYS_GUIDE.md)                | API Key 和密钥配置           | ✅ 已更新 |

**状态**: ✅ 部署文档完整且最新，已验证生产环境可用

---

### 📖 开发指南 (guide/)

| 文档                               | 说明                         | 状态                    |
| ---------------------------------- | ---------------------------- | ----------------------- |
| [开发工作流](guide/development.md) | 环境搭建、开发流程、工具使用 | ⚠️ 需要更新 uv 使用说明 |
| [测试指南](guide/testing.md)       | 测试策略、规范和最佳实践     | ✅ 已更新               |

**待补充**: 添加错题手册、AI 学习助手等新功能的开发指南

---

### 🔗 集成指南 (integration/)

| 文档                                                | 说明                            | 状态                     |
| --------------------------------------------------- | ------------------------------- | ------------------------ |
| [前端集成](integration/frontend.md)                 | Vue3 + Pinia 集成方案、API 调用 | ⚠️ 需要更新为 Pinia 模式 |
| [微信小程序开发](integration/wechat-miniprogram.md) | 小程序架构和开发规范            | ✅ 已实现                |
| [微信认证集成](integration/wechat-auth.md)          | 微信登录和用户绑定              | 🔜 规划中                |

**说明**: 小程序已完成基础开发，包含 TabBar、错题手册、学习记录等页面

---

### 📱 小程序专项 (miniprogram/)

| 文档                                            | 说明                     | 状态      |
| ----------------------------------------------- | ------------------------ | --------- |
| [小程序 README](../miniprogram/README.md)       | 小程序项目说明和快速开始 | ✅ 已更新 |
| [API 集成](miniprogram/api-integration.md)      | 后端 API 对接和数据交互  | ✅ 已实现 |
| [网络架构](miniprogram/network-architecture.md) | 请求层、缓存、错误处理   | ✅ 已实现 |
| [用户角色系统](miniprogram/user-role-system.md) | 权限管理和角色设计       | ✅ 已实现 |
| [故障排查](../miniprogram/TROUBLESHOOTING.md)   | 常见问题和解决方案       | ✅ 已更新 |

**当前状态**: ✅ 小程序已完成基础功能开发和关键修复

**已实现功能**:

- TabBar 导航（首页、错题、作业、学习、分析、我的）
- 错题手册列表和详情页
- 学习记录和问答
- 个人中心
- ✅ **图片上传修复** (2025-10-19): 超时问题、进度监听、顺序上传

---

### 🎨 前端开发 (frontend/)

| 文档                                          | 说明         | 状态          |
| --------------------------------------------- | ------------ | ------------- |
| [前端 README](../frontend/FRONTEND-README.md) | 前端项目说明 | ✅ 已更新     |
| [Pinia 状态管理](../frontend/src/stores/)     | 状态管理实现 | ✅ 代码即文档 |
| [组件库](../frontend/src/components/)         | 可复用组件   | ✅ 代码即文档 |

**已实现的 Pinia Stores**:

- `authStore` - 用户认证
- `learningStore` - 学习记录
- `homeworkStore` - 作业管理
- `analyticsStore` - 数据分析
- `userStore` - 用户信息

**状态**: ✅ 前端项目结构清晰，代码注释完善

---

### ⚙️ 运维文档 (operations/)

| 文档                                                   | 说明                        | 状态      |
| ------------------------------------------------------ | --------------------------- | --------- |
| [清理执行报告](operations/cleanup-execution-report.md) | 2025-10-09 环境清理完整记录 | ✅ 已归档 |
| [本地清理计划](operations/local-cleanup-plan.md)       | 本地开发环境清理方案        | ✅ 已完成 |
| [生产清理计划](operations/production-cleanup-plan.md)  | 生产服务器优化方案          | 🔜 规划中 |

---

### 💡 解决方案 (solutions/)

| 文档                                                        | 说明                           | 状态      |
| ----------------------------------------------------------- | ------------------------------ | --------- |
| [图片识别方案](solutions/IMAGE_RECOGNITION_SOLUTION.md)     | AI 图片识别服务集成            | ✅ 已实现 |
| [图片上传修复](solutions/image-upload-fix.md)               | 小程序图片上传功能完整修复方案 | ✅ 已修复 |
| [图片上传超时修复](solutions/fix-upload-timeout.md)         | 超时问题诊断和解决方案         | ✅ 已修复 |
| [AI 图片访问方案](solutions/ai_image_access_solution.py) ⭐ | 图片上传服务实现代码           | ✅ 已实现 |

**最新修复** (2025-10-19):

- ✅ 小程序图片上传超时问题 - 添加 60 秒 timeout、进度监听、顺序上传
- ✅ 详细错误处理 - 区分超时、网络故障、服务器错误
- ✅ 完整日志追踪 - 上传 URL、Token、HTTP 状态、响应数据

---

### 📦 历史文档归档 (archive/)

| 目录                       | 说明                                        | 归档时间   |
| -------------------------- | ------------------------------------------- | ---------- |
| `fixes-2025-10/`           | 2025 年 10 月修复记录（已整合到 CHANGELOG） | 2025-10-12 |
| `reports/`                 | 历史实施报告和总结                          | 2025-10-12 |
| `tasks-phase1/`            | Phase 1 任务文档                            | 2025-10-12 |
| `miniprogram-docs/`        | 小程序临时开发文档                          | 2025-10-12 |
| `PROJECT_STATUS_REPORT.md` | 旧版项目状态报告                            | 2025-10-12 |

**说明**: 归档文档保留用于历史参考，不再维护更新

---

## 👥 按角色导航

### 🆕 新加入的开发者

**推荐阅读顺序**:

1. [README.md](../README.md) - 项目概览
2. [架构概览](architecture/overview.md) - 理解系统设计
3. [开发工作流](guide/development.md) - 环境搭建
4. [API 概览](api/overview.md) - 了解接口规范
5. [.github/copilot-instructions.md](../.github/copilot-instructions.md) - 开发规范

**预计学习时间**: 1-2 天

---

### 👨‍💻 后端开发者

**核心文档**:

- [架构概览](architecture/overview.md) - 四层架构设计
- [数据访问层](architecture/data-access.md) - Repository 模式
- [API 端点](api/endpoints.md) - 接口实现参考
- [数据库设计](database/database-design.md) - 表结构和关系
- [安全策略](architecture/security.md) - 认证和限流
- [测试指南](guide/testing.md) - 测试策略

**快速命令**:

```bash
make db-init      # 数据库迁移
make test         # 运行测试
make lint         # 代码检查
make type-check   # 类型检查
```

---

### 🎨 前端开发者

**核心文档**:

- [前端 README](../frontend/FRONTEND-README.md) - 项目说明
- [API 端点](api/endpoints.md) - 后端接口文档
- [前端集成](integration/frontend.md) - Vue3 + Pinia 集成
- [数据模型](api/models.md) - 请求响应结构

**Pinia Stores**:

- `src/stores/auth.ts` - 用户认证
- `src/stores/learning.ts` - 学习记录
- `src/stores/homework.ts` - 作业管理
- `src/stores/analytics.ts` - 数据分析

**快速命令**:

```bash
cd frontend
npm run dev       # 启动开发服务器
npm run build     # 生产构建
npm run type-check # TypeScript 检查
```

---

### 📱 小程序开发者

**核心文档**:

- [小程序 README](../miniprogram/README.md) - 项目说明
- [API 集成](miniprogram/api-integration.md) - 后端对接
- [网络架构](miniprogram/network-architecture.md) - 请求封装
- [故障排查](../miniprogram/TROUBLESHOOTING.md) - 常见问题

**关键代码**:

- `utils/request.js` - 网络请求封装
- `utils/auth.js` - 认证逻辑
- `pages/mistakes/` - 错题手册页面
- `app.json` - 小程序配置

**开发环境**:

- 微信开发者工具
- AppID 配置（联系管理员获取）

---

### 🚀 运维工程师

**核心文档**:

- [生产部署标准流程](deployment/production-deployment-guide.md) ⭐
- [RDS 数据库配置](deployment/RDS_CONNECTION_GUIDE.md)
- [Redis 缓存配置](deployment/REDIS_CONNECTION_GUIDE.md)
- [安全密钥管理](deployment/SECURITY_KEYS_GUIDE.md)
- [可观测性](architecture/observability.md)

**部署命令**:

```bash
./scripts/deploy_to_production.sh  # 生产部署
./scripts/pre_deploy_check.sh      # 部署前检查
./scripts/verify_deployment.sh     # 部署验证
```

**监控端点**:

- `/api/v1/health` - 健康检查
- `/api/v1/health/metrics` - 性能指标

---

## 📚 学习路径

### Level 1: 基础 (1-2 天)

✅ 理解项目架构和技术栈
✅ 搭建本地开发环境
✅ 运行并测试基础功能
✅ 阅读核心 API 文档

---

### Level 2: 进阶 (1 周)

✅ 理解四层架构设计模式
✅ 掌握 Repository 和 Service 层
✅ 熟悉 Pinia 状态管理
✅ 了解 AI 服务集成（阿里云百炼）
✅ 掌握错题手册业务逻辑

---

### Level 3: 精通 (2-4 周)

✅ 独立实现新功能模块
✅ 优化性能和 N+1 查询
✅ 处理限流和安全策略
✅ 生产环境部署和运维
✅ 参与架构决策和重构

---

## 📊 文档统计

### 文档数量概览

| 分类     | 文档数 | 状态          |
| -------- | ------ | ------------- |
| 核心文档 | 4      | ✅ 已更新     |
| 架构设计 | 4      | ✅ 已更新     |
| API 文档 | 4      | ⚠️ 部分待更新 |
| 数据库   | 2      | ⚠️ 部分待补充 |
| 部署指南 | 5      | ✅ 已验证     |
| 开发指南 | 2      | ⚠️ 部分待更新 |
| 集成指南 | 3      | ⚠️ 部分待更新 |
| 小程序   | 5      | ✅ 已实现     |
| 前端     | 3      | ✅ 已更新     |
| 运维     | 3      | ⚠️ 部分规划中 |
| 解决方案 | 2      | ✅ 已更新     |
| 归档文档 | 5      | 📦 已归档     |

**总计**: ~40 个有效文档，~20 个归档文档

---

## 🎯 待完成任务

### 高优先级 (本周内)

- [ ] 自动生成 `api/models.md` - 基于 Pydantic 模型
- [ ] 更新 `api/errors.md` - 同步异常类型
- [ ] 更新 `guide/development.md` - 添加 uv 使用说明
- [ ] 补充 `database/migration-guide.md` - Alembic 最佳实践

### 中优先级 (2 周内)

- [ ] 更新 `integration/frontend.md` - 反映 Pinia 实现
- [ ] 创建 OpenAPI JSON 生成 CI 任务
- [ ] 添加 markdown-link-check CI 检查
- [ ] 建立文档模板和贡献指南

### 低优先级 (未来)

- [ ] 规划微信认证集成文档
- [ ] 规划生产清理计划
- [ ] 提取架构决策记录（ADR）
- [ ] 扩展性能优化指南

---

## 🔧 文档维护

### 更新原则

1. **代码优先**: 代码是单一真相来源，文档跟随代码更新
2. **自动生成**: API 文档尽可能从 OpenAPI/代码自动生成
3. **及时归档**: 过时文档及时移入 `archive/`
4. **版本标记**: 重要文档标注最后更新日期

### 维护流程

```
代码变更 → PR 包含文档更新 → Code Review + Doc Review → 合并 → 更新日期
```

### CI 检查（规划中）

- [ ] `markdownlint` - Markdown 格式检查
- [ ] `markdown-link-check` - 链接有效性检查
- [ ] `openapi-diff` - API 文档一致性检查

---

## 📞 反馈与贡献

### 发现文档问题？

- **错误或过时**: 创建 GitHub Issue，标签 `documentation`
- **缺失内容**: 提交 PR 补充，或在 Issue 中说明需求
- **改进建议**: 在项目 Discussions 中讨论

### 文档贡献指南

1. Fork 项目并创建分支
2. 更新文档内容
3. 运行 `markdownlint` 检查格式（如果可用）
4. 提交 PR，说明更新内容和原因
5. 等待 Review 和合并

---

## 📝 版本历史

| 日期       | 版本 | 主要变更                                         |
| ---------- | ---- | ------------------------------------------------ |
| 2025-10-12 | v2.0 | 完成文档全面重组，清理冗余内容，更新所有核心文档 |
| 2025-10-09 | v1.1 | 完成环境清理，归档历史文档                       |
| 2025-09    | v1.0 | 初始文档结构建立                                 |

---

**维护者**: 五好伴学开发团队
**联系方式**: 通过 GitHub Issues 或项目 Discussions
