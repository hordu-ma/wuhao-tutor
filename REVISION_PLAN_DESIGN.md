# AI 复习计划生成功能 - 完整设计方案

**版本**: v1.1
**日期**: 2025-11-21
**状态**: 开发中 (In Progress)
**优先级**: 中

---

## 一、功能概述

### 1.1 需求描述

在微信小程序学习报告页面增加"AI 复习计划"模块，通过以下流程为学生生成个性化的周期性复习指导：

```
错题本数据 → 导出 Markdown → 大模型分析 → 生成复习计划 → 导出 PDF → 上传阿里云 OSS → 小程序下载/预览
```

### 1.2 核心价值

| 维度 | 收益 |
|------|------|
| **学生体验** | 获得系统化的复习策略，替代碎片化的学习 |
| **学习效果** | 针对性复习薄弱知识点，提升掌握度 |
| **平台差异** | 与竞品差异化功能，提升用户粘性 |
| **数据应用** | 充分利用现有错题本数据，提高转化率 |

---

## 二、系统架构设计

### 2.1 数据流

```
┌─────────────────┐
│  RDS PostgreSQL │
│ (Mistake 表)    │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  1. 获取错题本 + 元数据              │
│     - 按知识点分组                   │
│     - 按日期范围筛选                │
│     - 计算错误率/频次                │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  2. 生成 Markdown 导出文本           │
│     - 错题统计汇总                   │
│     - 分类详情（题目+解析+建议）    │
│     - 知识点关联图                   │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  3. 调用百炼大模型                   │
│     - 系统提示词 (Prompt)           │
│     - 用户学习背景 (Context)        │
│     - Markdown 文本 (Content)       │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  4. 生成复习计划 JSON                │
│     - 周期规划（7天/14天/30天）     │
│     - 每日任务分解                   │
│     - 复习重点和方法                 │
│     - 评估标准                       │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  5. 生成 PDF 文档                    │
│     - 格式化排版                     │
│     - 嵌入图表                       │
│     - 添加水印（用户信息）          │
│     - 依赖: weasyprint + cairo      │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  6. 上传至阿里云 OSS                 │
│     - 存储路径: plans/{user_id}/    │
│     - 设置 Content-Type             │
│     - 获取签名 URL (如有需要)        │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  7. 返回下载 URL                     │
│     - 小程序调用 `wx.downloadFile`   │
│     - 支持 `wx.openDocument` 预览    │
└─────────────────────────────────────┘
```

### 2.2 系统组件

| 组件 | 层级 | 功能 | 新增/现有 |
|------|------|------|---------|
| **MistakeDataService** | Service | 错题本数据聚合 & Markdown 导出 | 现有 + 扩展 |
| **RevisionPlanService** | Service | 复习计划生成 & 缓存管理 | **新增** |
| **PDFGeneratorService** | Service | PDF 生成 (WeasyPrint) | **新增** |
| **AliyunOSSService** | Service | 文件上传与管理 | **新增/扩展** |
| **RevisionPlanRepository** | Repository | 复习计划持久化 (PostgreSQL) | **新增** |
| **RevisionPlan 模型** | Model | 复习计划数据结构 | **新增** |
| **/api/v1/revisions** | API | 复习计划 REST 接口 | **新增** |
| **小程序学习报告页** | Frontend | UI 展示 & 交互 (WXML/TS) | **现有** 改造 |

---

## 三、后端设计详解

### 3.1 数据模型

#### 3.1.1 RevisionPlan 模型（新增）

```python
# src/models/revision_plan.py

class RevisionPlan(BaseModel):
    """AI 复习计划"""
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id")
    
    # 元数据
    title: str  # "2025年1月学习复习计划"
    description: str  # 简短描述
    cycle_type: str  # "7days" | "14days" | "30days"
    status: str  # "draft" | "published" | "completed" | "expired"
    
    # 数据来源
    mistake_count: int  # 包含的错题数
    knowledge_points: list[str]  # JSON: 涉及的知识点
    date_range: dict  # JSON: {"start": "2025-01-01", "end": "2025-01-15"}
    
    # 复习计划内容（存储为 JSONB）
    plan_content: dict = Field(sa_column=Column(JSONB))  # 结构化的复习计划数据
    # {
    #   "overview": "...",
    #   "statistics": {...},
    #   "daily_tasks": [
    #     {
    #       "day": 1,
    #       "date": "2025-01-16",
    #       "tasks": [...],
    #       "estimated_hours": 1.5
    #     }
    #   ],
    #   "review_focus": [...],
    #   "assessment": {...}
    # }
    
    # 文件信息
    pdf_url: str | None  # 阿里云 OSS 下载链接
    pdf_size: int | None  # 文件大小（字节）
    markdown_url: str | None  # Markdown 源文件（可选存档）
    
    # 时间戳
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    expired_at: datetime | None  # 计划过期时间
    completed_at: datetime | None  # 完成时间
    
    # 使用统计
    download_count: int = 0
    view_count: int = 0
    is_shared: bool = False  # 是否分享过
    
    class Config:
        table_name = "revision_plans"
```

#### 3.1.2 RevisionPlanProgress 模型（可选，用于追踪学生进度）

```python
class RevisionPlanProgress(BaseModel):
    """复习计划完成进度"""
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    revision_plan_id: UUID = Field(foreign_key="revision_plan.id")
    user_id: UUID = Field(foreign_key="user.id")
    
    completed_tasks: list[int]  # 已完成任务索引
    completion_rate: float  # 0-100
    last_reviewed_at: datetime
    notes: str | None  # 用户笔记
    
    created_at: datetime
    updated_at: datetime
```

