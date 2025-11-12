# 🔴 紧急：登录问题根本原因 & 完整解决方案

## 问题根因确认 ✓

### Bug 位置: `src/services/user_service.py` - `_verify_password()` 方法

**问题代码:**

```python
def _verify_password(self, password: str, password_hash: str) -> bool:
    """验证密码 - 兼容 bcrypt 和 PBKDF2 两种算法"""
    if not password_hash:  # ❌ BUG 在这里！
        return False

    # 1. 尝试 bcrypt 验证（旧格式）
    if password_hash.startswith("$2b$") or password_hash.startswith("$2a$"):
        try:
            return pwd_context.verify(password, password_hash)
        except Exception:
            return False

    # 2. 尝试 PBKDF2 验证（新格式，salt:hash）
    try:
        salt, stored_hash = password_hash.split(":")
        calculated_hash = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000
        )
        return calculated_hash.hex() == stored_hash
    except (ValueError, AttributeError):
        return False
```

### 触发 Bug 的调用链:

**在 `authenticate_user()` 中:**

```python
if not self._verify_password(
    password, extract_orm_str(user, "password_hash")  # ← 这里返回的可能是""
):
    return None
```

**`extract_orm_str()` 的问题:**

```python
def safe_str(value: Any) -> str:
    """安全转换为字符串"""
    if value is None:
        return ""  # ← 返回空字符串！
    if isinstance(value, str):
        return value
    return str(value)
```

### 触发的场景:

1. **用户的 password_hash 字段为 NULL 或 None** (可能由某个 migrate 导致)
2. `extract_orm_str(user, "password_hash")` 返回空字符串 `""`
3. `_verify_password(password, "")` 接收到空字符串
4. 第一行的 `if not password_hash: return False` 直接返回 False
5. **所有用户都无法登录！** 💥

---

## 解决方案

### 方案 A：快速修复 (推荐，5 分钟)

**问题:** `_verify_password()` 没有区分 "无效 hash" 和 "空 hash"

**修复方法:** 添加详细的日志和错误处理

```python
def _verify_password(self, password: str, password_hash: str) -> bool:
    """验证密码 - 兼容 bcrypt 和 PBKDF2 两种算法"""
    # 检查密码哈希格式
    if not password_hash:
        logger.warning("Password hash is empty or None - user data may be corrupted")
        return False

    if not isinstance(password_hash, str):
        logger.warning(f"Password hash is not string: {type(password_hash)}")
        return False

    # 1. 尝试 bcrypt 验证（旧格式）
    if password_hash.startswith("$2b$") or password_hash.startswith("$2a$"):
        try:
            return pwd_context.verify(password, password_hash)
        except Exception as e:
            logger.error(f"Bcrypt verification failed: {str(e)}")
            return False

    # 2. 尝试 PBKDF2 验证（新格式，salt:hash）
    if ":" in password_hash:
        try:
            salt, stored_hash = password_hash.split(":")
            if not salt or not stored_hash:
                logger.warning("Invalid PBKDF2 format: empty salt or hash")
                return False
            calculated_hash = hashlib.pbkdf2_hmac(
                "sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000
            )
            return calculated_hash.hex() == stored_hash
        except (ValueError, AttributeError) as e:
            logger.error(f"PBKDF2 verification failed: {str(e)}")
            return False

    # 3. 未知格式
    logger.warning(f"Unknown password hash format: {password_hash[:20]}...")
    return False
```

---

### 方案 B：深层修复 (彻底解决，需要数据库检查)

**检查数据库中是否有 NULL 的 password_hash:**

```sql
-- 查询所有password_hash为NULL的用户
SELECT id, phone, password_hash FROM users WHERE password_hash IS NULL;

-- 如果有结果，需要修复这些用户的密码hash
UPDATE users
SET password_hash = 'corrupted_hash_needs_reset'
WHERE password_hash IS NULL;
```

---

### 方案 C：立即回滚 (最安全)

```bash
# 回滚最后一次提交
git revert HEAD

# 或者回到前一个版本
git reset --hard HEAD~1

# 然后推送到生产
git push origin main
```

---

## 诊断命令 (执行以确认问题)

```python
# 检查是否所有用户都有password_hash
import asyncio
from src.core.database import AsyncSessionLocal
from src.models.user import User
from sqlalchemy import select, func

async def diagnose():
    async with AsyncSessionLocal() as db:
        # 统计用户总数
        total_result = await db.execute(select(func.count(User.id)))
        total_users = total_result.scalar()

        # 统计password_hash为NULL的用户
        null_result = await db.execute(
            select(func.count(User.id)).where(User.password_hash == None)
        )
        null_count = null_result.scalar()

        # 统计password_hash为空字符串的用户
        empty_result = await db.execute(
            select(func.count(User.id)).where(User.password_hash == "")
        )
        empty_count = empty_result.scalar()

        print(f"总用户数: {total_users}")
        print(f"password_hash为NULL: {null_count}")
        print(f"password_hash为空字符串: {empty_count}")

        # 查询有问题的用户样本
        result = await db.execute(
            select(User.phone, User.password_hash)
            .where((User.password_hash == None) | (User.password_hash == ""))
            .limit(5)
        )
        rows = result.all()
        print(f"\n有问题的用户样本:")
        for phone, password_hash in rows:
            print(f"  Phone: {phone}, Hash: {repr(password_hash)}")

asyncio.run(diagnose())
```

---

## 我的推荐

### 立即执行的 3 个步骤:

1. **应用方案 A** (快速修复 `_verify_password()`)

   - 添加详细的日志
   - 添加类型检查
   - 推送到生产

2. **执行诊断命令** 确认 password_hash 的实际状态

3. **如果发现 NULL/空值** 执行数据库修复 SQL

### 优先级:

- 🔴 **P0**: 应用方案 A (防止继续扩散)
- 🟡 **P1**: 诊断并修复数据库
- 🟢 **P2**: 根本分析昨天的改动为什么会导致 NULL hash

---

## 根本原因追查

需要查看:

1. 最近是否有 migration 改变了 password_hash 字段定义
2. 昨天的修改是否触发了某个 cascade delete 或 set null 操作
3. pyproject.toml 中是否有新的 ORM 行为
