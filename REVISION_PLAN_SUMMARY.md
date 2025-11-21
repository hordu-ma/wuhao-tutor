# AI 复习计划生成功能 - 执行方案总结

**版本**: v1.0  
**状态**: 待确认  
**优先级**: 中等

---

## 一、功能概述

### 需求
在微信小程序学习报告页面增加"AI 复习计划"模块，通过以下流程为学生生成个性化的周期性复习指导：

```
错题本数据 → 导出 Markdown → 大模型分析 → 生成复习计划 → 导出 PDF → 上传 OSS → 小程序下载/预览
```

### 核心价值
- **学生体验**：系统化复习策略替代碎片化学习
- **学习效果**：针对性复习薄弱知识点
- **平台差异**：与竞品差异化功能，提升用户粘性
- **数据利用**：充分发挥现有错题本数据的价值

---

## 二、技术方案架构

### 2.1 系统分层

| 层级 | 组件 | 功能 | 状态 |
|------|------|------|------|
| **API** | `/api/v1/revisions` | REST 接口 | **新增** |
| **Service** | RevisionPlanService | 计划生成 + 缓存 | **新增** |
| | PDFGeneratorService | PDF 生成 (WeasyPrint) | **新增** |
| | AliyunOSSService | 文件存储 | **新增/扩展** |
| **Repository** | RevisionPlanRepository | 数据持久化 (PG) | **新增** |
| **Model** | RevisionPlan | 数据结构 | **新增** |
| **Frontend** | 小程序学习报告页 + 详情页 | UI 交互 | **改造现有** |

### 2.2 数据流图

```
┌──────────────┐
│ RDS PostgreSQL │
└──────┬───────┘
       │
       ▼
┌──────────────────────────────┐
│ 1. 聚合错题数据 (MistakeService)
│    - 按知识点分组
│    - 按日期范围筛选
│    - 计算统计信息
└──────┬───────────────────────┘
       │
       ▼
┌──────────────────────────────┐
│ 2. 生成 Markdown 文本
│    - 错题统计汇总
│    - 分类详情
│    - 知识点关联
└──────┬───────────────────────┘
       │
       ▼
┌──────────────────────────────┐
│ 3. 调用百炼大模型
│    - 系统提示词 (Prompt)
│    - 用户学习背景 (Context)
│    - 错题数据 (Content)
└──────┬───────────────────────┘
       │
       ▼
┌──────────────────────────────┐
│ 4. 生成复习计划 (JSON)
│    - 周期规划（7/14/30天）
│    - 每日任务分解
│    - 复习重点和方法
│    - 评估标准
└──────┬───────────────────────┘
       │
       ▼
┌──────────────────────────────┐
│ 5. 生成 PDF 文档
│    - 使用 weasyprint
│    - 格式化排版
│    - 嵌入图表和统计
│    - 添加水印
└──────┬───────────────────────┘
       │
       ▼
┌──────────────────────────────┐
│ 6. 上传 OSS + 返回 URL
│    - 存储到阿里云 OSS
│    - 更新数据库记录
│    - 返回签名下载链接
└──────────────────────────────┘
```

---

## 三、后端实现方案

### 3.1 新增数据模型

**RevisionPlan** - 复习计划主表

```python
字段包括：
- id: UUID 主键
- user_id: 用户 ID（外键）
- title: 计划标题
- cycle_type: 周期（7days|14days|30days）
- status: 状态（draft|published|completed|expired）
- mistake_count: 涉及错题数
- knowledge_points: JSONB 知识点列表
- date_range: JSONB 日期范围
- plan_content: JSONB 详细计划内容
- pdf_url: 阿里云 OSS 下载链接
- download_count: 下载次数
- view_count: 浏览次数
- created_at / updated_at / expired_at: 时间戳
```

### 3.2 核心 Service 类

**RevisionPlanService** - 计划生成核心逻辑

