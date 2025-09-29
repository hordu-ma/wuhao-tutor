# 上下文管理使用指南

> **📖 文档说明**
>
> 本指南说明如何使用优化后的文档体系进行有效的上下文管理，特别适用于AI助手快速理解项目。

---

## 🎯 文档体系概览

本项目采用分层式文档结构，为不同使用场景提供最适合的信息密度：

```
📚 文档层次结构
├── README.md                      # 🏠 主入口 - 完整上下文指南
├── DEVELOPER-QUICK-REFERENCE.md   # ⚡ 快速参考 - 核心信息卡片
├── PROJECT-CONTEXT.md             # 🧠 深度认知 - AI助手认知框架
├── CONTEXT-MANAGEMENT.md          # 📖 本文档 - 使用说明
└── docs/                         # 📁 专题文档 - 详细技术文档
    ├── DEVELOPMENT.md
    ├── ARCHITECTURE.md
    └── ...
```

---

## 🚀 快速上手 (2分钟)

### 对于新的AI助手对话窗口

**第一步：读取主文档**
```bash
# 阅读优先级 (按需选择)
1. README.md                    # 必读 - 完整项目概览
2. DEVELOPER-QUICK-REFERENCE.md # 推荐 - 核心信息速览
3. PROJECT-CONTEXT.md          # 可选 - 深度认知框架
```

**第二步：环境检查**
```bash
# 快速环境诊断
uv run python scripts/diagnose.py

# 查看项目状态
make status

# 检查服务状态
./scripts/status-dev.sh
```

**第三步：确定工作模式**
```bash
# 开发模式
./scripts/start-dev.sh          # 启动完整开发环境

# 只需后端
make dev                        # 仅启动后端API服务

# 诊断模式
./scripts/diagnose.py           # 仅进行环境检查
```

---

## 📋 文档使用策略

### 按使用场景选择文档

| 使用场景 | 推荐文档 | 阅读时间 |
|----------|----------|----------|
| 🔥 **新对话窗口** | README.md | 3-5分钟 |
| ⚡ **快速查询** | DEVELOPER-QUICK-REFERENCE.md | 1-2分钟 |
| 🧠 **深度理解** | PROJECT-CONTEXT.md | 5-8分钟 |
| 🛠️ **具体开发** | docs/DEVELOPMENT.md | 10-15分钟 |
| 🏗️ **架构理解** | docs/ARCHITECTURE.md | 15-20分钟 |
| 🔐 **安全相关** | docs/SECURITY.md | 8-10分钟 |

### 按角色选择文档

**AI助手 (推荐阅读顺序)**
1. `README.md` - 获取完整上下文
2. `DEVELOPER-QUICK-REFERENCE.md` - 掌握核心约定
3. `PROJECT-CONTEXT.md` - 建立认知框架
4. 按需查阅 `docs/` 专题文档

**新开发者**
1. `README.md` - 项目概览
2. `docs/DEVELOPMENT.md` - 开发工作流
3. `scripts/README.md` - 工具使用
4. 实践：`make quick-start`

**项目维护者**
1. `docs/ARCHITECTURE.md` - 架构设计
2. `docs/SECURITY.md` - 安全策略
3. `docs/OBSERVABILITY.md` - 监控体系
4. `docs/STATUS.md` - 项目状态

---

## 🔧 上下文管理最佳实践

### AI助手工作流

**开始新对话时**
```markdown
1. 读取 README.md 了解项目全貌
2. 运行环境诊断确认状态
3. 确认当前工作目标和范围
4. 根据需要查阅专题文档
```

**开发过程中**
```markdown
1. 遵循 DEVELOPER-QUICK-REFERENCE.md 中的约定
2. 使用项目提供的脚本工具
3. 参考 PROJECT-CONTEXT.md 的认知框架
4. 提交前运行完整检查
```

**遇到问题时**
```markdown
1. 查看 TROUBLESHOOTING.md 常见问题
2. 运行 ./scripts/diagnose.py 诊断
3. 查看相关 docs/ 专题文档
4. 联系项目维护者
```

### 文档更新策略

**何时更新文档**
- 架构变化 → 更新 `docs/ARCHITECTURE.md`
- 新增功能 → 更新 `README.md` + 相关专题文档
- 工具变更 → 更新 `DEVELOPER-QUICK-REFERENCE.md`
- 约定调整 → 更新 `PROJECT-CONTEXT.md`