### 3.2 Service 层设计

#### 3.2.1 RevisionPlanService (核心)

```python
# src/services/revision_plan_service.py

class RevisionPlanService:
    """复习计划生成服务"""
    
    def __init__(
        self,
        db: AsyncSession,
        mistake_service: MistakeService,
        bailian_service: BailianService,
        file_service: FileService,
    ):
        self.db = db
        self.mistake_service = mistake_service
        self.bailian_service = bailian_service
        self.file_service = file_service
        self.revision_repo = RevisionPlanRepository(db)
    
    async def generate_revision_plan(
        self,
        user_id: UUID,
        cycle_type: str = "7days",  # "7days" | "14days" | "30days"
        days_lookback: int = 30,  # 回顾近N天的错题
        force_regenerate: bool = False,  # 强制重新生成
    ) -> RevisionPlan:
        """
        生成个性化复习计划
        
        流程：
        1. 检查缓存（同一周期内已有未过期计划）
        2. 获取错题本数据
        3. 生成 Markdown 文本
        4. 调用大模型生成计划
        5. 生成 PDF
        6. 保存到数据库
        7. 返回计划对象
        """
        
        # 1. 缓存检查
        if not force_regenerate:
            cached_plan = await self._get_cached_plan(user_id, cycle_type)
            if cached_plan:
                logger.info(f"使用缓存复习计划: {cached_plan.id}")
                return cached_plan
        
        # 2. 获取错题数据
        mistakes_data = await self.mistake_service.get_mistakes_for_revision(
            user_id=user_id,
            days_lookback=days_lookback,
        )
        
        if not mistakes_data["items"]:
            raise ServiceError("没有错题数据，无法生成复习计划")
        
        # 3. 生成 Markdown 文本
        markdown_content = await self._generate_markdown_export(
            user_id=user_id,
            mistakes_data=mistakes_data,
        )
        
        # 4. 调用大模型
        plan_json = await self._call_ai_for_plan(
            user_id=user_id,
            markdown_content=markdown_content,
            cycle_type=cycle_type,
            mistakes_stats=mistakes_data["statistics"],
        )
        
        # 5. 生成 PDF
        pdf_info = await self._generate_pdf(
            user_id=user_id,
            plan_json=plan_json,
            markdown_content=markdown_content,
        )
        
        # 6. 保存到数据库
        revision_plan = await self.revision_repo.create({
            "user_id": user_id,
            "title": plan_json["title"],
            "description": plan_json.get("description", ""),
            "cycle_type": cycle_type,
            "status": "published",
            "mistake_count": len(mistakes_data["items"]),
            "knowledge_points": mistakes_data["knowledge_points"],
            "date_range": mistakes_data["date_range"],
            "plan_content": plan_json,
            "pdf_url": pdf_info["url"],
            "pdf_size": pdf_info["size"],
            "expired_at": self._calculate_expiry(cycle_type),
        })
        
        logger.info(f"✅ 复习计划生成成功: {revision_plan.id}")
        return revision_plan
    
    async def _get_cached_plan(
        self,
        user_id: UUID,
        cycle_type: str,
    ) -> RevisionPlan | None:
        """检查是否有有效的缓存计划"""
        # 查询最近的同类型计划
        # 如果存在且未过期，返回
        # 否则返回 None
        pass
    
    async def _generate_markdown_export(
        self,
        user_id: UUID,
        mistakes_data: dict,
    ) -> str:
        """将错题本导出为 Markdown 文本"""
        # 调用 MistakeService 的导出功能
        # 返回格式化的 Markdown 文本
        pass
    
    async def _call_ai_for_plan(
        self,
        user_id: UUID,
        markdown_content: str,
        cycle_type: str,
        mistakes_stats: dict,
    ) -> dict:
        """调用百炼大模型生成复习计划"""
        
        prompt = self._build_system_prompt(cycle_type)
        user_context = await self._build_user_context(user_id)
        
        messages = [
            {
                "role": "user",
                "content": f"""
请根据以下学生的错题数据生成一份详尽的{cycle_type}复习计划。

【学生信息】
{user_context}

【错题统计】
{mistakes_stats}

【错题详情】
{markdown_content}

【要求】
1. 制定明确的学习目标
2. 分解为每日任务（含时间估计）
3. 指定复习重点和方法
4. 提供自测题和评估标准
5. 考虑学生的学习风格和薄弱点

请以 JSON 格式返回，包含以下字段：
- title: 计划标题
- description: 简短描述
- overview: 概述
- statistics: 数据统计
- daily_tasks: 每日任务数组
- review_focus: 重点复习内容
- assessment: 评估标准
- tips: 学习建议
"""
            }
        ]
        
        response = await self.bailian_service.call_api(
            messages=messages,
            system_prompt=prompt,
            temperature=0.7,
            max_tokens=4000,
        )
        
        # 解析并验证 JSON
        plan_json = self._parse_json_response(response)
        return plan_json
    
    async def _generate_pdf(
        self,
        user_id: UUID,
        plan_json: dict,
        markdown_content: str,
    ) -> dict:
        """生成 PDF 文件并上传至 OSS"""
        
        # 调用 PDFGeneratorService
        pdf_generator = PDFGeneratorService()
        pdf_buffer = await pdf_generator.generate(
            title=plan_json["title"],
            content=plan_json,
            metadata={
                "user_id": str(user_id),
                "generated_at": datetime.utcnow().isoformat(),
                "markdown_source": markdown_content,
            }
        )
        
        # 上传到阿里云 OSS
        # 路径格式: revision-plans/{user_id}/{YYYYMMDD_HHMMSS}.pdf
        file_key = f"revision-plans/{user_id}/{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        # 使用 FileService (需配置为 Aliyun OSS backend)
        url = await self.file_service.save_file(
            file_buffer=pdf_buffer,
            file_key=file_key,
            content_type="application/pdf",
        )
        
        return {
            "url": url,
            "size": len(pdf_buffer.getvalue()),
        }
    
    def _build_system_prompt(self, cycle_type: str) -> str:
        """构建系统提示词"""
        return f"""
你是一位经验丰富的学习规划师。你的任务是根据学生的错题数据生成个性化的{cycle_type}复习计划。

## 规划原则
1. **数据驱动**：基于错题频率、错误类型决定复习重点
2. **循序渐进**：从基础概念到综合应用
3. **时间合理**：每日任务时间控制在 1-3 小时
4. **可执行性**：具体明确，包含具体方法和资源
5. **反馈机制**：包含自测和评估标准

## 复习计划结构
- 周期：{cycle_type}
- 目标：提升错题涉及知识点的掌握度
- 评估：包含前期、中期、后期评估

## 注意事项
- 考虑学生的认知水平和学习进度
- 避免过度安排，留出缓冲时间
- 每日任务应包含具体的学习方法（不只是题目）
"""
    
    async def _build_user_context(self, user_id: UUID) -> str:
        """构建用户学习背景上下文"""
        # 从数据库获取用户的：
        # - 年级/科目
        # - 平均学习时间
        # - 错题频率
        # - 薄弱知识点
        # 返回格式化文本
        pass
    
    def _calculate_expiry(self, cycle_type: str) -> datetime:
        """计算计划过期时间"""
        days_map = {
            "7days": 7,
            "14days": 14,
            "30days": 30,
        }
        days = days_map.get(cycle_type, 7)
        return datetime.utcnow() + timedelta(days=days)
    
    async def get_revision_plan(
        self,
        user_id: UUID,
        plan_id: UUID,
    ) -> RevisionPlan:
        """获取复习计划详情"""
        plan = await self.revision_repo.get_by_id(plan_id)
        
        if not plan or plan.user_id != user_id:
            raise ServiceError("计划不存在或无权访问")
        
        # 更新访问计数
        plan.view_count += 1
        await self.revision_repo.update(plan_id, {"view_count": plan.view_count})
        
        return plan
    
    async def list_revision_plans(
        self,
        user_id: UUID,
        limit: int = 10,
        offset: int = 0,
    ) -> dict:
        """获取复习计划列表"""
        plans = await self.revision_repo.find(
            filters={"user_id": user_id},
            order_by="created_at DESC",
            limit=limit,
            offset=offset,
        )
        
        total = await self.revision_repo.count({"user_id": user_id})
        
        return {
            "total": total,
            "items": plans,
            "limit": limit,
            "offset": offset,
        }
    
    async def download_revision_plan(
        self,
        user_id: UUID,
        plan_id: UUID,
    ) -> str:
        """记录下载统计"""
        plan = await self.get_revision_plan(user_id, plan_id)
        
        # 更新下载计数
        plan.download_count += 1
        await self.revision_repo.update(plan_id, {"download_count": plan.download_count})
        
        return plan.pdf_url
    
    def _parse_json_response(self, response: str) -> dict:
        """从 AI 响应中解析 JSON"""
        import json
        import re
        
        # 尝试找到 JSON 块
        match = re.search(r'\{[\s\S]*\}', response)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        
        # 如果失败，返回默认结构
        logger.warning(f"无法从 AI 响应解析 JSON，将使用默认结构")
        return self._generate_default_plan()
    
    def _generate_default_plan(self) -> dict:
        """生成默认复习计划结构"""
        return {
            "title": "个性化复习计划",
            "description": "基于你的错题数据生成的复习计划",
            "overview": "...",
            "statistics": {},
            "daily_tasks": [],
            "review_focus": [],
            "assessment": {},
            "tips": [],
        }
```

