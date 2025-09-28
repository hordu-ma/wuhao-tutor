"""
数据库查询优化和缓存策略模块
提供查询缓存、连接池优化、慢查询检测等性能优化功能
"""

import asyncio
import hashlib
import json
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, field
from functools import wraps
import logging
from enum import Enum

from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import text

from src.core.config import get_settings
from src.utils.cache import cache_manager

logger = logging.getLogger(__name__)
settings = get_settings()


class QueryType(Enum):
    """查询类型枚举"""
    SELECT = "SELECT"
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    UNKNOWN = "UNKNOWN"


@dataclass
class QueryMetrics:
    """查询指标"""
    query_hash: str
    query_type: QueryType
    execution_time: float
    timestamp: datetime
    table_name: Optional[str] = None
    affected_rows: int = 0
    cache_hit: bool = False


@dataclass
class SlowQuery:
    """慢查询记录"""
    query: str
    query_hash: str
    execution_time: float
    timestamp: datetime
    count: int = 1


class QueryCache:
    """查询缓存管理器"""

    def __init__(self, default_ttl: int = 300, max_cache_size: int = 1000):
        self.default_ttl = default_ttl
        self.max_cache_size = max_cache_size
        self.hit_count = 0
        self.miss_count = 0
        self.cache_keys: deque = deque(maxlen=max_cache_size)

    def _generate_cache_key(self, query: str, params: Optional[Dict[str, Any]] = None) -> str:
        """生成缓存键"""
        content = query
        if params:
            content += json.dumps(params, sort_keys=True, default=str)
        return f"query:{hashlib.md5(content.encode()).hexdigest()}"

    async def get(self, query: str, params: Optional[Dict[str, Any]] = None) -> Optional[Any]:
        """获取缓存结果"""
        cache_key = self._generate_cache_key(query, params)
        result = await cache_manager.get(cache_key)

        if result is not None:
            self.hit_count += 1
            logger.debug(f"Query cache hit: {cache_key}")
            return result

        self.miss_count += 1
        return None

    async def set(self, query: str, result: Any, params: Optional[Dict[str, Any]] = None, ttl: Optional[int] = None) -> None:
        """设置缓存结果"""
        cache_key = self._generate_cache_key(query, params)
        ttl = ttl or self.default_ttl

        await cache_manager.set(cache_key, result, ttl=ttl)

        # 管理缓存键
        if cache_key not in self.cache_keys:
            self.cache_keys.append(cache_key)

        logger.debug(f"Query cached: {cache_key}, TTL: {ttl}s")

    async def invalidate_pattern(self, pattern: str) -> int:
        """按模式清除缓存"""
        count = 0
        keys_to_remove = []

        for cache_key in list(self.cache_keys):
            if pattern in cache_key:
                await cache_manager.delete(cache_key)
                keys_to_remove.append(cache_key)
                count += 1

        # 从跟踪列表中移除
        for key in keys_to_remove:
            try:
                self.cache_keys.remove(key)
            except ValueError:
                pass

        logger.info(f"Invalidated {count} cache entries matching pattern: {pattern}")
        return count

    async def clear_all(self) -> None:
        """清除所有查询缓存"""
        count = 0
        for cache_key in list(self.cache_keys):
            await cache_manager.delete(cache_key)
            count += 1

        self.cache_keys.clear()
        self.hit_count = 0
        self.miss_count = 0

        logger.info(f"Cleared all query cache ({count} entries)")

    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        total_requests = self.hit_count + self.miss_count
        hit_rate = (self.hit_count / total_requests * 100) if total_requests > 0 else 0

        return {
            "hit_count": self.hit_count,
            "miss_count": self.miss_count,
            "hit_rate": round(hit_rate, 2),
            "cached_entries": len(self.cache_keys),
            "max_cache_size": self.max_cache_size
        }


