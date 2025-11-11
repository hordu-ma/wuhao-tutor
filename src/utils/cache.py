"""
Redis缓存工具模块
提供统一的缓存管理接口和装饰器
"""

import json
import pickle
import hashlib
from typing import Any, Optional, Union, Callable, Dict
from datetime import datetime, timedelta
from functools import wraps
import asyncio

import redis.asyncio as redis
from redis.asyncio import Redis
from redis.exceptions import RedisError

from src.core.config import settings
from src.core.logging import get_logger

logger = get_logger(__name__)


class RedisCache:
    """
    Redis缓存管理器
    提供异步缓存操作接口
    """

    def __init__(
        self,
        redis_client: Optional[Redis] = None,
        prefix: str = "wuhao",
        default_ttl: int = 3600,
    ):
        """
        初始化Redis缓存管理器

        Args:
            redis_client: Redis客户端实例
            prefix: 缓存键前缀
            default_ttl: 默认TTL（秒）
        """
        self.redis_client = redis_client or self._create_redis_client()
        self.prefix = prefix
        self.default_ttl = default_ttl

    def _create_redis_client(self) -> Redis:
        """创建Redis客户端"""
        return redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            password=settings.REDIS_PASSWORD,
            db=settings.REDIS_DB,
            decode_responses=False,  # 使用bytes类型以支持pickle序列化
            retry_on_timeout=True,
            health_check_interval=30,
        )

    def _make_key(self, key: str, namespace: str = "") -> str:
        """
        生成缓存键

        Args:
            key: 原始键
            namespace: 命名空间

        Returns:
            完整的缓存键
        """
        if namespace:
            return f"{self.prefix}:{namespace}:{key}"
        return f"{self.prefix}:{key}"

    def _serialize_value(self, value: Any) -> bytes:
        """
        序列化值

        Args:
            value: 要序列化的值

        Returns:
            序列化后的bytes
        """
        if isinstance(value, (str, int, float, bool)):
            return json.dumps(value).encode("utf-8")
        else:
            return pickle.dumps(value)

    def _deserialize_value(self, data: bytes) -> Any:
        """
        反序列化值

        Args:
            data: 序列化的数据

        Returns:
            反序列化后的值
        """
        try:
            # 先尝试JSON反序列化
            return json.loads(data.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            # 如果JSON失败，使用pickle
            return pickle.loads(data)

    async def get(self, key: str, namespace: str = "") -> Optional[Any]:
        """
        获取缓存值

        Args:
            key: 缓存键
            namespace: 命名空间

        Returns:
            缓存值或None
        """
        try:
            cache_key = self._make_key(key, namespace)
            data = await self.redis_client.get(cache_key)
            if data is None:
                logger.debug(f"Cache miss for key: {cache_key}")
                return None

            value = self._deserialize_value(data)
            logger.debug(f"Cache hit for key: {cache_key}")
            return value

        except RedisError as e:
            logger.error(f"Redis error when getting key {key}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error deserializing cached value for key {key}: {e}")
            return None

    async def set(
        self, key: str, value: Any, ttl: Optional[int] = None, namespace: str = ""
    ) -> bool:
        """
        设置缓存值

        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒）
            namespace: 命名空间

        Returns:
            是否设置成功
        """
        try:
            cache_key = self._make_key(key, namespace)
            serialized_value = self._serialize_value(value)
            expire_time = ttl or self.default_ttl

            result = await self.redis_client.setex(
                cache_key, expire_time, serialized_value
            )
            logger.debug(f"Cache set for key: {cache_key}, ttl: {expire_time}")
            return result

        except RedisError as e:
            logger.error(f"Redis error when setting key {key}: {e}")
            return False
        except Exception as e:
            logger.error(f"Error serializing value for key {key}: {e}")
            return False

    async def delete(self, key: str, namespace: str = "") -> bool:
        """
        删除缓存值

        Args:
            key: 缓存键
            namespace: 命名空间

        Returns:
            是否删除成功
        """
        try:
            cache_key = self._make_key(key, namespace)
            result = await self.redis_client.delete(cache_key)
            logger.debug(f"Cache deleted for key: {cache_key}")
            return bool(result)

        except RedisError as e:
            logger.error(f"Redis error when deleting key {key}: {e}")
            return False

    async def exists(self, key: str, namespace: str = "") -> bool:
        """
        检查缓存键是否存在

        Args:
            key: 缓存键
            namespace: 命名空间

        Returns:
            是否存在
        """
        try:
            cache_key = self._make_key(key, namespace)
            result = await self.redis_client.exists(cache_key)
            return bool(result)

        except RedisError as e:
            logger.error(f"Redis error when checking key {key}: {e}")
            return False

    async def expire(self, key: str, ttl: int, namespace: str = "") -> bool:
        """
        设置缓存键过期时间

        Args:
            key: 缓存键
            ttl: 过期时间（秒）
            namespace: 命名空间

        Returns:
            是否设置成功
        """
        try:
            cache_key = self._make_key(key, namespace)
            result = await self.redis_client.expire(cache_key, ttl)
            logger.debug(f"Cache expiry set for key: {cache_key}, ttl: {ttl}")
            return bool(result)

        except RedisError as e:
            logger.error(f"Redis error when setting expiry for key {key}: {e}")
            return False

    async def clear_namespace(self, namespace: str) -> int:
        """
        清空指定命名空间的所有缓存

        Args:
            namespace: 命名空间

        Returns:
            删除的键数量
        """
        try:
            pattern = self._make_key("*", namespace)
            keys = await self.redis_client.keys(pattern)
            if keys:
                deleted_count = await self.redis_client.delete(*keys)
                logger.info(f"Cleared {deleted_count} keys from namespace: {namespace}")
                return deleted_count
            return 0

        except RedisError as e:
            logger.error(f"Redis error when clearing namespace {namespace}: {e}")
            return 0

    async def get_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息

        Returns:
            统计信息字典
        """
        try:
            info = await self.redis_client.info()
            return {
                "connected_clients": info.get("connected_clients", 0),
                "used_memory": info.get("used_memory_human", "0B"),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "expired_keys": info.get("expired_keys", 0),
            }
        except RedisError as e:
            logger.error(f"Redis error when getting stats: {e}")
            return {}

    async def close(self):
        """关闭Redis连接"""
        if self.redis_client:
            await self.redis_client.close()


def cache_key_generator(*args, **kwargs) -> str:
    """
    生成缓存键的默认函数

    Args:
        *args: 位置参数
        **kwargs: 关键字参数

    Returns:
        生成的缓存键
    """
    # 过滤掉不可序列化的参数
    serializable_args = []
    for arg in args:
        try:
            json.dumps(arg, default=str)
            serializable_args.append(arg)
        except (TypeError, ValueError):
            serializable_args.append(str(arg))

    serializable_kwargs = {}
    for key, value in kwargs.items():
        try:
            json.dumps(value, default=str)
            serializable_kwargs[key] = value
        except (TypeError, ValueError):
            serializable_kwargs[key] = str(value)

    # 生成唯一的缓存键
    key_data = json.dumps(
        {"args": serializable_args, "kwargs": serializable_kwargs},
        sort_keys=True,
        default=str,
    )

    return hashlib.md5(key_data.encode()).hexdigest()


def cache(
    ttl: int = 3600,
    namespace: str = "default",
    key_generator: Optional[Callable] = None,
    cache_manager: Optional[RedisCache] = None,
):
    """
    缓存装饰器

    Args:
        ttl: 缓存时间（秒）
        namespace: 命名空间
        key_generator: 自定义键生成函数
        cache_manager: 缓存管理器实例

    Returns:
        装饰器函数
    """

    def decorator(func: Callable) -> Callable:
        _cache_manager = cache_manager or _get_default_cache_manager()
        _key_generator = key_generator or cache_key_generator

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = f"{func.__name__}:{_key_generator(*args, **kwargs)}"

            # 尝试从缓存获取
            cached_result = await _cache_manager.get(cache_key, namespace)
            if cached_result is not None:
                logger.debug(f"Cache hit for function: {func.__name__}")
                return cached_result

            # 执行函数
            logger.debug(f"Cache miss for function: {func.__name__}")
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)

            # 存储到缓存
            await _cache_manager.set(cache_key, result, ttl, namespace)
            return result

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # 对于同步函数，需要在事件循环中运行异步操作
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            return loop.run_until_complete(async_wrapper(*args, **kwargs))

        # 根据函数类型返回对应的包装器
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def cache_clear(namespace: str = "default", cache_manager: Optional[RedisCache] = None):
    """
    清空缓存装饰器

    Args:
        namespace: 要清空的命名空间
        cache_manager: 缓存管理器实例
    """

    def decorator(func: Callable) -> Callable:
        _cache_manager = cache_manager or _get_default_cache_manager()

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)
            await _cache_manager.clear_namespace(namespace)
            return result

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            loop.run_until_complete(_cache_manager.clear_namespace(namespace))
            return result

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# 全局缓存管理器实例
_cache_manager_instance: Optional[RedisCache] = None


def _get_default_cache_manager() -> RedisCache:
    """获取默认的缓存管理器实例"""
    global _cache_manager_instance
    if _cache_manager_instance is None:
        _cache_manager_instance = RedisCache()
    return _cache_manager_instance


def get_cache_manager() -> RedisCache:
    """
    获取缓存管理器实例

    Returns:
        RedisCache实例
    """
    return _get_default_cache_manager()


# 为方便使用导出的实例
cache_manager = get_cache_manager()


# ============================================================================
# 兼容性函数别名
# ============================================================================


def cache_result(ttl: int = 3600, namespace: str = "default"):
    """
    缓存结果装饰器（cache函数的别名）

    Args:
        ttl: 缓存时间（秒）
        namespace: 命名空间

    Returns:
        装饰器函数
    """
    return cache(ttl=ttl, namespace=namespace)


def cache_key(*args, **kwargs) -> str:
    """
    生成缓存键（cache_key_generator函数的别名）

    Args:
        *args: 位置参数
        **kwargs: 关键字参数

    Returns:
        生成的缓存键
    """
    return cache_key_generator(*args, **kwargs)