#### 3.2.2 PDFGeneratorService (新增)

```python
# src/services/pdf_generator_service.py

class PDFGeneratorService:
    """PDF 生成服务"""
    
    async def generate(
        self,
        title: str,
        content: dict,
        metadata: dict,
    ) -> BytesIO:
        """
        生成 PDF 文件
        
        使用 reportlab + weasyprint 组合：
        - reportlab: 用于简单表格和基础排版
        - weasyprint: 用于复杂 HTML 渲染
        
        ⚠️ 部署注意：
        在 Aliyun Linux 上需要安装系统依赖：
        yum install -y pango cairo cairo-gobject libffi-devel
        
        Args:
            title: 计划标题
            content: 复习计划 JSON 数据
            metadata: 元数据（用户信息、生成时间等）
        
        Returns:
            PDF 文件的 BytesIO 对象
        """
        
        # 1. 将 JSON 转换为 HTML
        html_content = self._build_html(title, content, metadata)
        
        # 2. 使用 weasyprint 生成 PDF
        pdf_bytes = self._render_html_to_pdf(html_content)
        
        return pdf_bytes
    
    def _build_html(self, title: str, content: dict, metadata: dict) -> str:
        """构建 PDF HTML 模板"""
        
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{title}</title>
    <style>
        @page {{
            size: A4;
            margin: 2cm;
        }}
        
        body {{
            font-family: 'SimSun', 'SimHei', sans-serif;
            line-height: 1.6;
            color: #333;
        }}
        
        .header {{
            text-align: center;
            border-bottom: 3px solid #007bff;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        
        .header h1 {{
            font-size: 28px;
            margin: 0 0 10px 0;
            color: #007bff;
        }}
        
        .metadata {{
            text-align: center;
            font-size: 12px;
            color: #666;
        }}
        
        .section {{
            margin-bottom: 25px;
        }}
        
        .section h2 {{
            font-size: 18px;
            color: #007bff;
            border-left: 4px solid #007bff;
            padding-left: 10px;
            margin-bottom: 15px;
        }}
        
        .overview {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 15px;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 15px;
            margin-bottom: 20px;
        }}
        
        .stat-card {{
            background: #e3f2fd;
            padding: 15px;
            border-radius: 5px;
            text-align: center;
        }}
        
        .stat-number {{
            font-size: 24px;
            font-weight: bold;
            color: #007bff;
        }}
        
        .stat-label {{
            font-size: 12px;
            color: #666;
            margin-top: 5px;
        }}
        
        .daily-task {{
            background: #fff;
            border: 1px solid #ddd;
            padding: 12px;
            margin-bottom: 10px;
            border-radius: 4px;
            page-break-inside: avoid;
        }}
        
        .task-day {{
            font-weight: bold;
            color: #007bff;
            margin-bottom: 8px;
        }}
        
        .task-items {{
            margin-left: 20px;
            font-size: 13px;
        }}
        
        .task-item {{
            margin-bottom: 5px;
            line-height: 1.4;
        }}
        
        .focus-list {{
            list-style: none;
            padding-left: 0;
        }}
        
        .focus-list li {{
            padding-left: 25px;
            margin-bottom: 8px;
            position: relative;
        }}
        
        .focus-list li:before {{
            content: "→";
            position: absolute;
            left: 0;
            color: #007bff;
        }}
        
        .assessment {{
            background: #fff3cd;
            padding: 15px;
            border-radius: 5px;
            border-left: 4px solid #ffc107;
        }}
        
        .footer {{
            text-align: center;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            font-size: 10px;
            color: #999;
        }}
        
        .watermark {{
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%) rotate(-45deg);
            font-size: 100px;
            color: rgba(0, 123, 255, 0.1);
            z-index: -1;
            white-space: nowrap;
        }}
    </style>
</head>
<body>
    <div class="watermark">{metadata.get('user_id', '五好伴学')}</div>
    
    <div class="header">
        <h1>{title}</h1>
        <p style="margin: 10px 0; font-size: 14px; color: #666;">
            {content.get('description', '')}
        </p>
        <div class="metadata">
            <p>生成时间：{metadata.get('generated_at', '')}</p>
        </div>
    </div>
    
    <!-- 概述 -->
    <div class="section">
        <h2>📋 计划概述</h2>
        <div class="overview">
            {content.get('overview', '个性化学习复习计划')}
        </div>
    </div>
    
    <!-- 统计信息 -->
    <div class="section">
        <h2>📊 数据统计</h2>
        <div class="stats-grid">
            {self._render_stats_cards(content.get('statistics', {}))}
        </div>
    </div>
    
    <!-- 每日任务 -->
    <div class="section">
        <h2>📅 每日任务规划</h2>
        {self._render_daily_tasks(content.get('daily_tasks', []))}
    </div>
    
    <!-- 复习重点 -->
    <div class="section">
        <h2>⭐ 复习重点</h2>
        <ul class="focus-list">
            {self._render_focus_points(content.get('review_focus', []))}
        </ul>
    </div>
    
    <!-- 评估标准 -->
    <div class="section">
        <h2>✓ 评估标准</h2>
        <div class="assessment">
            {self._render_assessment(content.get('assessment', {}))}
        </div>
    </div>
    
    <!-- 学习建议 -->
    {self._render_tips(content.get('tips', []))}
    
    <div class="footer">
        <p>© 2025 五好伴学 | 此文档由 AI 生成，仅供学习参考</p>
    </div>
</body>
</html>
        """
    
    def _render_stats_cards(self, stats: dict) -> str:
        """渲染统计卡片"""
        cards = []
        for key, value in stats.items():
            cards.append(f"""
                <div class="stat-card">
                    <div class="stat-number">{value}</div>
                    <div class="stat-label">{key}</div>
                </div>
            """)
        return "".join(cards)
    
    def _render_daily_tasks(self, tasks: list) -> str:
        """渲染每日任务"""
        tasks_html = []
        for task in tasks:
            items_html = "".join([
                f"<div class='task-item'>• {item}</div>"
                for item in task.get('tasks', [])
            ])
            tasks_html.append(f"""
                <div class="daily-task">
                    <div class="task-day">
                        第 {task.get('day')} 天 ({task.get('date')}) 
                        - 预计 {task.get('estimated_hours', 1.5)} 小时
                    </div>
                    <div class="task-items">{items_html}</div>
                </div>
            """)
        return "".join(tasks_html)
    
    def _render_focus_points(self, focus: list) -> str:
        """渲染重点"""
        return "".join([f"<li>{point}</li>" for point in focus])
    
    def _render_assessment(self, assessment: dict) -> str:
        """渲染评估标准"""
        html = []
        for criterion, details in assessment.items():
            html.append(f"<p><strong>{criterion}:</strong> {details}</p>")
        return "".join(html)
    
    def _render_tips(self, tips: list) -> str:
        """渲染学习建议"""
        if not tips:
            return ""
        
        tips_html = "".join([f"<li>{tip}</li>" for tip in tips])
        return f"""
        <div class="section">
            <h2>💡 学习建议</h2>
            <ul class="focus-list">{tips_html}</ul>
        </div>
        """
    
    def _render_html_to_pdf(self, html: str) -> BytesIO:
        """使用 weasyprint 将 HTML 渲染为 PDF"""
        from weasyprint import HTML, CSS
        
        pdf_bytes = BytesIO()
        HTML(string=html).write_pdf(pdf_bytes)
        pdf_bytes.seek(0)
        
        return pdf_bytes
```

