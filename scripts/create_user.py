#!/usr/bin/env python3
"""
用户账号创建脚本
用于管理员快速创建用户账号，自动生成密码
支持开发环境和生产环境
"""

import argparse
import asyncio
import re
import secrets
import string
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

import os

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.core.config import get_settings
from src.models.user import User
from src.repositories.base_repository import BaseRepository
from src.services.user_service import UserService


def generate_secure_password(length: int = 8) -> str:
    """生成安全的随机密码"""
    # 确保至少包含一个大写字母、一个小写字母和一个数字
    while True:
        password = "".join(
            secrets.choice(string.ascii_letters + string.digits) for _ in range(length)
        )

        # 检查是否满足复杂度要求
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)

        if has_upper and has_lower and has_digit:
            return password


def validate_phone(phone: str) -> bool:
    """验证手机号格式"""
    pattern = r"^1[3-9]\d{9}$"
    return bool(re.match(pattern, phone))


async def check_phone_exists(phone: str, user_repo: BaseRepository) -> bool:
    """检查手机号是否已存在"""
    try:
        existing_user = await user_repo.get_by_field("phone", phone)
        return existing_user is not None
    except Exception:
        return False


async def create_user_interactive(env_file: str):
    """交互式创建用户"""
    print("=" * 60)
    print("🎓 五好伴学 - 用户账号创建工具")
    print("=" * 60)

    # 获取手机号
    while True:
        phone = input("\n📱 请输入用户手机号: ").strip()
        if not phone:
            print("❌ 手机号不能为空，请重新输入")
            continue

        if not validate_phone(phone):
            print("❌ 手机号格式不正确，请输入11位有效手机号")
            continue

        break

    # 检查手机号是否已存在
    load_dotenv(env_file)
    settings = get_settings()
    database_url = settings.SQLALCHEMY_DATABASE_URI

    engine = create_async_engine(database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        user_service = UserService(session)

        # 检查手机号是否已存在
        try:
            existing_user = await user_service.user_repo.get_by_field("phone", phone)
            if existing_user:
                print(f"❌ 手机号 {phone} 已存在，请使用其他手机号")
                await engine.dispose()
                return
        except Exception as e:
            print(f"⚠️  手机号检查失败: {str(e)}")
            print("⚠️  将继续创建用户，请确保手机号唯一性")
            # 不返回，继续创建

        # 获取用户姓名
        while True:
            name = input("👤 请输入用户姓名: ").strip()
            if not name:
                print("❌ 姓名不能为空，请重新输入")
                continue
            if len(name) > 50:
                print("❌ 姓名长度不能超过50个字符")
                continue
            break

        # 生成密码
        password = generate_secure_password(8)
        print(f"\n🔐 生成的登录密码: {password}")
        print("⚠️  请妥善保存此密码，用户首次登录时需要使用")

        # 确认创建
        confirm = (
            input(f"\n确认创建用户账号吗？(手机号: {phone}, 姓名: {name}) [y/N]: ")
            .strip()
            .lower()
        )
        if confirm not in ["y", "yes", "是", "确认"]:
            print("❌ 操作已取消")
            await engine.dispose()
            return

        try:
            # 使用正确的密码哈希格式创建用户
            # 使用UserService的密码哈希方法
            password_hash = user_service._hash_password(password)

            user_data = {
                "phone": phone,
                "password_hash": password_hash,
                "name": name,
                "nickname": name,
                "role": "student",
                "is_active": True,
                "is_verified": True,
                "login_count": 0,
            }

            user = await user_service.user_repo.create(user_data)

            print("\n" + "=" * 60)
            print("✅ 用户账号创建成功！")
            print("=" * 60)
            print(f"👤 用户ID: {user.id}")
            print(f"📱 手机号: {user.phone}")
            print(f"👤 姓名: {user.name}")
            print(f"🔐 密码: {password}")
            print(f"📧 角色: {user.role}")
            print(f"✅ 状态: {'激活' if user.is_active else '未激活'}")
            print(f"✅ 验证: {'已验证' if user.is_verified else '未验证'}")
            print(f"📅 创建时间: {user.created_at}")
            print("=" * 60)

            print("\n📋 使用说明:")
            print("1. 将手机号和密码告知用户")
            print("2. 用户可以使用手机号+密码登录")
            print("3. 建议用户首次登录后修改密码")
            print("4. 可以引导用户完善个人信息（学校、年级等）")

        except Exception as e:
            print(f"❌ 创建用户失败: {str(e)}")
        finally:
            await engine.dispose()


def main():
    """主函数"""
    print("=" * 60)
    print("🎓 五好伴学 - 用户账号创建工具")
    print("=" * 60)

    # 环境选择
    while True:
        print("\n请选择目标环境:")
        print("1. 开发环境 (development) - 本地数据库")
        print("2. 生产环境 (production) - 阿里云数据库")
        env_choice = input("请选择 [1/2]: ").strip()

        if env_choice == "1":
            env_file = ".env"
            env_name = "开发环境"
            break
        elif env_choice == "2":
            env_file = ".env.production"
            env_name = "生产环境"
            break
        else:
            print("❌ 请输入 1 或 2")

    print(f"\n🔧 目标环境: {env_name}")
    print(f"📄 配置文件: {env_file}")

    try:
        # 检查环境文件是否存在
        if not Path(env_file).exists():
            print(f"❌ 配置文件 {env_file} 不存在")
            return

        # 运行异步函数
        asyncio.run(create_user_interactive(env_file))

    except KeyboardInterrupt:
        print("\n\n❌ 操作已取消")
    except Exception as e:
        print(f"\n❌ 脚本执行出错: {str(e)}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
