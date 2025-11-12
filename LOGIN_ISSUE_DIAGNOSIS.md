# 🔴 紧急诊断：用户登录问题分析

**问题描述：**

- 用户 13800000001 昨天遇到登录问题（已修复）
- 用户 18765617300 今天无法登录（密码：study456B，之前正常）
- 其他用户也开始反馈无法登录

**关键时间线：**

- 提交: e4e90ba (2025-11-11 18:01:38) "update README.md & fix the auto error"
- 改动文件：README.md, pyproject.toml, src/models/review.py, src/services/user_service.py

---

## 🔍 根因分析

### 改动 1：src/services/user_service.py - 密码验证逻辑改动

**昨天前的实现：**

```python
def _verify_password(self, password: str, password_hash: str) -> bool:
    """验证密码"""
    try:
        salt, stored_hash = password_hash.split(":")
        calculated_hash = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000
        )
        return calculated_hash.hex() == stored_hash
    except:
        return False
```

**问题：** 只支持 PBKDF2 格式（salt:hash）

**昨天后的改动：**
添加了 bcrypt 格式支持：

```python
def _verify_password(self, password: str, password_hash: str) -> bool:
    """验证密码 - 兼容 bcrypt 和 PBKDF2 两种算法"""
    if not password_hash:
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

### 🚨 发现的隐藏 Bug：

**Bug 1：异常处理过度宽松**
在 PBKDF2 验证部分：

```python
except (ValueError, AttributeError):
    return False
```

如果 password_hash 为任何非标准格式，会直接返回 False！

**Bug 2：可能的 None 检查问题**
如果 password_hash 是 None，早期检查会返回 False，但 extract_orm_str()可能返回 None

**Bug 3：bcrypt 验证可能失败**

- `pwd_context.verify()`可能抛出的异常被吞掉
- 如果所有用户的 hash 突然变成 bcrypt 格式但验证失败，所有用户都无法登录

### 改动 2：miniprogram 变更（可能的幕后黑手）

**auth.js 改动：**

- 存储策略改为 `{ ttl: 0, strategy: 'userInfo' }`
- ttl: 0 可能导致永久缓存或缓存失效

**config/index.js 改动：**

- userInfoTTL: 从 24 小时改为 30 天

**问题：** 这些变更可能导致旧 token 无法刷新或验证失败

### 改动 3：pyproject.toml 变更

- 可能更新了某个依赖版本，导致密码验证库行为变化

---

## 💡 最可能的根本原因

### 假设 A：密码 Hash 格式混乱（概率: 60%）

**症状：**

- 数据库中用户密码 hash 格式不一致
- 或者某个 migrate 改变了 hash 存储格式但没有更新验证逻辑

**验证方式：**
直接查询数据库中用户的 password_hash 字段格式

### 假设 B：bcrypt 验证代码有 bug（概率: 30%）

**症状：**

- pwd_context.verify()抛出异常但被吞掉
- 或者 pwd_context 初始化有问题

**验证方式：**
检查 pwd_context 是否正确初始化，测试 bcrypt 验证

### 假设 C：Token 过期/刷新问题（概率: 10%）

**症状：**

- Token 本身不过期但验证失败
- 或者新的缓存策略导致 token 无效

---

## 🔧 建议的解决方案顺序

1. **立即回滚** 昨天的 user_service.py 改动
2. **检查** 所有用户的 password_hash 格式
3. **修复** 密码验证逻辑中的 bug
4. **测试** 登录流程