### 3.3 API 端点设计

#### 3.3.1 路由定义

```python
# src/api/v1/endpoints/revisions.py

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import Optional

router = APIRouter(prefix="/revisions", tags=["revisions"])

@router.post("/generate")
async def generate_revision_plan(
    cycle_type: str = Query("7days", regex="^(7days|14days|30days)$"),
    force_regenerate: bool = Query(False),
    user_id: UUID = Depends(get_current_user),
    service: RevisionPlanService = Depends(get_revision_plan_service),
) -> dict:
    """
    生成复习计划
    
    - **cycle_type**: 计划周期 (7days|14days|30days)
    - **force_regenerate**: 是否强制重新生成（忽略缓存）
    
    返回：复习计划对象 + PDF 下载链接
    
    ⚠️ 耗时操作（可能 30-60 秒），建议前端显示进度条
    """
    try:
        plan = await service.generate_revision_plan(
            user_id=user_id,
            cycle_type=cycle_type,
            force_regenerate=force_regenerate,
        )
        
        return {
            "status": "success",
            "data": {
                "id": str(plan.id),
                "title": plan.title,
                "cycle_type": plan.cycle_type,
                "pdf_url": plan.pdf_url,
                "plan_content": plan.plan_content,
                "created_at": plan.created_at.isoformat(),
            }
        }
    except ServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"生成复习计划失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="服务器内部错误")


@router.get("/{plan_id}")
async def get_revision_plan(
    plan_id: UUID,
    user_id: UUID = Depends(get_current_user),
    service: RevisionPlanService = Depends(get_revision_plan_service),
) -> dict:
    """获取复习计划详情"""
    try:
        plan = await service.get_revision_plan(user_id, plan_id)
        
        return {
            "status": "success",
            "data": {
                "id": str(plan.id),
                "title": plan.title,
                "description": plan.description,
                "cycle_type": plan.cycle_type,
                "status": plan.status,
                "mistake_count": plan.mistake_count,
                "knowledge_points": plan.knowledge_points,
                "plan_content": plan.plan_content,
                "pdf_url": plan.pdf_url,
                "view_count": plan.view_count,
                "download_count": plan.download_count,
                "created_at": plan.created_at.isoformat(),
                "expired_at": plan.expired_at.isoformat() if plan.expired_at else None,
            }
        }
    except ServiceError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("")
async def list_revision_plans(
    limit: int = Query(10, ge=1, le=50),
    offset: int = Query(0, ge=0),
    user_id: UUID = Depends(get_current_user),
    service: RevisionPlanService = Depends(get_revision_plan_service),
) -> dict:
    """获取复习计划列表（分页）"""
    result = await service.list_revision_plans(user_id, limit, offset)
    
    return {
        "status": "success",
        "data": {
            "total": result["total"],
            "items": [
                {
                    "id": str(p.id),
                    "title": p.title,
                    "cycle_type": p.cycle_type,
                    "status": p.status,
                    "mistake_count": p.mistake_count,
                    "created_at": p.created_at.isoformat(),
                    "expired_at": p.expired_at.isoformat() if p.expired_at else None,
                    "view_count": p.view_count,
                }
                for p in result["items"]
            ],
            "limit": limit,
            "offset": offset,
        }
    }


@router.get("/{plan_id}/download")
async def download_revision_plan(
    plan_id: UUID,
    user_id: UUID = Depends(get_current_user),
    service: RevisionPlanService = Depends(get_revision_plan_service),
):
    """
    获取 PDF 下载链接
    
    返回：PDF 文件的 OSS 签名链接 (Signed URL)
    
    前端 (小程序) 处理流程：
    1. 调用此接口获取 url
    2. 使用 `wx.downloadFile({ url: res.data.pdf_url })` 下载
    3. 使用 `wx.openDocument()` 预览
    """
    try:
        pdf_url = await service.download_revision_plan(user_id, plan_id)
        
        return {
            "status": "success",
            "data": {
                "pdf_url": pdf_url,
            }
        }
    except ServiceError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{plan_id}")
async def delete_revision_plan(
    plan_id: UUID,
    user_id: UUID = Depends(get_current_user),
    service: RevisionPlanService = Depends(get_revision_plan_service),
) -> dict:
    """删除复习计划"""
    try:
        await service.delete_revision_plan(user_id, plan_id)
        
        return {
            "status": "success",
            "message": "计划已删除"
        }
    except ServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

---

## 四、前端设计

### 4.1 UI 组件结构

#### 4.1.1 学习报告页面改造

```
学习报告页面 (pages/analytics 或 pages/report)
│
├─ 统计概览（现有）
│  ├─ 学习时间
│  ├─ 问题数量
│  └─ 错题数
│
├─ 📋 AI 复习计划（新增模块）
│  │
│  ├─ 状态展示区
│  │  ├─ 最新计划卡片
│  │  │  ├─ 标题
│  │  │  ├─ 周期（7/14/30天）
│  │  │  ├─ 涉及错题数
│  │  │  └─ 生成时间
│  │  │
│  │  └─ 计划历史列表
│  │
│  ├─ 操作按钮区
│  │  ├─ "生成新计划" 按钮
│  │  ├─ 周期选择器（7/14/30天）
│  │  ├─ "刷新" 按钮（重新生成）
│  │  └─ "下载 PDF" 按钮
│  │
│  ├─ 计划内容预览
│  │  ├─ 概述
│  │  ├─ 每日任务摘要（前3天）
│  │  └─ "查看详情" 链接
│  │
│  └─ 加载/错误状态
│     ├─ 生成中动画
│     ├─ 进度条
│     └─ 错误提示
```

#### 4.1.2 新增子页面

```
复习计划详情页 (pages/revision-detail)
│
├─ 顶部
│  ├─ 标题 + 周期标签
│  ├─ 生成时间 + 过期时间
│  └─ 分享 + 删除按钮
│
├─ 标签页切换
│  ├─ 概览标签
│  │  ├─ 计划描述
│  │  ├─ 数据统计卡片
│  │  └─ 学习建议
│  │
│  ├─ 每日任务标签
│  │  ├─ 日期筛选器
│  │  └─ 任务列表（可收起）
│  │
│  ├─ 重点复习标签
│  │  └─ 知识点列表
│  │
│  └─ 评估标签
│     └─ 评估标准和自测题
│
└─ 底部
   ├─ 下载 PDF 按钮
   ├─ 分享计划
   └─ 返回按钮
