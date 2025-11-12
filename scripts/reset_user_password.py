#!/usr/bin/env python3
"""
生产环境密码重置脚本
用法: python scripts/reset_user_password.py <phone> <new_password>
"""

import argparse
import asyncio
import sys

from sqlalchemy import select

from src.core.database import AsyncSessionLocal
from src.models.user import User
from src.services.user_service import UserService


async def reset_password(phone: str, new_password: str):
    """重置用户密码"""
    async with AsyncSessionLocal() as db:
        # 查找用户
        result = await db.execute(select(User).where(User.phone == phone))
        user = result.scalar_one_or_none()

        if not user:
            print(f"❌ 用户 {phone} 不存在")
            return False

        # 创建service并重置密码
        user_service = UserService(db)
        new_hash = user_service._hash_password(new_password)

        # 直接更新
        user.password_hash = new_hash
        db.add(user)
        await db.commit()

        print(f"✅ 用户 {phone} 的密码已重置")
        print(f"   新密码: {new_password}")
        print(f"   Hash: {new_hash[:50]}...")
        return True


async def main():
    parser = argparse.ArgumentParser(description="重置用户密码")
    parser.add_argument("phone", help="用户手机号")
    parser.add_argument("password", help="新密码")

    args = parser.parse_args()

    if len(args.phone) != 11:
        print("❌ 手机号格式错误")
        return False

    if len(args.password) < 6:
        print("❌ 密码长度至少6个字符")
        return False

    return await reset_password(args.phone, args.password)


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