关键方法：
- `generate_revision_plan()` - 生成计划（主入口）
  - 检查缓存（24小时内同周期计划）
  - 获取错题数据
  - 生成 Markdown 文本
  - 调用大模型
  - 生成 PDF
  - 上传至阿里云 OSS 并保存记录

- `_call_ai_for_plan()` - 调用百炼大模型
  - 使用系统提示词
  - 传入用户背景信息
  - 返回 JSON 格式计划

- `_generate_markdown_export()` - 导出错题为 Markdown
  - 调用现有 MistakeService
  - 格式化为易于 AI 理解的文本

- `_get_cached_plan()` - 缓存检查
  - 使用 Redis
  - 24 小时 TTL

- `list_revision_plans()` - 列表查询
- `get_revision_plan()` - 详情查询
- `download_revision_plan()` - 下载（更新统计）

**PDFGeneratorService** - PDF 生成

- `generate()` - 主方法
  - JSON → HTML（使用 Jinja2 模板）
  - HTML → PDF（使用 weasyprint）
  - 包含格式化排版、图表、水印
  - **注意**: 生产环境需安装 `pango`, `cairo`, `libffi-devel`

### 3.3 API 端点设计

```
POST   /api/v1/revisions/generate
       生成新计划
       参数: cycle_type, force_regenerate
       
GET    /api/v1/revisions
       获取计划列表（分页）
       
GET    /api/v1/revisions/{plan_id}
       获取计划详情
       
GET    /api/v1/revisions/{plan_id}/download
       获取 PDF 下载链接 (OSS Signed URL)
       
DELETE /api/v1/revisions/{plan_id}
       删除计划
```

### 3.4 大模型集成

**提示词结构**

```
系统提示词：
- 身份：学习规划师
- 任务：基于错题数据生成{周期}复习计划
- 约束：每日任务时间合理（1-3h）、难度递进、可执行性强

用户消息：
- 学生背景（年级、科目、学习风格）
- 错题统计（总数、分类、频率）
- 错题详情（Markdown 格式）
- 具体要求（目标、方法、评估等）

输出格式：
JSON 结构化数据，包含：
- title、description、overview
- statistics（数据统计）
- daily_tasks（数组，每项包含 day、date、tasks、estimated_hours）
- review_focus（重点列表）
- assessment（评估标准）
- tips（学习建议）
```

### 3.5 性能优化

**缓存策略**
- 同一用户、同一周期、24 小时内的计划视为有效缓存
- 新增错题后自动失效
- 用户可手动强制重新生成

**异步处理**
- 大模型调用（30-60 秒）
- PDF 生成（10-20 秒）
- 使用 FastAPI 后台任务或 Celery
- 前端轮询或 WebSocket 推送进度

**成本控制**
- 单次调用成本：~¥0.1-0.5
- 缓存机制将大幅降低调用频率
- 可选包年套餐（~¥1000/月）

---

## 四、前端实现方案 (微信小程序)

### 4.1 UI 结构

**在学习报告页 (`pages/report/index`) 添加新模块**

```
┌─ 学习报告页面
│
├─ 统计概览（现有）
│  └─ 学习时间、问题数、错题数等
│
└─ 📋 AI 复习计划（新增模块）
   │
   ├─ 最新计划卡片
   │  ├─ 标题 + 周期标签
   │  ├─ 数据统计（错题数、知识点数）
   │  ├─ 计划预览（概述摘要）
   │  └─ "查看详情" / "下载 PDF" 按钮
   │
   ├─ 周期选择器（7/14/30 天）
   │
   ├─ "生成复习计划" 按钮（主操作）
   │  └─ 显示进度条（模拟或真实进度）
   │
   ├─ "刷新" 按钮（重新生成）
   │
   ├─ 计划历史列表
   │  └─ 可选的历史计划切换
   │
   └─ 加载/错误状态处理
      ├─ 生成中动画 + 进度
      └─ 错误提示 + 重试
```

### 4.2 新增子页面

**复习计划详情页** (`miniprogram/pages/revision-detail/index`)