```

### 4.2 小程序端代码示例

```typescript
// miniprogram/pages/revision-plan/index.wxml

<view class="revision-plan-container">
  <!-- 标题 -->
  <view class="header">
    <text class="title">📋 AI 复习计划</text>
    <text class="subtitle">基于你的错题数据，智能生成个性化复习指导</text>
  </view>

  <!-- 状态显示 -->
  <view class="status-section" wx:if="{{!loading && !error}}">
    <!-- 最新计划卡片 -->
    <view class="plan-card" wx:if="{{currentPlan}}">
      <view class="plan-header">
        <text class="plan-title">{{currentPlan.title}}</text>
        <view class="plan-meta">
          <text class="tag">{{cycleTypeLabel}}</text>
          <text class="time">{{formatDate(currentPlan.created_at)}}</text>
        </view>
      </view>
      
      <view class="plan-stats">
        <view class="stat">
          <text class="stat-number">{{currentPlan.mistake_count}}</text>
          <text class="stat-label">涉及错题</text>
        </view>
        <view class="stat">
          <text class="stat-number">{{currentPlan.knowledge_points.length}}</text>
          <text class="stat-label">知识点</text>
        </view>
        <view class="stat">
          <text class="stat-number">{{cycleType === '7days' ? 7 : cycleType === '14days' ? 14 : 30}}</text>
          <text class="stat-label">天数</text>
        </view>
      </view>

      <view class="plan-preview">
        <text class="preview-title">计划预览</text>
        <text class="preview-text">{{currentPlan.plan_content.overview}}</text>
      </view>

      <view class="plan-actions">
        <button class="btn btn-primary" bindtap="onViewDetail">查看详情</button>
        <button class="btn btn-secondary" bindtap="onDownloadPDF">下载 PDF</button>
      </view>
    </view>

    <!-- 无计划提示 -->
    <view class="empty-state" wx:else>
      <view class="empty-icon">📭</view>
      <text class="empty-text">还没有复习计划</text>
      <text class="empty-hint">生成第一个复习计划，开启智能学习之旅</text>
    </view>
  </view>

  <!-- 生成控制区 -->
  <view class="control-section">
    <view class="cycle-selector">
      <text class="selector-label">选择计划周期：</text>
      <view class="cycle-options">
        <view class="option {{cycleType === '7days' ? 'active' : ''}}"
              bindtap="onSelectCycle"
              data-cycle="7days">
          7天
        </view>
        <view class="option {{cycleType === '14days' ? 'active' : ''}}"
              bindtap="onSelectCycle"
              data-cycle="14days">
          14天
        </view>
        <view class="option {{cycleType === '30days' ? 'active' : ''}}"
              bindtap="onSelectCycle"
              data-cycle="30days">
          30天
        </view>
      </view>
    </view>

    <button class="btn btn-large {{generating ? 'disabled' : 'btn-primary'}}"
            bindtap="onGeneratePlan"
            disabled="{{generating}}">
      <text wx:if="{{!generating}}">🚀 生成复习计划</text>
      <text wx:else>生成中... {{progress}}%</text>
    </button>

    <button class="btn btn-secondary" 
            bindtap="onRefresh"
            disabled="{{generating}}">
      刷新（重新生成）
    </button>
  </view>

  <!-- 历史列表 -->
  <view class="history-section" wx:if="{{plans.length > 1}}">
    <text class="section-title">计划历史</text>
    <view class="plan-list">
      <view class="plan-item {{plan.id === currentPlan.id ? 'active' : ''}}"
            wx:for="{{plans}}"
            wx:key="id"
            bindtap="onSelectPlan"
            data-plan-id="{{plan.id}}">
        <view class="item-header">
          <text class="item-title">{{plan.title}}</text>
          <view class="item-meta">
            <text class="status {{plan.status}}">{{formatStatus(plan.status)}}</text>
            <text class="date">{{formatDate(plan.created_at)}}</text>
          </view>
        </view>
        <text class="item-desc">{{plan.mistake_count}} 个错题 • {{plan.knowledge_points.length}} 个知识点</text>
      </view>
    </view>
  </view>

  <!-- 加载状态 -->
  <view class="loading" wx:if="{{loading}}">
    <view class="loading-spinner"></view>
    <text>正在为你生成个性化复习计划...</text>
    <view class="progress-bar">
      <view class="progress" style="width: {{progress}}%"></view>
    </view>
  </view>

  <!-- 错误处理 -->
  <view class="error-message" wx:if="{{error}}">
    <text class="error-icon">⚠️</text>
    <text class="error-text">{{error}}</text>
    <button class="btn btn-secondary" bindtap="onRetry">重试</button>
  </view>
