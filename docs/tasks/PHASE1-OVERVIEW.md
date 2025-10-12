# Phase 1 错题手册开发任务总览

> **项目**: 五好伴学 - 错题手册功能  
> **总工期**: 4 周 (2025-10 ~ 2025-11)  
> **优先级**: 🔥 P0 最高  
> **开发策略**: 渐进式委派给 Coding Agent

---

## 📋 任务拆分

### ✅ Task 1.1: 数据库设计与迁移

**文档**: [TASK-1.1-DATABASE-DESIGN.md](./TASK-1.1-DATABASE-DESIGN.md)

| 项目 | 详情 |
|------|------|
| **工作量** | 3-4 天 |
| **难度** | ⭐⭐ (中等) |
| **前置依赖** | 无 |
| **输出** | Alembic 迁移脚本 + 索引优化 + 单元测试 |

**核心任务**:
- 创建 `mistake_reviews` 表 (复习记录)
- 优化 `mistake_records` 表 (添加新字段)
- 设计 8 个性能优化索引
- 支持 SQLite (开发) 和 PostgreSQL (生产)

**验收标准**:
- [x] `MistakeReview` 模型类完整定义
- [x] Alembic 迁移脚本 (upgrade + downgrade)
- [x] 8 个索引创建 (包括 GIN 索引)
- [x] 外键和检查约束
- [x] 单元测试覆盖率 >80%
- [x] 性能测试通过 (<100ms)

---

### ✅ Task 1.2: MistakeService 业务逻辑

**文档**: [TASK-1.2-MISTAKE-SERVICE.md](./TASK-1.2-MISTAKE-SERVICE.md)

| 项目 | 详情 |
|------|------|
| **工作量** | 5-6 天 |
| **难度** | ⭐⭐⭐ (较高) |
| **前置依赖** | Task 1.1 完成 |
| **输出** | Repository + Service + 算法 + 测试 |

**核心任务**:
- 实现 `MistakeRepository` 和 `MistakeReviewRepository`
- 实现艾宾浩斯遗忘曲线算法
- 完整的 CRUD 操作
- 复习计划生成
- AI 知识点分析集成

**验收标准**:
- [x] Repository 层完整实现 (12 个方法)
- [x] 遗忘曲线算法实现和测试
- [x] MistakeService 所有方法实现
- [x] Schema 定义完整
- [x] 单元测试覆盖率 >85%
- [x] 集成测试通过

---

### ⏳ Task 1.3: 错题 API 路由

**文档**: 待创建 `TASK-1.3-MISTAKE-API.md`

| 项目 | 详情 |
|------|------|
| **工作量** | 3-4 天 |
| **难度** | ⭐⭐ (中等) |
| **前置依赖** | Task 1.2 完成 |
| **输出** | FastAPI 路由 + 权限验证 + 集成测试 |

**核心任务**:
- 设计 RESTful API 路由
- 实现请求验证和错误处理
- 添加权限验证中间件
- API 文档生成 (OpenAPI)

**API 端点**:
```
GET    /api/v1/mistakes              # 错题列表
POST   /api/v1/mistakes              # 创建错题
GET    /api/v1/mistakes/{id}         # 错题详情
DELETE /api/v1/mistakes/{id}         # 删除错题
POST   /api/v1/mistakes/{id}/review  # 完成复习
GET    /api/v1/mistakes/today-review # 今日复习任务
GET    /api/v1/mistakes/statistics   # 统计数据
```

---

### ⏳ Task 1.4: 前端组件开发

**文档**: 待创建 `TASK-1.4-FRONTEND-COMPONENTS.md`

| 项目 | 详情 |
|------|------|
| **工作量** | 3-4 天 |
| **难度** | ⭐⭐ (中等) |
| **前置依赖** | Task 1.3 完成 |
| **输出** | Vue3 组件 + Pinia Store + ECharts 图表 |

**核心任务**:
- 错题列表组件 (分页、筛选、搜索)
- 错题详情组件 (图片展示、知识点标签)
- 今日复习组件 (复习卡片、进度条)
- 统计图表组件 (ECharts)
- Pinia Store (状态管理)

