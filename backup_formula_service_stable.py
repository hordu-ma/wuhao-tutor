"""
数学公式渲染服务
将LaTeX格式的数学公式转换为图片URL，适配微信小程序显示
"""

import hashlib
import logging
import re
from typing import Any, Dict, List, Optional
from urllib.parse import quote

import httpx

from src.core.config import get_settings
from src.core.exceptions import ServiceError
from src.utils.file_upload import get_ai_image_access_service

logger = logging.getLogger(__name__)
settings = get_settings()


class FormulaService:
    """数学公式渲染服务"""

    def __init__(self):
        self.ai_image_service = get_ai_image_access_service()
        self.client = httpx.AsyncClient(timeout=30.0)

        # QuickLaTeX配置
        self.quicklatex_api = "https://quicklatex.com/latex3.f"
        self.default_formula_size = "\\large"  # 公式大小
        self.cache_prefix = "formula_cache/"  # OSS缓存路径前缀

    async def process_text_with_formulas(self, text: str) -> str:
        """
        处理包含LaTeX公式的文本，将公式转换为图片URL

        Args:
            text: 原始文本内容

        Returns:
            处理后的文本，公式已替换为图片标签
        """
        if not text:
            return text

        try:
            # 1. 检测并提取公式
            formulas = self._extract_formulas(text)
            if not formulas:
                return text

            # 2. 批量渲染公式
            formula_urls = await self._batch_render_formulas(formulas)

            # 3. 替换原文中的公式
            processed_text = await self._replace_formulas_with_images(
                text, formulas, formula_urls
            )

            logger.info(
                f"成功处理 {len(formulas)} 个数学公式",
                extra={
                    "formula_count": len(formulas),
                    "original_length": len(text),
                    "processed_length": len(processed_text),
                },
            )

            return processed_text

        except Exception as e:
            logger.error(f"公式处理失败: {e}", exc_info=True)
            # 出错时返回原文本，不影响正常功能
            return text

    def _extract_formulas(self, text: str) -> List[Dict[str, Any]]:
        """
        从文本中提取LaTeX公式

        Returns:
            List[Dict]: 公式信息列表，包含 {type, content, full_match}
        """
        formulas = []

        # 1. 匹配块级公式 $$...$$
        block_pattern = r"\$\$\s*(.*?)\s*\$\$"
        for match in re.finditer(block_pattern, text, re.DOTALL):
            formulas.append(
                {
                    "type": "block",
                    "content": match.group(1).strip(),
                    "full_match": match.group(0),
                    "start": match.start(),
                    "end": match.end(),
                }
            )

        # 2. 匹配行内公式 $...$（排除已被块级公式包含的部分）
        inline_pattern = r"(?<!\$)\$([^$\n]+)\$(?!\$)"
        for match in re.finditer(inline_pattern, text):
            # 检查是否在块级公式内
            is_inside_block = any(
                block["start"] <= match.start() < block["end"]
                for block in formulas
                if block["type"] == "block"
            )

            if not is_inside_block:
                formulas.append(
                    {
                        "type": "inline",
                        "content": match.group(1).strip(),
                        "full_match": match.group(0),
                        "start": match.start(),
                        "end": match.end(),
                    }
                )

        # 按位置排序
        formulas.sort(key=lambda x: x["start"])

        logger.debug(f"提取到 {len(formulas)} 个公式")
        return formulas

    async def _batch_render_formulas(
        self, formulas: List[Dict[str, Any]]
    ) -> Dict[str, str]:
        """
        批量渲染公式为图片URL

        Returns:
            Dict: {formula_content: image_url}
        """
        formula_urls = {}

        for formula_info in formulas:
            content = formula_info["content"]
            if not content:
                continue

            try:
                # 生成缓存键
                cache_key = self._generate_cache_key(content, formula_info["type"])

                # 检查缓存
                cached_url = await self._get_cached_formula_url(cache_key)
                if cached_url:
                    formula_urls[content] = cached_url
                    continue

                # 渲染新公式
                image_url = await self._render_single_formula(
                    content, formula_info["type"], cache_key
                )

                if image_url:
                    formula_urls[content] = image_url

            except Exception as e:
                logger.warning(f"渲染公式失败: {content[:50]}... - {e}")
                continue

        return formula_urls

    def _generate_cache_key(self, content: str, formula_type: str) -> str:
        """生成公式缓存键"""
        # 使用内容和类型生成MD5哈希
        text_to_hash = f"{formula_type}:{content}:{self.default_formula_size}"
        return hashlib.md5(text_to_hash.encode("utf-8")).hexdigest()

    async def _get_cached_formula_url(self, cache_key: str) -> Optional[str]:
        """检查公式缓存"""
        try:
            # 构建缓存文件路径，优先检查PNG
            png_path = f"{self.cache_prefix}{cache_key}.png"
            svg_path = f"{self.cache_prefix}{cache_key}.svg"

            # 检查OSS中是否存在（这里暂时返回None，因为检查文件存在需要特殊处理）
            # TODO: 实现OSS文件存在检查
            return None
        except Exception:
            return None

    async def _render_single_formula(
        self, content: str, formula_type: str, cache_key: str
    ) -> Optional[str]:
        """
        渲染单个公式

        Args:
            content: LaTeX公式内容
            formula_type: 公式类型 (inline/block)
            cache_key: 缓存键

        Returns:
            图片URL或None
        """
        try:
            # 1. 准备LaTeX代码
            latex_code = self._prepare_latex_code(content, formula_type)

            # 2. 调用QuickLaTeX API
            image_content = await self._call_quicklatex_api(latex_code)
            if not image_content:
                return None

            # 3. 保存到OSS
            if image_content.startswith("data:image/png;base64,"):
                # PNG格式，保存为PNG文件
                import base64

                base64_data = image_content.split(",")[1]
                image_bytes = base64.b64decode(base64_data)

                cache_path = f"{self.cache_prefix}{cache_key}.png"
                try:
                    image_url = await self.ai_image_service.upload_file(
                        file_data=image_bytes,
                        object_name=cache_path,
                        content_type="image/png",
                    )
                    return image_url
                except Exception as e:
                    logger.warning(f"上传PNG到OSS失败: {e}")
                    return None
            else:
                # SVG格式
                cache_path = f"{self.cache_prefix}{cache_key}.svg"
                try:
                    image_url = await self.ai_image_service.upload_file(
                        file_data=image_content.encode("utf-8"),
                        object_name=cache_path,
                        content_type="image/svg+xml",
                    )
                    return image_url
                except Exception as e:
                    logger.warning(f"上传SVG到OSS失败: {e}")
                    return None

        except Exception as e:
            logger.error(f"渲染公式失败: {content} - {e}")
            return None

    def _prepare_latex_code(self, content: str, formula_type: str) -> str:
        """准备LaTeX代码"""
        # 清理内容
        clean_content = content.strip()

        # 根据类型添加适当的LaTeX环境
        if formula_type == "block":
            # 块级公式，居中显示
            latex_code = f"\\documentclass{{standalone}}\n\\begin{{document}}\n\\{self.default_formula_size} ${clean_content}$\n\\end{{document}}"
        else:
            # 行内公式
            latex_code = f"\\documentclass{{standalone}}\n\\begin{{document}}\n\\{self.default_formula_size} ${clean_content}$\n\\end{{document}}"

        return latex_code

    async def _call_quicklatex_api(self, latex_code: str) -> Optional[str]:
        """
        调用QuickLaTeX API渲染公式

        Args:
            latex_code: 完整的LaTeX代码

        Returns:
            SVG内容或None
        """
        try:
            # QuickLaTeX请求参数
            payload = {
                "formula": latex_code,
                "fsize": "17px",  # 字体大小
                "fcolor": "000000",  # 字体颜色(黑色)
                "mode": "0",  # 0=SVG, 1=PNG
                "out": "1",  # 输出格式
                "remhost": "quicklatex.com",
            }

            # 发送请求
            response = await self.client.post(
                self.quicklatex_api,
                data=payload,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

            if response.status_code != 200:
                logger.warning(f"QuickLaTeX API返回错误: {response.status_code}")
                return None

            response_text = response.text

            # 解析响应 (QuickLaTeX返回格式: status url log)
            lines = response_text.strip().split("\n")
            if len(lines) < 2:
                logger.warning(f"QuickLaTeX响应格式异常: {response_text}")
                return None

            status = lines[0].strip()
            if status != "0":  # 0表示成功
                logger.warning(f"QuickLaTeX渲染失败: status={status}")
                return None

            # 解析URL（格式：url params...）
            url_line = lines[1].strip()
            image_url = url_line.split()[0]  # 只取第一部分作为URL

            # 下载图片内容
            image_response = await self.client.get(image_url)
            if image_response.status_code == 200:
                # 根据URL判断是PNG还是SVG
                if image_url.endswith(".png"):
                    # 返回PNG的base64编码
                    import base64

                    image_b64 = base64.b64encode(image_response.content).decode("utf-8")
                    return f"data:image/png;base64,{image_b64}"
                else:
                    # SVG直接返回内容
                    return image_response.text

            return None

        except Exception as e:
            logger.error(f"调用QuickLaTeX API失败: {e}")
            return None

    async def _replace_formulas_with_images(
        self, text: str, formulas: List[Dict[str, Any]], formula_urls: Dict[str, str]
    ) -> str:
        """将文本中的公式替换为图片标签"""
        processed_text = text

        # 按位置倒序替换，避免位置偏移
        for formula_info in reversed(formulas):
            content = formula_info["content"]
            full_match = formula_info["full_match"]

            if content in formula_urls:
                image_url = formula_urls[content]
                formula_type = formula_info["type"]

                # 生成图片标签
                if formula_type == "block":
                    # 块级公式，居中显示
                    img_tag = f'<div class="math-formula-block" style="text-align: center; margin: 10px 0;"><img src="{image_url}" alt="{content}" style="max-width: 100%; height: auto;" /></div>'
                else:
                    # 行内公式
                    img_tag = f'<img class="math-formula-inline" src="{image_url}" alt="{content}" style="display: inline; vertical-align: middle; max-height: 1.2em;" />'

                # 替换原文
                processed_text = processed_text.replace(full_match, img_tag, 1)

        return processed_text

    async def cleanup(self):
        """清理资源"""
        await self.client.aclose()


# 全局实例
_formula_service: Optional[FormulaService] = None


def get_formula_service() -> FormulaService:
    """获取公式服务实例"""
    global _formula_service
    if _formula_service is None:
        _formula_service = FormulaService()
    return _formula_service