</view>
```

```typescript
// miniprogram/pages/revision-plan/index.ts

import { api } from '@/utils/api'
import { toast } from '@/utils/toast'

Page({
  data: {
    // 状态
    loading: false,
    generating: false,
    error: null,
    progress: 0,

    // 数据
    cycleType: '7days',
    currentPlan: null,
    plans: [],

    // UI
    tabActive: 0,
  },

  onLoad() {
    this.loadPlans()
  },

  onShow() {
    // 重新加载（防止页面切换后数据过期）
    this.loadPlans()
  },

  async loadPlans() {
    this.setData({ loading: true })
    try {
      const res = await api.revisions.listPlans({
        limit: 10,
        offset: 0,
      })

      const plans = res.data.items || []
      this.setData({
        plans,
        currentPlan: plans[0] || null,
      })
    } catch (err) {
      toast.error('加载复习计划失败')
      logger.error('loadPlans failed:', err)
    } finally {
      this.setData({ loading: false })
    }
  },

  async onGeneratePlan() {
    if (this.data.generating) return

    this.setData({ generating: true, progress: 0, error: null })

    try {
      // 模拟进度更新（实际由后端推送或前端轮询）
      const progressInterval = setInterval(() => {
        const current = this.data.progress
        if (current < 90) {
          this.setData({ progress: current + Math.random() * 20 })
        }
      }, 1000)

      const res = await api.revisions.generatePlan({
        cycle_type: this.data.cycleType,
        force_regenerate: false,
      })

      clearInterval(progressInterval)
      this.setData({ progress: 100 })

      // 更新 UI
      const newPlan = res.data
      const plans = [newPlan, ...this.data.plans]
      this.setData({
        currentPlan: newPlan,
        plans: plans.slice(0, 10), // 只保留最近10个
      })

      toast.success('复习计划生成成功！')

      // 1秒后隐藏加载状态
      setTimeout(() => {
        this.setData({ generating: false, progress: 0 })
      }, 1000)
    } catch (err: any) {
      this.setData({
        generating: false,
        error: err.message || '生成复习计划失败，请重试',
      })
      logger.error('generatePlan failed:', err)
    }
  },

  onSelectCycle(e: any) {
    const cycle = e.currentTarget.dataset.cycle
    this.setData({ cycleType: cycle })
  },

  onRefresh() {
    // 强制重新生成
    this.setData({ cycleType: this.data.cycleType }, () => {
      this.onGeneratePlan()
    })
  },

  async onDownloadPDF() {
    if (!this.data.currentPlan?.pdf_url) {
      toast.error('PDF 文件不可用')
      return
    }

    try {
      toast.loading('准备下载...')

      const res = await api.revisions.downloadPlan(this.data.currentPlan.id)
      const pdf_url = res.data.pdf_url

      // 记录下载
      wx.downloadFile({
        url: pdf_url,
        success: (res) => {
          // 保存到相册或本地
          wx.saveFile({
            tempFilePath: res.tempFilePath,
            success: () => {
              toast.success('下载完成，已保存到本地')
            },
          })
        },
        fail: (err) => {
          toast.error('下载失败，请检查网络')
          logger.error('downloadFile failed:', err)
        },
      })
    } catch (err) {
      toast.error('获取下载链接失败')
      logger.error('downloadPlan failed:', err)
    }
  },

  onViewDetail() {
    if (!this.data.currentPlan) return

    wx.navigateTo({
      url: `/pages/revision-detail/index?plan_id=${this.data.currentPlan.id}`,
    })
  },

  onSelectPlan(e: any) {
    const planId = e.currentTarget.dataset.planId
    const plan = this.data.plans.find(p => p.id === planId)
    if (plan) {
      this.setData({ currentPlan: plan })
    }
  },

  onRetry() {
    this.setData({ error: null })
    this.onGeneratePlan()
  },

  formatDate(date: string) {
    // 格式化时间
    return new Date(date).toLocaleDateString('zh-CN', {
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    })
  },

  formatStatus(status: string) {
    const statusMap: any = {
      draft: '草稿',
      published: '已发布',
      completed: '已完成',
      expired: '已过期',
    }
    return statusMap[status] || status
  },
})
```

---

## 五、技术实现细节

### 5.1 大模型提示词优化

#### 5.1.1 核心提示词模板

```
你是一位资深的学习规划师和教育顾问。