```
┌─ 顶部
│  ├─ 计划标题 + 周期标签
│  ├─ 生成时间 + 过期时间
│  └─ 分享 + 删除按钮
│
├─ 标签页切换 (Tabs)
│  ├─ 概览
│  │  ├─ 计划描述文字
│  │  ├─ 数据统计卡片
│  │  └─ 学习建议
│  │
│  ├─ 每日任务
│  │  ├─ 日期导航
│  │  └─ 任务列表（可展开/收起）
│  │
│  ├─ 重点复习
│  │  └─ 知识点列表
│  │
│  └─ 评估标准
│     └─ 自测题和评估指标
│
└─ 底部
   ├─ "下载 PDF" 按钮 (调用 wx.downloadFile)
   ├─ "分享计划" (调用 onShareAppMessage)
   └─ "返回"
```

### 4.3 前端关键功能

**主页面交互**
```typescript
- onGeneratePlan()：调用生成 API，显示进度条
- onSelectCycle()：选择计划周期
- onRefresh()：强制重新生成
- onDownloadPDF()：调用 wx.downloadFile + wx.openDocument
- onViewDetail()：跳转到详情页
- formatDate()、formatStatus()：数据格式化
```

**详情页交互**
```typescript
- 标签页切换
- 每日任务展开/收起
- PDF 在线预览 (wx.openDocument)
- 分享功能 (onShareAppMessage)
```

---

## 五、数据库变更

### 5.1 新增表

**revision_plans** - 复习计划表

```sql
CREATE TABLE revision_plans (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id),
    title VARCHAR(255),
    description TEXT,
    cycle_type VARCHAR(20),  -- 7days|14days|30days
    status VARCHAR(20) DEFAULT 'draft',
    mistake_count INT DEFAULT 0,
    knowledge_points JSONB DEFAULT '[]',
    date_range JSONB,
    plan_content JSONB,  -- 核心计划数据
    pdf_url VARCHAR(500),
    pdf_size INT,
    download_count INT DEFAULT 0,
    view_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    expired_at TIMESTAMP,
    completed_at TIMESTAMP
);

-- 索引
CREATE INDEX idx_user_id ON revision_plans(user_id);
CREATE INDEX idx_created_at ON revision_plans(created_at DESC);
CREATE INDEX idx_expired_at ON revision_plans(expired_at);
```

**revision_plan_progress** - 完成进度表（可选）

