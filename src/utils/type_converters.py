"""
SQLAlchemy 类型安全转换工具
解决 ORM 对象属性的类型转换问题
"""

from typing import Any, Optional, List, Dict
from uuid import UUID
from datetime import datetime
import json


def safe_str(value: Any) -> str:
    """安全转换为字符串"""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return str(value)


def safe_int(value: Any) -> Optional[int]:
    """安全转换为整数"""
    if value is None:
        return None
    if isinstance(value, int):
        return value
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def safe_float(value: Any) -> Optional[float]:
    """安全转换为浮点数"""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def safe_bool(value: Any) -> bool:
    """安全转换为布尔值"""
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ("true", "1", "yes", "on")
    try:
        return bool(value)
    except (ValueError, TypeError):
        return False


def safe_uuid_str(value: Any) -> str:
    """安全转换UUID为字符串"""
    if value is None:
        return ""
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, str):
        return value
    return str(value)


def safe_datetime_str(value: Any) -> Optional[str]:
    """安全转换日期时间为ISO字符串"""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, str):
        return value
    return str(value)


def safe_json_loads(value: Any) -> Optional[Dict[str, Any]]:
    """安全解析JSON字符串"""
    if value is None:
        return None
    if isinstance(value, dict):
        return value
    if isinstance(value, str) and value.strip():
        try:
            return json.loads(value)
        except (json.JSONDecodeError, ValueError):
            return None
    return None


def safe_json_dumps(value: Any) -> str:
    """安全序列化为JSON字符串"""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    try:
        return json.dumps(value, ensure_ascii=False, default=str)
    except (TypeError, ValueError):
        return str(value)


def extract_orm_value(orm_obj: Any, attr_name: str, default: Any = None) -> Any:
    """
    从ORM对象安全提取属性值

    Args:
        orm_obj: ORM对象
        attr_name: 属性名
        default: 默认值

    Returns:
        属性的实际值，而非Column对象
    """
    if orm_obj is None:
        return default

    try:
        # 使用getattr获取属性值，这样可以获得实际值而不是Column对象
        value = getattr(orm_obj, attr_name, default)

        # 如果值是None，返回默认值
        if value is None:
            return default

        return value
    except AttributeError:
        return default


def extract_orm_str(orm_obj: Any, attr_name: str, default: str = "") -> str:
    """从ORM对象提取字符串属性"""
    value = extract_orm_value(orm_obj, attr_name, default)
    return safe_str(value)


def extract_orm_int(
    orm_obj: Any, attr_name: str, default: Optional[int] = None
) -> Optional[int]:
    """从ORM对象提取整数属性"""
    value = extract_orm_value(orm_obj, attr_name, default)
    return safe_int(value)


def extract_orm_float(
    orm_obj: Any, attr_name: str, default: Optional[float] = None
) -> Optional[float]:
    """从ORM对象提取浮点数属性"""
    value = extract_orm_value(orm_obj, attr_name, default)
    return safe_float(value)


def extract_orm_bool(orm_obj: Any, attr_name: str, default: bool = False) -> bool:
    """从ORM对象提取布尔属性"""
    value = extract_orm_value(orm_obj, attr_name, default)
    return safe_bool(value)


def extract_orm_uuid_str(orm_obj: Any, attr_name: str, default: str = "") -> str:
    """从ORM对象提取UUID并转为字符串"""
    value = extract_orm_value(orm_obj, attr_name, default)
    return safe_uuid_str(value)


def extract_orm_datetime_str(
    orm_obj: Any, attr_name: str, default: Optional[str] = None
) -> Optional[str]:
    """从ORM对象提取日期时间并转为字符串"""
    value = extract_orm_value(orm_obj, attr_name, default)
    return safe_datetime_str(value)


def convert_orm_list_to_str_list(orm_list: List[Any], attr_name: str) -> List[str]:
    """将ORM对象列表的某个属性转为字符串列表"""
    if not orm_list:
        return []

    result = []
    for orm_obj in orm_list:
        if orm_obj is not None:
            value = extract_orm_str(orm_obj, attr_name)
            if value:
                result.append(value)

    return result


def convert_orm_list_to_uuid_str_list(orm_list: List[Any], attr_name: str) -> List[str]:
    """将ORM对象列表的某个UUID属性转为字符串列表"""
    if not orm_list:
        return []

    result = []
    for orm_obj in orm_list:
        if orm_obj is not None:
            value = extract_orm_uuid_str(orm_obj, attr_name)
            if value:
                result.append(value)

    return result