## 用户背景
- 年级/科目：[用户信息]
- 学习风格：[学习风格分析]
- 当前状态：[学习进度]

## 任务
基于以下错题数据，为学生制定一份[周期]的个性化复习计划。

## 错题分析
[Markdown 格式的错题数据]

## 要求
1. **目标明确**：明确指出通过本计划要达成的学习目标
2. **计划细致**：分解为具体的每日任务，每项任务应包含：
   - 学习内容
   - 学习方法（不仅是题目，要有技巧）
   - 预期耗时
   - 自检标准

3. **难度递进**：第一周基础巩固，后续逐步提升
4. **可执行性**：每日任务时间合理（1-3小时），有具体学习资源建议
5. **反馈机制**：提供每周检查点和月末评估标准
6. **激励性**：包含积极的学习建议和鼓励语言

## 输出格式
返回 JSON，包含：
{
  "title": "标题",
  "description": "简述",
  "overview": "计划概述文字（200字左右）",
  "statistics": {
    "错题总数": XX,
    "涉及知识点": XX,
    ...
  },
  "daily_tasks": [
    {
      "day": 1,
      "date": "2025-01-16",
      "tasks": ["任务1", "任务2", ...],
      "estimated_hours": 1.5
    }
  ],
  "review_focus": ["重点1", "重点2", ...],
  "assessment": {
    "第一周检查": "...",
    "月末评估": "..."
  },
  "tips": ["建议1", "建议2", ...]
}
```

### 5.2 性能优化策略

#### 5.2.1 缓存机制

```python
# 缓存策略
- 同一用户、同一周期内 24 小时内的计划视为有效缓存
- 新增错题后，缓存自动失效
- 用户可手动强制重新生成（忽略缓存）

