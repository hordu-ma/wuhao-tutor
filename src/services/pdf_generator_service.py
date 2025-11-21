"""
PDF生成服务
用于将复习计划生成为PDF文件
"""

from io import BytesIO
from typing import Any, Dict, List

try:
    from weasyprint import HTML
except OSError as e:
    # 允许在缺少系统依赖的环境中导入，但在使用时报错
    import logging

    logging.getLogger(__name__).warning(f"WeasyPrint 系统依赖缺失: {e}")
    HTML = None
except ImportError as e:
    import logging

    logging.getLogger(__name__).warning(f"WeasyPrint 未安装: {e}")
    HTML = None

from src.core.logging import get_logger

logger = get_logger(__name__)


class PDFGeneratorService:
    """PDF 生成服务"""

    async def generate(
        self,
        title: str,
        content: Dict[str, Any],
        metadata: Dict[str, Any],
    ) -> BytesIO:
        """
        生成 PDF 文件

        使用 weasyprint 将 HTML 渲染为 PDF

        Args:
            title: 计划标题
            content: 复习计划 JSON 数据
            metadata: 元数据（用户信息、生成时间等）

        Returns:
            PDF 文件的 BytesIO 对象
        """
        try:
            # 1. 将 JSON 转换为 HTML
            html_content = self._build_html(title, content, metadata)

            # 2. 使用 weasyprint 生成 PDF
            pdf_bytes = self._render_html_to_pdf(html_content)

            return pdf_bytes
        except Exception as e:
            logger.error(f"PDF生成失败: {str(e)}", exc_info=True)
            raise

    def _build_html(
        self, title: str, content: Dict[str, Any], metadata: Dict[str, Any]
    ) -> str:
        """构建 PDF HTML 模板"""

        # 辅助函数：安全获取字典值
        def get_val(data: Dict, key: str, default: Any = "") -> Any:
            return data.get(key, default)

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
    <div class="watermark">{get_val(metadata, "user_id", "五好伴学")}</div>
    
    <div class="header">
        <h1>{title}</h1>
        <p style="margin: 10px 0; font-size: 14px; color: #666;">
            {get_val(content, "description", "")}
        </p>
        <div class="metadata">
            <p>生成时间：{get_val(metadata, "generated_at", "")}</p>
        </div>
    </div>
    
    <!-- 概述 -->
    <div class="section">
        <h2>📋 计划概述</h2>
        <div class="overview">
            {get_val(content, "overview", "个性化学习复习计划")}
        </div>
    </div>
    
    <!-- 统计信息 -->
    <div class="section">
        <h2>📊 数据统计</h2>
        <div class="stats-grid">
            {self._render_stats_cards(get_val(content, "statistics", {}))}
        </div>
    </div>
    
    <!-- 每日任务 -->
    <div class="section">
        <h2>📅 每日任务规划</h2>
        {self._render_daily_tasks(get_val(content, "daily_tasks", []))}
    </div>
    
    <!-- 复习重点 -->
    <div class="section">
        <h2>⭐ 复习重点</h2>
        <ul class="focus-list">
            {self._render_focus_points(get_val(content, "review_focus", []))}
        </ul>
    </div>
    
    <!-- 评估标准 -->
    <div class="section">
        <h2>✓ 评估标准</h2>
        <div class="assessment">
            {self._render_assessment(get_val(content, "assessment", {}))}
        </div>
    </div>
    
    <!-- 学习建议 -->
    {self._render_tips(get_val(content, "tips", []))}
    
    <div class="footer">
        <p>© 2025 五好伴学 | 此文档由 AI 生成，仅供学习参考</p>
    </div>
</body>
</html>
        """

    def _render_stats_cards(self, stats: Dict[str, Any]) -> str:
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

    def _render_daily_tasks(self, tasks: List[Dict[str, Any]]) -> str:
        """渲染每日任务"""
        tasks_html = []
        for task in tasks:
            items_html = "".join(
                [
                    f"<div class='task-item'>• {item}</div>"
                    for item in task.get("tasks", [])
                ]
            )
            tasks_html.append(f"""
                <div class="daily-task">
                    <div class="task-day">
                        第 {task.get("day")} 天 ({task.get("date")}) 
                        - 预计 {task.get("estimated_hours", 1.5)} 小时
                    </div>
                    <div class="task-items">{items_html}</div>
                </div>
            """)
        return "".join(tasks_html)

    def _render_focus_points(self, focus: List[str]) -> str:
        """渲染重点"""
        return "".join([f"<li>{point}</li>" for point in focus])

    def _render_assessment(self, assessment: Dict[str, Any]) -> str:
        """渲染评估标准"""
        html = []
        for criterion, details in assessment.items():
            html.append(f"<p><strong>{criterion}:</strong> {details}</p>")
        return "".join(html)

    def _render_tips(self, tips: List[str]) -> str:
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
        if HTML is None:
            raise RuntimeError("WeasyPrint 未正确安装或缺少系统依赖，无法生成 PDF")

        pdf_bytes = BytesIO()
        HTML(string=html).write_pdf(pdf_bytes)
        pdf_bytes.seek(0)

        return pdf_bytes
