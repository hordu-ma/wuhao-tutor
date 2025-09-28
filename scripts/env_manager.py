#!/usr/bin/env python3
"""
环境变量管理脚本
用于管理不同环境的配置文件和环境变量
"""

import os
import sys
import json
import shutil
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Any
import secrets
import re


class EnvironmentManager:
    """环境管理器"""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.config_dir = self.project_root / "config"
        self.templates_dir = self.config_dir / "templates"

        # 确保目录存在
        self.config_dir.mkdir(exist_ok=True)
        self.templates_dir.mkdir(exist_ok=True)

        # 环境配置
        self.environments = {
            "development": {
                "description": "开发环境配置",
                "file": ".env.dev",
                "template": "env.dev.template"
            },
            "testing": {
                "description": "测试环境配置",
                "file": ".env.test",
                "template": "env.test.template"
            },
            "staging": {
                "description": "预发布环境配置",
                "file": ".env.staging",
                "template": "env.staging.template"
            },
            "production": {
                "description": "生产环境配置",
                "file": ".env.prod",
                "template": "env.prod.template"
            }
        }

    def create_templates(self):
        """创建环境配置模板"""
        print("🔧 创建环境配置模板...")

        # 开发环境模板
        dev_template = self._get_dev_template()
        self._write_template("env.dev.template", dev_template)

        # 测试环境模板
        test_template = self._get_test_template()
        self._write_template("env.test.template", test_template)

        # 预发布环境模板
        staging_template = self._get_staging_template()
        self._write_template("env.staging.template", staging_template)

        # 生产环境模板
        prod_template = self._get_prod_template()
        self._write_template("env.prod.template", prod_template)

        print("✅ 环境配置模板创建完成")

    def _write_template(self, filename: str, content: str):
        """写入模板文件"""
        template_path = self.templates_dir / filename
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  ✓ {filename}")

    def _get_dev_template(self) -> str:
        """获取开发环境模板"""
        return '''# 五好伴学 - 开发环境配置
# Development Environment Configuration

# 环境标识
ENVIRONMENT=development

# 应用配置
PROJECT_NAME=五好伴学
VERSION=0.1.0
DEBUG=true
HOST=127.0.0.1
PORT=8000

# 安全配置
SECRET_KEY=dev_secret_key_please_change_in_production
ACCESS_TOKEN_EXPIRE_MINUTES=480
ALGORITHM=HS256

# CORS配置（开发环境允许所有源）
BACKEND_CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,http://localhost:8080

# 数据库配置（开发环境使用SQLite）
SQLALCHEMY_DATABASE_URI=sqlite+aiosqlite:///./wuhao_tutor_dev.db

# PostgreSQL配置（可选）
POSTGRES_SERVER=localhost
POSTGRES_USER=wuhao_dev
POSTGRES_PASSWORD=dev_password_2024
POSTGRES_DB=wuhao_tutor_dev
POSTGRES_PORT=5432

# Redis配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=dev_redis_2024
REDIS_DB=0

# 日志配置
LOG_LEVEL=DEBUG
LOG_FORMAT=console

# 阿里云百炼智能体配置
BAILIAN_APPLICATION_ID=your_application_id_here
BAILIAN_API_KEY=sk-your_api_key_here
BAILIAN_BASE_URL=https://dashscope.aliyuncs.com/api/v1
BAILIAN_TIMEOUT=30
BAILIAN_MAX_RETRIES=3

# 阿里云配置
ALICLOUD_ACCESS_KEY_ID=your_access_key_id
ALICLOUD_ACCESS_KEY_SECRET=your_access_key_secret
ALICLOUD_REGION=cn-hangzhou

# 文件存储配置
OSS_BUCKET_NAME=wuhao-tutor-files-dev
OSS_ENDPOINT=oss-cn-hangzhou.aliyuncs.com
UPLOAD_MAX_SIZE=10485760
UPLOAD_DIR=./uploads

# 性能监控配置（开发环境宽松配置）
ENABLE_METRICS=true
SLOW_QUERY_THRESHOLD=2.0
RATE_LIMIT_PER_IP=1000
RATE_LIMIT_PER_USER=500
RATE_LIMIT_AI_SERVICE=100

# 缓存配置
CACHE_ENABLED=true
CACHE_DEFAULT_TTL=300
AI_CACHE_ENABLED=true
AI_CACHE_TTL=3600
'''

    def _get_test_template(self) -> str:
        """获取测试环境模板"""
        return '''# 五好伴学 - 测试环境配置
# Testing Environment Configuration

# 环境标识
ENVIRONMENT=testing

# 应用配置
PROJECT_NAME=五好伴学测试
VERSION=0.1.0
DEBUG=true
HOST=127.0.0.1
PORT=8001

# 安全配置
SECRET_KEY=test_secret_key_for_testing_only
ACCESS_TOKEN_EXPIRE_MINUTES=5
ALGORITHM=HS256

# CORS配置
BACKEND_CORS_ORIGINS=http://localhost:3000

# 数据库配置（测试环境使用内存SQLite）
SQLALCHEMY_DATABASE_URI=sqlite+aiosqlite:///:memory:

# Redis配置（测试环境可选）
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=test_redis_2024
REDIS_DB=1

# 日志配置
LOG_LEVEL=DEBUG
LOG_FORMAT=console

# 阿里云配置（测试环境使用Mock）
BAILIAN_APPLICATION_ID=test_application_id
BAILIAN_API_KEY=sk-test_api_key
BAILIAN_BASE_URL=http://localhost:8080/mock
BAILIAN_TIMEOUT=10
BAILIAN_MAX_RETRIES=1

# 文件存储配置
UPLOAD_MAX_SIZE=1048576
UPLOAD_DIR=./test_uploads

# 性能监控配置（测试环境禁用）
ENABLE_METRICS=false
RATE_LIMIT_ENABLED=false
CACHE_ENABLED=false
AI_CACHE_ENABLED=false
'''

    def _get_staging_template(self) -> str:
        """获取预发布环境模板"""
        return '''# 五好伴学 - 预发布环境配置
# Staging Environment Configuration

# 环境标识
ENVIRONMENT=staging

# 应用配置
PROJECT_NAME=五好伴学预发布
VERSION=0.1.0
DEBUG=false
HOST=0.0.0.0
PORT=8000

# 安全配置（请在实际部署时修改）
SECRET_KEY=staging_secret_key_please_change
ACCESS_TOKEN_EXPIRE_MINUTES=480
ALGORITHM=HS256

# CORS配置（预发布环境指定域名）
BACKEND_CORS_ORIGINS=https://staging.wuhao-tutor.com,https://staging-admin.wuhao-tutor.com

# 数据库配置
POSTGRES_SERVER=staging-postgres
POSTGRES_USER=wuhao_staging
POSTGRES_PASSWORD=staging_password_please_change
POSTGRES_DB=wuhao_tutor_staging
POSTGRES_PORT=5432

# Redis配置
REDIS_HOST=staging-redis
REDIS_PORT=6379
REDIS_PASSWORD=staging_redis_password_please_change
REDIS_DB=0

# 日志配置
LOG_LEVEL=INFO
LOG_FORMAT=json

# 阿里云百炼智能体配置
BAILIAN_APPLICATION_ID=your_staging_application_id
BAILIAN_API_KEY=sk-your_staging_api_key
BAILIAN_BASE_URL=https://dashscope.aliyuncs.com/api/v1
BAILIAN_TIMEOUT=30
BAILIAN_MAX_RETRIES=3

# 阿里云配置
ALICLOUD_ACCESS_KEY_ID=your_staging_access_key_id
ALICLOUD_ACCESS_KEY_SECRET=your_staging_access_key_secret
ALICLOUD_REGION=cn-hangzhou

# 文件存储配置
OSS_BUCKET_NAME=wuhao-tutor-files-staging
OSS_ENDPOINT=oss-cn-hangzhou.aliyuncs.com
UPLOAD_MAX_SIZE=10485760
UPLOAD_DIR=/app/uploads

# 性能监控配置
ENABLE_METRICS=true
SLOW_QUERY_THRESHOLD=1.0
RATE_LIMIT_PER_IP=200
RATE_LIMIT_PER_USER=100
RATE_LIMIT_AI_SERVICE=50

# 缓存配置
CACHE_ENABLED=true
CACHE_DEFAULT_TTL=300
AI_CACHE_ENABLED=true
AI_CACHE_TTL=3600
'''

    def _get_prod_template(self) -> str:
        """获取生产环境模板"""
        return '''# 五好伴学 - 生产环境配置
# Production Environment Configuration

# 环境标识
ENVIRONMENT=production

# 应用配置
PROJECT_NAME=五好伴学
VERSION=0.1.0
DEBUG=false
HOST=0.0.0.0
PORT=8000

# 安全配置（必须修改！）
SECRET_KEY=CHANGE_ME_IN_PRODUCTION_AT_LEAST_32_CHARS
ACCESS_TOKEN_EXPIRE_MINUTES=480
ALGORITHM=HS256

# CORS配置（生产环境严格限制）
BACKEND_CORS_ORIGINS=https://wuhao-tutor.com,https://admin.wuhao-tutor.com

# 数据库配置
POSTGRES_SERVER=prod-postgres
POSTGRES_USER=wuhao_prod
POSTGRES_PASSWORD=CHANGE_ME_STRONG_PASSWORD
POSTGRES_DB=wuhao_tutor
POSTGRES_PORT=5432

# Redis配置
REDIS_HOST=prod-redis
REDIS_PORT=6379
REDIS_PASSWORD=CHANGE_ME_REDIS_PASSWORD
REDIS_DB=0

# 日志配置
LOG_LEVEL=INFO
LOG_FORMAT=json

# 阿里云百炼智能体配置（必须配置！）
BAILIAN_APPLICATION_ID=CHANGE_ME_YOUR_APPLICATION_ID
BAILIAN_API_KEY=sk-CHANGE_ME_YOUR_API_KEY
BAILIAN_BASE_URL=https://dashscope.aliyuncs.com/api/v1
BAILIAN_TIMEOUT=30
BAILIAN_MAX_RETRIES=3

# 阿里云配置（必须配置！）
ALICLOUD_ACCESS_KEY_ID=CHANGE_ME_ACCESS_KEY_ID
ALICLOUD_ACCESS_KEY_SECRET=CHANGE_ME_ACCESS_KEY_SECRET
ALICLOUD_REGION=cn-hangzhou

# 文件存储配置
OSS_BUCKET_NAME=wuhao-tutor-files
OSS_ENDPOINT=oss-cn-hangzhou.aliyuncs.com
OSS_ACCESS_KEY_ID=CHANGE_ME_OSS_ACCESS_KEY
OSS_ACCESS_KEY_SECRET=CHANGE_ME_OSS_SECRET_KEY
UPLOAD_MAX_SIZE=10485760
UPLOAD_DIR=/app/uploads

# 短信服务配置
SMS_ACCESS_KEY_ID=CHANGE_ME_SMS_ACCESS_KEY
SMS_ACCESS_KEY_SECRET=CHANGE_ME_SMS_SECRET_KEY
SMS_SIGN_NAME=五好伴学
SMS_TEMPLATE_CODE=SMS_123456789

# 微信配置
WECHAT_APP_ID=CHANGE_ME_WECHAT_APP_ID
WECHAT_APP_SECRET=CHANGE_ME_WECHAT_APP_SECRET
WECHAT_MINI_PROGRAM_APP_ID=CHANGE_ME_MINI_PROGRAM_APP_ID
WECHAT_MINI_PROGRAM_APP_SECRET=CHANGE_ME_MINI_PROGRAM_SECRET

# 性能监控配置（生产环境严格配置）
ENABLE_METRICS=true
METRICS_PORT=9090
SLOW_QUERY_THRESHOLD=0.5
RATE_LIMIT_PER_IP=60
RATE_LIMIT_PER_USER=30
RATE_LIMIT_AI_SERVICE=10

# 缓存配置
CACHE_ENABLED=true
CACHE_DEFAULT_TTL=300
AI_CACHE_ENABLED=true
AI_CACHE_TTL=3600
'''

    def create_env_file(self, environment: str, force: bool = False):
        """从模板创建环境文件"""
        if environment not in self.environments:
            print(f"❌ 不支持的环境: {environment}")
            return False

        env_info = self.environments[environment]
        template_path = self.templates_dir / env_info["template"]
        env_path = self.project_root / env_info["file"]

        if not template_path.exists():
            print(f"❌ 模板文件不存在: {template_path}")
            return False

        if env_path.exists() and not force:
            print(f"⚠️  环境文件已存在: {env_path}")
            print("使用 --force 参数强制覆盖")
            return False

        # 复制模板到环境文件
        shutil.copy2(template_path, env_path)

        # 如果是生产环境，生成强密钥
        if environment == "production":
            self._secure_production_env(env_path)

        print(f"✅ 已创建{env_info['description']}: {env_path}")
        return True

    def _secure_production_env(self, env_path: Path):
        """加固生产环境配置"""
        with open(env_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 生成强密钥
        strong_secret = secrets.token_urlsafe(64)
        content = content.replace(
            "SECRET_KEY=CHANGE_ME_IN_PRODUCTION_AT_LEAST_32_CHARS",
            f"SECRET_KEY={strong_secret}"
        )

        with open(env_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print("  🔒 已生成强安全密钥")

    def switch_environment(self, environment: str):
        """切换环境配置"""
        if environment not in self.environments:
            print(f"❌ 不支持的环境: {environment}")
            return False

        env_info = self.environments[environment]
        source_path = self.project_root / env_info["file"]
        target_path = self.project_root / ".env"

        if not source_path.exists():
            print(f"❌ 环境文件不存在: {source_path}")
            print(f"请先运行: python scripts/env_manager.py create {environment}")
            return False

        # 备份当前.env文件
        if target_path.exists():
            backup_path = target_path.with_suffix('.env.backup')
            shutil.copy2(target_path, backup_path)
            print(f"  📦 已备份当前配置到: {backup_path}")

        # 复制环境配置
        shutil.copy2(source_path, target_path)
        print(f"✅ 已切换到{env_info['description']}")

        # 设置环境变量
        os.environ["ENVIRONMENT"] = environment
        print(f"  🔧 环境变量 ENVIRONMENT={environment}")

        return True

    def validate_environment(self, environment: str | None = None):
        """验证环境配置"""
        if environment:
            env_file = self.project_root / self.environments[environment]["file"]
        else:
            env_file = self.project_root / ".env"

        if not env_file.exists():
            print(f"❌ 环境文件不存在: {env_file}")
            return False

        print(f"🔍 验证环境配置: {env_file}")

        # 读取环境变量
        env_vars = {}
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key] = value

        # 验证必需配置
        validation_results = []

        # 基础配置验证
        required_vars = [
            "ENVIRONMENT", "PROJECT_NAME", "SECRET_KEY",
            "BAILIAN_APPLICATION_ID", "BAILIAN_API_KEY"
        ]

        for var in required_vars:
            if var not in env_vars or not env_vars[var]:
                validation_results.append(f"❌ {var}: 未配置或为空")
            elif "CHANGE_ME" in env_vars[var]:
                validation_results.append(f"⚠️  {var}: 需要修改默认值")
            else:
                validation_results.append(f"✅ {var}: 已配置")

        # 安全性验证
        if "SECRET_KEY" in env_vars:
            secret_key = env_vars["SECRET_KEY"]
            if len(secret_key) < 32:
                validation_results.append("❌ SECRET_KEY: 长度不足32位")
            elif secret_key in ["dev_secret_key_please_change_in_production", "test_secret_key_for_testing_only"]:
                validation_results.append("⚠️  SECRET_KEY: 使用了开发/测试密钥，生产环境需要修改")

        # API密钥验证
        if "BAILIAN_API_KEY" in env_vars:
            api_key = env_vars["BAILIAN_API_KEY"]
            if not api_key.startswith("sk-"):
                validation_results.append("❌ BAILIAN_API_KEY: 格式错误，应以'sk-'开头")

        # 打印验证结果
        for result in validation_results:
            print(f"  {result}")

        # 统计
        success_count = len([r for r in validation_results if r.startswith("✅")])
        warning_count = len([r for r in validation_results if r.startswith("⚠️")])
        error_count = len([r for r in validation_results if r.startswith("❌")])

        print(f"\n📊 验证结果: {success_count}项通过, {warning_count}项警告, {error_count}项错误")

        return error_count == 0

    def list_environments(self):
        """列出所有环境"""
        print("📋 可用环境:")

        for env_name, env_info in self.environments.items():
            env_path = self.project_root / env_info["file"]
            template_path = self.templates_dir / env_info["template"]

            status_icon = "✅" if env_path.exists() else "❌"
            template_icon = "📄" if template_path.exists() else "❌"

            print(f"  {status_icon} {env_name:<12} - {env_info['description']}")
            print(f"     配置文件: {env_info['file']} {template_icon}")
            print(f"     模    板: {env_info['template']}")
            print()

    def generate_docker_env(self, environment: str):
        """生成Docker环境文件"""
        if environment not in self.environments:
            print(f"❌ 不支持的环境: {environment}")
            return False

        env_info = self.environments[environment]
        source_path = self.project_root / env_info["file"]
        docker_env_path = self.project_root / f".env.docker.{environment}"

        if not source_path.exists():
            print(f"❌ 环境文件不存在: {source_path}")
            return False

        # 读取原始配置
        with open(source_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Docker环境调整
        docker_adjustments = {
            "HOST": "0.0.0.0",
            "POSTGRES_SERVER": "postgres",
            "REDIS_HOST": "redis",
            "UPLOAD_DIR": "/app/uploads"
        }

        lines = content.split('\n')
        modified_lines = []

        for line in lines:
            if '=' in line and not line.strip().startswith('#'):
                key = line.split('=')[0]
                if key in docker_adjustments:
                    modified_lines.append(f"{key}={docker_adjustments[key]}")
                else:
                    modified_lines.append(line)
            else:
                modified_lines.append(line)

        # 写入Docker环境文件
        with open(docker_env_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(modified_lines))

        print(f"✅ 已生成Docker环境配置: {docker_env_path}")
        return True

    def cleanup_env_files(self):
        """清理环境文件"""
        print("🧹 清理环境文件...")

        cleanup_patterns = [
            ".env.backup*",
            ".env.docker.*",
            "*.env.tmp"
        ]

        cleaned_count = 0
        for pattern in cleanup_patterns:
            for file_path in self.project_root.glob(pattern):
                file_path.unlink()
                print(f"  🗑️  删除: {file_path.name}")
                cleaned_count += 1

        if cleaned_count == 0:
            print("  ✨ 没有需要清理的文件")
        else:
            print(f"✅ 已清理 {cleaned_count} 个文件")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="五好伴学环境管理工具")
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # 创建模板命令
    subparsers.add_parser("init", help="初始化环境配置模板")

    # 创建环境文件命令
    create_parser = subparsers.add_parser("create", help="从模板创建环境文件")
    create_parser.add_argument("environment", choices=["development", "testing", "staging", "production"], help="环境类型")
    create_parser.add_argument("--force", "-f", action="store_true", help="强制覆盖已存在的文件")

    # 切换环境命令
    switch_parser = subparsers.add_parser("switch", help="切换当前环境")
    switch_parser.add_argument("environment", choices=["development", "testing", "staging", "production"], help="目标环境")

    # 验证环境命令
    validate_parser = subparsers.add_parser("validate", help="验证环境配置")
    validate_parser.add_argument("environment", nargs="?", choices=["development", "testing", "staging", "production"], help="指定环境（可选）")

    # 列出环境命令
    subparsers.add_parser("list", help="列出所有环境状态")

    # 生成Docker环境文件命令
    docker_parser = subparsers.add_parser("docker", help="生成Docker环境文件")
    docker_parser.add_argument("environment", choices=["development", "testing", "staging", "production"], help="环境类型")

    # 清理命令
    subparsers.add_parser("cleanup", help="清理临时环境文件")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    manager = EnvironmentManager()

    try:
        if args.command == "init":
            manager.create_templates()
        elif args.command == "create":
            manager.create_env_file(args.environment, args.force)
        elif args.command == "switch":
            manager.switch_environment(args.environment)
        elif args.command == "validate":
            manager.validate_environment(args.environment)
        elif args.command == "list":
            manager.list_environments()
        elif args.command == "docker":
            manager.generate_docker_env(args.environment)
        elif args.command == "cleanup":
            manager.cleanup_env_files()
    except KeyboardInterrupt:
        print("\n⏹️  操作已取消")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 执行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
