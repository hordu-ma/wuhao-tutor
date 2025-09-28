"""
安全和限流模块
实现API访问频率限制、AI服务调用限流和安全中间件
"""

import asyncio
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
import hashlib
import logging
from enum import Enum

from fastapi import Request, Response, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from src.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class RateLimitType(Enum):
    """限流类型枚举"""
    PER_IP = "per_ip"
    PER_USER = "per_user"
    PER_ENDPOINT = "per_endpoint"
    AI_SERVICE = "ai_service"


@dataclass
class RateLimitRule:
    """限流规则"""
    limit: int  # 限制次数
    window: int  # 时间窗口（秒）
    rule_type: RateLimitType
    endpoint: Optional[str] = None
    message: str = "请求过于频繁，请稍后重试"


class TokenBucket:
    """令牌桶算法实现"""

    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = capacity
        self.last_refill = time.time()

    def consume(self, tokens: int = 1) -> bool:
        """消费令牌"""
        self._refill()
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False

    def _refill(self) -> None:
        """补充令牌"""
        now = time.time()
        tokens_to_add = (now - self.last_refill) * self.refill_rate
        self.tokens = min(self.capacity, self.tokens + tokens_to_add)
        self.last_refill = now


class SlidingWindowCounter:
    """滑动窗口计数器"""

    def __init__(self, window_size: int, max_requests: int):
        self.window_size = window_size
        self.max_requests = max_requests
        self.requests: deque = deque()

    def is_allowed(self) -> bool:
        """检查是否允许请求"""
        now = time.time()
        # 清理过期请求
        while self.requests and self.requests[0] <= now - self.window_size:
            self.requests.popleft()

        if len(self.requests) < self.max_requests:
            self.requests.append(now)
            return True
        return False

    def get_remaining_requests(self) -> int:
        """获取剩余请求数"""
        now = time.time()
        while self.requests and self.requests[0] <= now - self.window_size:
            self.requests.popleft()
        return max(0, self.max_requests - len(self.requests))

    def get_reset_time(self) -> int:
        """获取重置时间"""
        if not self.requests:
            return 0
        return int(self.requests[0] + self.window_size)


class RateLimiter:
    """综合限流器"""

    def __init__(self):
        self.counters: Dict[str, SlidingWindowCounter] = {}
        self.buckets: Dict[str, TokenBucket] = {}
        self.rules: List[RateLimitRule] = []
        self._setup_default_rules()

    def _setup_default_rules(self) -> None:
        """设置默认限流规则"""
        self.rules = [
            # IP限流：每分钟100次请求
            RateLimitRule(
                limit=100,
                window=60,
                rule_type=RateLimitType.PER_IP,
                message="来自您IP地址的请求过于频繁，请稍后重试"
            ),
            # 用户限流：每分钟50次请求
            RateLimitRule(
                limit=50,
                window=60,
                rule_type=RateLimitType.PER_USER,
                message="您的请求过于频繁，请稍后重试"
            ),
            # AI服务限流：每分钟20次请求
            RateLimitRule(
                limit=20,
                window=60,
                rule_type=RateLimitType.AI_SERVICE,
                message="AI服务调用过于频繁，请稍后重试"
            ),
            # 敏感端点限流
            RateLimitRule(
                limit=10,
                window=60,
                rule_type=RateLimitType.PER_ENDPOINT,
                endpoint="/api/v1/auth/login",
                message="登录尝试过于频繁，请稍后重试"
            ),
        ]

    def add_rule(self, rule: RateLimitRule) -> None:
        """添加限流规则"""
        self.rules.append(rule)

    def _get_key(self, request: Request, rule: RateLimitRule, user_id: Optional[str] = None) -> str:
        """生成限流键"""
        if rule.rule_type == RateLimitType.PER_IP:
            return f"ip:{request.client.host if request.client else 'unknown'}"
        elif rule.rule_type == RateLimitType.PER_USER and user_id:
            return f"user:{user_id}"
        elif rule.rule_type == RateLimitType.PER_ENDPOINT and rule.endpoint:
            ip = request.client.host if request.client else 'unknown'
            return f"endpoint:{rule.endpoint}:ip:{ip}"
        elif rule.rule_type == RateLimitType.AI_SERVICE:
            # AI服务限流可以基于用户或IP
            if user_id:
                return f"ai:user:{user_id}"
            else:
                return f"ai:ip:{request.client.host if request.client else 'unknown'}"
        return "default"

    def is_allowed(self, request: Request, user_id: Optional[str] = None) -> tuple[bool, Optional[RateLimitRule], Optional[dict]]:
        """检查请求是否被允许"""
        for rule in self.rules:
            # 检查端点匹配
            if rule.endpoint and request.url.path != rule.endpoint:
                continue

            # 跳过需要用户ID但没有提供的规则
            if rule.rule_type == RateLimitType.PER_USER and not user_id:
                continue

            key = self._get_key(request, rule, user_id)

            # 获取或创建计数器
            if key not in self.counters:
                self.counters[key] = SlidingWindowCounter(rule.window, rule.limit)

            counter = self.counters[key]
            if not counter.is_allowed():
                # 返回限流信息
                rate_limit_info = {
                    'limit': rule.limit,
                    'remaining': counter.get_remaining_requests(),
                    'reset': counter.get_reset_time(),
                    'window': rule.window
                }
                return False, rule, rate_limit_info

        return True, None, None

    def is_ai_service_allowed(self, user_id: Optional[str] = None, ip: Optional[str] = None) -> bool:
        """检查AI服务调用是否被允许"""
        key = f"ai:user:{user_id}" if user_id else f"ai:ip:{ip or 'unknown'}"

        if key not in self.buckets:
            # 创建令牌桶：20个令牌，每3秒补充1个
            self.buckets[key] = TokenBucket(capacity=20, refill_rate=1/3)

        return self.buckets[key].consume()

    def cleanup_old_counters(self) -> None:
        """清理过期的计数器"""
        current_time = time.time()
        keys_to_remove = []

        for key, counter in self.counters.items():
            # 如果计数器长时间没有请求，清理它
            if (not counter.requests or
                current_time - counter.requests[-1] > counter.window_size * 2):
                keys_to_remove.append(key)

        for key in keys_to_remove:
            del self.counters[key]

        # 清理令牌桶
        bucket_keys_to_remove = []
        for key, bucket in self.buckets.items():
            if current_time - bucket.last_refill > 300:  # 5分钟无活动
                bucket_keys_to_remove.append(key)

        for key in bucket_keys_to_remove:
            del self.buckets[key]


