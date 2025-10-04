# 文档重组和清理方案

**创建时间**: 2025-10-04  
**状态**: 待执行  
**目标**: 整理项目文档结构，删除过时内容，优化文档导航

---

## 📊 当前文档状态分析

### 文档数量统计
- **总文档数**: 72个 Markdown 文档
- **根目录文档**: 7个
- **docs/ 文档**: 34个
- **miniprogram/ 文档**: 12个
- **frontend/ 文档**: 1个
- **其他**: 18个（AI工具配置、组件README等）

### 主要问题识别

1. **根目录混乱**: 包含多个规划文档，职责不清
2. **重复内容**: 多个文档描述相同的内容
3. **过时文档**: Phase 1-3 的临时文档散落各处
4. **层级混乱**: 子项目文档位置不统一
5. **文档引用**: 多处文档引用路径需要更新

---

## 🎯 新文档组织结构

```
wuhao-tutor/
├── README.md                          # 项目入口，概览和快速开始
├── WARP.md                            # Warp AI 开发指南
├── AI-CONTEXT.md                      # AI助手上下文
├── CONTRIBUTING.md                    # 贡献指南（新增）
│
├── docs/                              # 📚 所有技术文档集中管理
│   ├── README.md                      # 文档导航中心
│   │
│   ├── guide/                         # 📖 开发指南
│   │   ├── getting-started.md        # 快速开始
│   │   ├── development.md            # 开发工作流（原DEVELOPMENT.md）
│   │   ├── testing.md                # 测试指南（原TESTING.md）
│   │   └── deployment.md             # 部署指南（原DEPLOYMENT.md）
│   │
│   ├── architecture/                  # 🏗️ 架构设计
│   │   ├── overview.md               # 架构概览（原ARCHITECTURE.md）
│   │   ├── data-access.md            # 数据访问层（原DATA-ACCESS.md）
│   │   ├── security.md               # 安全策略（原SECURITY.md）
│   │   └── observability.md          # 可观测性（原OBSERVABILITY.md）
│   │
│   ├── api/                          # 🔌 API文档
│   │   ├── overview.md
│   │   ├── endpoints.md
│   │   ├── models.md
│   │   ├── errors.md
│   │   ├── sdk-js.md
│   │   └── sdk-python.md
│   │
│   ├── integration/                  # 🔗 集成指南
│   │   ├── frontend.md               # 前端集成（原FRONTEND-INTEGRATION.md）
│   │   ├── wechat-miniprogram.md     # 小程序开发（原development/WECHAT_...md）
│   │   └── wechat-auth.md            # 微信认证（原WECHAT_AUTH_IMPLEMENTATION.md）
│   │
│   ├── operations/                   # ⚙️ 运维文档
│   │   ├── database-migration.md     # 数据库迁移（原MIGRATION.md）
│   │   └── monitoring.md             # 监控配置
│   │
│   ├── reference/                    # 📚 参考文档
│   │   ├── glossary.md               # 术语表（原GLOSSARY.md）
│   │   ├── learning-guide.md         # 学习指南（原development/LEARNING_GUIDE.md）
│   │   └── project-status.md         # 项目状态（原PROJECT_STATUS_REPORT.md）
│   │
│   └── archived/                     # 🗄️ 历史归档
│       ├── README.md                 # 归档文档说明
│       ├── phase1/                   # Phase 1 历史文档
│       ├── phase2/                   # Phase 2 历史文档
│       ├── phase3/                   # Phase 3 历史文档
│       └── deprecated/               # 已废弃的文档
│
├── frontend/                         # Vue3 前端项目
│   ├── README.md                     # 前端项目说明
│   └── docs/                         # 前端专属文档（如需要）
│       └── components.md             # 组件文档
│
├── miniprogram/                      # 微信小程序项目
│   ├── README.md                     # 小程序项目说明
│   └── docs/                         # 小程序专属文档
│       ├── api-integration.md        # API集成（原API_INTEGRATION_GUIDE.md）
│       ├── network-architecture.md   # 网络架构（原NETWORK_ARCHITECTURE.md）
│       └── user-role-system.md       # 用户角色系统（合并多个文档）
│
└── scripts/                          # 开发脚本
    └── README.md                     # 脚本使用说明
```

---

## 🗑️ 待删除文档清单