class TypeSafeORM:
    """ORM对象类型安全包装器，提供类型安全的属性访问"""

    def __init__(self, orm_obj: Any) -> None:
        self._orm_obj = orm_obj

    def get_str(self, attr_name: str, default: str = "") -> str:
        """获取字符串属性"""
        return extract_orm_str(self._orm_obj, attr_name, default)

    def get_int(self, attr_name: str, default: Optional[int] = None) -> Optional[int]:
        """获取整数属性"""
        return extract_orm_int(self._orm_obj, attr_name, default)

    def get_float(
        self, attr_name: str, default: Optional[float] = None
    ) -> Optional[float]:
        """获取浮点数属性"""
        return extract_orm_float(self._orm_obj, attr_name, default)

    def get_bool(self, attr_name: str, default: bool = False) -> bool:
        """获取布尔属性"""
        return extract_orm_bool(self._orm_obj, attr_name, default)

    def get_uuid_str(self, attr_name: str, default: str = "") -> str:
        """获取UUID字符串属性"""
        return extract_orm_uuid_str(self._orm_obj, attr_name, default)

    def get_datetime_str(
        self, attr_name: str, default: Optional[str] = None
    ) -> Optional[str]:
        """获取日期时间字符串属性"""
        return extract_orm_datetime_str(self._orm_obj, attr_name, default)

    def get_json(
        self, attr_name: str, default: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """获取JSON属性"""
        value = extract_orm_value(self._orm_obj, attr_name, None)
        result = safe_json_loads(value)
        return result if result is not None else default


def wrap_orm(orm_obj: Any) -> TypeSafeORM:
    """将ORM对象包装为类型安全对象"""
    return TypeSafeORM(orm_obj)


# 常用的响应构造辅助函数


def build_user_response_data(user_obj: Any) -> Dict[str, Any]:
    """构建用户响应数据"""
    if not user_obj:
        return {}

    safe_user = wrap_orm(user_obj)

    return {
        "id": safe_user.get_uuid_str("id"),
        "phone": safe_user.get_str("phone"),
        "name": safe_user.get_str("name"),
        "nickname": safe_user.get_str("nickname"),
        "role": safe_user.get_str("role"),
        "is_active": safe_user.get_bool("is_active"),
        "is_verified": safe_user.get_bool("is_verified"),
        "avatar_url": safe_user.get_str("avatar_url"),
        "created_at": safe_user.get_datetime_str("created_at"),
        "updated_at": safe_user.get_datetime_str("updated_at"),
    }


def build_session_response_data(session_obj: Any) -> Dict[str, Any]:
    """构建会话响应数据"""
    if not session_obj:
        return {}

    safe_session = wrap_orm(session_obj)

    return {
        "id": safe_session.get_uuid_str("id"),
        "user_id": safe_session.get_str("user_id"),
        "device_type": safe_session.get_str("device_type"),
        "device_id": safe_session.get_str("device_id"),
        "expires_at": safe_session.get_str("expires_at"),
        "is_revoked": safe_session.get_bool("is_revoked"),
        "ip_address": safe_session.get_str("ip_address"),
        "user_agent": safe_session.get_str("user_agent"),
        "created_at": safe_session.get_datetime_str("created_at"),
    }


def build_homework_response_data(homework_obj: Any) -> Dict[str, Any]:
    """构建作业响应数据"""
    if not homework_obj:
        return {}

    safe_homework = wrap_orm(homework_obj)

    return {
        "id": safe_homework.get_uuid_str("id"),
        "title": safe_homework.get_str("title"),
        "description": safe_homework.get_str("description"),
        "subject": safe_homework.get_str("subject"),
        "grade_level": safe_homework.get_str("grade_level"),
        "difficulty_level": safe_homework.get_str("difficulty_level"),
        "homework_type": safe_homework.get_str("homework_type"),
        "creator_id": safe_homework.get_str("creator_id"),
        "is_active": safe_homework.get_bool("is_active"),
        "max_score": safe_homework.get_float("max_score"),
        "time_limit": safe_homework.get_int("time_limit"),
        "created_at": safe_homework.get_datetime_str("created_at"),
        "updated_at": safe_homework.get_datetime_str("updated_at"),
    }