**更新检查清单**
```bash
# 文档一致性检查
1. README.md 信息是否最新
2. DEVELOPER-QUICK-REFERENCE.md 命令是否有效
3. PROJECT-CONTEXT.md 认知是否准确
4. docs/ 专题文档是否同步
```

---

## 🎨 个性化使用技巧

### 快速导航技巧

**查找特定信息**
```bash
# 快速搜索关键概念
grep -r "关键词" docs/
grep -r "函数名" src/

# 查看特定脚本帮助
./scripts/script-name.sh --help
python scripts/script-name.py --help
```

**书签式阅读**
```markdown
# 常用文档路径收藏
README.md#快速启动                    # 环境搭建
DEVELOPER-QUICK-REFERENCE.md#快速命令参考  # 常用命令
docs/DEVELOPMENT.md#代码风格与结构约定     # 编码规范
docs/API/endpoints.md                 # API接口文档
```

### 上下文缓存策略

**第一次接触项目**
1. 完整阅读 `README.md`
2. 记录关键信息：技术栈、目录结构、启动命令
3. 建立项目认知基线

**后续对话**
1. 快速浏览 `DEVELOPER-QUICK-REFERENCE.md`
2. 确认项目状态和环境
3. 专注具体问题解决

---

## 📊 文档质量保证

### 文档测试

**可执行性测试**
```bash
# 测试文档中的命令是否有效
make help                    # Makefile命令
./scripts/start-dev.sh      # 启动脚本
uv run python scripts/diagnose.py  # 诊断脚本
```

**信息准确性验证**
```bash
# 验证文档信息与实际代码一致
make status                 # 检查项目状态
./scripts/status-dev.sh     # 检查服务状态
```

### 反馈与改进

**发现问题时**
1. 记录问题的具体位置和内容
2. 提出改进建议
3. 创建 GitHub Issue (标签: `docs`)
4. 或直接提交 PR 修复

**改进建议**
- 信息过时 → 及时更新
- 信息缺失 → 补充完善
- 结构混乱 → 重新组织
- 使用困难 → 简化说明

---

## 🔄 版本控制

### 文档版本管理

**主要版本更新** (如 0.1.x → 0.2.x)
- 全面审查所有文档
- 更新技术栈信息
- 调整架构说明
- 更新功能描述

**次要版本更新** (如 0.1.1 → 0.1.2)
- 更新相关变更的文档
- 检查命令有效性
- 更新状态信息

### 文档同步检查

**提交前检查**
```bash
# 确保文档与代码同步
1. 新增功能是否更新了 README.md
2. API变更是否更新了相关文档
3. 脚本变更是否更新了使用说明
4. 配置变更是否更新了环境说明
```

---

## 💡 高效使用建议

### 针对不同任务的文档组合

**快速问题排查**
```
README.md (项目概览)
→ DEVELOPER-QUICK-REFERENCE.md (快速命令)
→ ./scripts/diagnose.py (环境诊断)
```

**深度功能开发**
```
README.md (项目理解)
→ docs/ARCHITECTURE.md (架构设计)
→ docs/DEVELOPMENT.md (开发规范)
→ 相关源代码目录
```

**API接口开发**
```
README.md (基础了解)
→ docs/api/ (API文档)
→ src/api/ (代码实现)
→ tests/integration/ (测试用例)
```

### 时间管理

**5分钟快速了解**
- `DEVELOPER-QUICK-REFERENCE.md`

**15分钟全面了解**
- `README.md` + `PROJECT-CONTEXT.md`

**30分钟深度学习**
- 完整文档体系 + 实践操作

---

## 📞 获取帮助

### 文档相关问题

1. **内容问题**: 检查 `docs/` 目录下的专题文档
2. **使用问题**: 查看本文档或联系维护者
3. **技术问题**: 运行 `./scripts/diagnose.py` 诊断
4. **改进建议**: 提交 GitHub Issue 或 Pull Request

### 联系方式

- **项目维护者**: Liguo Ma <maliguo@outlook.com>
- **文档问题**: GitHub Issues (标签: `docs`)
- **功能建议**: GitHub Issues (标签: `enhancement`)

---

## 🏷️ 元信息

- **文档创建**: 2024-12-19
- **最后更新**: 2024-12-19
- **维护者**: Liguo Ma
- **版本**: 1.0.0
- **状态**: ✅ 稳定版本

---

**💡 记住：好的上下文管理能显著提高开发效率和代码质量！**
