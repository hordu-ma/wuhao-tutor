# Homework 模块备份说明

> **备份时间**: 2025-10-26  
> **备份原因**: Homework 功能在小程序中无用户访问入口，已由 Learning（作业问答）模块覆盖  
> **备份位置**: `/backup/`

---

## 📦 备份内容清单

### 小程序端（Miniprogram）

```
backup/miniprogram/
├── pages/
│   └── homework/               # Homework 相关页面（3个）
│       ├── list/               # 作业列表页
│       ├── detail/             # 作业详情页
│       └── submit/             # 作业提交页
└── api/
    └── homework.js             # Homework API 调用模块
```

**文件统计**:

- 页面文件: 约 15 个文件（.js, .wxml, .wxss, .json）
- 代码行数: 约 1200 行

---

### 后端（Backend）

```
backup/backend/
├── api/
│   ├── homework.py                  # Homework API 端点（9个端点）
│   └── homework_compatibility.py    # 兼容层端点（2个端点）
└── services/
    ├── homework_service.py          # Homework 业务逻辑服务
    └── homework_api_service.py      # Homework API 服务层
```

**文件统计**:

- API 端点: 11 个
- 代码行数: 约 2000 行
- 依赖关系:
  - BailianService（AI 服务）
  - KnowledgeExtractionService（知识点提取）
  - FileUploadService（文件上传）

---

## 🔧 已执行的修改

### 1. 小程序配置文件

#### `miniprogram/app.json`

```diff
  "pages": [
    "pages/index/index",
    "pages/mistakes/list/index",
-   "pages/homework/list/index",
-   "pages/homework/detail/index",
-   "pages/homework/submit/index",
    "pages/learning/index/index",
    // ...
  ]
```

#### `miniprogram/api/index.js`

```diff
- const homeworkAPI = require('./homework.js');
+ // const homeworkAPI = require('./homework.js'); // 已备份

  const api = {
-   homework: homeworkAPI,
+   // homework: homeworkAPI, // 功能已由 learning 模块覆盖
    learning: learningAPI,
    // ...
  };
```

#### `miniprogram/config/index.js`

```diff
  tabBar: {
    student: [
-     { pagePath: 'pages/homework/list/index', text: '作业' },
+     { pagePath: 'pages/mistakes/list/index', text: '错题本' },
+     { pagePath: 'pages/learning/index/index', text: '作业问答' },
      // ...
    ]
  }
```

#### `miniprogram/pages/role-selection/index.js`

```diff
  if (selectedRole === 'teacher') {
-   targetPage = '/pages/homework/list/index';
+   targetPage = '/pages/index/index'; // 作业批改功能已移除
  }
```

---

## 🔄 如何恢复 Homework 功能

### 方案 A: 完整恢复（不推荐）

如果需要完全恢复 Homework 功能：

```bash
# 1. 恢复小程序页面
cp -r backup/miniprogram/pages/homework miniprogram/pages/

# 2. 恢复小程序 API
cp backup/miniprogram/api/homework.js miniprogram/api/

# 3. 编辑 miniprogram/app.json，添加页面注册
# 在 pages 数组中添加：
#   "pages/homework/list/index",
#   "pages/homework/detail/index",
#   "pages/homework/submit/index",

# 4. 编辑 miniprogram/api/index.js，恢复导入
# 取消注释:
#   const homeworkAPI = require('./homework.js');
#   homework: homeworkAPI,

# 5. 编辑 miniprogram/config/index.js，恢复 tabBar 配置
# 在需要的角色 tabBar 中添加 homework 入口

# 6. 编辑 miniprogram/pages/role-selection/index.js
# 恢复教师角色跳转：
#   targetPage = '/pages/homework/list/index';

# 7. 后端文件无需恢复（未被删除，仍在原位置）
```

---

### 方案 B: 部分恢复（推荐）

如果只需要部分功能，建议**重构后集成到 Learning 模块**：

1. 从 `backup/` 中提取需要的函数/组件
2. 重构后集成到 `pages/learning/` 目录
3. 复用后端的 `homework_service.py` 中的业务逻辑
4. 避免重复造轮子

---

## ⚠️ 重要提示

### 为什么备份而不删除？

1. **保留历史**: 代码包含业务逻辑，可能有参考价值
2. **快速回滚**: 如果产品需求变更，可以快速恢复
3. **学习资源**: 新成员可以查看完整的功能实现
4. **审计追踪**: 保留完整的开发历史

### 数据库影响

- ❌ **无需处理数据库**: 即使数据库中有 homework 相关数据，也不影响系统运行
- ✅ **冗余数据**: 数据库表保留，不会导致错误
- ✅ **后端 API**: 后端 API 端点仍然存在（虽然前端不再调用）

### 后端文件处理

**重要**: 后端文件**未被删除**，原因：

1. 其他服务可能有依赖（需要进一步分析）
2. 数据库模型定义在这些文件中
3. 删除后端文件风险较高，需要更全面的测试

**建议**: 后端文件标记为 `@deprecated`，但暂时保留：

```python
# src/api/v1/endpoints/homework.py
"""
@deprecated 2025-10-26
原因: 小程序端已移除 homework 功能，改用 learning 模块
状态: 端点保留但不再被前端调用
复查: 2026-01-26
"""
```

---

## 📊 影响范围

### ✅ 已确认无影响

- ❌ **TabBar**: 没有 homework 入口，移除后用户体验无变化
- ❌ **首页导航**: 首页无 homework 跳转链接
- ❌ **其他页面**: 其他页面无 homework 调用
- ✅ **Learning 模块**: 已覆盖作业问答功能，无缺失

### ⚠️ 潜在影响（需监控）

- **教师角色**: 登录后不再跳转到 homework/list，改为跳转首页
- **深层链接**: 如果有外部链接指向 homework 页面，会 404（需要检查）
- **分享链接**: 旧的分享链接可能失效（需要检查分享记录）

---

## 🔍 验证检查清单

恢复功能前，请确认：

- [ ] 确认产品需求确实需要恢复 homework 功能
- [ ] 检查 Learning 模块是否已覆盖所需功能
- [ ] 评估重构集成 vs 完整恢复的成本
- [ ] 准备回归测试方案
- [ ] 通知用户功能变更（如有必要）

---

## 📞 联系方式

如有问题或需要恢复功能，请联系：

- **技术负责人**: [项目维护者]
- **备份创建者**: AI Assistant
- **备份日期**: 2025-10-26
- **项目文档**: `docs/operations/homework-actual-usage-analysis.md`

---

## 📚 相关文档

- `docs/operations/api-usage-report.md` - API 使用情况分析
- `docs/operations/homework-learning-merge-analysis.md` - 功能合并可行性分析
- `docs/operations/homework-actual-usage-analysis.md` - 实际使用情况详细分析
- `docs/operations/unused-code-verification-plan.md` - 未使用代码验证方案

---

**最后更新**: 2025-10-26  
**备份版本**: v1.0  
**状态**: 已备份，可安全恢复
