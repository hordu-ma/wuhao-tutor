#!/usr/bin/env python3
"""
数据库迁移验证和测试脚本
用于验证数据库迁移的完整性和功能测试
"""

import asyncio
import sys
import os
from typing import Dict, List, Optional, Any
from pathlib import Path
import logging
from datetime import datetime, timezone
import uuid

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.sql import text

from src.core.config import get_settings
from src.models import *  # 导入所有模型

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DatabaseTester:
    """数据库测试器"""

    def __init__(self, environment: str = "development"):
        """
        初始化数据库测试器

        Args:
            environment: 环境名称
        """
        os.environ["ENVIRONMENT"] = environment
        self.settings = get_settings()
        self.environment = environment
        self.engine = None
        self.session_factory = None

        logger.info(f"初始化数据库测试器 - 环境: {environment}")

    async def setup(self) -> bool:
        """设置数据库连接"""
        try:
            self.engine = create_async_engine(
                str(self.settings.SQLALCHEMY_DATABASE_URI),
                echo=False
            )

            self.session_factory = async_sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine,
                class_=AsyncSession,
            )

            logger.info("✅ 数据库连接设置成功")
            return True

        except Exception as e:
            logger.error(f"❌ 数据库连接设置失败: {e}")
            return False

    async def cleanup(self) -> None:
        """清理数据库连接"""
        if self.engine:
            await self.engine.dispose()
            logger.info("✅ 数据库连接已清理")

    async def test_connection(self) -> bool:
        """测试数据库连接"""
        try:
            async with self.engine.begin() as conn:
                result = await conn.execute(text("SELECT 1"))
                assert result.scalar() == 1

            logger.info("✅ 数据库连接测试通过")
            return True

        except Exception as e:
            logger.error(f"❌ 数据库连接测试失败: {e}")
            return False

    async def test_table_structure(self) -> bool:
        """测试数据库表结构"""
        try:
            async with self.engine.begin() as conn:
                # 检查所有预期的表
                expected_tables = [
                    'users', 'user_sessions', 'homework',
                    'homework_submissions', 'homework_images', 'homework_reviews'
                ]

                for table_name in expected_tables:
                    result = await conn.execute(
                        text(
                            "SELECT column_name, data_type, is_nullable "
                            "FROM information_schema.columns "
                            "WHERE table_name = :table_name "
                            "ORDER BY ordinal_position"
                        ),
                        {"table_name": table_name}
                    )
                    columns = result.fetchall()

                    if not columns:
                        logger.error(f"❌ 表 '{table_name}' 不存在或无列信息")
                        return False

                    logger.info(f"✅ 表 '{table_name}' 结构正常 ({len(columns)} 列)")

                # 检查外键约束
                result = await conn.execute(
                    text(
                        "SELECT tc.constraint_name, tc.table_name, kcu.column_name, "
                        "ccu.table_name AS foreign_table_name, ccu.column_name AS foreign_column_name "
                        "FROM information_schema.table_constraints AS tc "
                        "JOIN information_schema.key_column_usage AS kcu "
                        "ON tc.constraint_name = kcu.constraint_name "
                        "JOIN information_schema.constraint_column_usage AS ccu "
                        "ON ccu.constraint_name = tc.constraint_name "
                        "WHERE tc.constraint_type = 'FOREIGN KEY'"
                    )
                )
                foreign_keys = result.fetchall()
                logger.info(f"✅ 外键约束检查通过 ({len(foreign_keys)} 个外键)")

                # 检查索引
                result = await conn.execute(
                    text(
                        "SELECT indexname, tablename FROM pg_indexes "
                        "WHERE schemaname = 'public' AND indexname NOT LIKE '%_pkey'"
                    )
                )
                indexes = result.fetchall()
                logger.info(f"✅ 索引检查通过 ({len(indexes)} 个自定义索引)")

            return True

        except Exception as e:
            logger.error(f"❌ 表结构测试失败: {e}")
            return False

    async def test_basic_operations(self) -> bool:
        """测试基本数据库操作"""
        try:
            async with self.session_factory() as session:
                # 测试用户表操作
                test_user_data = {
                    'id': uuid.uuid4(),
                    'phone': '13800000001',
                    'password_hash': 'test_hash',
                    'name': 'Test User',
                    'role': 'student'
                }

                # 插入测试数据
                await session.execute(
                    text(
                        "INSERT INTO users (id, phone, password_hash, name, role, created_at, updated_at) "
                        "VALUES (:id, :phone, :password_hash, :name, :role, NOW(), NOW())"
                    ),
                    test_user_data
                )

                # 查询测试数据
                result = await session.execute(
                    text("SELECT name, role FROM users WHERE phone = :phone"),
                    {"phone": test_user_data['phone']}
                )
                user = result.fetchone()

                if not user or user.name != test_user_data['name']:
                    logger.error("❌ 用户数据插入/查询测试失败")
                    return False

                # 更新测试数据
                await session.execute(
                    text("UPDATE users SET name = :new_name WHERE phone = :phone"),
                    {"new_name": "Updated Test User", "phone": test_user_data['phone']}
                )

                # 验证更新
                result = await session.execute(
                    text("SELECT name FROM users WHERE phone = :phone"),
                    {"phone": test_user_data['phone']}
                )
                updated_user = result.fetchone()

                if not updated_user or updated_user.name != "Updated Test User":
                    logger.error("❌ 用户数据更新测试失败")
                    return False

                # 清理测试数据
                await session.execute(
                    text("DELETE FROM users WHERE phone = :phone"),
                    {"phone": test_user_data['phone']}
                )

                await session.commit()

            logger.info("✅ 基本数据库操作测试通过")
            return True

        except Exception as e:
            logger.error(f"❌ 基本操作测试失败: {e}")
            return False

    async def test_complex_operations(self) -> bool:
        """测试复杂数据库操作"""
        try:
            async with self.session_factory() as session:
                # 创建测试用户
                user_id = uuid.uuid4()
                await session.execute(
                    text(
                        "INSERT INTO users (id, phone, password_hash, name, role, created_at, updated_at) "
                        "VALUES (:id, :phone, :password_hash, :name, :role, NOW(), NOW())"
                    ),
                    {
                        'id': user_id,
                        'phone': '13800000002',
                        'password_hash': 'test_hash',
                        'name': 'Complex Test User',
                        'role': 'student'
                    }
                )

                # 创建测试作业
                homework_id = uuid.uuid4()
                await session.execute(
                    text(
                        "INSERT INTO homework (id, title, subject, grade_level, creator_id, created_at, updated_at) "
                        "VALUES (:id, :title, :subject, :grade_level, :creator_id, NOW(), NOW())"
                    ),
                    {
                        'id': homework_id,
                        'title': 'Test Homework',
                        'subject': 'math',
                        'grade_level': 'grade_5',
                        'creator_id': user_id
                    }
                )

                # 创建测试提交
                submission_id = uuid.uuid4()
                await session.execute(
                    text(
                        "INSERT INTO homework_submissions (id, homework_id, student_id, student_name, status, created_at, updated_at) "
                        "VALUES (:id, :homework_id, :student_id, :student_name, :status, NOW(), NOW())"
                    ),
                    {
                        'id': submission_id,
                        'homework_id': homework_id,
                        'student_id': user_id,
                        'student_name': 'Complex Test User',
                        'status': 'uploaded'
                    }
                )

                # 测试联合查询
                result = await session.execute(
                    text(
                        "SELECT h.title, hs.status, u.name "
                        "FROM homework h "
                        "JOIN homework_submissions hs ON h.id = hs.homework_id "
                        "JOIN users u ON hs.student_id = u.id "
                        "WHERE h.id = :homework_id"
                    ),
                    {"homework_id": homework_id}
                )
                join_result = result.fetchone()

                if not join_result or join_result.title != 'Test Homework':
                    logger.error("❌ 联合查询测试失败")
                    return False

                # 测试事务回滚
                try:
                    async with session.begin():
                        await session.execute(
                            text("UPDATE homework SET title = :title WHERE id = :id"),
                            {"title": "Rollback Test", "id": homework_id}
                        )
                        # 故意引发错误来测试回滚
                        await session.execute(text("SELECT 1/0"))
                except:
                    pass  # 预期的错误

                # 验证事务回滚
                result = await session.execute(
                    text("SELECT title FROM homework WHERE id = :id"),
                    {"id": homework_id}
                )
                title_after_rollback = result.scalar()

                if title_after_rollback != 'Test Homework':
                    logger.error("❌ 事务回滚测试失败")
                    return False

                # 清理测试数据
                await session.execute(
                    text("DELETE FROM homework_submissions WHERE id = :id"),
                    {"id": submission_id}
                )
                await session.execute(
                    text("DELETE FROM homework WHERE id = :id"),
                    {"id": homework_id}
                )
                await session.execute(
                    text("DELETE FROM users WHERE id = :id"),
                    {"id": user_id}
                )

                await session.commit()

            logger.info("✅ 复杂数据库操作测试通过")
            return True

        except Exception as e:
            logger.error(f"❌ 复杂操作测试失败: {e}")
            return False

    async def test_performance(self) -> bool:
        """测试数据库性能"""
        try:
            async with self.session_factory() as session:
                # 批量插入性能测试
                start_time = datetime.now()
                user_ids = []

                # 插入100个测试用户
                for i in range(100):
                    user_id = uuid.uuid4()
                    user_ids.append(user_id)
                    await session.execute(
                        text(
                            "INSERT INTO users (id, phone, password_hash, name, role, created_at, updated_at) "
                            "VALUES (:id, :phone, :password_hash, :name, :role, NOW(), NOW())"
                        ),
                        {
                            'id': user_id,
                            'phone': f'1380000{i:04d}',
                            'password_hash': 'test_hash',
                            'name': f'Performance Test User {i}',
                            'role': 'student'
                        }
                    )

                insert_time = (datetime.now() - start_time).total_seconds()

                # 查询性能测试
                start_time = datetime.now()
                result = await session.execute(
                    text("SELECT COUNT(*) FROM users WHERE role = 'student'")
                )
                count = result.scalar()
                query_time = (datetime.now() - start_time).total_seconds()

                # 清理测试数据
                for user_id in user_ids:
                    await session.execute(
                        text("DELETE FROM users WHERE id = :id"),
                        {"id": user_id}
                    )

                await session.commit()

                logger.info(f"✅ 性能测试通过 - 插入耗时: {insert_time:.3f}s, 查询耗时: {query_time:.3f}s")
                logger.info(f"   批量插入速率: {100/insert_time:.1f} records/sec")

                # 性能警告
                if insert_time > 5.0:
                    logger.warning(f"⚠️  批量插入性能较慢: {insert_time:.3f}s")
                if query_time > 1.0:
                    logger.warning(f"⚠️  查询性能较慢: {query_time:.3f}s")

            return True

        except Exception as e:
            logger.error(f"❌ 性能测试失败: {e}")
            return False

    async def generate_test_report(self) -> Dict[str, Any]:
        """生成测试报告"""
        report = {
            "environment": self.environment,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "database_config": {
                "host": self.settings.POSTGRES_SERVER,
                "port": self.settings.POSTGRES_PORT,
                "database": self.settings.POSTGRES_DB,
                "user": self.settings.POSTGRES_USER
            },
            "test_results": {}
        }

        # 运行所有测试
        tests = [
            ("connection", self.test_connection),
            ("table_structure", self.test_table_structure),
            ("basic_operations", self.test_basic_operations),
            ("complex_operations", self.test_complex_operations),
            ("performance", self.test_performance)
        ]

        all_passed = True
        for test_name, test_func in tests:
            logger.info(f"🔄 运行测试: {test_name}")
            try:
                result = await test_func()
                report["test_results"][test_name] = {
                    "passed": result,
                    "error": None
                }
                if not result:
                    all_passed = False
            except Exception as e:
                report["test_results"][test_name] = {
                    "passed": False,
                    "error": str(e)
                }
                all_passed = False
                logger.error(f"❌ 测试异常: {test_name} - {e}")

        report["overall_result"] = all_passed
        return report

    async def run_all_tests(self) -> bool:
        """运行所有数据库测试"""
        logger.info("🚀 开始数据库测试...")

        if not await self.setup():
            return False

        try:
            report = await self.generate_test_report()

            # 输出测试结果
            logger.info("📊 测试报告:")
            logger.info(f"  环境: {report['environment']}")
            logger.info(f"  时间: {report['timestamp']}")
            logger.info(f"  数据库: {report['database_config']['host']}:{report['database_config']['port']}/{report['database_config']['database']}")

            passed_tests = sum(1 for result in report['test_results'].values() if result['passed'])
            total_tests = len(report['test_results'])

            logger.info(f"  测试结果: {passed_tests}/{total_tests} 通过")

            for test_name, result in report['test_results'].items():
                status = "✅" if result['passed'] else "❌"
                error_info = f" ({result['error']})" if result['error'] else ""
                logger.info(f"    {status} {test_name}{error_info}")

            if report['overall_result']:
                logger.info("🎉 所有数据库测试通过!")
            else:
                logger.error("💥 部分数据库测试失败!")

            return report['overall_result']

        finally:
            await self.cleanup()


async def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="数据库迁移验证和测试脚本")
    parser.add_argument(
        "--env",
        choices=["development", "testing", "production"],
        default="development",
        help="环境名称 (默认: development)"
    )
    parser.add_argument(
        "--test",
        choices=["all", "connection", "structure", "operations", "performance"],
        default="all",
        help="运行指定测试 (默认: all)"
    )

    args = parser.parse_args()

    tester = DatabaseTester(args.env)

    if not await tester.setup():
        sys.exit(1)

    try:
        if args.test == "all":
            success = await tester.run_all_tests()
        elif args.test == "connection":
            success = await tester.test_connection()
        elif args.test == "structure":
            success = await tester.test_table_structure()
        elif args.test == "operations":
            success = await tester.test_basic_operations() and await tester.test_complex_operations()
        elif args.test == "performance":
            success = await tester.test_performance()

        sys.exit(0 if success else 1)

    finally:
        await tester.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