# 缓存存储
- 使用 Redis（推荐）
- Key 格式：revision_plan:{user_id}:{cycle_type}
- TTL：24 小时
```

#### 5.2.2 异步处理

```python
# 后端使用后台任务
- 大模型调用（耗时 30-60s）
- PDF 生成（耗时 10-20s）
- 使用 Celery/APScheduler 异步处理
- 前端轮询查询状态或使用 WebSocket 推送

# 前端显示进度
- 模拟进度条（0-90%）
- 完成后跳转到详情页
- 支持后台生成，用户可先离开
```

### 5.3 成本控制

| 方案 | 成本 | 特点 |
|------|------|------|
| **按次计费** | ~¥0.1-0.5/次 | 频率控制（24h缓存），用户量大时总成本可控 |
| **包月套餐** | ~¥1000/月 | 百炼包年包月方案，适合用户规模 > 1000 |
| **免费额度** | ~3000次/月 | 初期使用，满足小规模用户 |

### 5.4 文件存储

```python
# 存储选项
1. **本地文件系统**
   - 简单，无额外成本
   - 风险：服务器硬盘容量有限
   - 适合：初期测试

2. **阿里云 OSS**（推荐）
   - URL 可直接分享
   - 自动过期清理
   - 成本：~¥0.12/GB/月

3. **七牛云**
   - 国内 CDN，加载快
   - 成本相似

配置：
- 存储位置：revision-plans/{user_id}/{timestamp}.pdf
- 访问权限：私有 + 预签名 URL（1小时有效期）
- 自动删除：30天无访问自动清理
```

---

## 六、数据库迁移

### 6.1 新增表

```sql
-- revision_plans 表
CREATE TABLE revision_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    title VARCHAR(255) NOT NULL,
    description TEXT,
    cycle_type VARCHAR(20) NOT NULL, -- 7days|14days|30days
    status VARCHAR(20) NOT NULL DEFAULT 'draft', -- draft|published|completed|expired
    
    mistake_count INT NOT NULL DEFAULT 0,
    knowledge_points JSONB NOT NULL DEFAULT '[]',
    date_range JSONB NOT NULL,
    
    plan_content JSONB NOT NULL,
    pdf_url VARCHAR(500),
    pdf_size INT,
    markdown_url VARCHAR(500),
    
    download_count INT NOT NULL DEFAULT 0,
    view_count INT NOT NULL DEFAULT 0,
    is_shared BOOLEAN NOT NULL DEFAULT FALSE,
    
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expired_at TIMESTAMP,
    completed_at TIMESTAMP,
    
    CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX idx_revision_plans_user_id ON revision_plans(user_id);
CREATE INDEX idx_revision_plans_created_at ON revision_plans(created_at DESC);
CREATE INDEX idx_revision_plans_expired_at ON revision_plans(expired_at);

-- revision_plan_progress 表（可选）
CREATE TABLE revision_plan_progress (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    revision_plan_id UUID NOT NULL REFERENCES revision_plans(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    completed_tasks JSONB NOT NULL DEFAULT '[]',
    completion_rate NUMERIC(5, 2) NOT NULL DEFAULT 0,
    last_reviewed_at TIMESTAMP,
    notes TEXT,
    
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_progress_revision_plan_id ON revision_plan_progress(revision_plan_id);
CREATE INDEX idx_progress_user_id ON revision_plan_progress(user_id);
```

### 6.2 迁移脚本

```bash
# alembic/versions/XXX_add_revision_plans.py

def upgrade():
    op.create_table(
        'revision_plans',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        # ... 其他字段 ...
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_index('idx_revision_plans_user_id', 'revision_plans', ['user_id'])

def downgrade():
    op.drop_table('revision_plans')
```

---

## 七、集成检查清单

### 7.1 后端集成

- [x] 创建 RevisionPlan 数据模型
- [x] 创建 RevisionPlanRepository
- [x] 实现 RevisionPlanService
- [x] 实现 PDFGeneratorService
- [ ] 添加 /api/v1/revisions 路由
- [x] 添加大模型提示词配置 (集成在 Service 中)
- [x] 配置 PDF 文件存储（OSS/本地）
- [x] 数据库迁移脚本
- [ ] 异步任务配置（可选）
- [ ] 单元测试 + 集成测试
- [ ] 日志和监控

### 7.2 前端集成

- [ ] 在学习报告页添加"AI 复习计划"模块
- [ ] 实现复习计划主页面
- [ ] 实现复习计划详情页面
- [ ] 实现 PDF 下载功能
- [ ] 添加 API 调用（api.revisions）
- [ ] 错误处理和提示
- [ ] 加载状态和进度条
- [ ] 缓存管理
- [ ] 单元测试
-