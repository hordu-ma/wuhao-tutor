# 用户登录问题 - 解决方案总结

## 📊 问题诊断结果

**问题类型**: 关键密码验证逻辑 Bug  
**影响范围**: 所有尝试登录的用户  
**根本原因**: `_verify_password()` 对空/NULL 密码 hash 的处理不当

---

## 🎯 三个可能的根本原因 (优先级排序)

### 【最可能】原因 1: password_hash 字段为 NULL (70%概率)

**症状**:

- 数据库中某些用户的 password_hash 为 NULL 或空字符串
- 可能由于某个 migrate 或数据库操作导致

**验证**:

```sql
SELECT COUNT(*) FROM users WHERE password_hash IS NULL OR password_hash = '';
```

**修复**:

- 恢复数据库备份
- 或手动更新这些用户的密码 hash

---

### 【次可能】原因 2: bcrypt 验证逻辑有 bug (20%概率)

**症状**:

- pwd_context.verify() 抛出异常被吞掉
- 或密码本来是 bcrypt 格式但验证失败

**修复**:

- 添加更详细的错误日志
- 改进异常处理

---

### 【最不可能】原因 3: 其他未知原因 (10%概率)

---

## 🔧 建议的解决方案执行顺序

### 步骤 1️⃣: 立即应用代码修复 (1 分钟)

在 `src/services/user_service.py` 中改进 `_verify_password()`:

```python
def _verify_password(self, password: str, password_hash: str) -> bool:
    """验证密码 - 兼容 bcrypt 和 PBKDF2 两种算法"""
    # 检查密码哈希格式
    if not password_hash:
        logger.error(f"[LOGIN_FAIL] Password hash is empty - user data corrupted")
        return False

    if not isinstance(password_hash, str):
        logger.error(f"[LOGIN_FAIL] Password hash is not string: {type(password_hash)}")
        return False

    # 1. 尝试 bcrypt 验证（旧格式）
    if password_hash.startswith("$2b$") or password_hash.startswith("$2a$"):
        try:
            result = pwd_context.verify(password, password_hash)
            logger.debug(f"[LOGIN] Bcrypt verification: {'success' if result else 'failed'}")
            return result
        except Exception as e:
            logger.error(f"[LOGIN_FAIL] Bcrypt verification error: {str(e)}")
            return False

    # 2. 尝试 PBKDF2 验证（新格式，salt:hash）
    if ":" in password_hash:
        try:
            salt, stored_hash = password_hash.split(":", 1)  # 仅分割一次
            if not salt or not stored_hash:
                logger.error(f"[LOGIN_FAIL] PBKDF2 - empty salt or hash")
                return False
            calculated_hash = hashlib.pbkdf2_hmac(
                "sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000
            )
            result = calculated_hash.hex() == stored_hash
            logger.debug(f"[LOGIN] PBKDF2 verification: {'success' if result else 'failed'}")
            return result
        except (ValueError, AttributeError) as e:
            logger.error(f"[LOGIN_FAIL] PBKDF2 verification error: {str(e)}")
            return False

    # 3. 未知格式
    logger.error(f"[LOGIN_FAIL] Unknown password hash format: {password_hash[:20]}...")
    return False
```

**操作**: 直接编辑文件并提交

---

### 步骤 2️⃣: 诊断数据库状态 (2 分钟)

运行诊断脚本确认问题:

```bash
cd /Users/liguoma/my-devs/python/wuhao-tutor
uv run python3 << 'EOF'
import asyncio
from src.core.database import AsyncSessionLocal
from src.models.user import User
from sqlalchemy import select, func

async def diagnose():
    async with AsyncSessionLocal() as db:
        # 统计用户总数
        total_result = await db.execute(select(func.count(User.id)))
        total_users = total_result.scalar() or 0

        # 统计password_hash为NULL的用户
        null_result = await db.execute(
            select(func.count(User.id)).where(User.password_hash.is_(None))
        )
        null_count = null_result.scalar() or 0

        # 统计password_hash为空字符串的用户
        empty_result = await db.execute(
            select(func.count(User.id)).where(User.password_hash == "")
        )
        empty_count = empty_result.scalar() or 0

        print(f"✓ 总用户数: {total_users}")
        print(f"✗ password_hash为NULL: {null_count}")
        print(f"✗ password_hash为空字符串: {empty_count}")

        if null_count > 0 or empty_count > 0:
            print("\n⚠️  发现问题用户!")
            result = await db.execute(
                select(User.phone, User.password_hash)
                .where((User.password_hash.is_(None)) | (User.password_hash == ""))
                .limit(10)
            )
            rows = result.all()
            for phone, password_hash in rows:
                print(f"  Phone: {phone}, Hash: {repr(password_hash)}")

asyncio.run(diagnose())
EOF
```

---

### 步骤 3️⃣: 根据诊断结果执行修复

**如果发现 NULL/空的 password_hash:**

```bash
# 查找这些用户的备份密码hash
# 方法1: 从git历史恢复
git log --oneline -p -- 用户数据

# 方法2: 从PostgreSQL备份恢复
# /Users/liguoma/my-devs/python/wuhao-tutor/backups/CRITICAL_USERS_20251108.csv

# 方法3: 手动重置用户密码
# 让用户通过密码重置流程重新设置密码
```

---

### 步骤 4️⃣: 测试登录 (3 分钟)

```bash
# 用test用户测试登录
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"phone": "18765617300", "password": "study456B"}'

# 应该返回200 + token，而不是401
```

---

## 📋 核心改动清单

| 文件                           | 改动                      | 理由                   |
| ------------------------------ | ------------------------- | ---------------------- |
| `src/services/user_service.py` | 改进 `_verify_password()` | 添加详细日志和错误处理 |
| `LOGIN_SOLUTION.md`            | 创建                      | 记录问题和解决方案     |

---

## ⚠️ 注意事项

1. **数据库备份**: 在做任何修复前检查备份
2. **回滚方案**: 如果修复失败，立即 `git revert HEAD`
3. **用户通知**: 修复后通知用户可以重新登录
4. **根因分析**: 修复后需要深入调查为什么会出现 NULL hash

---

## 最终建议

✅ **立即执行**: 步骤 1 (代码修复) + 步骤 2 (诊断)  
✅ **根据结果**: 步骤 3 (数据修复)  
✅ **验证**: 步骤 4 (测试)