### 一、完全过时/重复的文档（建议直接删除）

#### 根目录
```
❌ CURRENT_DEVELOPMENT_GUIDE.md       # 内容已过时，被 NEXT_DEVELOPMENT_PLAN.md 替代
❌ MVP-DEVELOPMENT-PLAN.md            # MVP阶段已完成，内容已归档
```

#### docs/ 目录
```
❌ docs/DOCUMENTATION_UPDATE_SUMMARY.md   # 临时更新记录，无长期价值
❌ docs/TASK_5_IMAGE_OCR_OPTIMIZATION_SUMMARY.md  # 特定任务完成总结，应归档
```

#### docs/archived/ 目录（已经在归档区，但可精简）
```
❌ docs/archived/DIAGNOSTIC_FIX_REPORT.md    # 临时修复报告
❌ docs/archived/PHASE3_TODO_LIST_1_SUMMARY.md  # 临时任务列表
❌ docs/archived/TASK_1_5_COMPLETION_SUMMARY.md  # 已有更完整的总结
```

#### miniprogram/ 目录
```
❌ miniprogram/DEVELOPMENT-PROGRESS-REPORT.md  # 进度报告，应归档
❌ miniprogram/NETWORK_LAYER_SUMMARY.md        # 内容已整合到文档
❌ miniprogram/UI_INTEGRATION_SUMMARY.md       # 临时总结文档

# docs/ 子目录中的临时文档
❌ miniprogram/docs/PHASE3_TODO_LIST1_COMPLETION.md
❌ miniprogram/docs/TODO-1.3-1.4-COMPLETION.md
❌ miniprogram/docs/TODO-2.5-account-security-guide.md

# pages/ 子目录中的临时完成总结
❌ miniprogram/pages/analysis/TODO-3.4-COMPLETION-SUMMARY.md
❌ miniprogram/pages/profile/TODO-3.5-COMPLETION-SUMMARY.md
```

#### docs/history/ 目录（保留结构，但清理重复）
```
# Phase 2 中重复的文档（保留最终总结即可）
❌ docs/history/phase2/PHASE2_COMPLETION_SUMMARY.md  # 有更完整的 FINAL_SUMMARY
❌ docs/history/phase2/PHASE2_QUICK_COMMANDS.md      # 临时命令记录
❌ docs/history/phase2/PHASE2_RECOVERY_GUIDE.md      # 恢复指南，已不需要
❌ docs/history/phase2/PHASE2_STATUS_SNAPSHOT.md     # 状态快照，已不需要
❌ docs/history/phase2/PHASE2_TEST_FIX_REPORT.md     # 可合并到 FINAL_SUMMARY
❌ docs/history/phase2/PHASE2_TEST_GUIDE.md          # 临时测试指南
❌ docs/history/phase2/PHASE2_TEST_RESULTS.md        # 可合并到 FINAL_SUMMARY

# Phase 3 中的临时文档
❌ docs/history/phase3/TASK-1.5-EXECUTION-GUIDE.md   # 执行指南，已完成
❌ docs/history/phase3/TASK-1.5-TESTING-PLAN.md      # 测试计划，已完成
❌ docs/history/phase3/TODO-LIST-1-COMPLETION-README.md  # 临时完成文档
```

### 二、需要归档的文档（移动到 docs/archived/）

```
📦 NEXT_DEVELOPMENT_PLAN.md                    → docs/archived/phase4/
📦 docs/PROJECT_STATUS_REPORT.md               → docs/reference/project-status.md (更新后保留)
📦 miniprogram/DEVELOPMENT-PROGRESS-REPORT.md  → docs/archived/miniprogram/
```

### 三、需要合并的文档

#### 微信小程序用户系统文档（合并为一个）
```
合并：
- miniprogram/docs/permission-system-guide.md
- miniprogram/docs/role-tabbar-system-guide.md
- miniprogram/docs/user-role-system-complete.md

目标：
→ miniprogram/docs/user-role-system.md (统一的用户系统文档)
```

#### API 集成文档（简化）
```
合并：
- miniprogram/docs/API_INTEGRATION_GUIDE.md
- miniprogram/docs/API_QUICK_START.md

目标：
→ miniprogram/docs/api-integration.md (统一的API集成指南)
```

---

## 📝 需要更新引用的核心文档

