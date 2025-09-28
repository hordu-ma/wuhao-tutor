#!/usr/bin/env python3
"""
数据库备份和恢复脚本
支持PostgreSQL数据库的自动备份、恢复和管理
"""

import asyncio
import sys
import os
import subprocess
import json
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime, timezone
import logging
import shutil
import gzip

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.config import get_settings

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DatabaseBackupManager:
    """数据库备份管理器"""

    def __init__(self, environment: str = "production"):
        """
        初始化备份管理器

        Args:
            environment: 环境名称
        """
        os.environ["ENVIRONMENT"] = environment
        self.settings = get_settings()
        self.environment = environment
        self.backup_dir = project_root / "backups"
        self.backup_dir.mkdir(exist_ok=True)

        logger.info(f"初始化备份管理器 - 环境: {environment}")
        logger.info(f"备份目录: {self.backup_dir}")

    def _get_pg_dump_command(self) -> List[str]:
        """获取pg_dump命令参数"""
        return [
            "pg_dump",
            "-h", self.settings.POSTGRES_SERVER,
            "-p", str(self.settings.POSTGRES_PORT),
            "-U", self.settings.POSTGRES_USER,
            "-d", self.settings.POSTGRES_DB,
            "--no-password",
            "--verbose",
            "--clean",
            "--if-exists",
            "--create"
        ]

    def _get_pg_restore_command(self) -> List[str]:
        """获取pg_restore基础命令参数"""
        return [
            "psql",
            "-h", self.settings.POSTGRES_SERVER,
            "-p", str(self.settings.POSTGRES_PORT),
            "-U", self.settings.POSTGRES_USER,
            "--no-password",
            "-v", "ON_ERROR_STOP=1"
        ]

    def _set_pgpassword(self) -> Dict[str, str]:
        """设置PostgreSQL密码环境变量"""
        env = os.environ.copy()
        if self.settings.POSTGRES_PASSWORD:
            env["PGPASSWORD"] = self.settings.POSTGRES_PASSWORD
        return env

    def create_backup(self, backup_name: Optional[str] = None, compress: bool = True) -> tuple[bool, str]:
        """
        创建数据库备份

        Args:
            backup_name: 备份名称，如果为None则自动生成
            compress: 是否压缩备份文件

        Returns:
            (success, backup_file_path)
        """
        try:
            # 生成备份文件名
            if not backup_name:
                timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
                backup_name = f"{self.settings.POSTGRES_DB}_{self.environment}_{timestamp}"

            backup_file = self.backup_dir / f"{backup_name}.sql"

            logger.info(f"🔄 开始创建数据库备份: {backup_name}")
            logger.info(f"   目标文件: {backup_file}")

            # 执行pg_dump
            cmd = self._get_pg_dump_command()
            env = self._set_pgpassword()

            with open(backup_file, 'w', encoding='utf-8') as f:
                result = subprocess.run(
                    cmd,
                    stdout=f,
                    stderr=subprocess.PIPE,
                    env=env,
                    text=True,
                    timeout=3600  # 1小时超时
                )

            if result.returncode != 0:
                error_msg = result.stderr or "未知错误"
                logger.error(f"❌ 数据库备份失败: {error_msg}")
                if backup_file.exists():
                    backup_file.unlink()
                return False, ""

            # 压缩备份文件
            final_backup_file = str(backup_file)
            if compress:
                compressed_file = backup_file.with_suffix('.sql.gz')
                with open(backup_file, 'rb') as f_in:
                    with gzip.open(compressed_file, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)

                backup_file.unlink()  # 删除未压缩文件
                final_backup_file = str(compressed_file)

            # 获取文件大小
            file_size = Path(final_backup_file).stat().st_size
            size_mb = file_size / (1024 * 1024)

            logger.info(f"✅ 数据库备份成功!")
            logger.info(f"   备份文件: {final_backup_file}")
            logger.info(f"   文件大小: {size_mb:.2f} MB")

            # 创建备份元数据
            self._save_backup_metadata(backup_name, final_backup_file, file_size, compress)

            return True, final_backup_file

        except subprocess.TimeoutExpired:
            logger.error("❌ 数据库备份超时")
            return False, ""
        except Exception as e:
            logger.error(f"❌ 创建备份失败: {e}")
            return False, ""

    def restore_backup(self, backup_file: str, target_db: Optional[str] = None) -> bool:
        """
        从备份文件恢复数据库

        Args:
            backup_file: 备份文件路径
            target_db: 目标数据库名，如果为None则使用配置中的数据库

        Returns:
            恢复是否成功
        """
        # 初始化临时文件变量
        temp_file = None

        try:
            backup_path = Path(backup_file)
            if not backup_path.exists():
                logger.error(f"❌ 备份文件不存在: {backup_file}")
                return False

            logger.info(f"🔄 开始恢复数据库备份: {backup_path.name}")
            logger.warning("⚠️  此操作将完全替换现有数据库内容!")

            # 如果是压缩文件，先解压
            restore_file = backup_path

            if backup_path.suffix == '.gz':
                temp_file = backup_path.with_suffix('')
                logger.info("🔄 解压备份文件...")
                with gzip.open(backup_path, 'rb') as f_in:
                    with open(temp_file, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                restore_file = temp_file

            # 执行恢复
            cmd = self._get_pg_restore_command()
            if target_db:
                cmd.extend(["-d", target_db])
            else:
                cmd.extend(["-d", "postgres"])  # 连接到默认数据库执行CREATE DATABASE

            env = self._set_pgpassword()

            with open(restore_file, 'r', encoding='utf-8') as f:
                result = subprocess.run(
                    cmd,
                    stdin=f,
                    stderr=subprocess.PIPE,
                    env=env,
                    text=True,
                    timeout=3600
                )

            # 清理临时文件
            if temp_file and temp_file.exists():
                temp_file.unlink()

            if result.returncode != 0:
                error_msg = result.stderr or "未知错误"
                logger.error(f"❌ 数据库恢复失败: {error_msg}")
                return False

            logger.info("✅ 数据库恢复成功!")
            return True

        except subprocess.TimeoutExpired:
            logger.error("❌ 数据库恢复超时")
            return False
        except Exception as e:
            logger.error(f"❌ 恢复备份失败: {e}")
            return False
        finally:
            # 确保清理临时文件
            if temp_file and temp_file.exists():
                temp_file.unlink()

    def list_backups(self) -> List[Dict[str, Any]]:
        """列出所有备份文件"""
        backups = []

        # 扫描备份文件
        for file_path in self.backup_dir.glob("*.sql*"):
            if file_path.is_file():
                stat = file_path.stat()
                backup_info = {
                    "name": file_path.stem.replace('.sql', ''),
                    "file_path": str(file_path),
                    "file_name": file_path.name,
                    "size": stat.st_size,
                    "size_mb": round(stat.st_size / (1024 * 1024), 2),
                    "created_at": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc),
                    "compressed": file_path.suffix == '.gz'
                }

                # 尝试加载元数据
                metadata = self._load_backup_metadata(backup_info["name"])
                if metadata:
                    backup_info.update(metadata)

                backups.append(backup_info)

        # 按创建时间排序
        backups.sort(key=lambda x: x["created_at"], reverse=True)
        return backups

    def delete_backup(self, backup_name: str) -> bool:
        """
        删除指定备份

        Args:
            backup_name: 备份名称

        Returns:
            删除是否成功
        """
        try:
            # 查找备份文件
            sql_file = self.backup_dir / f"{backup_name}.sql"
            gz_file = self.backup_dir / f"{backup_name}.sql.gz"

            deleted = False
            if sql_file.exists():
                sql_file.unlink()
                deleted = True
                logger.info(f"✅ 已删除备份文件: {sql_file.name}")

            if gz_file.exists():
                gz_file.unlink()
                deleted = True
                logger.info(f"✅ 已删除备份文件: {gz_file.name}")

            # 删除元数据
            metadata_file = self.backup_dir / f"{backup_name}.metadata.json"
            if metadata_file.exists():
                metadata_file.unlink()

            if not deleted:
                logger.error(f"❌ 备份文件不存在: {backup_name}")
                return False

            return True

        except Exception as e:
            logger.error(f"❌ 删除备份失败: {e}")
            return False

    def cleanup_old_backups(self, keep_count: int = 10, keep_days: int = 30) -> int:
        """
        清理旧的备份文件

        Args:
            keep_count: 保留的备份数量
            keep_days: 保留的天数

        Returns:
            删除的备份数量
        """
        try:
            backups = self.list_backups()
            deleted_count = 0

            cutoff_date = datetime.now(timezone.utc).timestamp() - (keep_days * 24 * 3600)

            # 保留最新的 keep_count 个备份，删除超过 keep_days 天的备份
            for i, backup in enumerate(backups):
                should_delete = False

                if i >= keep_count:
                    should_delete = True
                    reason = f"超过保留数量限制 ({keep_count})"
                elif backup["created_at"].timestamp() < cutoff_date:
                    should_delete = True
                    reason = f"超过保留天数限制 ({keep_days}天)"

                if should_delete:
                    reason = "过期" if should_delete else ""
                    if self.delete_backup(backup["name"]):
                        deleted_count += 1
                        logger.info(f"🗑️  已删除旧备份: {backup['name']} ({reason})")

            logger.info(f"✅ 备份清理完成，删除了 {deleted_count} 个旧备份")
            return deleted_count

        except Exception as e:
            logger.error(f"❌ 清理备份失败: {e}")
            return 0

    def _save_backup_metadata(self, backup_name: str, file_path: str, file_size: int, compressed: bool) -> None:
        """保存备份元数据"""
        try:
            metadata = {
                "backup_name": backup_name,
                "file_path": file_path,
                "file_size": file_size,
                "compressed": compressed,
                "environment": self.environment,
                "database_name": self.settings.POSTGRES_DB,
                "database_host": self.settings.POSTGRES_SERVER,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "created_by": "db_backup.py",
                "version": "1.0"
            }

            metadata_file = self.backup_dir / f"{backup_name}.metadata.json"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)

        except Exception as e:
            logger.warning(f"⚠️  保存备份元数据失败: {e}")

    def _load_backup_metadata(self, backup_name: str) -> Optional[Dict[str, Any]]:
        """加载备份元数据"""
        try:
            metadata_file = self.backup_dir / f"{backup_name}.metadata.json"
            if metadata_file.exists():
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception:
            pass
        return None

    def verify_backup(self, backup_file: str) -> bool:
        """
        验证备份文件完整性

        Args:
            backup_file: 备份文件路径

        Returns:
            验证是否成功
        """
        try:
            backup_path = Path(backup_file)
            if not backup_path.exists():
                logger.error(f"❌ 备份文件不存在: {backup_file}")
                return False

            logger.info(f"🔍 验证备份文件: {backup_path.name}")

            # 检查文件大小
            file_size = backup_path.stat().st_size
            if file_size == 0:
                logger.error("❌ 备份文件为空")
                return False

            # 如果是压缩文件，尝试解压验证
            if backup_path.suffix == '.gz':
                try:
                    with gzip.open(backup_path, 'rt', encoding='utf-8') as f:
                        # 读取文件头部验证
                        header = f.read(1024)
                        if not header.strip():
                            logger.error("❌ 压缩备份文件内容为空")
                            return False

                        # 检查是否包含SQL DDL语句
                        if 'CREATE' not in header.upper() and 'INSERT' not in header.upper():
                            logger.warning("⚠️  备份文件可能不包含有效的SQL语句")

                except gzip.BadGzipFile:
                    logger.error("❌ 备份文件压缩格式损坏")
                    return False
            else:
                # 普通SQL文件验证
                try:
                    with open(backup_path, 'r', encoding='utf-8') as f:
                        header = f.read(1024)
                        if not header.strip():
                            logger.error("❌ 备份文件内容为空")
                            return False
                except UnicodeDecodeError:
                    logger.error("❌ 备份文件编码格式错误")
                    return False

            logger.info(f"✅ 备份文件验证通过")
            logger.info(f"   文件大小: {file_size / (1024 * 1024):.2f} MB")
            return True

        except Exception as e:
            logger.error(f"❌ 验证备份文件失败: {e}")
            return False


