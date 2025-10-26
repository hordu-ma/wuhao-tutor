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


async def export_users_to_markdown(users, md_path: Path, session: AsyncSession):
    """导出用户信息到 Markdown 文档"""
    from datetime import datetime

    with open(md_path, "w", encoding="utf-8") as f:
        # 写入文档头
        f.write("# 生产环境用户信息报告\n\n")
        f.write(f"**导出时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**总用户数**: {len(users)}\n\n")
        f.write("---\n\n")

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

        f.write("## 用户角色统计\n\n")
        for role, count in roles:
            f.write(f"- **{role}**: {count} 人\n")
        f.write("\n---\n\n")

        # 用户详细信息表格
        f.write("## 用户详细信息\n\n")
        f.write(
            "| 序号 | 姓名 | 昵称 | 手机号 | 角色 | 年级 | 学校 | 班级 | 激活状态 | 验证状态 | 创建时间 | 更新时间 | 用户ID |\n"
        )
        f.write(
            "|------|------|------|--------|------|------|------|------|----------|----------|----------|----------|--------|\n"
        )

        for idx, user in enumerate(users, 1):
            (
                user_id,
                phone,
                name,
                nickname,
                role,
                grade_level,
                school,
                class_name,
                is_active,
                is_verified,
                created_at,
                updated_at,
            ) = user

            status = "✓ 激活" if is_active else "✗ 禁用"
            verified = "✓ 已验证" if is_verified else "✗ 未验证"
            nickname_str = nickname or "-"
            grade_str = grade_level or "-"
            school_str = school or "-"
            class_str = class_name or "-"
            created_str = str(created_at)[:19] if created_at else "-"
            updated_str = str(updated_at)[:19] if updated_at else "-"

            f.write(
                f"| {idx} | {name} | {nickname_str} | {phone} | "
                f"{role} | {grade_str} | {school_str} | {class_str} | {status} | {verified} | "
                f"{created_str} | {updated_str} | `{user_id}` |\n"
            )

        f.write("\n---\n\n")
        f.write(
            "**注意**: 此文档包含敏感信息，已被添加到 .gitignore，请勿提交到版本控制系统。\n"
        )


async def get_production_users(export_to_md: bool = False):
    """获取生产环境用户列表

    Args:
        export_to_md: 是否导出为 Markdown 文档
    """
    # 加载生产环境配置
    load_dotenv(".env.production")

    # 构建数据库连接URL
    user = os.getenv("POSTGRES_USER", "postgres")
    password = os.getenv("POSTGRES_PASSWORD")
    host = os.getenv("POSTGRES_SERVER") or os.getenv("POSTGRES_HOST", "localhost")
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
                    phone, 
                    name, 
                    nickname,
                    role, 
                    grade_level, 
                    school,
                    class_name,
                    is_active,
                    is_verified,
                    created_at,
                    updated_at
                FROM users 
                WHERE deleted_at IS NULL
                ORDER BY created_at DESC
            """
            )

            result = await session.execute(query)
            users = result.fetchall()

            if export_to_md:
                # 导出为 Markdown 文档
                md_path = Path(__file__).parent.parent / "production_users_report.md"
                await export_users_to_markdown(users, md_path, session)
                print(f"\n✓ 用户信息已导出到: {md_path}")
                return

            print(f"\n=== 生产环境用户信息 ({len(users)} 个活跃用户) ===\n")

            if not users:
                print("未找到任何用户")
                return

            # 打印表头
            print(
                f"{'序号':<4} {'姓名':<15} {'手机号':<15} {'角色':<10} {'年级':<10} {'状态':<8} {'验证':<8} {'创建时间':<20}"
            )
            print("=" * 120)

            # 打印用户信息
            for idx, user in enumerate(users, 1):
                (
                    user_id,
                    phone,
                    name,
                    nickname,
                    role,
                    grade_level,
                    school,
                    class_name,
                    is_active,
                    is_verified,
                    created_at,
                    updated_at,
                ) = user

                status = "✓激活" if is_active else "✗禁用"
                verified = "✓已验" if is_verified else "✗未验"
                grade_str = grade_level or "-"
                created_str = str(created_at)[:19] if created_at else "-"

                print(
                    f"{idx:<4} {name:<15} {phone:<15} "
                    f"{role:<10} {grade_str:<10} {status:<8} {verified:<8} {created_str:<20}"
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
    import argparse

    parser = argparse.ArgumentParser(description="查询生产环境用户信息")
    parser.add_argument("--export", action="store_true", help="导出为 Markdown 文档")
    args = parser.parse_args()

    asyncio.run(get_production_users(export_to_md=args.export))