class QueryMonitor:
    """查询监控器"""

    def __init__(self, slow_query_threshold: float = 1.0, max_slow_queries: int = 100):
        self.slow_query_threshold = slow_query_threshold
        self.max_slow_queries = max_slow_queries
        self.query_metrics: deque = deque(maxlen=10000)
        self.slow_queries: Dict[str, SlowQuery] = {}
        self.query_stats: Dict[str, Dict] = defaultdict(lambda: {
            'count': 0,
            'total_time': 0.0,
            'avg_time': 0.0,
            'max_time': 0.0,
            'min_time': float('inf')
        })

    def record_query(self, query: str, execution_time: float,
                    affected_rows: int = 0, cache_hit: bool = False) -> None:
        """记录查询指标"""
        query_hash = hashlib.md5(query.encode()).hexdigest()
        query_type = self._detect_query_type(query)
        table_name = self._extract_table_name(query)

        # 记录指标
        metrics = QueryMetrics(
            query_hash=query_hash,
            query_type=query_type,
            execution_time=execution_time,
            timestamp=datetime.utcnow(),
            table_name=table_name,
            affected_rows=affected_rows,
            cache_hit=cache_hit
        )

        self.query_metrics.append(metrics)

        # 更新统计
        stats = self.query_stats[query_hash]
        stats['count'] += 1
        stats['total_time'] += execution_time
        stats['avg_time'] = stats['total_time'] / stats['count']
        stats['max_time'] = max(stats['max_time'], execution_time)
        stats['min_time'] = min(stats['min_time'], execution_time)

        # 检查慢查询
        if execution_time > self.slow_query_threshold:
            self._record_slow_query(query, query_hash, execution_time)

    def _detect_query_type(self, query: str) -> QueryType:
        """检测查询类型"""
        query_upper = query.strip().upper()
        if query_upper.startswith('SELECT'):
            return QueryType.SELECT
        elif query_upper.startswith('INSERT'):
            return QueryType.INSERT
        elif query_upper.startswith('UPDATE'):
            return QueryType.UPDATE
        elif query_upper.startswith('DELETE'):
            return QueryType.DELETE
        return QueryType.UNKNOWN

    def _extract_table_name(self, query: str) -> Optional[str]:
        """提取表名（简单实现）"""
        try:
            query_upper = query.strip().upper()
            if 'FROM' in query_upper:
                parts = query_upper.split('FROM')[1].split()
                if parts:
                    table_name = parts[0].strip()
                    # 移除可能的schema前缀
                    if '.' in table_name:
                        table_name = table_name.split('.')[-1]
                    return table_name.strip('`"[]')
        except:
            pass
        return None

    def _record_slow_query(self, query: str, query_hash: str, execution_time: float) -> None:
        """记录慢查询"""
        if query_hash in self.slow_queries:
            slow_query = self.slow_queries[query_hash]
            slow_query.count += 1
            slow_query.execution_time = max(slow_query.execution_time, execution_time)
            slow_query.timestamp = datetime.utcnow()
        else:
            if len(self.slow_queries) >= self.max_slow_queries:
                # 移除最旧的记录
                oldest_hash = min(self.slow_queries.keys(),
                                key=lambda k: self.slow_queries[k].timestamp)
                del self.slow_queries[oldest_hash]

            self.slow_queries[query_hash] = SlowQuery(
                query=query,
                query_hash=query_hash,
                execution_time=execution_time,
                timestamp=datetime.utcnow()
            )

        logger.warning(f"Slow query detected: {execution_time:.3f}s - {query[:100]}...")

    def get_query_stats(self, minutes: int = 60) -> Dict[str, Any]:
        """获取查询统计"""
        cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)
        recent_metrics = [m for m in self.query_metrics if m.timestamp > cutoff_time]

        if not recent_metrics:
            return {
                'total_queries': 0,
                'avg_execution_time': 0.0,
                'cache_hit_rate': 0.0,
                'query_types': {},
                'table_activity': {}
            }

        # 统计查询类型
        query_types = defaultdict(int)
        table_activity = defaultdict(int)
        total_time = 0.0
        cache_hits = 0

        for metrics in recent_metrics:
            query_types[metrics.query_type.value] += 1
            if metrics.table_name:
                table_activity[metrics.table_name] += 1
            total_time += metrics.execution_time
            if metrics.cache_hit:
                cache_hits += 1

        return {
            'total_queries': len(recent_metrics),
            'avg_execution_time': round(total_time / len(recent_metrics), 3),
            'cache_hit_rate': round((cache_hits / len(recent_metrics)) * 100, 2),
            'query_types': dict(query_types),
            'table_activity': dict(sorted(table_activity.items(),
                                        key=lambda x: x[1], reverse=True)[:10])
        }

    def get_slow_queries(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取慢查询列表"""
        sorted_queries = sorted(
            self.slow_queries.values(),
            key=lambda x: x.execution_time,
            reverse=True
        )[:limit]

        return [
            {
                'query': sq.query[:200] + '...' if len(sq.query) > 200 else sq.query,
                'execution_time': sq.execution_time,
                'count': sq.count,
                'last_seen': sq.timestamp.isoformat()
            }
            for sq in sorted_queries
        ]

    def clear_slow_queries(self) -> None:
        """清除慢查询记录"""
        count = len(self.slow_queries)
        self.slow_queries.clear()
        logger.info(f"Cleared {count} slow query records")


class CachedQuery:
    """查询缓存装饰器"""

    def __init__(self, ttl: int = 300, cache_key: Optional[str] = None,
                 invalidate_on: Optional[List[str]] = None):
        self.ttl = ttl
        self.cache_key = cache_key
        self.invalidate_on = invalidate_on or []

    def __call__(self, func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            # 生成缓存键
            if self.cache_key:
                cache_key = self.cache_key
            else:
                key_data = f"{func.__name__}:{args}:{kwargs}"
                cache_key = f"cached_query:{hashlib.md5(key_data.encode()).hexdigest()}"

            # 尝试从缓存获取
            cached_result = await cache_manager.get(cache_key)
            if cached_result is not None:
                query_monitor.record_query(
                    query=f"CACHED:{func.__name__}",
                    execution_time=0.001,
                    cache_hit=True
                )
                return cached_result

            # 执行查询
            start_time = time.time()
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time

            # 缓存结果
            await cache_manager.set(cache_key, result, ttl=self.ttl)

            # 记录指标
            query_monitor.record_query(
                query=f"FUNC:{func.__name__}",
                execution_time=execution_time,
                cache_hit=False
            )

            return result

        return wrapper


class DatabaseOptimizer:
    """数据库优化器"""

    def __init__(self):
        self.connection_pool_stats = {}
        self.optimization_suggestions = []

    async def analyze_performance(self, db: AsyncSession) -> Dict[str, Any]:
        """分析数据库性能"""
        analysis = {
            'timestamp': datetime.utcnow().isoformat(),
            'query_performance': query_monitor.get_query_stats(),
            'slow_queries': query_monitor.get_slow_queries(),
            'cache_performance': query_cache.get_stats(),
            'connection_info': await self._get_connection_info(db),
            'optimization_suggestions': self._get_optimization_suggestions()
        }

        return analysis

    async def _get_connection_info(self, db: AsyncSession) -> Dict[str, Any]:
        """获取连接信息"""
        try:
            # PostgreSQL
            result = await db.execute(text("SELECT count(*) FROM pg_stat_activity"))
            active_connections = result.scalar() or 0

            result = await db.execute(text("SELECT setting FROM pg_settings WHERE name = 'max_connections'"))
            max_connections = result.scalar() or 1

            max_conn_int = int(max_connections) if max_connections else 1
            active_conn_int = int(active_connections) if active_connections else 0

            return {
                'active_connections': active_conn_int,
                'max_connections': max_conn_int,
                'connection_usage': round((active_conn_int / max_conn_int) * 100, 2) if max_conn_int > 0 else 0.0,
                'database_type': 'postgresql'
            }
        except:
            # SQLite或其他数据库
            return {
                'active_connections': 1,
                'max_connections': 1,
                'connection_usage': 100.0,
                'database_type': 'sqlite'
            }

    def _get_optimization_suggestions(self) -> List[Dict[str, Any]]:
        """获取优化建议"""
        suggestions = []

        # 检查缓存命中率
        cache_stats = query_cache.get_stats()
        if cache_stats['hit_rate'] < 50:
            suggestions.append({
                'type': 'cache',
                'priority': 'medium',
                'message': f"查询缓存命中率较低 ({cache_stats['hit_rate']}%)，考虑增加缓存TTL或优化查询",
                'action': 'increase_cache_ttl'
            })

        # 检查慢查询
        slow_queries = query_monitor.get_slow_queries(limit=5)
        if slow_queries:
            suggestions.append({
                'type': 'performance',
                'priority': 'high',
                'message': f"发现 {len(slow_queries)} 个慢查询，建议优化索引或查询逻辑",
                'action': 'optimize_slow_queries',
                'details': [sq['query'][:100] for sq in slow_queries[:3]]
            })

        # 检查查询频率
        query_stats = query_monitor.get_query_stats()
        if query_stats['total_queries'] > 1000:  # 每小时超过1000次查询
            suggestions.append({
                'type': 'performance',
                'priority': 'medium',
                'message': f"查询频率较高 ({query_stats['total_queries']}/小时)，建议增加缓存使用",
                'action': 'increase_caching'
            })

        return suggestions

    async def optimize_query_cache(self) -> Dict[str, Any]:
        """优化查询缓存"""
        # 清理过期缓存
        await query_cache.clear_all()

        # 重置监控数据
        query_monitor.query_metrics.clear()

        return {
            'action': 'cache_optimization',
            'timestamp': datetime.utcnow().isoformat(),
            'message': '查询缓存已优化'
        }


# 创建全局实例
query_cache = QueryCache()
query_monitor = QueryMonitor()
db_optimizer = DatabaseOptimizer()


# SQLAlchemy 事件监听器
@event.listens_for(Engine, "before_cursor_execute")
def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """查询执行前的事件"""
    context._query_start_time = time.time()


@event.listens_for(Engine, "after_cursor_execute")
def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """查询执行后的事件"""
    if hasattr(context, '_query_start_time'):
        execution_time = time.time() - context._query_start_time
        affected_rows = cursor.rowcount if hasattr(cursor, 'rowcount') else 0

        # 记录查询指标
        query_monitor.record_query(
            query=statement,
            execution_time=execution_time,
            affected_rows=affected_rows
        )


def get_query_cache() -> QueryCache:
    """获取查询缓存实例"""
    return query_cache


def get_query_monitor() -> QueryMonitor:
    """获取查询监控实例"""
    return query_monitor


def get_database_optimizer() -> DatabaseOptimizer:
    """获取数据库优化器实例"""
    return db_optimizer


# 辅助函数
async def cached_db_query(db: AsyncSession, query: str, params: Optional[Dict[str, Any]] = None,
                         ttl: int = 300) -> Any:
    """执行带缓存的数据库查询"""
    # 检查缓存
    cached_result = await query_cache.get(query, params)
    if cached_result is not None:
        query_monitor.record_query(query, 0.001, cache_hit=True)
        return cached_result

    # 执行查询
    start_time = time.time()
    if params:
        result = await db.execute(text(query), params)
    else:
        result = await db.execute(text(query))

    execution_time = time.time() - start_time

    # 获取结果 - 更安全的Result对象处理
    try:
        # 尝试获取行数据
        data = result.fetchall()
        if data:
            # 转换为可序列化格式
            serializable_data = [dict(row._mapping) for row in data]
        else:
            # 如果没有行数据，可能是DML操作
            affected_rows = getattr(result, 'rowcount', 0) or 0
            serializable_data = {"affected_rows": affected_rows}
    except Exception:
        # 如果fetchall失败，尝试获取affected rows
        try:
            affected_rows = getattr(result, 'rowcount', 0) or 0
            serializable_data = {"affected_rows": affected_rows}
        except Exception:
            # 最终回退
            serializable_data = {"affected_rows": 0}

    # 缓存结果
    await query_cache.set(query, serializable_data, params, ttl)

    # 记录指标
    affected_rows = getattr(result, 'rowcount', 0) or 0
    query_monitor.record_query(query, execution_time, affected_rows=affected_rows)

    return serializable_data


async def invalidate_cache_for_table(table_name: str) -> int:
    """使指定表的缓存失效"""
    pattern = f"table:{table_name}"
    return await query_cache.invalidate_pattern(pattern)
