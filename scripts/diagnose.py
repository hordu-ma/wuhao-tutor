#!/usr/bin/env python3
"""
五好伴学项目诊断脚本
检查项目的各个模块是否正常工作
"""

import asyncio
import os
import sys
import traceback
from pathlib import Path
from typing import List, Tuple

# 添加src到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))


class DiagnosticRunner:
    """诊断运行器"""

    def __init__(self):
        self.results: List[Tuple[str, bool, str]] = []

    def test_module_imports(self) -> None:
        """测试模块导入"""
        print("🔍 测试模块导入...")

        modules = [
            "src.main",
            "src.core.config",
            "src.core.database",
            "src.core.logging",
            "src.models.base",
            "src.models.user",
            "src.models.homework",
            "src.models.learning",
            "src.schemas.common",
            "src.schemas.auth",
            "src.schemas.bailian",
            "src.services.bailian_service",
            "src.services.user_service",
            "src.services.learning_service",
            "src.api.v1.api",
            "src.api.v1.endpoints.auth",
            "src.api.v1.endpoints.learning",
        ]

        failed_imports = []

        for module in modules:
            try:
                __import__(module)
                print(f"  ✅ {module}")
            except Exception as e:
                print(f"  ❌ {module}: {str(e)}")
                failed_imports.append((module, str(e)))

        success = len(failed_imports) == 0
        message = (
            "所有模块导入成功" if success else f"{len(failed_imports)}个模块导入失败"
        )
        self.results.append(("模块导入", success, message))

        if failed_imports:
            for module, error in failed_imports:
                print(f"    详细错误 - {module}: {error}")

    def test_configuration(self) -> None:
        """测试配置加载"""
        print("\\n⚙️ 测试配置加载...")

        try:
            from src.core.config import get_settings

            # 测试开发环境配置
            os.environ["ENVIRONMENT"] = "development"
            dev_settings = get_settings()
            print(f"  ✅ 开发环境配置: {dev_settings.ENVIRONMENT}")
            print(f"    - CORS Origins: {len(dev_settings.BACKEND_CORS_ORIGINS)}个")
            print(f"    - 数据库: {dev_settings.SQLALCHEMY_DATABASE_URI}")

            # 测试测试环境配置
            os.environ["ENVIRONMENT"] = "testing"
            test_settings = get_settings()
            print(f"  ✅ 测试环境配置: {test_settings.ENVIRONMENT}")

            self.results.append(("配置加载", True, "配置加载正常"))

        except Exception as e:
            print(f"  ❌ 配置加载失败: {e}")
            self.results.append(("配置加载", False, str(e)))

    def test_fastapi_app(self) -> None:
        """测试FastAPI应用创建"""
        print("\\n🚀 测试FastAPI应用创建...")

        try:
            from src.main import create_app

            app = create_app()
            route_count = len(app.routes)

            print(f"  ✅ 应用创建成功: {app.title}")
            print(f"    - 路由数量: {route_count}")
            print(f"    - 文档URL: {app.docs_url}")

            # 检查主要路由
            api_routes = [
                route
                for route in app.routes
                if hasattr(route, "path") and route.path.startswith("/api")
            ]
            print(f"    - API路由: {len(api_routes)}个")

            self.results.append(
                ("FastAPI应用", True, f"应用创建成功，{route_count}个路由")
            )

        except Exception as e:
            print(f"  ❌ FastAPI应用创建失败: {e}")
            self.results.append(("FastAPI应用", False, str(e)))

    async def test_database_connection(self) -> None:
        """测试数据库连接（异步）"""
        print("\\n🗄️ 测试数据库连接...")

        try:
            from src.core.database import async_session, get_db

            # 测试会话创建
            async with async_session() as session:
                # 简单查询测试
                from sqlalchemy import text

                result = await session.execute(text("SELECT 1 as test"))
                row = result.fetchone()

                if row and row[0] == 1:
                    print("  ✅ 数据库连接成功")
                    self.results.append(("数据库连接", True, "数据库连接正常"))
                else:
                    print("  ❌ 数据库查询结果异常")
                    self.results.append(("数据库连接", False, "查询结果异常"))

        except Exception as e:
            print(f"  ❌ 数据库连接失败: {e}")
            self.results.append(("数据库连接", False, str(e)))

    def test_services(self) -> None:
        """测试服务创建"""
        print("\\n🔧 测试服务创建...")

        try:
            from src.services.bailian_service import get_bailian_service

            # 测试百炼服务创建
            bailian_service = get_bailian_service()
            print("  ✅ 百炼AI服务创建成功")

            # 测试配置
            if hasattr(bailian_service, "config"):
                print(
                    f"    - API Key: {'已配置' if bailian_service.config.api_key else '未配置'}"
                )
                print(f"    - Base URL: {bailian_service.config.base_url}")

            self.results.append(("服务创建", True, "服务创建正常"))

        except Exception as e:
            print(f"  ❌ 服务创建失败: {e}")
            self.results.append(("服务创建", False, str(e)))

    def test_models(self) -> None:
        """测试数据模型"""
        print("\\n📊 测试数据模型...")

        try:
            from src.models.homework import HomeworkSubmission
            from src.models.learning import Answer, ChatSession, Question
            from src.models.user import User

            # 测试模型类定义
            models = [
                ("User", User),
                ("ChatSession", ChatSession),
                ("Question", Question),
                ("Answer", Answer),
                ("HomeworkSubmission", HomeworkSubmission),
            ]

            for name, model_class in models:
                if hasattr(model_class, "__tablename__"):
                    print(f"  ✅ {name}模型: {model_class.__tablename__}")
                else:
                    print(f"  ⚠️ {name}模型: 缺少__tablename__")

            self.results.append(("数据模型", True, f"{len(models)}个模型定义正常"))

        except Exception as e:
            print(f"  ❌ 数据模型测试失败: {e}")
            self.results.append(("数据模型", False, str(e)))

    def test_schemas(self) -> None:
        """测试Schema模型"""
        print("\\n📝 测试Schema模型...")

        try:
            from src.schemas.auth import LoginRequest, LoginResponse
            from src.schemas.common import ErrorResponse, SuccessResponse
            from src.schemas.learning import AskQuestionRequest, AskQuestionResponse

            # 测试Schema创建
            schemas = [
                ("LoginRequest", LoginRequest),
                ("LoginResponse", LoginResponse),
                ("AskQuestionRequest", AskQuestionRequest),
                ("AskQuestionResponse", AskQuestionResponse),
                ("SuccessResponse", SuccessResponse),
                ("ErrorResponse", ErrorResponse),
            ]

            for name, schema_class in schemas:
                # 检查是否是Pydantic模型
                if hasattr(schema_class, "model_fields"):
                    print(f"  ✅ {name}: Pydantic模型")
                else:
                    print(f"  ⚠️ {name}: 可能不是有效的Pydantic模型")

            self.results.append(("Schema模型", True, f"{len(schemas)}个Schema定义正常"))

        except Exception as e:
            print(f"  ❌ Schema模型测试失败: {e}")
            self.results.append(("Schema模型", False, str(e)))

    def print_summary(self) -> None:
        """打印诊断总结"""
        print("\\n" + "=" * 60)
        print("📋 诊断总结")
        print("=" * 60)

        total = len(self.results)
        passed = sum(1 for _, success, _ in self.results if success)
        failed = total - passed

        print(f"总计: {total}项检查")
        print(f"通过: {passed}项 ✅")
        print(f"失败: {failed}项 ❌")

        if failed > 0:
            print("\\n失败项详情:")
            for name, success, message in self.results:
                if not success:
                    print(f"  ❌ {name}: {message}")

        print(
            "\\n状态: "
            + (
                "🟢 所有检查通过"
                if failed == 0
                else "🟡 部分检查失败" if failed < total // 2 else "🔴 多项检查失败"
            )
        )

        return failed == 0


async def main():
    """主函数"""
    print("🔍 五好伴学项目诊断")
    print("=" * 60)

    runner = DiagnosticRunner()

    # 运行所有检查
    runner.test_module_imports()
    runner.test_configuration()
    runner.test_fastapi_app()
    await runner.test_database_connection()
    runner.test_services()
    runner.test_models()
    runner.test_schemas()

    # 打印总结
    success = runner.print_summary()

    return 0 if success else 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\\n诊断被用户中断")
        sys.exit(130)
    except Exception as e:
        print(f"\\n诊断过程中出现未预期错误: {e}")
        traceback.print_exc()
        sys.exit(1)