**技术栈**:
- Vue 3 Composition API
- TypeScript
- Pinia (状态管理)
- ECharts (数据可视化)
- Vite (构建工具)

---

## 📊 进度跟踪

### Week 1 (2025-10-14 ~ 2025-10-18)

- [ ] **Day 1-2**: Task 1.1 数据库设计
  - [ ] 创建 `MistakeReview` 模型
  - [ ] 编写 Alembic 迁移脚本
  - [ ] 添加索引和约束
  
- [ ] **Day 3-4**: Task 1.1 测试和优化
  - [ ] 单元测试编写
  - [ ] 性能测试
  - [ ] 文档完善
  
- [ ] **Day 5**: Task 1.1 验收和 Code Review

**预期输出**: 
- ✅ 数据库表结构完整
- ✅ 迁移脚本可用
- ✅ 测试覆盖率 >80%

---

### Week 2 (2025-10-21 ~ 2025-10-25)

- [ ] **Day 1-2**: Task 1.2 Repository 层
  - [ ] `MistakeRepository` 实现
  - [ ] `MistakeReviewRepository` 实现
  - [ ] Repository 单元测试
  
- [ ] **Day 3-4**: Task 1.2 算法层
  - [ ] 艾宾浩斯遗忘曲线算法
  - [ ] 掌握度计算逻辑
  - [ ] 算法单元测试
  
- [ ] **Day 5**: Task 1.2 Service 层开始
  - [ ] `MistakeService` 框架搭建
  - [ ] CRUD 方法实现

**预期输出**:
- ✅ Repository 层完整
- ✅ 算法实现和测试
- ⏳ Service 层 50% 完成

---

### Week 3 (2025-10-28 ~ 2025-11-01)

- [ ] **Day 1-2**: Task 1.2 Service 层完成
  - [ ] 复习计划生成
  - [ ] AI 服务集成
  - [ ] 统计分析实现
  
- [ ] **Day 3**: Task 1.2 测试和优化
  - [ ] Service 单元测试
  - [ ] 集成测试
  - [ ] 性能优化
  
- [ ] **Day 4-5**: Task 1.3 API 路由开始
  - [ ] 路由设计
  - [ ] 请求验证
  - [ ] 错误处理

**预期输出**:
- ✅ Service 层完整
- ✅ 测试覆盖率 >85%
- ⏳ API 路由 50% 完成

---

### Week 4 (2025-11-04 ~ 2025-11-08)

- [ ] **Day 1-2**: Task 1.3 API 完成
  - [ ] 权限验证
  - [ ] API 文档生成
  - [ ] 集成测试
  
- [ ] **Day 3-5**: Task 1.4 前端组件
  - [ ] 错题列表组件
  - [ ] 复习组件
  - [ ] 统计图表组件
  - [ ] Pinia Store

**预期输出**:
- ✅ API 完整可用
- ✅ 前端组件完整
- ✅ 端到端测试通过

---

## 🎯 里程碑验收

### 里程碑 1: 错题手册 MVP (2025-11-08)

**验收标准**:

✅ **后端**:
- [x] 数据库表结构完整且优化
- [x] Service 层业务逻辑完整
- [x] API 路由完整且有文档
- [x] 单元测试覆盖率 >85%
- [x] 集成测试通过

✅ **前端**:
- [x] 错题列表可查看和筛选
- [x] 可以添加和删除错题
- [x] 今日复习功能可用
- [x] 复习完成后掌握度更新
- [x] 统计图表正确展示

✅ **功能**:
- [x] 用户可以手动添加错题记录
- [x] 系统自动生成今日复习清单
- [x] 复习完成后更新掌握度
- [x] 遗忘曲线算法正确计算复习时间
- [x] 连续 5 次正确后标记为"已掌握"

✅ **性能**:
- [x] 错题列表查询 <100ms
- [x] 复习记录创建 <200ms
- [x] 统计数据查询 <300ms

