"""
文件处理工具函数
提供文件验证、处理、格式化等实用功能
"""

import hashlib
import mimetypes
import os
import re
from pathlib import Path
from typing import Optional, Tuple, Set
from PIL import Image
import magic


# 支持的文件类型
ALLOWED_IMAGE_TYPES = {
    'image/jpeg', 'image/jpg', 'image/png', 'image/webp', 'image/gif'
}

ALLOWED_DOCUMENT_TYPES = {
    'application/pdf', 'text/plain', 'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
}

ALLOWED_TYPES = ALLOWED_IMAGE_TYPES | ALLOWED_DOCUMENT_TYPES

# 文件大小限制
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_IMAGE_DIMENSION = 4000  # 最大图片尺寸


def validate_file_type(content_type: str, filename: str = None) -> bool:
    """
    验证文件类型是否被支持

    Args:
        content_type: MIME类型
        filename: 文件名（可选，用于辅助判断）

    Returns:
        bool: 是否支持该文件类型
    """
    if not content_type:
        return False

    # 标准化MIME类型
    content_type = content_type.lower().strip()

    # 特殊处理一些常见的变体
    if content_type == 'image/jpg':
        content_type = 'image/jpeg'

    return content_type in ALLOWED_TYPES


def get_file_extension(filename: str) -> str:
    """
    获取文件扩展名

    Args:
        filename: 文件名

    Returns:
        str: 文件扩展名（包含点号）
    """
    if not filename:
        return ''

    return Path(filename).suffix.lower()


def generate_safe_filename(original_filename: str, file_id: str) -> str:
    """
    生成安全的文件名

    Args:
        original_filename: 原始文件名
        file_id: 文件ID

    Returns:
        str: 安全的文件名
    """
    if not original_filename:
        return f"{file_id}.bin"

    # 获取扩展名
    ext = get_file_extension(original_filename)

    # 清理文件ID，只保留字母数字和连字符
    safe_id = re.sub(r'[^a-zA-Z0-9\-]', '', file_id)

    return f"{safe_id}{ext}"


def calculate_file_hash(file_content: bytes, algorithm: str = 'sha256') -> str:
    """
    计算文件哈希值

    Args:
        file_content: 文件内容
        algorithm: 哈希算法（md5, sha1, sha256）

    Returns:
        str: 十六进制哈希值
    """
    if algorithm == 'md5':
        hasher = hashlib.md5()
    elif algorithm == 'sha1':
        hasher = hashlib.sha1()
    else:
        hasher = hashlib.sha256()

    hasher.update(file_content)
    return hasher.hexdigest()


def format_file_size(size_bytes: int) -> str:
    """
    格式化文件大小为人类可读格式

    Args:
        size_bytes: 文件大小（字节）

    Returns:
        str: 格式化的大小字符串
    """
    if size_bytes == 0:
        return "0 B"

    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    size = float(size_bytes)

    while size >= 1024.0 and i < len(size_names) - 1:
        size /= 1024.0
        i += 1

    return f"{size:.1f} {size_names[i]}"


def get_mime_type(filename: str, file_content: bytes = None) -> str:
    """
    获取文件的MIME类型

    Args:
        filename: 文件名
        file_content: 文件内容（可选，用于更准确的检测）

    Returns:
        str: MIME类型
    """
    # 首先尝试根据文件名猜测
    mime_type, _ = mimetypes.guess_type(filename)

    if mime_type:
        return mime_type

    # 如果有文件内容，使用magic库检测
    if file_content:
        try:
            mime_type = magic.from_buffer(file_content, mime=True)
            if mime_type:
                return mime_type
        except Exception:
            pass

    # 根据扩展名手动映射
    ext = get_file_extension(filename).lower()
    ext_mapping = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.webp': 'image/webp',
        '.pdf': 'application/pdf',
        '.txt': 'text/plain',
        '.doc': 'application/msword',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    }

    return ext_mapping.get(ext, 'application/octet-stream')