```sql
CREATE TABLE revision_plan_progress (
    id UUID PRIMARY KEY,
    revision_plan_id UUID REFERENCES revision_plans(id),
    user_id UUID REFERENCES users(id),
    completed_tasks JSONB DEFAULT '[]',
    completion_rate NUMERIC(5,2) DEFAULT 0,
    last_reviewed_at TIMESTAMP,
    notes TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

### 5.2 迁移脚本

创建 Alembic 迁移文件实现上述表的创建。

---

## 六、集成工作量估算

### 后端开发
- 数据模型定义：2 小时
- Service 层实现：8 小时
  - RevisionPlanService：6 小时
  - PDFGeneratorService：2 小时
- Repository 实现：1 小时
- API 路由实现：2 小时
- 大模型提示词调优：2 小时
- 单元/集成测试：4 小时
- **小计：19 小时**

### 前端开发
- 主页面模块实现：6 小时
- 详情页面实现：4 小时
- API 调用集成：2 小时
- 进度条 + 错误处理：2 小时
- 测试 + 调试：2 小时
- **小计：16 小时**

### 数据库 + 部署
- 数据库迁移脚本：1 小时
- 生产部署 + 测试：2 小时
- **小计：3 小时**

**总计：~38 小时（约 5 个工作日）**

---

## 七、可选扩展功能

### 7.1 Phase 2 方案
1. **进度追踪**
   - RevisionPlanProgress 表
   - 用户标记任务完成，系统追踪完成率
   - 显示进度仪表板

2. **AI 交互反馈**
   - 用户可反馈计划效果（太简单/太难）
   - 大模型根据反馈调整后续计划

3. **计划分享**
   - 生成分享链接
   - 同学间可查看（去除敏感个人信息）
   - 建立学习社区

4. **微信小程序模板消息**
   - 计划过期提醒
   - 计划完成恭喜
   - 推送新计划

5. **导出选项扩展**
   - Markdown、Word、Excel 格式
   - 支持打印优化
   - 生成学习资源库链接

### 7.2 性能优化
- 预生成常见提示词模板
- PDF 批量生成队列
- CDN 加速 PDF 分发
- WebSocket 实时进度推送

---

## 八、风险评估 & 应对

| 风险 | 概率 | 影响 | 应对方案 |
|------|------|------|---------|
| **大模型调用超时** | 中 | 用户体验差 | 设置 120s 超时 + 重试 3 次 |
| **生成内容质量不稳定** | 中 | 复习效果差 | 提示词多轮调优 + 用户反馈机制 |
| **PDF 生成失败** | 低 | 无法下载 | 降级为 HTML 导出 + 重试 |
| **成本超预期** | 中 | 运营成本↑ | 缓存 + 配额管理 + 用户限流 |
| **存储容量溢出** | 低 | 服务中断 | 30 天自动清理 + 定期监控 |
| **数据库查询慢** | 低 | 加载缓慢 | 添加索引 + 查询优化 |

---

## 九、验收标准

### 功能完整性
- ✅ 用户可生成 3 种周期的复习计划
- ✅ 计划内容包含完整的每日任务和评估标准
- ✅ PDF 排版美观，格式规范
- ✅ 支持下载、删除、分享等操作

### 性能指标
- ✅ 计划生成耗时 < 120 秒
- ✅ PDF 文件大小 < 5MB
- ✅ 列表加载 < 2 秒
- ✅ 缓存命中率 > 70%

### 用户体验
- ✅ UI 简洁直观，操作流畅
- ✅ 进度提示清晰
- ✅ 错误提示有建议和重试选项
- ✅ 支持离线查看（本地缓存）

### 稳定性
- ✅ 无未捕获异常
- ✅ 大模型调用失败时有优雅降级
- ✅ 数据库事务完整性保证
- ✅ 关键操作有日志记录

---

## 十、建议的开发顺序

### Week 1
1. 数据模型 + Repository
2. RevisionPlanService 核心方法
3. 单元测试

### Week 2
1. PDFGeneratorService
2. API 路由实现
3. 大模型提示词调优

### Week 3
1. 前端主页面 + 详情页
2. API 集成
3. 功能测试

### Week 4
1. 性能优化 + 缓存
2. 生产部署
3. 用户验收测试

---

## 十一、文件结构参考

```
后端新增文件：
src/models/revision_plan.py           # 数据模型
src/repositories/revision_plan.py     # Repository
src/services/revision_plan_service.py # Service（核心）
src/services/pdf_generator_service.py # PDF 生成
src/api/v1/endpoints/revisions.py     # API 路由
alembic/versions/XXX_add_revision.py  # 迁移脚本

前端新增文件：
miniprogram/pages/revision-plan/
  ├─ index.wxml
  ├─ index.ts
  └─ style.wxss

miniprogram/pages/revision-detail/
  ├─ index.wxml
  ├─ index.ts
  └─ style.wxss

miniprogram/utils/api.ts              # 新增 revisions API 调用
```

---

## 十二、下一步行动

### 确认要点
1. ✅ 功能范围是否清晰
2. ✅ 技术方案是否可行
3. ✅ 工作量和时间表是否合理
4. ✅ 优先级和扩展功能是否正确

### 待你确认
- [ ] 是否同意此方案
- [ ] 是否需要调整某些设计细节
- [ ] 是否可以开始开发
- [ ] 是否需要补充或澄清某些方面

---

**文档完成于**: 2025-01-15  
**方案状态**: 待你确认  
**联系**: 随时可讨论细节和调整