✅ **文档**:
- [x] API 文档完整 (Swagger UI)
- [x] 数据库 ER 图
- [x] 算法文档
- [x] 用户使用指南

---

## 🔧 技术栈

### 后端
- **框架**: FastAPI 0.104+
- **ORM**: SQLAlchemy 2.0 (Async)
- **数据库**: PostgreSQL 14+ (生产) / SQLite (开发)
- **迁移**: Alembic
- **测试**: pytest + pytest-asyncio
- **AI 服务**: 阿里云百炼 (可选)

### 前端
- **框架**: Vue 3.4+ (Composition API)
- **语言**: TypeScript 5.0+
- **状态管理**: Pinia 2.1+
- **UI 组件**: Element Plus / Ant Design Vue
- **图表**: ECharts 5.4+
- **构建**: Vite 5.0+

### 工具
- **包管理**: uv (Python) / pnpm (Node.js)
- **代码格式化**: Black (Python) / Prettier (TypeScript)
- **类型检查**: mypy (Python) / TypeScript
- **Git 规范**: Conventional Commits

---

## 📚 相关文档

### 设计文档
- [x] [数据库表结构设计](../database/mistake_reviews_schema.md)
- [x] [遗忘曲线算法说明](../algorithms/spaced_repetition.md)
- [ ] [API 接口文档](../api/mistakes.md)
- [ ] [前端组件设计](../frontend/mistake-components.md)

### 参考文档
- [项目总览 README](../../README.md)
- [开发路线图](../../DEVELOPMENT_ROADMAP.md)
- [架构文档](../architecture/overview.md)
- [开发指南](../development/setup.md)

---

## 🚨 风险和缓解

### 风险 1: 数据库迁移失败
**概率**: 低 | **影响**: 高

**缓解措施**:
- 在测试环境先验证迁移脚本
- 准备回滚脚本 (downgrade)
- 生产环境迁移前备份数据

### 风险 2: 算法准确性问题
**概率**: 中 | **影响**: 中

**缓解措施**:
- 充分的单元测试覆盖
- 边界条件测试
- 使用成熟的 SuperMemo 2 算法
- 支持手动调整复习时间

### 风险 3: 性能不达标
**概率**: 低 | **影响**: 中

**缓解措施**:
- 设计充分的索引
- 使用查询缓存 (Redis)
- 分页查询避免大数据量
- 性能测试和基准建立

### 风险 4: AI 服务不稳定
**概率**: 中 | **影响**: 低

**缓解措施**:
- AI 分析设为可选功能
- 失败时使用默认知识点
- 添加重试机制
- 超时控制 (5 秒)

---

## 📝 提交规范

### Commit Message 格式

```
<type>(<scope>): <subject>

<body>

<footer>
```

**类型 (type)**:
- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档更新
- `test`: 测试相关
- `refactor`: 重构
- `perf`: 性能优化
- `chore`: 构建/工具更新

**示例**:
```bash
feat(mistake): 实现错题复习记录表

- 创建 MistakeReview 模型
- 添加 Alembic 迁移脚本
- 设计 8 个性能优化索引

Refs: TASK-1.1
```

---

## 💡 最佳实践

### 1. 代码质量
- 遵循项目编码规范 (Black + mypy)
- 每个函数添加 Docstring
- 复杂逻辑添加注释
- 避免硬编码,使用配置

### 2. 测试驱动
- 先写测试,后写实现 (TDD)
- 单元测试覆盖率 >85%
- 集成测试覆盖核心流程
- 性能测试建立基准

### 3. 渐进交付
- 每个 Task 独立可验收
- 及时 Code Review
- 小步快跑,持续集成
- 每周至少一次部署

### 4. 文档优先
- API 先设计后实现
- 算法逻辑文档化
- 保持文档与代码同步
- 提供使用示例

---

## 📞 联系方式

**项目负责人**: [Your Name]  
**技术咨询**: [Email]  
**问题反馈**: GitHub Issues  
**代码审查**: Pull Request

---

**创建时间**: 2025-10-12  
**最后更新**: 2025-10-12  
**版本**: v1.0

---

*祝开发顺利! 🚀*
