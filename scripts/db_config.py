#!/usr/bin/env python3
"""
数据库配置管理和环境切换脚本
支持不同环境的数据库配置管理和切换
"""

import os
import sys
import json
import asyncio
from typing import Dict, Optional, Any
from pathlib import Path
from dataclasses import dataclass, asdict
import logging

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.config import get_settings, Settings, DevelopmentSettings, ProductionSettings, TestingSettings

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class DatabaseConfig:
    """数据库配置数据类"""
    host: str
    port: int
    user: str
    password: str
    database: str
    driver: str = "postgresql+asyncpg"

    @property
    def connection_url(self) -> str:
        """生成连接URL"""
        if self.password:
            return f"{self.driver}://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"
        else:
            return f"{self.driver}://{self.user}@{self.host}:{self.port}/{self.database}"

    @property
    def sync_connection_url(self) -> str:
        """生成同步连接URL（用于Alembic）"""
        driver = self.driver.replace("+asyncpg", "")
        if self.password:
            return f"{driver}://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"
        else:
            return f"{driver}://{self.user}@{self.host}:{self.port}/{self.database}"


class DatabaseConfigManager:
    """数据库配置管理器"""

    def __init__(self):
        self.config_file = project_root / ".env"
        self.templates_dir = project_root / "config" / "database"
        self.templates_dir.mkdir(parents=True, exist_ok=True)

    def get_predefined_configs(self) -> Dict[str, DatabaseConfig]:
        """获取预定义的数据库配置"""
        return {
            "development": DatabaseConfig(
                host="localhost",
                port=5432,
                user="wuhao_dev",
                password="dev_password_2024",
                database="wuhao_tutor_dev"
            ),
            "testing": DatabaseConfig(
                host="localhost",
                port=5432,
                user="wuhao_test",
                password="test_password_2024",
                database="wuhao_tutor_test"
            ),
            "production": DatabaseConfig(
                host="localhost",
                port=5432,
                user="wuhao_prod",
                password="",  # 生产环境密码需要单独设置
                database="wuhao_tutor"
            ),
            "docker": DatabaseConfig(
                host="postgres",
                port=5432,
                user="postgres",
                password="postgres123",
                database="wuhao_tutor"
            ),
            "cloud": DatabaseConfig(
                host="your-postgres-host.com",
                port=5432,
                user="wuhao_user",
                password="",  # 需要设置实际密码
                database="wuhao_tutor"
            )
        }

    def save_config_template(self, name: str, config: DatabaseConfig) -> None:
        """保存配置模板到文件"""
        template_file = self.templates_dir / f"{name}.json"
        with open(template_file, 'w', encoding='utf-8') as f:
            json.dump(asdict(config), f, indent=2, ensure_ascii=False)
        logger.info(f"✅ 配置模板已保存: {template_file}")

    def load_config_template(self, name: str) -> Optional[DatabaseConfig]:
        """从文件加载配置模板"""
        template_file = self.templates_dir / f"{name}.json"
        if not template_file.exists():
            return None

        with open(template_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        return DatabaseConfig(**data)

    def list_config_templates(self) -> list[str]:
        """列出所有配置模板"""
        templates = []
        if self.templates_dir.exists():
            for file in self.templates_dir.glob("*.json"):
                templates.append(file.stem)
        return templates

    def generate_env_config(self, config: DatabaseConfig, environment: str = "production") -> str:
        """生成.env配置内容"""
        env_content = f"""# 五好伴学 - {environment.title()} 环境数据库配置
ENVIRONMENT={environment}

# PostgreSQL数据库配置
POSTGRES_SERVER={config.host}
POSTGRES_PORT={config.port}
POSTGRES_USER={config.user}
POSTGRES_PASSWORD={config.password}
POSTGRES_DB={config.database}

# SQLAlchemy数据库URL
SQLALCHEMY_DATABASE_URI={config.connection_url}

# Redis配置 (可选)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0

# 应用基础配置
PROJECT_NAME=五好伴学
VERSION=0.1.0
API_V1_STR=/api/v1
SECRET_KEY=your-secret-key-change-in-production

# 阿里云百炼配置
BAILIAN_APPLICATION_ID=db9f923dc3ae48dd9127929efa5eb108
BAILIAN_API_KEY=sk-your-api-key-here
BAILIAN_BASE_URL=https://dashscope.aliyuncs.com/api/v1

# 文件上传配置
UPLOAD_MAX_SIZE=10485760
UPLOAD_DIR=./uploads
"""
        return env_content

    def update_env_file(self, config: DatabaseConfig, environment: str = "production") -> bool:
        """更新.env文件"""
        try:
            env_content = self.generate_env_config(config, environment)

            # 备份现有配置
            if self.config_file.exists():
                backup_file = self.config_file.with_suffix(f".env.backup.{environment}")
                backup_file.write_text(self.config_file.read_text(), encoding='utf-8')
                logger.info(f"📦 已备份现有配置到: {backup_file}")

            # 写入新配置
            self.config_file.write_text(env_content, encoding='utf-8')
            logger.info(f"✅ 已更新环境配置文件: {self.config_file}")
            return True

        except Exception as e:
            logger.error(f"❌ 更新配置文件失败: {e}")
            return False

    def get_current_config(self) -> Optional[DatabaseConfig]:
        """获取当前配置"""
        try:
            settings = get_settings()
            return DatabaseConfig(
                host=settings.POSTGRES_SERVER,
                port=int(settings.POSTGRES_PORT),
                user=settings.POSTGRES_USER,
                password=settings.POSTGRES_PASSWORD,
                database=settings.POSTGRES_DB
            )
        except Exception as e:
            logger.error(f"❌ 获取当前配置失败: {e}")
            return None

    def validate_config(self, config: DatabaseConfig) -> tuple[bool, list[str]]:
        """验证数据库配置"""
        errors = []

        if not config.host:
            errors.append("数据库主机地址不能为空")

        if not (1 <= config.port <= 65535):
            errors.append("数据库端口必须在1-65535范围内")

        if not config.user:
            errors.append("数据库用户名不能为空")

        if not config.database:
            errors.append("数据库名不能为空")

        # 生产环境必须设置密码
        if not config.password and config.database.endswith("_prod"):
            errors.append("生产环境必须设置数据库密码")

        return len(errors) == 0, errors


class DatabaseConfigCLI:
    """数据库配置命令行接口"""

    def __init__(self):
        self.manager = DatabaseConfigManager()

    def cmd_list(self) -> None:
        """列出所有配置模板"""
        print("📋 预定义配置模板:")
        predefined = self.manager.get_predefined_configs()
        for name, config in predefined.items():
            print(f"  • {name}: {config.user}@{config.host}:{config.port}/{config.database}")

        print("\n💾 自定义配置模板:")
        custom = self.manager.list_config_templates()
        if custom:
            for name in custom:
                config = self.manager.load_config_template(name)
                if config:
                    print(f"  • {name}: {config.user}@{config.host}:{config.port}/{config.database}")
        else:
            print("  (无)")

    def cmd_show(self, name: str) -> None:
        """显示指定配置的详细信息"""
        # 先检查预定义配置
        predefined = self.manager.get_predefined_configs()
        if name in predefined:
            config = predefined[name]
        else:
            # 检查自定义配置
            config = self.manager.load_config_template(name)
            if not config:
                print(f"❌ 配置模板 '{name}' 不存在")
                return

        print(f"📊 配置详情: {name}")
        print(f"  主机: {config.host}")
        print(f"  端口: {config.port}")
        print(f"  用户: {config.user}")
        print(f"  密码: {'***' if config.password else '(未设置)'}")
        print(f"  数据库: {config.database}")
        print(f"  连接URL: {config.connection_url}")

    def cmd_apply(self, name: str, environment: str = "production") -> None:
        """应用指定配置到环境"""
        # 获取配置
        predefined = self.manager.get_predefined_configs()
        if name in predefined:
            config = predefined[name]
        else:
            config = self.manager.load_config_template(name)
            if not config:
                print(f"❌ 配置模板 '{name}' 不存在")
                return

        # 验证配置
        valid, errors = self.manager.validate_config(config)
        if not valid:
            print("❌ 配置验证失败:")
            for error in errors:
                print(f"  • {error}")
            return

        # 应用配置
        if self.manager.update_env_file(config, environment):
            print(f"✅ 已应用配置 '{name}' 到 {environment} 环境")
        else:
            print(f"❌ 应用配置失败")

    def cmd_current(self) -> None:
        """显示当前配置"""
        config = self.manager.get_current_config()
        if config:
            print("📊 当前数据库配置:")
            print(f"  主机: {config.host}")
            print(f"  端口: {config.port}")
            print(f"  用户: {config.user}")
            print(f"  密码: {'***' if config.password else '(未设置)'}")
            print(f"  数据库: {config.database}")
        else:
            print("❌ 无法获取当前配置")

    def cmd_save(self, name: str, host: str, port: int, user: str, password: str, database: str) -> None:
        """保存自定义配置模板"""
        config = DatabaseConfig(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database
        )

        # 验证配置
        valid, errors = self.manager.validate_config(config)
        if not valid:
            print("❌ 配置验证失败:")
            for error in errors:
                print(f"  • {error}")
            return

        # 保存配置
        self.manager.save_config_template(name, config)
        print(f"✅ 已保存配置模板: {name}")

    def cmd_init_templates(self) -> None:
        """初始化预定义配置模板"""
        predefined = self.manager.get_predefined_configs()
        for name, config in predefined.items():
            self.manager.save_config_template(name, config)
        print(f"✅ 已初始化 {len(predefined)} 个预定义配置模板")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="数据库配置管理工具")
    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    # list命令
    subparsers.add_parser('list', help='列出所有配置模板')

    # show命令
    show_parser = subparsers.add_parser('show', help='显示配置详情')
    show_parser.add_argument('name', help='配置名称')

    # apply命令
    apply_parser = subparsers.add_parser('apply', help='应用配置')
    apply_parser.add_argument('name', help='配置名称')
    apply_parser.add_argument('--env', default='production', help='环境名称')

    # current命令
    subparsers.add_parser('current', help='显示当前配置')

    # save命令
    save_parser = subparsers.add_parser('save', help='保存自定义配置')
    save_parser.add_argument('name', help='配置名称')
    save_parser.add_argument('--host', required=True, help='数据库主机')
    save_parser.add_argument('--port', type=int, default=5432, help='数据库端口')
    save_parser.add_argument('--user', required=True, help='数据库用户')
    save_parser.add_argument('--password', default='', help='数据库密码')
    save_parser.add_argument('--database', required=True, help='数据库名')

    # init-templates命令
    subparsers.add_parser('init-templates', help='初始化预定义配置模板')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    cli = DatabaseConfigCLI()

    if args.command == 'list':
        cli.cmd_list()
    elif args.command == 'show':
        cli.cmd_show(args.name)
    elif args.command == 'apply':
        cli.cmd_apply(args.name, args.env)
    elif args.command == 'current':
        cli.cmd_current()
    elif args.command == 'save':
        cli.cmd_save(args.name, args.host, args.port, args.user, args.password, args.database)
    elif args.command == 'init-templates':
        cli.cmd_init_templates()


if __name__ == "__main__":
    main()
