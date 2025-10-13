#!/usr/bin/env python3
"""
服务器端执行的测试账号创建脚本
在生产服务器上直接运行，直接操作生产数据库
"""

import asyncio
import hashlib
import os
import secrets
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append("/opt/wuhao-tutor")

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.models.user import GradeLevel, User, UserRole
from src.repositories.base_repository import BaseRepository


def hash_password(password: str) -> str:
    """密码哈希 - 与UserService保持一致"""
    salt = secrets.token_hex(16)
    password_hash = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000
    )
    return f"{salt}:{password_hash.hex()}"


async def create_test_students():
    """创建三个测试学生账号"""

    # 测试学生数据
    test_students = [
        {
            "phone": "18888333726",
            "password": "Test123A",
            "name": "张小明",
            "nickname": "小明同学",
            "school": "北京市第一中学",
            "grade_level": GradeLevel.SENIOR_2.value,
            "class_name": "高二(3)班",
        },
        {
            "phone": "18765617300",
            "password": "Study456B",
            "name": "李小华",
            "nickname": "华华学霸",
            "school": "上海实验中学",
            "grade_level": GradeLevel.JUNIOR_3.value,
            "class_name": "初三(1)班",
        },
        {
            "phone": "15552877177",
            "password": "Learn789C",
            "name": "王小红",
            "nickname": "红红好学",
            "school": "广州育才中学",
            "grade_level": GradeLevel.SENIOR_1.value,
            "class_name": "高一(2)班",
        },
    ]

    async for db in get_db():
        user_repo = BaseRepository(User, db)
        created_users = []

        for student_data in test_students:
            # 检查用户是否已存在
            existing_user = await user_repo.get_by_field("phone", student_data["phone"])
            if existing_user:
                print(
                    f"✅ 用户 {student_data['name']} ({student_data['phone']}) 已存在"
                )
                created_users.append(
                    {"user": existing_user, "password": student_data["password"]}
                )
                continue

            # 准备用户数据
            password = student_data.pop("password")
            user_data = {
                **student_data,
                "password_hash": hash_password(password),
                "role": UserRole.STUDENT.value,
                "is_active": True,
                "is_verified": True,
                "login_count": 0,
            }

            # 创建用户
            try:
                user = await user_repo.create(user_data)
                await db.commit()
                await db.refresh(user)

                created_users.append({"user": user, "password": password})

                print(f"✅ 成功创建用户: {user.name} ({user.phone})")

            except Exception as e:
                await db.rollback()
                print(f"❌ 创建用户失败 {student_data['name']}: {str(e)}")
                continue

        print(f"\n🎉 操作完成: 可用测试账号共 {len(created_users)} 个")

        # 输出账号信息
        print("\n" + "=" * 60)
        print("📋 生产环境测试账号列表")
        print("=" * 60)

        for i, user_info in enumerate(created_users, 1):
            user = user_info["user"]
            password = user_info["password"]

            print(f"\n🔸 测试账号 {i}:")
            print(f"   姓名: {user.name}")
            print(f"   昵称: {user.nickname or '未设置'}")
            print(f"   手机号: {user.phone}")
            print(f"   密码: {password}")
            print(f"   学校: {user.school or '未设置'}")
            print(f"   年级: {user.grade_level or '未设置'}")
            print(f"   班级: {user.class_name or '未设置'}")
            print(f"   用户ID: {user.id}")

        print(f"\n🔗 登录地址: https://121.199.173.244")
        print(f"📖 API文档: https://121.199.173.244/docs")

        return created_users


async def main():
    """主函数"""
    print("🚀 开始在生产环境创建测试学生账号...")

    try:
        created_users = await create_test_students()

        if created_users:
            print(f"\n✅ 任务完成! 共有 {len(created_users)} 个可用测试账号")
        else:
            print("\n❌ 没有可用的测试账号")

    except Exception as e:
        print(f"\n❌ 脚本执行失败: {str(e)}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
