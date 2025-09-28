#!/usr/bin/env python3
"""
五好伴学部署管理脚本
用于管理应用的部署、启动、停止和监控
"""

import os
import sys
import json
import time
import subprocess
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Any
import yaml
import requests
from datetime import datetime


class DeploymentManager:
    """部署管理器"""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.docker_compose_file = self.project_root / "docker-compose.yml"
        self.docker_compose_dev_file = self.project_root / "docker-compose.dev.yml"
        self.env_file = self.project_root / ".env"

        # 服务配置
        self.services = {
            "app": {
                "name": "wuhao-tutor-app",
                "health_endpoint": "http://localhost:8000/health",
                "required": True
            },
            "postgres": {
                "name": "wuhao-postgres",
                "health_command": ["docker", "exec", "wuhao-postgres", "pg_isready", "-U", "wuhao_prod"],
                "required": True
            },
            "redis": {
                "name": "wuhao-redis",
                "health_command": ["docker", "exec", "wuhao-redis", "redis-cli", "ping"],
                "required": True
            },
            "nginx": {
                "name": "wuhao-nginx",
                "health_endpoint": "http://localhost/health",
                "required": False
            }
        }

    def check_prerequisites(self) -> bool:
        """检查部署前置条件"""
        print("🔍 检查部署前置条件...")

        prerequisites = []

        # 检查Docker
        try:
            result = subprocess.run(["docker", "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                prerequisites.append(("✅ Docker", result.stdout.strip()))
            else:
                prerequisites.append(("❌ Docker", "未安装或无法访问"))
        except FileNotFoundError:
            prerequisites.append(("❌ Docker", "未安装"))

        # 检查Docker Compose
        try:
            result = subprocess.run(["docker-compose", "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                prerequisites.append(("✅ Docker Compose", result.stdout.strip()))
            else:
                prerequisites.append(("❌ Docker Compose", "未安装或无法访问"))
        except FileNotFoundError:
            prerequisites.append(("❌ Docker Compose", "未安装"))

        # 检查配置文件
        if self.docker_compose_file.exists():
            prerequisites.append(("✅ docker-compose.yml", "存在"))
        else:
            prerequisites.append(("❌ docker-compose.yml", "不存在"))

        if self.env_file.exists():
            prerequisites.append(("✅ 环境配置文件", "存在"))
        else:
            prerequisites.append(("⚠️  环境配置文件", "不存在，使用默认配置"))

        # 检查必需目录
        required_dirs = ["uploads", "logs", "secrets"]
        for dir_name in required_dirs:
            dir_path = self.project_root / dir_name
            if dir_path.exists():
                prerequisites.append((f"✅ {dir_name}/", "存在"))
            else:
                dir_path.mkdir(exist_ok=True)
                prerequisites.append((f"✅ {dir_name}/", "已创建"))

        # 打印检查结果
        for status, detail in prerequisites:
            print(f"  {status}: {detail}")

        # 检查是否有错误
        errors = [p for p in prerequisites if p[0].startswith("❌")]
        if errors:
            print(f"\n❌ 发现 {len(errors)} 个错误，请先解决这些问题")
            return False

        warnings = [p for p in prerequisites if p[0].startswith("⚠️")]
        if warnings:
            print(f"\n⚠️  发现 {len(warnings)} 个警告")

        print("✅ 前置条件检查完成")
        return True

    def build_images(self, no_cache: bool = False, target: str = "runtime") -> bool:
        """构建Docker镜像"""
        print(f"🔨 构建Docker镜像 (target: {target})...")

        cmd = ["docker-compose", "build"]
        if no_cache:
            cmd.append("--no-cache")

        cmd.extend(["--build-arg", f"BUILD_ENV=production"])

        try:
            result = subprocess.run(cmd, cwd=self.project_root, check=True)
            print("✅ 镜像构建完成")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ 镜像构建失败: {e}")
            return False

    def deploy(self, environment: str = "production", pull: bool = True, build: bool = True) -> bool:
        """部署应用"""
        print(f"🚀 开始部署到 {environment} 环境...")

        # 选择配置文件
        if environment == "development":
            compose_file = self.docker_compose_dev_file
        else:
            compose_file = self.docker_compose_file

        if not compose_file.exists():
            print(f"❌ 配置文件不存在: {compose_file}")
            return False

        try:
            # 拉取最新镜像
            if pull and environment != "development":
                print("📥 拉取最新镜像...")
                subprocess.run(["docker-compose", "-f", str(compose_file), "pull"],
                             cwd=self.project_root, check=True)

            # 构建镜像
            if build:
                if not self.build_images():
                    return False

            # 启动服务
            print("🏃 启动服务...")
            subprocess.run(["docker-compose", "-f", str(compose_file), "up", "-d"],
                         cwd=self.project_root, check=True)

            # 等待服务健康检查
            if not self.wait_for_services():
                print("❌ 服务健康检查失败")
                return False

            print("✅ 部署完成")
            return True

        except subprocess.CalledProcessError as e:
            print(f"❌ 部署失败: {e}")
            return False

    def start_services(self, services: List[str] | None = None) -> bool:
        """启动服务"""
        service_list = services if services is not None else list(self.services.keys())
        print(f"🏃 启动服务: {', '.join(service_list)}")

        try:
            cmd = ["docker-compose", "start"]
            cmd.extend(service_list)
            subprocess.run(cmd, cwd=self.project_root, check=True)

            print("✅ 服务启动完成")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ 服务启动失败: {e}")
            return False

    def stop_services(self, services: List[str] | None = None) -> bool:
        """停止服务"""
        service_list = services if services is not None else list(self.services.keys())
        print(f"🛑 停止服务: {', '.join(service_list)}")

        try:
            cmd = ["docker-compose", "stop"]
            cmd.extend(service_list)
            subprocess.run(cmd, cwd=self.project_root, check=True)

            print("✅ 服务停止完成")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ 服务停止失败: {e}")
            return False

    def restart_services(self, services: List[str] | None = None) -> bool:
        """重启服务"""
        service_list = services if services is not None else list(self.services.keys())
        print(f"🔄 重启服务: {', '.join(service_list)}")

        try:
            cmd = ["docker-compose", "restart"]
            cmd.extend(service_list)
            subprocess.run(cmd, cwd=self.project_root, check=True)

            # 等待服务健康检查
            if not self.wait_for_services(service_list):
                print("❌ 服务重启后健康检查失败")
                return False

            print("✅ 服务重启完成")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ 服务重启失败: {e}")
            return False

    def wait_for_services(self, services: List[str] | None = None, timeout: int = 300) -> bool:
        """等待服务健康检查"""
        service_list = services if services is not None else [s for s, config in self.services.items() if config["required"]]
        print(f"⏳ 等待服务健康检查: {', '.join(service_list)}")

        start_time = time.time()

        while time.time() - start_time < timeout:
            healthy_services = []

            for service in service_list:
                if self.check_service_health(service):
                    healthy_services.append(service)

            if len(healthy_services) == len(service_list):
                print("✅ 所有服务健康检查通过")
                return True

            unhealthy_services = set(service_list) - set(healthy_services)
            print(f"  ⏳ 等待服务: {', '.join(unhealthy_services)}")
            time.sleep(5)

        print(f"❌ 服务健康检查超时 ({timeout}s)")
        return False

    def check_service_health(self, service: str) -> bool:
        """检查单个服务健康状态"""
        if service not in self.services:
            return False

        config = self.services[service]

        try:
            # HTTP健康检查
            if "health_endpoint" in config:
                response = requests.get(config["health_endpoint"], timeout=5)
                return response.status_code == 200

            # 命令行健康检查
            if "health_command" in config:
                result = subprocess.run(config["health_command"],
                                      capture_output=True, timeout=10)
                return result.returncode == 0

            # Docker容器状态检查
            result = subprocess.run(
                ["docker", "inspect", "--format", "{{.State.Health.Status}}", config["name"]],
                capture_output=True, text=True, timeout=10
            )

            if result.returncode == 0:
                status = result.stdout.strip()
                return status == "healthy" or status == "none"  # none表示没有配置健康检查

        except Exception:
            pass

        return False

    def get_service_status(self) -> Dict[str, Any]:
        """获取所有服务状态"""
        status = {}

        for service, config in self.services.items():
            service_status = {
                "name": config["name"],
                "required": config["required"],
                "healthy": False,
                "running": False,
                "details": {}
            }

            try:
                # 检查容器是否运行
                result = subprocess.run(
                    ["docker", "inspect", "--format", "{{.State.Running}}", config["name"]],
                    capture_output=True, text=True, timeout=10
                )

                if result.returncode == 0:
                    service_status["running"] = result.stdout.strip() == "true"

                # 检查健康状态
                service_status["healthy"] = self.check_service_health(service)

                # 获取详细信息
                result = subprocess.run(
                    ["docker", "inspect", config["name"]],
                    capture_output=True, text=True, timeout=10
                )

                if result.returncode == 0:
                    inspect_data = json.loads(result.stdout)[0]
                    service_status["details"] = {
                        "created": inspect_data["Created"],
                        "started": inspect_data["State"]["StartedAt"],
                        "status": inspect_data["State"]["Status"],
                        "restart_count": inspect_data["RestartCount"]
                    }

            except Exception as e:
                service_status["details"]["error"] = str(e)

            status[service] = service_status

        return status

    def show_status(self):
        """显示服务状态"""
        print("📊 服务状态:")

        status = self.get_service_status()

        for service, info in status.items():
            running_icon = "🟢" if info["running"] else "🔴"
            health_icon = "✅" if info["healthy"] else "❌"
            required_icon = "🔒" if info["required"] else "📦"

            print(f"  {required_icon} {service:<12} {running_icon} Running: {info['running']:<5} {health_icon} Healthy: {info['healthy']}")

            if "error" in info["details"]:
                print(f"    ❌ Error: {info['details']['error']}")
            elif info["running"]:
                details = info["details"]
                if "started" in details:
                    started_time = details["started"][:19].replace("T", " ")
                    print(f"    📅 Started: {started_time}")
                if "restart_count" in details and details["restart_count"] > 0:
                    print(f"    🔄 Restarts: {details['restart_count']}")

    def show_logs(self, service: str | None = None, tail: int = 100, follow: bool = False):
        """查看服务日志"""
        cmd = ["docker-compose", "logs"]

        if tail:
            cmd.extend(["--tail", str(tail)])

        if follow:
            cmd.append("-f")

        if service is not None:
            cmd.append(service)
            print(f"📋 查看 {service} 服务日志 (最近{tail}行):")
        else:
            print(f"📋 查看所有服务日志 (最近{tail}行):")

        try:
            subprocess.run(cmd, cwd=self.project_root)
        except KeyboardInterrupt:
            print("\n⏹️  日志查看已停止")

    def backup_data(self, backup_dir: str | None = None):
        """备份数据"""
        if backup_dir is None:
            backup_dir = str(self.project_root / "backups" / datetime.now().strftime("%Y%m%d_%H%M%S"))

        backup_path = Path(backup_dir)
        backup_path.mkdir(parents=True, exist_ok=True)

        print(f"💾 开始数据备份到: {backup_path}")

        try:
            # 备份数据库
            print("  📊 备份PostgreSQL数据库...")
            db_backup_file = backup_path / "postgres_backup.sql"
            subprocess.run([
                "docker", "exec", "wuhao-postgres",
                "pg_dump", "-U", "wuhao_prod", "-d", "wuhao_tutor",
                "-f", "/tmp/backup.sql"
            ], check=True)

            subprocess.run([
                "docker", "cp", "wuhao-postgres:/tmp/backup.sql", str(db_backup_file)
            ], check=True)

            # 备份Redis数据
            print("  🗄️  备份Redis数据...")
            redis_backup_file = backup_path / "redis_backup.rdb"
            subprocess.run([
                "docker", "cp", "wuhao-redis:/data/dump.rdb", str(redis_backup_file)
            ], check=True)

            # 备份上传文件
            print("  📁 备份上传文件...")
            uploads_backup_dir = backup_path / "uploads"
            subprocess.run([
                "docker", "cp", "wuhao-tutor-app:/app/uploads", str(uploads_backup_dir)
            ], check=True)

            # 备份配置文件
            print("  ⚙️  备份配置文件...")
            config_files = [".env", "docker-compose.yml", "nginx/"]
            for config_file in config_files:
                src_path = self.project_root / config_file
                if src_path.exists():
                    if src_path.is_dir():
                        subprocess.run(["cp", "-r", str(src_path), str(backup_path)], check=True)
                    else:
                        subprocess.run(["cp", str(src_path), str(backup_path)], check=True)

            print(f"✅ 数据备份完成: {backup_path}")

        except subprocess.CalledProcessError as e:
            print(f"❌ 数据备份失败: {e}")

    def cleanup(self, remove_volumes: bool = False):
        """清理资源"""
        print("🧹 清理Docker资源...")

        try:
            # 停止并删除容器
            subprocess.run(["docker-compose", "down"], cwd=self.project_root)

            if remove_volumes:
                print("  🗑️  删除数据卷...")
                subprocess.run(["docker-compose", "down", "-v"], cwd=self.project_root)

            # 清理未使用的镜像
            print("  🖼️  清理未使用的镜像...")
            subprocess.run(["docker", "image", "prune", "-f"])

            # 清理未使用的网络
            print("  🌐 清理未使用的网络...")
            subprocess.run(["docker", "network", "prune", "-f"])

            print("✅ 清理完成")

        except subprocess.CalledProcessError as e:
            print(f"❌ 清理失败: {e}")

    def update_application(self, version: str = "latest"):
        """更新应用"""
        print(f"🔄 更新应用到版本: {version}")

        try:
            # 备份数据
            print("1️⃣ 备份当前数据...")
            self.backup_data()

            # 拉取新版本
            print("2️⃣ 拉取新版本...")
            subprocess.run(["git", "pull", "origin", "main"], cwd=self.project_root, check=True)

            # 重新构建和部署
            print("3️⃣ 重新构建和部署...")
            if not self.deploy(build=True, pull=True):
                print("❌ 部署失败，请检查日志")
                return False

            print("✅ 应用更新完成")
            return True

        except subprocess.CalledProcessError as e:
            print(f"❌ 应用更新失败: {e}")
            return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="五好伴学部署管理工具")
    parser.add_argument("--env", "-e", choices=["development", "production"],
                       default="production", help="部署环境")

    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # 检查命令
    subparsers.add_parser("check", help="检查部署前置条件")

    # 构建命令
    build_parser = subparsers.add_parser("build", help="构建Docker镜像")
    build_parser.add_argument("--no-cache", action="store_true", help="不使用缓存构建")
    build_parser.add_argument("--target", default="runtime", help="构建目标阶段")

    # 部署命令
    deploy_parser = subparsers.add_parser("deploy", help="部署应用")
    deploy_parser.add_argument("--no-pull", action="store_true", help="不拉取最新镜像")
    deploy_parser.add_argument("--no-build", action="store_true", help="不重新构建镜像")

    # 服务管理命令
    start_parser = subparsers.add_parser("start", help="启动服务")
    start_parser.add_argument("services", nargs="*", help="指定服务名称")

    stop_parser = subparsers.add_parser("stop", help="停止服务")
    stop_parser.add_argument("services", nargs="*", help="指定服务名称")

    restart_parser = subparsers.add_parser("restart", help="重启服务")
    restart_parser.add_argument("services", nargs="*", help="指定服务名称")

    # 状态命令
    subparsers.add_parser("status", help="查看服务状态")

    # 日志命令
    logs_parser = subparsers.add_parser("logs", help="查看服务日志")
    logs_parser.add_argument("service", nargs="?", help="服务名称")
    logs_parser.add_argument("--tail", "-t", type=int, default=100, help="显示最近N行")
    logs_parser.add_argument("--follow", "-f", action="store_true", help="实时跟踪日志")

    # 备份命令
    backup_parser = subparsers.add_parser("backup", help="备份数据")
    backup_parser.add_argument("--dir", help="备份目录")

    # 更新命令
    update_parser = subparsers.add_parser("update", help="更新应用")
    update_parser.add_argument("--version", default="latest", help="版本号")

    # 清理命令
    cleanup_parser = subparsers.add_parser("cleanup", help="清理资源")
    cleanup_parser.add_argument("--volumes", action="store_true", help="同时删除数据卷")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    manager = DeploymentManager()

    try:
        if args.command == "check":
            success = manager.check_prerequisites()
            sys.exit(0 if success else 1)

        elif args.command == "build":
            success = manager.build_images(args.no_cache, args.target)
            sys.exit(0 if success else 1)

        elif args.command == "deploy":
            if not manager.check_prerequisites():
                sys.exit(1)
            success = manager.deploy(args.env, not args.no_pull, not args.no_build)
            sys.exit(0 if success else 1)

        elif args.command == "start":
            success = manager.start_services(args.services if args.services else None)
            sys.exit(0 if success else 1)

        elif args.command == "stop":
            success = manager.stop_services(args.services if args.services else None)
            sys.exit(0 if success else 1)

        elif args.command == "restart":
            success = manager.restart_services(args.services if args.services else None)
            sys.exit(0 if success else 1)

        elif args.command == "status":
            manager.show_status()

        elif args.command == "logs":
            manager.show_logs(args.service, args.tail, args.follow)

        elif args.command == "backup":
            manager.backup_data(args.dir)

        elif args.command == "update":
            success = manager.update_application(args.version)
            sys.exit(0 if success else 1)

        elif args.command == "cleanup":
            manager.cleanup(args.volumes)

    except KeyboardInterrupt:
        print("\n⏹️  操作已取消")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 执行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
