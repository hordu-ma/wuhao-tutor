#!/usr/bin/env python3
"""查询生产环境用户信息"""
import asyncio
import os
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker


async def get_production_users():
    """获取生产环境用户列表"""
    # 加载生产环境配置
    load_dotenv(".env.production")

    # 构建数据库连接URL
    user = os.getenv("POSTGRES_USER", "postgres")
    password = os.getenv("POSTGRES_PASSWORD")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.getenv("POSTGRES_DB", "wuhao_tutor")

    if not password:
        print("错误: 未找到数据库密码配置")
        return

    database_url = f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{db}"

    try:
        engine = create_async_engine(database_url, echo=False)
        async_session = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )

        async with async_session() as session:
            # 查询用户信息
            query = text(
                """
                SELECT 
                    id::text as id,
                    username, 
                    email, 
                    phone, 
                    role, 
                    grade, 
                    is_active,
                    created_at,
                    last_login_at
                FROM users 
                WHERE deleted_at IS NULL
                ORDER BY created_at DESC
            """
            )

            result = await session.execute(query)
            users = result.fetchall()

            print(f"\n=== 生产环境用户信息 ({len(users)} 个活跃用户) ===\n")

            if not users:
                print("未找到任何用户")
                return

            # 打印表头
            print(
                f"{'序号':<4} {'用户名':<20} {'邮箱':<30} {'手机':<15} {'角色':<10} {'年级':<10} {'状态':<6} {'创建时间':<20} {'最后登录':<20}"
            )
            print("=" * 165)

            # 打印用户信息
            for idx, user in enumerate(users, 1):
                (
                    user_id,
                    username,
                    email,
                    phone,
                    role,
                    grade,
                    is_active,
                    created_at,
                    last_login,
                ) = user

                status = "✓激活" if is_active else "✗禁用"
                grade_str = grade or "-"
                email_str = email or "-"
                phone_str = phone or "-"
                created_str = str(created_at)[:19] if created_at else "-"
                last_login_str = str(last_login)[:19] if last_login else "从未登录"

                print(
                    f"{idx:<4} {username:<20} {email_str:<30} {phone_str:<15} "
                    f"{role:<10} {grade_str:<10} {status:<6} {created_str:<20} {last_login_str:<20}"
                )

                # 详细信息
                if idx <= 5:  # 只显示前5个用户的ID
                    print(f"     └─ ID: {user_id}")

            print("\n")

            # 统计信息
            roles_query = text(
                """
                SELECT role, COUNT(*) as count
                FROM users
                WHERE deleted_at IS NULL
                GROUP BY role
            """
            )
            roles_result = await session.execute(roles_query)
            roles = roles_result.fetchall()

            print("=== 用户角色统计 ===")
            for role, count in roles:
                print(f"  {role}: {count} 人")

        await engine.dispose()

    except Exception as e:
        print(f"错误: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(get_production_users())
