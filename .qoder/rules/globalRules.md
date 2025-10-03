---
trigger: always_on
alwaysApply: true
---
# 🤖 AI 协作指令 v3.1

## 📋 快速上下文 (每次对话必读)

**环境**: macOS M4 | zsh | `~/my-devs/{python,typescript,swift,rust}/`  
**技术栈优先级**: Python > TypeScript/Vue3 > Swift > Rust  
**响应语言**: 中文 | **解释风格**: 怎么做 + 为什么 + 权衡

### 开始前确认清单
- [ ] 识别项目语言/框架（查看文件扩展名、package.json、Cargo.toml 等）
- [ ] 理解架构模式（MVVM/MVC/Composables 等）
- [ ] 匹配下方对应的编码规范

---

## 🚫 不可妥协 (4 条核心原则)

1. **类型 + 错误安全**: 完整类型注解 + 具体异常类型（禁用 `try-catch-all`）
2. **零硬编码凭证**: 所有敏感信息使用环境变量/Keychain
3. **函数单一职责**: ≤ 60 行，复杂逻辑拆分子函数
4. **提供上下文**: 不仅说"怎么做"，更要解释"为什么"和"权衡"

---

## 🎨 语言规范 (按使用频率排序)

### Python (主力)
- **工具**: `uv` 管理依赖 | **格式**: Black (line-length=88)
- **类型**: 强制类型注解 (mypy strict) | **测试**: pytest + 边界条件
- **异常**: 具体异常类型，禁用裸 `except:` | **文档**: Google 风格 docstring

### TypeScript (主力)
- **工具**: `nvm` + Prettier (printWidth=100) + ESLint
- **类型**: 严格模式 (`strict: true`) | **测试**: Jest/Vitest
- **Vue3 规范**:
  - **组合式 API** 优先 (setup script)
  - **响应式**: `ref`/`reactive` 明确区分 | **组件**: SFC 单文件组件
  - **路由**: Vue Router 类型安全 | **状态**: Pinia (类型化 store)

### Swift (辅助)
- **架构**: MVVM | **UI**: SwiftUI | **并发**: async/await 优先
- **命名**: SwiftLint 默认规则 | **内存**: 闭包使用 `[weak self]`
- **依赖**: CocoaPods/SPM | **测试**: XCTest

### Rust (辅助)
- **工具**: Cargo + rustfmt + clippy
- **错误处理**: `Result<T, E>` 优先，避免 `unwrap()` 
- **所有权**: 明确生命周期注解 | **测试**: 内置测试框架

---

## 🤝 协作模式

### 复杂任务处理 (必须遵循)
**启用条件**: 多步骤任务、重构、新功能开发  
**工作流程**:
1. **创建 Todo List**: 分解任务为 ≤ 5 项清晰步骤
2. **逐项执行**: 每次只处理一个 todo，标记为 `in-progress`
3. **验证检查**: 完成后立即验证（运行测试/编译检查）
4. **Git 操作提示**: 通过验证后提示提交
   ```bash
   git add <修改的文件>
   git commit -m "type(scope): 描述"
   ```
5. **继续下一项**: 标记 `completed`，进入下一个 todo

**示例场景**:
- ❌ 简单任务（修改一个变量）→ 直接执行
- ✅ 复杂任务（添加认证系统）→ 启动 todo list 模式

### 代码输出
- ✅ **直接生成**符合规范的完整代码（自动识别项目语言）
- ❌ **避免**示例代码块（除非用户明确要求）
- ✅ 读取大块上下文，而非多次小范围读取
- ✅ **框架感知**: 自动适配 Vue3/SwiftUI/async 等现代模式

### Git 提交规范
```
类型(范围): 简洁描述
```
**类型**: `feat` | `fix` | `docs` | `refactor` | `test` | `chore`  
**示例**:  
- `feat(api): 添加用户认证接口` (Python/FastAPI)
- `fix(components): 修复 Composable 响应式丢失` (Vue3)
- `refactor(mvvm): 重构姿态检测 ViewModel` (Swift)

### 质量标准
- 核心功能必须有单元测试（边界条件 + 异常路径）
- 复杂算法注释时间/空间复杂度
- 优先正确性和可读性，瓶颈出现后再优化
- **项目识别**: 通过 `package.json`/`Cargo.toml`/`Podfile` 自动判断技术栈

---

**更新**: 2025-10-03 | **版本**: v3.1 | **优化**: 新增 Todo List 工作流