class RateLimitMiddleware(BaseHTTPMiddleware):
    """限流中间件"""

    def __init__(self, app, rate_limiter: RateLimiter):
        super().__init__(app)
        self.rate_limiter = rate_limiter

    async def dispatch(self, request: Request, call_next) -> Response:
        """处理请求限流"""
        # 跳过健康检查等端点
        if request.url.path in ["/health", "/", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)

        # 获取用户ID（如果有的话）
        user_id = None
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            # 这里可以解析JWT获取用户ID，暂时跳过
            pass

        # 检查限流
        allowed, rule, rate_limit_info = self.rate_limiter.is_allowed(request, user_id)

        if not allowed and rule and rate_limit_info:
            response = JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "code": "RATE_LIMITED",
                    "message": rule.message,
                    "details": {
                        "limit": rate_limit_info["limit"],
                        "window_seconds": rate_limit_info["window"],
                        "retry_after": rate_limit_info["reset"] - int(time.time())
                    }
                }
            )

            # 添加标准限流头
            response.headers["X-RateLimit-Limit"] = str(rate_limit_info["limit"])
            response.headers["X-RateLimit-Remaining"] = str(rate_limit_info["remaining"])
            response.headers["X-RateLimit-Reset"] = str(rate_limit_info["reset"])
            response.headers["Retry-After"] = str(rate_limit_info["reset"] - int(time.time()))

            return response

        # 处理请求
        response = await call_next(request)

        # 添加限流信息头（如果有的话）
        if rate_limit_info:
            response.headers["X-RateLimit-Limit"] = str(rate_limit_info["limit"])
            response.headers["X-RateLimit-Remaining"] = str(rate_limit_info["remaining"])
            response.headers["X-RateLimit-Reset"] = str(rate_limit_info["reset"])

        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """安全头中间件"""

    async def dispatch(self, request: Request, call_next) -> Response:
        """添加安全头"""
        response = await call_next(request)

        # 添加安全头
        security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Content-Security-Policy": (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self'; "
                "connect-src 'self'; "
                "frame-ancestors 'none'"
            )
        }

        # 在生产环境添加HSTS
        if not settings.DEBUG:
            security_headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )

        for header, value in security_headers.items():
            response.headers[header] = value

        return response


class AIServiceLimiter:
    """AI服务专用限流器"""

    def __init__(self, rate_limiter: RateLimiter):
        self.rate_limiter = rate_limiter
        self.call_count = defaultdict(int)
        self.last_reset = defaultdict(float)

    async def check_limit(self, user_id: Optional[str] = None, ip: Optional[str] = None) -> bool:
        """检查AI服务调用限制"""
        if not self.rate_limiter.is_ai_service_allowed(user_id, ip):
            logger.warning(f"AI service rate limit exceeded for user:{user_id} ip:{ip}")
            return False
        return True

    def get_usage_stats(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """获取使用统计"""
        key = f"user:{user_id}" if user_id else "anonymous"
        return {
            "calls_today": self.call_count.get(key, 0),
            "last_call": self.last_reset.get(key, 0)
        }


# 创建全局实例
rate_limiter = RateLimiter()
ai_service_limiter = AIServiceLimiter(rate_limiter)


def get_rate_limiter() -> RateLimiter:
    """获取限流器实例"""
    return rate_limiter


def get_ai_service_limiter() -> AIServiceLimiter:
    """获取AI服务限流器实例"""
    return ai_service_limiter


async def cleanup_rate_limiters() -> None:
    """定期清理限流器的后台任务"""
    while True:
        try:
            rate_limiter.cleanup_old_counters()
            await asyncio.sleep(300)  # 每5分钟清理一次
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Error cleaning up rate limiters: {e}")
            await asyncio.sleep(300)


# 装饰器：AI服务调用限流
def ai_rate_limit(func: Callable) -> Callable:
    """AI服务调用限流装饰器"""
    async def wrapper(*args, **kwargs):
        # 获取用户信息（这里需要根据实际情况调整）
        user_id = kwargs.get('user_id')

        if not await ai_service_limiter.check_limit(user_id=user_id):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "code": "AI_SERVICE_RATE_LIMITED",
                    "message": "AI服务调用过于频繁，请稍后重试"
                }
            )

        return await func(*args, **kwargs)

    return wrapper


def get_client_ip(request: Request) -> str:
    """获取客户端IP地址"""
    # 检查代理头
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip

    return request.client.host if request.client else "unknown"


def hash_ip(ip: str) -> str:
    """对IP地址进行哈希处理（隐私保护）"""
    return hashlib.sha256(ip.encode()).hexdigest()[:16]