执行重组后，以下文档需要更新内部链接：

### 1. README.md（根目录）
```markdown
更新链接：
- 文档导航: docs/README.md
- MVP开发计划: docs/archived/mvp-plan.md
- 下一步计划: docs/reference/project-status.md
```

### 2. WARP.md
```markdown
更新链接：
- AI-CONTEXT.md → AI-CONTEXT.md (保持)
- ARCHITECTURE.md → docs/architecture/overview.md
- docs/DEVELOPMENT.md → docs/guide/development.md
- docs/api/ → docs/api/ (保持)
- .github/copilot-instructions.md → .github/copilot-instructions.md (保持)
```

### 3. AI-CONTEXT.md
```markdown
更新链接：
- README.md → README.md (保持)
- MVP-DEVELOPMENT-PLAN.md → docs/archived/mvp-plan.md
- docs/README.md → docs/README.md (保持)
- docs/ARCHITECTURE.md → docs/architecture/overview.md
- docs/DEVELOPMENT.md → docs/guide/development.md
- docs/SECURITY.md → docs/architecture/security.md
- docs/TESTING.md → docs/guide/testing.md
- docs/history/ → docs/archived/ (更新路径)
```

### 4. docs/README.md（文档导航中心）
```markdown
完全重写，反映新的文档结构
```

---

## 🔄 执行步骤

### 阶段1: 备份和准备（5分钟）
```bash
# 1. 创建备份
cp -r docs docs_backup_$(date +%Y%m%d)
cp -r miniprogram/docs miniprogram/docs_backup_$(date +%Y%m%d)

# 2. 创建新目录结构
mkdir -p docs/{guide,architecture,integration,operations,reference}
mkdir -p docs/archived/{phase1,phase2,phase3,phase4,deprecated}
mkdir -p miniprogram/docs
```

### 阶段2: 移动和重组文档（20分钟）
```bash
# 按照上述新结构移动文档
# 示例命令将在执行时提供
```

### 阶段3: 合并重复文档（15分钟）
```bash
# 合并小程序用户系统文档
# 合并API集成文档
# 整合Phase历史文档
```

### 阶段4: 删除过时文档（10分钟）
```bash
# 根据清单删除确认的过时文档
```

### 阶段5: 更新引用链接（20分钟）
```bash
# 更新所有核心文档中的链接
# 运行链接检查工具
```

### 阶段6: 验证和测试（10分钟）
```bash
# 验证所有链接有效
# 检查文档渲染
# 确认导航清晰
```

---

## ✅ 预期成果

### 改进指标
- **文档数量减少**: 72个 → 约45个（减少37%）
- **层级更清晰**: 3级目录结构，职责明确
- **导航更便捷**: 统一的文档导航入口
- **维护更简单**: 减少重复，降低维护成本

### 核心优势
1. **新手友好**: 清晰的文档路径，快速找到所需信息
2. **AI友好**: 结构化的文档组织，便于AI理解和引用
3. **维护友好**: 减少重复，更新一处即可
4. **历史清晰**: 归档文档独立管理，不干扰当前开发

---

## 🤝 待确认事项

请确认以下删除操作：

### 高优先级删除（强烈建议）
- [ ] `CURRENT_DEVELOPMENT_GUIDE.md` - 完全过时
- [ ] `MVP-DEVELOPMENT-PLAN.md` - MVP已完成，可归档
- [ ] `docs/DOCUMENTATION_UPDATE_SUMMARY.md` - 临时文档
- [ ] 所有 `miniprogram/pages/*/TODO-*-COMPLETION-SUMMARY.md` - 临时完成总结

### 中优先级删除（建议）
- [ ] `docs/history/phase2/` 中的8个文档 → 保留 `PHASE2_FINAL_SUMMARY.md` 和 `README.md`
- [ ] `docs/history/phase3/` 中的4个文档 → 保留 `TASK-1.5-COMPLETION-REPORT.md` 和 `README.md`
- [ ] `miniprogram/` 根目录的3个总结文档

### 需要评估（您决定）
- [ ] `docs/archived/` 中的3个诊断文档 - 是否有参考价值？
- [ ] `.qoder/rules/globalRules.md` - Qoder AI工具配置，是否还在使用？

---

**下一步**: 等待您的确认后，开始执行文档重组
