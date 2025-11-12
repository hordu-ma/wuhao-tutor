#!/usr/bin/env python3
"""
修复用户密码脚本

将指定用户的密码hash重置为使用当前正确的PBKDF2算法生成的格式。
这是一个紧急修复脚本，用于处理密码验证失败的情况。

使用方法:
    python scripts/fix_user_password.py <phone> <password>

示例:
    python scripts/fix_user_password.py 18765617300 study456B
"""

import asyncio
import hashlib
import secrets
import sys
from pathlib import Path

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.database import get_db_session
from src.repositories.user_repository import UserRepository


async def generate_pbkdf2_hash(password: str) -> str:
    """生成PBKDF2格式的密码hash"""
    salt = secrets.token_hex(16)
    password_hash = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000
    )
    return f"{salt}:{password_hash.hex()}"


async def fix_user_password(phone: str, password: str) -> None:
    """修复指定用户的密码"""
    print(f"\n🔧 修复用户密码")
    print(f"   电话: {phone}")
    print(f"   新密码: {password}")
    print(f"   算法: PBKDF2-SHA256")

    try:
        # 获取数据库会话
        async with await get_db_session() as db:
            user_repo = UserRepository(db)

            # 查询用户
            print(f"\n📍 查询用户...")
            user = await user_repo.get_by_field("phone", phone)
            if not user:
                print(f"❌ 用户不存在: {phone}")
                return

            print(f"✅ 找到用户: {user.name} ({phone})")

            # 生成新的hash
            print(f"\n🔐 生成新的密码hash...")
            new_hash = await generate_pbkdf2_hash(password)
            print(f"✅ 新hash: {new_hash[:50]}...")

            # 验证这个新hash是否可以验证密码
            print(f"\n✔️  验证新hash...")
            salt, stored_hash = new_hash.split(":", 1)
            calculated_hash = hashlib.pbkdf2_hmac(
                "sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000
            )
            if calculated_hash.hex() == stored_hash:
                print(f"✅ 新hash验证成功")
            else:
                print(f"❌ 新hash验证失败 - 这不应该发生!")
                return

            # 更新数据库
            print(f"\n💾 更新数据库...")
            user_id = str(user.id)
            await user_repo.update(user_id, {"password_hash": new_hash})
            print(f"✅ 密码hash已更新")

            print(f"\n✅ 用户密码修复成功！")
            print(f"   用户: {phone}")
            print(f"   新密码可用来登录")

    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback

        traceback.print_exc()


async def main():
    """主函数"""
    if len(sys.argv) != 3:
        print("使用方法: python scripts/fix_user_password.py <phone> <password>")
        print("示例:     python scripts/fix_user_password.py 18765617300 study456B")
        sys.exit(1)

    phone = sys.argv[1]
    password = sys.argv[2]

    # 验证密码长度
    if len(password) < 6:
        print("❌ 密码长度至少6个字符")
        sys.exit(1)

    await fix_user_password(phone, password)


if __name__ == "__main__":
    asyncio.run(main())
