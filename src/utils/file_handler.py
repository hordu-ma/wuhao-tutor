"""
简化的文件处理工具类
为API层提供文件验证、保存和管理功能
"""

import os
import shutil
import mimetypes
from typing import Optional, Dict, Any
from pathlib import Path
from PIL import Image
from fastapi import UploadFile
from src.core.config import get_settings

settings = get_settings()

# 支持的图片格式
SUPPORTED_IMAGE_FORMATS = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/gif",
    "image/webp",
}

# 最大文件大小 (10MB)
MAX_FILE_SIZE = 10 * 1024 * 1024


def validate_image_file(file: UploadFile) -> bool:
    """
    验证上传的文件是否为有效的图片

    Args:
        file: FastAPI UploadFile对象

    Returns:
        是否为有效图片
    """
    if not file.filename:
        return False

    # 检查文件扩展名
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in [".jpg", ".jpeg", ".png", ".gif", ".webp"]:
        return False

    # 检查MIME类型
    if file.content_type not in SUPPORTED_IMAGE_FORMATS:
        return False

    return True


async def save_uploaded_file(
    file: UploadFile, category: str, filename: str, user_id: str
) -> str:
    """
    保存上传的文件

    Args:
        file: 上传的文件
        category: 文件分类
        filename: 存储文件名
        user_id: 用户ID

    Returns:
        保存的文件相对路径
    """
    # 构建存储路径
    upload_dir = Path(settings.UPLOAD_DIR)
    category_dir = upload_dir / category / user_id

    # 确保目录存在
    category_dir.mkdir(parents=True, exist_ok=True)

    # 完整文件路径
    file_path = category_dir / filename

    # 保存文件
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)

    # 返回相对路径
    relative_path = os.path.join(category, user_id, filename)
    return relative_path


async def get_file_info(file_path: str) -> Dict[str, Any]:
    """
    获取文件信息

    Args:
        file_path: 文件路径

    Returns:
        文件信息字典
    """
    info = {
        "exists": False,
        "size": 0,
        "mime_type": None,
        "width": None,
        "height": None,
    }

    if not os.path.exists(file_path):
        return info

    info["exists"] = True
    info["size"] = os.path.getsize(file_path)
    info["mime_type"] = mimetypes.guess_type(file_path)[0]

    # 如果是图片，获取尺寸信息
    if info["mime_type"] and info["mime_type"].startswith("image/"):
        try:
            with Image.open(file_path) as img:
                info["width"] = img.width
                info["height"] = img.height
        except Exception:
            pass

    return info


async def delete_file(file_path: str) -> bool:
    """
    删除文件

    Args:
        file_path: 文件路径

    Returns:
        是否删除成功
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False
    except Exception:
        return False


def generate_file_url(relative_path: str) -> str:
    """
    生成文件访问URL

    Args:
        relative_path: 文件相对路径

    Returns:
        文件访问URL
    """
    base_url = getattr(settings, "FILE_BASE_URL", "/api/v1/files/preview")
    return f"{base_url}/{relative_path}"


def get_file_category(filename: str) -> str:
    """
    根据文件名确定文件分类

    Args:
        filename: 文件名

    Returns:
        文件分类
    """
    file_ext = os.path.splitext(filename)[1].lower()

    if file_ext in [".jpg", ".jpeg", ".png", ".gif", ".webp"]:
        return "images"
    elif file_ext in [".pdf", ".doc", ".docx"]:
        return "documents"
    else:
        return "general"


def ensure_upload_directory() -> None:
    """
    确保上传目录存在
    """
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)

    # 创建基本的分类目录
    categories = ["images", "documents", "homework", "general"]
    for category in categories:
        (upload_dir / category).mkdir(exist_ok=True)


def cleanup_temp_files(temp_dir: str) -> None:
    """
    清理临时文件

    Args:
        temp_dir: 临时目录路径
    """
    try:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
    except Exception:
        pass