def validate_image_file(file_content: bytes) -> Tuple[bool, Optional[str], Optional[Tuple[int, int]]]:
    """
    验证图片文件

    Args:
        file_content: 文件内容

    Returns:
        Tuple[bool, Optional[str], Optional[Tuple[int, int]]]:
        (是否有效, 错误信息, 图片尺寸)
    """
    try:
        with Image.open(io.BytesIO(file_content)) as img:
            width, height = img.size

            # 检查图片尺寸
            if width > MAX_IMAGE_DIMENSION or height > MAX_IMAGE_DIMENSION:
                return False, f"图片尺寸过大，最大支持 {MAX_IMAGE_DIMENSION}x{MAX_IMAGE_DIMENSION}", (width, height)

            # 检查图片格式
            if img.format.lower() not in ['jpeg', 'png', 'gif', 'webp']:
                return False, f"不支持的图片格式: {img.format}", (width, height)

            return True, None, (width, height)

    except Exception as e:
        return False, f"无效的图片文件: {str(e)}", None


def sanitize_filename(filename: str) -> str:
    """
    清理文件名，移除危险字符

    Args:
        filename: 原始文件名

    Returns:
        str: 清理后的文件名
    """
    if not filename:
        return "untitled"

    # 移除路径分隔符和危险字符
    dangerous_chars = r'[<>:"/\\|?*\x00-\x1f]'
    cleaned = re.sub(dangerous_chars, '_', filename)

    # 移除开头和结尾的点和空格
    cleaned = cleaned.strip('. ')

    # 确保文件名不为空且不超过255个字符
    if not cleaned:
        cleaned = "untitled"

    if len(cleaned) > 255:
        name, ext = os.path.splitext(cleaned)
        max_name_len = 255 - len(ext)
        cleaned = name[:max_name_len] + ext

    return cleaned


def is_image_file(content_type: str) -> bool:
    """
    判断是否为图片文件

    Args:
        content_type: MIME类型

    Returns:
        bool: 是否为图片
    """
    return content_type.lower() in ALLOWED_IMAGE_TYPES


def is_document_file(content_type: str) -> bool:
    """
    判断是否为文档文件

    Args:
        content_type: MIME类型

    Returns:
        bool: 是否为文档
    """
    return content_type.lower() in ALLOWED_DOCUMENT_TYPES


def get_file_category(content_type: str) -> str:
    """
    根据MIME类型获取文件分类

    Args:
        content_type: MIME类型

    Returns:
        str: 文件分类 (image/document/other)
    """
    content_type = content_type.lower()

    if content_type in ALLOWED_IMAGE_TYPES:
        return 'image'
    elif content_type in ALLOWED_DOCUMENT_TYPES:
        return 'document'
    else:
        return 'other'


def create_thumbnail(image_content: bytes, max_size: Tuple[int, int] = (200, 200)) -> Optional[bytes]:
    """
    创建图片缩略图

    Args:
        image_content: 图片内容
        max_size: 最大尺寸 (width, height)

    Returns:
        Optional[bytes]: 缩略图内容，失败返回None
    """
    try:
        import io
        from PIL import Image

        with Image.open(io.BytesIO(image_content)) as img:
            # 转换为RGB模式（处理RGBA等格式）
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')

            # 创建缩略图
            img.thumbnail(max_size, Image.Resampling.LANCZOS)

            # 保存为JPEG格式
            output = io.BytesIO()
            img.save(output, format='JPEG', quality=85, optimize=True)
            return output.getvalue()

    except Exception:
        return None


def validate_file_content(content: bytes, content_type: str, filename: str) -> Tuple[bool, Optional[str]]:
    """
    全面验证文件内容

    Args:
        content: 文件内容
        content_type: MIME类型
        filename: 文件名

    Returns:
        Tuple[bool, Optional[str]]: (是否有效, 错误信息)
    """
    # 检查文件大小
    if len(content) == 0:
        return False, "文件为空"

    if len(content) > MAX_FILE_SIZE:
        return False, f"文件大小超过限制 ({format_file_size(MAX_FILE_SIZE)})"

    # 检查文件类型
    if not validate_file_type(content_type, filename):
        return False, f"不支持的文件类型: {content_type}"

    # 如果是图片，进行额外验证
    if is_image_file(content_type):
        is_valid, error, _ = validate_image_file(content)
        if not is_valid:
            return False, error

    return True, None


# 需要导入io模块
import io
