"""
数学公式渲染服务
将LaTeX格式的数学公式转换为图片URL，适配微信小程序显示
"""

import asyncio
import hashlib
import logging
import re
import time
from typing import Any, Dict, List, Optional
from urllib.parse import quote

import httpx

from src.core.config import get_settings
from src.core.exceptions import ServiceError
from src.core.monitoring import get_formula_metrics
from src.utils.file_upload import get_ai_image_access_service

logger = logging.getLogger(__name__)
settings = get_settings()


class FormulaService:
    """数学公式渲染服务"""

    def __init__(self):
        self.ai_image_service = get_ai_image_access_service()
        self.client = httpx.AsyncClient(timeout=30.0)

        # 监控指标
        self.metrics = get_formula_metrics()

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
        """
        检查公式缓存（多层缓存策略）

        优先级：
        1. 数据库缓存（最快）
        2. OSS 文件存在检查

        Returns:
            缓存的图片 URL 或 None
        """
        try:
            # 1. 先查数据库缓存
            from src.core.database import get_db
            from src.repositories.formula_cache_repository import FormulaCacheRepository

            async with get_db() as db:
                cache_repo = FormulaCacheRepository(db)
                cached = await cache_repo.get_by_hash(cache_key)

                if cached and cached.image_url:
                    logger.debug(f"✅ 数据库缓存命中: {cache_key[:8]}...")

                    # 验证 URL 是否仍然有效（可选，增加一次网络请求）
                    if await self._verify_url(cached.image_url):
                        # 数据库缓存有效，更新命中计数（异步，不等待）
                        try:
                            await cache_repo.increment_hit_count(cache_key)
                        except Exception as e:
                            logger.debug(f"更新命中计数失败（不影响主流程）: {e}")
                        return cached.image_url
                    else:
                        logger.warning(
                            f"缓存 URL 已失效，将重新渲染: {cache_key[:8]}..."
                        )
                        return None

            # 2. 数据库中没有，尝试检查 OSS（备用方案）
            logger.debug(f"数据库缓存未命中: {cache_key[:8]}...")

            # OSS 文件存在检查（如果 OSS 有 head_object 方法）
            # 由于 file_exists 可能未实现，这里使用 try-except 包裹
            try:
                png_path = f"{self.cache_prefix}{cache_key}.png"
                svg_path = f"{self.cache_prefix}{cache_key}.svg"

                # 检查 PNG 文件
                if hasattr(self.ai_image_service, "file_exists"):
                    if await self.ai_image_service.file_exists(png_path):
                        url = await self.ai_image_service.get_url(png_path)
                        logger.info(f"OSS 缓存命中（PNG）: {cache_key[:8]}...")
                        # 回写到数据库缓存
                        await self._save_to_db_cache(cache_key, "", url, "inline")
                        return url

                    # 检查 SVG 文件
                    if await self.ai_image_service.file_exists(svg_path):
                        url = await self.ai_image_service.get_url(svg_path)
                        logger.info(f"OSS 缓存命中（SVG）: {cache_key[:8]}...")
                        await self._save_to_db_cache(cache_key, "", url, "inline")
                        return url
            except Exception as oss_err:
                logger.debug(f"OSS 检查失败（可能不支持）: {oss_err}")

            return None

        except Exception as e:
            logger.error(f"缓存检查失败: {e}")
            return None

    async def _verify_url(self, url: str, timeout: float = 3.0) -> bool:
        """
        验证 URL 是否有效（HTTP HEAD 请求）

        Args:
            url: 要验证的 URL
            timeout: 超时时间（秒）

        Returns:
            URL 是否有效
        """
        try:
            response = await self.client.head(url, timeout=timeout)
            return response.status_code == 200
        except Exception:
            return False

    async def _save_to_db_cache(
        self, latex_hash: str, latex_content: str, image_url: str, formula_type: str
    ) -> None:
        """
        保存到数据库缓存

        Args:
            latex_hash: LaTeX 哈希
            latex_content: 原始内容
            image_url: 图片 URL
            formula_type: 公式类型
        """
        try:
            from src.core.database import get_db
            from src.repositories.formula_cache_repository import FormulaCacheRepository

            async with get_db() as db:
                cache_repo = FormulaCacheRepository(db)
                await cache_repo.create_cache(
                    latex_hash=latex_hash,
                    latex_content=latex_content,
                    image_url=image_url,
                    formula_type=formula_type,
                )
                logger.debug(f"已保存到数据库缓存: {latex_hash[:8]}...")
        except Exception as e:
            logger.warning(f"保存数据库缓存失败（不影响主流程）: {e}")

    async def _render_single_formula(
        self, content: str, formula_type: str, cache_key: str
    ) -> Optional[str]:
        """
        渲染单个公式（带降级策略）

        Args:
            content: LaTeX公式内容
            formula_type: 公式类型 (inline/block)
            cache_key: 缓存键

        Returns:
            图片URL或None
        """
        start_time = time.time()
        try:
            # 记录请求
            self.metrics.record_request(formula_type)

            # 1. 准备LaTeX代码
            latex_code = self._prepare_latex_code(content, formula_type)

            # 2. 调用QuickLaTeX API（带降级）
            image_content = await self._call_quicklatex_api_with_fallback(
                latex_code, content, formula_type
            )

            if not image_content:
                logger.warning(f"公式渲染失败，使用降级方案: {content[:50]}...")
                self.metrics.record_failure("quicklatex", f"Formula: {content[:50]}")
                return None

            # 3. 保存到OSS
            image_url = await self._upload_to_oss(
                image_content, cache_key, formula_type
            )

            if not image_url:
                self.metrics.record_failure("oss_upload", f"Formula: {content[:50]}")
                return None

            # 4. 保存到数据库缓存
            await self._save_to_db_cache(
                latex_hash=cache_key,
                latex_content=content,
                image_url=image_url,
                formula_type=formula_type,
            )

            # 记录成功
            response_time = time.time() - start_time
            self.metrics.record_success(response_time, formula_type)

            logger.info(f"✅ 公式渲染成功: {cache_key[:8]}... -> {image_url[:50]}...")
            return image_url

        except Exception as e:
            logger.error(f"渲染公式失败: {content[:50]}... - {e}")
            self.metrics.record_failure("unexpected", str(e))
            return None

    async def _call_quicklatex_api_with_fallback(
        self, latex_code: str, original_content: str, formula_type: str
    ) -> Optional[str]:
        """
        调用 QuickLaTeX API（带降级策略）

        降级策略：
        1. 首次调用失败 -> 重试 1 次
        2. 仍失败 -> 返回 None（上层处理）

        Args:
            latex_code: 完整 LaTeX 代码
            original_content: 原始公式内容
            formula_type: 公式类型

        Returns:
            图片内容或 None
        """
        max_retries = 2
        retry_delay = 1.0  # 秒

        for attempt in range(max_retries):
            try:
                result = await self._call_quicklatex_api(latex_code)

                if result:
                    if attempt > 0:
                        logger.info(f"QuickLaTeX 重试成功（第 {attempt + 1} 次）")
                    return result

                # API 返回 None，等待后重试
                if attempt < max_retries - 1:
                    logger.warning(f"QuickLaTeX 失败，{retry_delay}秒后重试...")
                    await asyncio.sleep(retry_delay)

            except Exception as e:
                logger.error(
                    f"QuickLaTeX API 调用异常（尝试 {attempt + 1}/{max_retries}）: {e}"
                )

                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)

        # 所有重试都失败
        logger.error(
            f"QuickLaTeX 最终失败，已尝试 {max_retries} 次: {original_content[:50]}..."
        )
        return None

    async def _upload_to_oss(
        self, image_content: str, cache_key: str, formula_type: str
    ) -> Optional[str]:
        """
        上传图片到 OSS

        Args:
            image_content: 图片内容（base64 或 SVG）
            cache_key: 缓存键
            formula_type: 公式类型

        Returns:
            OSS URL 或 None
        """
        try:
            if image_content.startswith("data:image/png;base64,"):
                # PNG格式，保存为PNG文件
                import base64

                base64_data = image_content.split(",")[1]
                image_bytes = base64.b64decode(base64_data)

                cache_path = f"{self.cache_prefix}{cache_key}.png"

                image_url = await self.ai_image_service.upload_file(
                    file_data=image_bytes,
                    object_name=cache_path,
                    content_type="image/png",
                )
                logger.debug(f"PNG 已上传到 OSS: {cache_path}")
                return image_url

            else:
                # SVG格式
                cache_path = f"{self.cache_prefix}{cache_key}.svg"

                image_url = await self.ai_image_service.upload_file(
                    file_data=image_content.encode("utf-8"),
                    object_name=cache_path,
                    content_type="image/svg+xml",
                )
                logger.debug(f"SVG 已上传到 OSS: {cache_path}")
                return image_url

        except Exception as e:
            logger.error(f"上传到 OSS 失败: {e}")
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