class DatabaseBackupCLI:
    """数据库备份命令行接口"""

    def __init__(self):
        self.manager = None

    def cmd_create(self, env: str, name: Optional[str], compress: bool) -> None:
        """创建备份"""
        self.manager = DatabaseBackupManager(env)
        success, backup_file = self.manager.create_backup(name, compress)
        if success:
            print(f"✅ 备份创建成功: {backup_file}")
        else:
            print("❌ 备份创建失败")
            sys.exit(1)

    def cmd_restore(self, env: str, backup_file: str, target_db: Optional[str]) -> None:
        """恢复备份"""
        self.manager = DatabaseBackupManager(env)

        # 确认恢复操作
        print(f"⚠️  即将恢复数据库备份: {backup_file}")
        print(f"   目标环境: {env}")
        if target_db:
            print(f"   目标数据库: {target_db}")
        print("   此操作将完全替换现有数据库内容!")

        confirm = input("确认继续吗? (yes/N): ").strip().lower()
        if confirm != 'yes':
            print("❌ 操作已取消")
            return

        success = self.manager.restore_backup(backup_file, target_db)
        if success:
            print("✅ 数据库恢复成功")
        else:
            print("❌ 数据库恢复失败")
            sys.exit(1)

    def cmd_list(self, env: str) -> None:
        """列出所有备份"""
        self.manager = DatabaseBackupManager(env)
        backups = self.manager.list_backups()

        if not backups:
            print("📋 暂无备份文件")
            return

        print(f"📋 备份列表 (环境: {env}):")
        print(f"{'名称':<30} {'大小':<10} {'压缩':<6} {'创建时间':<20}")
        print("-" * 75)

        for backup in backups:
            compressed = "是" if backup["compressed"] else "否"
            created_at = backup["created_at"].strftime("%Y-%m-%d %H:%M:%S")
            print(f"{backup['name']:<30} {backup['size_mb']:>7.2f}MB {compressed:<6} {created_at}")

    def cmd_delete(self, env: str, backup_name: str) -> None:
        """删除备份"""
        self.manager = DatabaseBackupManager(env)

        confirm = input(f"确认删除备份 '{backup_name}'? (yes/N): ").strip().lower()
        if confirm != 'yes':
            print("❌ 操作已取消")
            return

        success = self.manager.delete_backup(backup_name)
        if success:
            print(f"✅ 备份已删除: {backup_name}")
        else:
            print("❌ 删除备份失败")
            sys.exit(1)

    def cmd_cleanup(self, env: str, keep_count: int, keep_days: int) -> None:
        """清理旧备份"""
        self.manager = DatabaseBackupManager(env)
        deleted_count = self.manager.cleanup_old_backups(keep_count, keep_days)
        print(f"✅ 清理完成，删除了 {deleted_count} 个旧备份")

    def cmd_verify(self, env: str, backup_file: str) -> None:
        """验证备份文件"""
        self.manager = DatabaseBackupManager(env)
        success = self.manager.verify_backup(backup_file)
        if success:
            print("✅ 备份文件验证通过")
        else:
            print("❌ 备份文件验证失败")
            sys.exit(1)


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="数据库备份管理工具")

    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    # create命令
    create_parser = subparsers.add_parser('create', help='创建数据库备份')
    create_parser.add_argument(
        "--env",
        choices=["development", "testing", "production"],
        default="production",
        help="环境名称 (默认: production)"
    )
    create_parser.add_argument('--name', help='备份名称')
    create_parser.add_argument('--no-compress', action='store_true', help='不压缩备份文件')

    # restore命令
    restore_parser = subparsers.add_parser('restore', help='恢复数据库备份')
    restore_parser.add_argument(
        "--env",
        choices=["development", "testing", "production"],
        default="production",
        help="环境名称 (默认: production)"
    )
    restore_parser.add_argument('backup_file', help='备份文件路径')
    restore_parser.add_argument('--target-db', help='目标数据库名')

    # list命令
    list_parser = subparsers.add_parser('list', help='列出所有备份')
    list_parser.add_argument(
        "--env",
        choices=["development", "testing", "production"],
        default="production",
        help="环境名称 (默认: production)"
    )

    # delete命令
    delete_parser = subparsers.add_parser('delete', help='删除备份')
    delete_parser.add_argument(
        "--env",
        choices=["development", "testing", "production"],
        default="production",
        help="环境名称 (默认: production)"
    )
    delete_parser.add_argument('backup_name', help='备份名称')

    # cleanup命令
    cleanup_parser = subparsers.add_parser('cleanup', help='清理旧备份')
    cleanup_parser.add_argument(
        "--env",
        choices=["development", "testing", "production"],
        default="production",
        help="环境名称 (默认: production)"
    )
    cleanup_parser.add_argument('--keep-count', type=int, default=10, help='保留备份数量')
    cleanup_parser.add_argument('--keep-days', type=int, default=30, help='保留天数')

    # verify命令
    verify_parser = subparsers.add_parser('verify', help='验证备份文件')
    verify_parser.add_argument(
        "--env",
        choices=["development", "testing", "production"],
        default="production",
        help="环境名称 (默认: production)"
    )
    verify_parser.add_argument('backup_file', help='备份文件路径')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    cli = DatabaseBackupCLI()

    if args.command == 'create':
        cli.cmd_create(args.env, args.name, not args.no_compress)
    elif args.command == 'restore':
        cli.cmd_restore(args.env, args.backup_file, args.target_db)
    elif args.command == 'list':
        cli.cmd_list(args.env)
    elif args.command == 'delete':
        cli.cmd_delete(args.env, args.backup_name)
    elif args.command == 'cleanup':
        cli.cmd_cleanup(args.env, args.keep_count, args.keep_days)
    elif args.command == 'verify':
        cli.cmd_verify(args.env, args.backup_file)


if __name__ == "__main__":
    main()
