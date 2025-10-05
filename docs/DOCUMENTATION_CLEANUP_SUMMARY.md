# 文档整理总结 (2025-10-05)

> **整理人**: AI Agent  
> **整理时间**: 2025-10-05  
> **原因**: 架构策略调整为 MCP+RAG 两阶段演进，部分文档需要更新或归档

---

## ✅ 已完成更新的核心文档

### 根目录文档
- ✅ **README.md** - 已更新为 MCP+RAG 混合策略
- ✅ **AI-CONTEXT.md** - 已更新开发计划和技术债务状态
- ✅ **NEXT_STEPS.md** - 已更新为 Phase 4 当前任务（TD-006）

---

## ⚠️ 需要更新的文档

### docs/ 核心文档

#### 1. **DEVELOPMENT_ROADMAP.md** (需要重大更新)
**当前问题**: 
- 仍使用"RAG 后置策略"描述
- 任务优先级和时间线已过时
- 缺少 TD-002, TD-003, TD-005 的完成状态

**建议更新**:
```markdown
# 标题改为: 五好伴学 - 开发路线图 (MCP+RAG 混合策略)
# 策略改为: MCP 优先（精确查询）→ RAG 增强（语义检索）两阶段演进
# 增加 Phase 4 已完成任务清单
# 更新 Phase 5-6 时间线
```

#### 2. **PROJECT_DEVELOPMENT_STATUS.md** (需要部分更新)
**当前问题**:
- 技术债务清单未更新（TD-002/003/005 已完成）
- RAG 系统仍标注为"缺失"，应改为"计划中"
- 整体评级和完成度需要调整

**建议更新**:
- 更新技术债务表格（标记已完成项）
- 更新向量数据库状态：从"缺失"改为"📋 计划集成 PGVector (Phase 6)"
- 更新整体状况评级：从 B- 提升到 B+

---

## 📦 建议归档的文档

### docs/reports/ 历史报告
这些文档记录了历史开发过程，有参考价值但不需要频繁更新：

- **TD-002-KNOWLEDGE-EXTRACTION-SUMMARY.md** - 知识点提取完成报告
- **TD-003-KNOWLEDGE-GRAPH-PROGRESS.md** - 知识图谱导入完成报告
- **TD-005-ANSWER-QUALITY-PROGRESS.md** - 答案质量评估完成报告
- **FRONTEND_REFACTOR_SUMMARY.md** - 前端重构总结
- **LOGIN_FIX_SUMMARY.md** - 登录修复总结

**处理建议**: 保留在当前位置，这些是项目历史记录

### docs/archived/ 已归档文档
- **BACKEND_ALIGNMENT_FINAL.md** - 已归档，保持不动

---

## 🗑️ 建议删除的文档

### 重复或过时的文档

#### docs/guide/ 目录
- **PHASE4_DEVELOPMENT_PLAN.md** - 可能与 DEVELOPMENT_ROADMAP.md 重复
  - **建议**: 检查内容，如果重复则删除

#### docs/history/ 目录
- **LOGIN_DEBUG.md** - 登录问题已修复，调试文档可删除
  - **建议**: 删除（已有 LOGIN_FIX_SUMMARY.md）

---

## 📝 需要创建的新文档

### 1. **TD-006-MCP-CONTEXT-PROGRESS.md**
**位置**: `docs/reports/`  
**用途**: 记录 MCP 上下文构建服务的开发进度  
**创建时机**: TD-006 完成后

### 2. **MCP_RAG_ARCHITECTURE.md** (可选)
**位置**: `docs/architecture/`  
**用途**: 详细说明 MCP+RAG 混合策略的技术架构  
**内容**:
- MCP 上下文构建原理
- RAG 向量检索原理
- 两者融合策略
- 性能优化方案

---

## 🔧 快速整理命令

### 更新文档
```bash
# 1. 更新 DEVELOPMENT_ROADMAP.md
# 手动编辑，调整为 MCP+RAG 策略

# 2. 更新 PROJECT_DEVELOPMENT_STATUS.md
# 手动编辑，更新技术债务状态
```

### 删除过时文档（谨慎）
```bash
# 如果确认不需要，可以删除
# rm docs/history/LOGIN_DEBUG.md
```

---

## 📋 文档整理检查清单

### 优先级 1 (本周完成)
- [ ] 更新 `DEVELOPMENT_ROADMAP.md`
- [ ] 更新 `PROJECT_DEVELOPMENT_STATUS.md`
- [ ] 检查 `PHASE4_DEVELOPMENT_PLAN.md` 是否重复

### 优先级 2 (后续优化)
- [ ] 创建 `MCP_RAG_ARCHITECTURE.md`（待 TD-006 完成后）
- [ ] 审查 `docs/guide/` 目录其他文档
- [ ] 审查 `docs/api/` 是否需要更新

### 优先级 3 (可选)
- [ ] 整理 `docs/integration/` 目录
- [ ] 更新 API 文档
- [ ] 更新运维文档

---

## 🎯 文档管理原则

### 保留原则
1. **历史记录有价值** - 技术报告、开发总结保留在 `docs/reports/`
2. **架构文档重要** - 所有架构设计文档必须保留并更新
3. **操作文档实用** - 部署、运维、测试文档必须保持最新

### 归档原则
1. **已完成任务的进度报告** - 移至 `docs/archived/` 或保持在 `docs/reports/`
2. **过时的技术方案** - 移至 `docs/archived/`

### 删除原则
1. **完全重复的文档** - 删除副本，保留主副本
2. **临时调试文档** - 问题已解决后删除
3. **错误或误导性内容** - 直接删除

---

## 📞 后续行动

**立即执行** (本次提交):
- ✅ 创建本文档 (`DOCUMENTATION_CLEANUP_SUMMARY.md`)
- ✅ 提交所有已更新的根目录文档

**后续任务** (Week 2):
- 更新 `DEVELOPMENT_ROADMAP.md`
- 更新 `PROJECT_DEVELOPMENT_STATUS.md`
- 检查并清理重复文档

**长期维护**:
- 每个 Phase 结束后审查文档
- 保持文档与代码同步
- 及时归档历史文档

---

**最后更新**: 2025-10-05  
**下次审查**: Phase 4 完成后 (预计 2025-10-12)
