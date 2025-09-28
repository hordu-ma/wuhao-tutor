#!/usr/bin/env python3
"""
数据库管理便捷脚本
集成数据库初始化、配置、测试、备份等功能的统一管理工具
"""

import asyncio
import sys
import os
from typing import Dict, List, Optional, Any
from pathlib import Path
import logging
import subprocess

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DatabaseManager:
    """数据库管理器"""

    def __init__(self):
        self.scripts_dir = Path(__file__).parent
        self.project_root = self.scripts_dir.parent

    def run_script(self, script_name: str, args: List[str] | None = None) -> bool:
        """运行指定脚本"""
        script_path = self.scripts_dir / script_name
        if not script_path.exists():
            logger.error(f"❌ 脚本不存在: {script_path}")
            return False

        cmd = [sys.executable, str(script_path)]
        if args:
            cmd.extend(args)

        try:
            logger.info(f"🔄 执行命令: {' '.join(cmd)}")
            result = subprocess.run(cmd, check=True, text=True)
            return result.returncode == 0
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ 脚本执行失败: {e}")
            return False

    def cmd_setup(self, env: str = "development", use_docker: bool = False) -> None:
        """设置数据库环境"""
        logger.info(f"🚀 设置数据库环境: {env}")

        if use_docker:
            logger.info("🐳 使用Docker启动数据库服务...")
            self.start_docker_services()

        # 配置数据库连接
        logger.info("⚙️  配置数据库连接...")
        if not self.run_script("db_config.py", ["apply", env, "--env", env]):
            logger.error("❌ 配置数据库连接失败")
            return

        # 初始化数据库
        logger.info("🏗️  初始化数据库...")
        if not self.run_script("init_database.py", ["--env", env]):
            logger.error("❌ 初始化数据库失败")
            return

        # 测试数据库
        logger.info("🧪 测试数据库...")
        if not self.run_script("test_database.py", ["--env", env, "--test", "all"]):
            logger.error("❌ 数据库测试失败")
            return

        logger.info("✅ 数据库环境设置完成!")

    def cmd_init(self, env: str = "production") -> None:
        """初始化数据库"""
        logger.info(f"🏗️  初始化数据库环境: {env}")
        success = self.run_script("init_database.py", ["--env", env])
        if success:
            logger.info("✅ 数据库初始化完成")
        else:
            logger.error("❌ 数据库初始化失败")

    def cmd_test(self, env: str = "development", test_type: str = "all") -> None:
        """测试数据库"""
        logger.info(f"🧪 测试数据库环境: {env}")
        success = self.run_script("test_database.py", ["--env", env, "--test", test_type])
        if success:
            logger.info("✅ 数据库测试通过")
        else:
            logger.error("❌ 数据库测试失败")

    def cmd_backup(self, env: str = "production", name: str | None = None) -> None:
        """备份数据库"""
        logger.info(f"💾 备份数据库环境: {env}")
        args = ["create", "--env", env]
        if name:
            args.extend(["--name", name])

        success = self.run_script("db_backup.py", args)
        if success:
            logger.info("✅ 数据库备份完成")
        else:
            logger.error("❌ 数据库备份失败")

    def cmd_restore(self, env: str, backup_file: str) -> None:
        """恢复数据库"""
        logger.info(f"🔄 恢复数据库环境: {env}")
        success = self.run_script("db_backup.py", ["restore", "--env", env, backup_file])
        if success:
            logger.info("✅ 数据库恢复完成")
        else:
            logger.error("❌ 数据库恢复失败")

    def cmd_config(self, action: str, *args) -> None:
        """数据库配置管理"""
        logger.info(f"⚙️  数据库配置操作: {action}")
        success = self.run_script("db_config.py", [action] + list(args))
        if success:
            logger.info("✅ 配置操作完成")
        else:
            logger.error("❌ 配置操作失败")

    def cmd_migrate(self, env: str = "production", action: str = "upgrade") -> None:
        """数据库迁移"""
        logger.info(f"🔄 数据库迁移: {action}")

        # 设置环境变量
        os.environ["ENVIRONMENT"] = env

        if action == "upgrade":
            cmd = ["alembic", "upgrade", "head"]
        elif action == "downgrade":
            cmd = ["alembic", "downgrade", "-1"]
        elif action == "history":
            cmd = ["alembic", "history", "--verbose"]
        elif action == "current":
            cmd = ["alembic", "current", "--verbose"]
        else:
            logger.error(f"❌ 未知的迁移操作: {action}")
            return

        try:
            result = subprocess.run(cmd, cwd=self.project_root, check=True, text=True)
            logger.info("✅ 数据库迁移完成")
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ 数据库迁移失败: {e}")

    def start_docker_services(self) -> bool:
        """启动Docker数据库服务"""
        docker_compose_file = self.project_root / "docker-compose.dev.yml"

        if not docker_compose_file.exists():
            logger.error("❌ Docker Compose配置文件不存在")
            return False

        try:
            # 启动数据库服务
            cmd = ["docker-compose", "-f", str(docker_compose_file), "up", "-d", "postgres", "redis"]
            result = subprocess.run(cmd, check=True, text=True)

            if result.returncode == 0:
                logger.info("✅ Docker数据库服务启动成功")

                # 等待服务启动
                logger.info("⏳ 等待数据库服务就绪...")
                import time
                time.sleep(10)

                return True
            else:
                logger.error("❌ Docker数据库服务启动失败")
                return False

        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Docker服务启动失败: {e}")
            return False

    def stop_docker_services(self) -> bool:
        """停止Docker数据库服务"""
        docker_compose_file = self.project_root / "docker-compose.dev.yml"

        try:
            cmd = ["docker-compose", "-f", str(docker_compose_file), "down"]
            result = subprocess.run(cmd, check=True, text=True)

            if result.returncode == 0:
                logger.info("✅ Docker数据库服务已停止")
                return True
            else:
                logger.error("❌ 停止Docker服务失败")
                return False

        except subprocess.CalledProcessError as e:
            logger.error(f"❌ 停止Docker服务失败: {e}")
            return False

    def cmd_docker(self, action: str) -> None:
        """Docker服务管理"""
        if action == "start":
            success = self.start_docker_services()
        elif action == "stop":
            success = self.stop_docker_services()
        elif action == "restart":
            self.stop_docker_services()
            success = self.start_docker_services()
        elif action == "logs":
            docker_compose_file = self.project_root / "docker-compose.dev.yml"
            cmd = ["docker-compose", "-f", str(docker_compose_file), "logs", "-f", "postgres", "redis"]
            subprocess.run(cmd)
            return
        else:
            logger.error(f"❌ 未知的Docker操作: {action}")
            return

        if success:
            logger.info(f"✅ Docker服务{action}完成")
        else:
            logger.error(f"❌ Docker服务{action}失败")

    def cmd_status(self, env: str = "development") -> None:
        """检查数据库状态"""
        logger.info(f"📊 检查数据库状态 - 环境: {env}")

        # 检查连接
        logger.info("🔍 检查数据库连接...")
        self.run_script("init_database.py", ["--env", env, "--check-only"])

        # 显示配置信息
        logger.info("⚙️  当前数据库配置:")
        self.run_script("db_config.py", ["current"])

        # 显示备份列表
        logger.info("💾 备份文件列表:")
        self.run_script("db_backup.py", ["list", "--env", env])

    def cmd_reset(self, env: str = "development") -> None:
        """重置数据库"""
        if env == "production":
            logger.error("❌ 不允许重置生产环境数据库!")
            return

        logger.warning(f"⚠️  即将重置数据库环境: {env}")
        confirm = input("确认继续吗? 这将删除所有数据! (yes/N): ").strip().lower()
        if confirm != 'yes':
            logger.info("❌ 操作已取消")
            return

        logger.info("🔄 重置数据库...")

        # 删除数据库并重新创建
        success = self.run_script("init_database.py", ["--env", env])
        if success:
            logger.info("✅ 数据库重置完成")
        else:
            logger.error("❌ 数据库重置失败")

    def show_help(self) -> None:
        """显示帮助信息"""
        help_text = """
🗃️  数据库管理工具 - 五好伴学项目

📋 可用命令:

🚀 环境管理:
  setup [--env ENV] [--docker]     完整设置数据库环境
  init [--env ENV]                 初始化数据库
  reset [--env ENV]                重置数据库（仅非生产环境）
  status [--env ENV]               检查数据库状态

🧪 测试验证:
  test [--env ENV] [--type TYPE]   测试数据库功能

⚙️  配置管理:
  config <action> [args...]        数据库配置操作
    - list                         列出配置模板
    - show <name>                  显示配置详情
    - apply <name> [--env ENV]     应用配置
    - current                      显示当前配置

🔄 数据库迁移:
  migrate [--env ENV] [--action ACTION]  数据库迁移
    - upgrade (默认)               升级到最新版本
    - downgrade                    回滚一个版本
    - history                      查看迁移历史
    - current                      查看当前版本

💾 备份恢复:
  backup [--env ENV] [--name NAME] 创建数据库备份
  restore --env ENV <backup_file>  恢复数据库备份

🐳 Docker服务:
  docker <action>                  Docker服务管理
    - start                        启动服务
    - stop                         停止服务
    - restart                      重启服务
    - logs                         查看日志

📖 环境说明:
  development - 开发环境 (默认使用SQLite)
  testing     - 测试环境
  production  - 生产环境 (默认)

💡 使用示例:
  python manage_db.py setup --env development --docker
  python manage_db.py test --env development
  python manage_db.py backup --env production
  python manage_db.py migrate --env production
  python manage_db.py config apply production
        """
        print(help_text)


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(
        description="数据库管理工具",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    # setup命令
    setup_parser = subparsers.add_parser('setup', help='完整设置数据库环境')
    setup_parser.add_argument('--env', default='development', help='环境名称')
    setup_parser.add_argument('--docker', action='store_true', help='使用Docker服务')

    # init命令
    init_parser = subparsers.add_parser('init', help='初始化数据库')
    init_parser.add_argument('--env', default='production', help='环境名称')

    # test命令
    test_parser = subparsers.add_parser('test', help='测试数据库')
    test_parser.add_argument('--env', default='development', help='环境名称')
    test_parser.add_argument('--type', default='all', help='测试类型')

    # backup命令
    backup_parser = subparsers.add_parser('backup', help='备份数据库')
    backup_parser.add_argument('--env', default='production', help='环境名称')
    backup_parser.add_argument('--name', help='备份名称')

    # restore命令
    restore_parser = subparsers.add_parser('restore', help='恢复数据库')
    restore_parser.add_argument('--env', required=True, help='环境名称')
    restore_parser.add_argument('backup_file', help='备份文件路径')

    # config命令
    config_parser = subparsers.add_parser('config', help='配置管理')
    config_parser.add_argument('action', help='配置操作')
    config_parser.add_argument('args', nargs='*', help='操作参数')

    # migrate命令
    migrate_parser = subparsers.add_parser('migrate', help='数据库迁移')
    migrate_parser.add_argument('--env', default='production', help='环境名称')
    migrate_parser.add_argument('--action', default='upgrade', help='迁移操作')

    # docker命令
    docker_parser = subparsers.add_parser('docker', help='Docker服务管理')
    docker_parser.add_argument('action', help='Docker操作')

    # status命令
    status_parser = subparsers.add_parser('status', help='检查数据库状态')
    status_parser.add_argument('--env', default='development', help='环境名称')

    # reset命令
    reset_parser = subparsers.add_parser('reset', help='重置数据库')
    reset_parser.add_argument('--env', default='development', help='环境名称')

    # help命令
    subparsers.add_parser('help', help='显示详细帮助')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    manager = DatabaseManager()

    if args.command == 'setup':
        manager.cmd_setup(args.env, args.docker)
    elif args.command == 'init':
        manager.cmd_init(args.env)
    elif args.command == 'test':
        manager.cmd_test(args.env, args.type)
    elif args.command == 'backup':
        manager.cmd_backup(args.env, args.name)
    elif args.command == 'restore':
        manager.cmd_restore(args.env, args.backup_file)
    elif args.command == 'config':
        manager.cmd_config(args.action, *args.args)
    elif args.command == 'migrate':
        manager.cmd_migrate(args.env, args.action)
    elif args.command == 'docker':
        manager.cmd_docker(args.action)
    elif args.command == 'status':
        manager.cmd_status(args.env)
    elif args.command == 'reset':
        manager.cmd_reset(args.env)
    elif args.command == 'help':
        manager.show_help()


if __name__ == "__main__":
    main()
