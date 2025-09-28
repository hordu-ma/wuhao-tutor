#!/usr/bin/env python3
"""
五好伴学密钥管理脚本
用于生成、管理和验证各种密钥和证书
"""

import os
import sys
import secrets
import string
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Any
import json
import hashlib
import base64
from datetime import datetime, timedelta
import subprocess


class SecretsManager:
    """密钥管理器"""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.secrets_dir = self.project_root / "secrets"
        self.ssl_dir = self.project_root / "nginx" / "ssl"

        # 确保目录存在
        self.secrets_dir.mkdir(exist_ok=True)
        self.ssl_dir.mkdir(exist_ok=True, parents=True)

        # 密钥配置
        self.secrets_config = {
            "postgres_password": {
                "description": "PostgreSQL数据库密码",
                "length": 32,
                "chars": string.ascii_letters + string.digits,
                "file": "postgres_password.txt"
            },
            "redis_password": {
                "description": "Redis缓存密码",
                "length": 32,
                "chars": string.ascii_letters + string.digits,
                "file": "redis_password.txt"
            },
            "grafana_password": {
                "description": "Grafana管理员密码",
                "length": 16,
                "chars": string.ascii_letters + string.digits,
                "file": "grafana_password.txt"
            },
            "jwt_secret": {
                "description": "JWT签名密钥",
                "length": 64,
                "chars": string.ascii_letters + string.digits + "+-_=",
                "file": "jwt_secret.txt"
            },
            "api_key": {
                "description": "API访问密钥",
                "length": 48,
                "chars": string.ascii_letters + string.digits,
                "file": "api_key.txt"
            },
            "encryption_key": {
                "description": "数据加密密钥",
                "length": 32,
                "chars": None,  # 使用字节生成
                "file": "encryption_key.txt"
            }
        }

    def generate_password(self, length: int = 32, chars: str | None = None) -> str:
        """生成安全密码"""
        if chars is None:
            # 生成字节密钥并转换为base64
            key_bytes = secrets.token_bytes(length)
            return base64.urlsafe_b64encode(key_bytes).decode('utf-8')
        else:
            return ''.join(secrets.choice(chars) for _ in range(length))

    def generate_secret(self, secret_name: str, force: bool = False) -> bool:
        """生成单个密钥"""
        if secret_name not in self.secrets_config:
            print(f"❌ 未知的密钥类型: {secret_name}")
            return False

        config = self.secrets_config[secret_name]
        secret_file = self.secrets_dir / config["file"]

        if secret_file.exists() and not force:
            print(f"⚠️  密钥文件已存在: {secret_file}")
            print("使用 --force 参数强制覆盖")
            return False

        # 生成密钥
        password = self.generate_password(config["length"], config["chars"])

        # 保存到文件
        with open(secret_file, 'w', encoding='utf-8') as f:
            f.write(password)

        # 设置文件权限（仅所有者可读写）
        secret_file.chmod(0o600)

        print(f"✅ 已生成 {config['description']}: {secret_file}")
        return True

    def generate_all_secrets(self, force: bool = False) -> bool:
        """生成所有密钥"""
        print("🔐 生成所有密钥...")

        success_count = 0
        for secret_name in self.secrets_config:
            if self.generate_secret(secret_name, force):
                success_count += 1

        print(f"✅ 成功生成 {success_count}/{len(self.secrets_config)} 个密钥")
        return success_count == len(self.secrets_config)

    def list_secrets(self):
        """列出所有密钥状态"""
        print("📋 密钥状态:")

        for secret_name, config in self.secrets_config.items():
            secret_file = self.secrets_dir / config["file"]

            if secret_file.exists():
                # 获取文件信息
                stat = secret_file.stat()
                modified_time = datetime.fromtimestamp(stat.st_mtime)
                file_size = stat.st_size
                permissions = oct(stat.st_mode)[-3:]

                status_icon = "✅"
                if permissions != "600":
                    status_icon = "⚠️"

                print(f"  {status_icon} {secret_name:<20} - {config['description']}")
                print(f"     文件: {config['file']}")
                print(f"     大小: {file_size} bytes")
                print(f"     权限: {permissions}")
                print(f"     修改: {modified_time.strftime('%Y-%m-%d %H:%M:%S')}")
            else:
                print(f"  ❌ {secret_name:<20} - {config['description']}")
                print(f"     文件: {config['file']} (不存在)")
            print()

    def validate_secrets(self) -> bool:
        """验证密钥完整性"""
        print("🔍 验证密钥完整性...")

        validation_results = []

        for secret_name, config in self.secrets_config.items():
            secret_file = self.secrets_dir / config["file"]

            if not secret_file.exists():
                validation_results.append(f"❌ {secret_name}: 文件不存在")
                continue

            # 检查文件权限
            permissions = oct(secret_file.stat().st_mode)[-3:]
            if permissions != "600":
                validation_results.append(f"⚠️  {secret_name}: 文件权限不安全 ({permissions})")

            # 检查文件内容
            try:
                with open(secret_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()

                if not content:
                    validation_results.append(f"❌ {secret_name}: 文件内容为空")
                elif len(content) < 16:
                    validation_results.append(f"⚠️  {secret_name}: 密钥长度可能不足")
                else:
                    validation_results.append(f"✅ {secret_name}: 验证通过")

            except Exception as e:
                validation_results.append(f"❌ {secret_name}: 读取失败 - {e}")

        # 打印验证结果
        for result in validation_results:
            print(f"  {result}")

        # 统计
        success_count = len([r for r in validation_results if r.startswith("✅")])
        warning_count = len([r for r in validation_results if r.startswith("⚠️")])
        error_count = len([r for r in validation_results if r.startswith("❌")])

        print(f"\n📊 验证结果: {success_count}项通过, {warning_count}项警告, {error_count}项错误")

        return error_count == 0

    def rotate_secret(self, secret_name: str) -> bool:
        """轮换密钥"""
        if secret_name not in self.secrets_config:
            print(f"❌ 未知的密钥类型: {secret_name}")
            return False

        config = self.secrets_config[secret_name]
        secret_file = self.secrets_dir / config["file"]
        backup_file = self.secrets_dir / f"{config['file']}.backup"

        print(f"🔄 轮换密钥: {secret_name}")

        # 备份原密钥
        if secret_file.exists():
            with open(secret_file, 'r', encoding='utf-8') as f:
                old_content = f.read()
            with open(backup_file, 'w', encoding='utf-8') as f:
                f.write(old_content)
            backup_file.chmod(0o600)
            print(f"  📦 已备份原密钥到: {backup_file}")

        # 生成新密钥
        if self.generate_secret(secret_name, force=True):
            print(f"✅ 密钥轮换完成: {secret_name}")
            print("⚠️  请记得重启相关服务以应用新密钥")
            return True
        else:
            print(f"❌ 密钥轮换失败: {secret_name}")
            return False

    def generate_ssl_cert(self, domain: str, days: int = 365) -> bool:
        """生成自签名SSL证书"""
        print(f"🔐 生成SSL证书: {domain}")

        key_file = self.ssl_dir / f"{domain}.key"
        cert_file = self.ssl_dir / f"{domain}.crt"

        try:
            # 生成私钥
            print("  🔑 生成私钥...")
            subprocess.run([
                "openssl", "genrsa", "-out", str(key_file), "2048"
            ], check=True, capture_output=True)

            # 生成证书签名请求
            print("  📄 生成证书...")
            subprocess.run([
                "openssl", "req", "-new", "-x509",
                "-key", str(key_file),
                "-out", str(cert_file),
                "-days", str(days),
                "-subj", f"/CN={domain}/O=Wuhao Tutor/C=CN"
            ], check=True, capture_output=True)

            # 设置文件权限
            key_file.chmod(0o600)
            cert_file.chmod(0o644)

            print(f"✅ SSL证书生成完成:")
            print(f"  🔑 私钥: {key_file}")
            print(f"  📜 证书: {cert_file}")
            print(f"  ⏰ 有效期: {days} 天")

            return True

        except subprocess.CalledProcessError as e:
            print(f"❌ SSL证书生成失败: {e}")
            return False
        except FileNotFoundError:
            print("❌ 未找到openssl命令，请安装OpenSSL")
            return False

    def generate_dhparam(self, bits: int = 2048) -> bool:
        """生成DH参数文件"""
        print(f"🔐 生成DH参数文件 ({bits} bits)...")

        dhparam_file = self.ssl_dir / "dhparam.pem"

        try:
            subprocess.run([
                "openssl", "dhparam", "-out", str(dhparam_file), str(bits)
            ], check=True)

            dhparam_file.chmod(0o644)

            print(f"✅ DH参数文件生成完成: {dhparam_file}")
            return True

        except subprocess.CalledProcessError as e:
            print(f"❌ DH参数文件生成失败: {e}")
            return False
        except FileNotFoundError:
            print("❌ 未找到openssl命令，请安装OpenSSL")
            return False

    def create_htpasswd(self, username: str, password: str | None = None) -> bool:
        """创建HTTP基本认证文件"""
        if not password:
            password = self.generate_password(16, string.ascii_letters + string.digits)
            print(f"🔑 生成的密码: {password}")

        htpasswd_file = self.project_root / "nginx" / ".htpasswd"

        try:
            # 使用bcrypt加密密码
            import crypt
            import hashlib
            try:
                # 尝试使用 METHOD_BLKFISH (如果可用)
                encrypted_password = crypt.crypt(password, crypt.mksalt(getattr(crypt, 'METHOD_BLKFISH', crypt.METHOD_SHA512)))
            except AttributeError:
                # 如果不支持，使用SHA512
                encrypted_password = crypt.crypt(password, crypt.mksalt(crypt.METHOD_SHA512))

            with open(htpasswd_file, 'a', encoding='utf-8') as f:
                f.write(f"{username}:{encrypted_password}\n")

            htpasswd_file.chmod(0o600)

            print(f"✅ 已添加用户到HTTP认证文件: {username}")
            print(f"  📁 文件: {htpasswd_file}")

            return True

        except Exception as e:
            print(f"❌ 创建HTTP认证文件失败: {e}")
            return False

    def export_secrets(self, output_file: str | None = None) -> bool:
        """导出密钥（加密）"""
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"secrets_export_{timestamp}.json"

        output_path = Path(output_file)

        print(f"📤 导出密钥到: {output_path}")

        secrets_data = {
            "export_time": datetime.now().isoformat(),
            "secrets": {}
        }

        for secret_name, config in self.secrets_config.items():
            secret_file = self.secrets_dir / config["file"]
            if secret_file.exists():
                with open(secret_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()

                # 简单的base64编码（实际使用中应该用更强的加密）
                encoded_content = base64.b64encode(content.encode('utf-8')).decode('utf-8')
                secrets_data["secrets"][secret_name] = {
                    "description": config["description"],
                    "content": encoded_content,
                    "file": config["file"]
                }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(secrets_data, f, indent=2, ensure_ascii=False)

        output_path.chmod(0o600)

        print(f"✅ 密钥导出完成: {len(secrets_data['secrets'])} 个密钥")
        print("⚠️  请安全保存导出文件并在使用后删除")

        return True

    def cleanup_old_secrets(self, days: int = 30):
        """清理旧的密钥备份"""
        print(f"🧹 清理 {days} 天前的密钥备份...")

        cutoff_time = datetime.now() - timedelta(days=days)
        cleaned_count = 0

        for file_path in self.secrets_dir.glob("*.backup"):
            if file_path.stat().st_mtime < cutoff_time.timestamp():
                file_path.unlink()
                print(f"  🗑️  删除: {file_path.name}")
                cleaned_count += 1

        if cleaned_count == 0:
            print("  ✨ 没有需要清理的备份文件")
        else:
            print(f"✅ 已清理 {cleaned_count} 个备份文件")

    def setup_production_secrets(self):
        """设置生产环境密钥"""
        print("🏭 设置生产环境密钥...")

        # 生成所有密钥
        self.generate_all_secrets(force=False)

        # 生成SSL证书
        domains = ["wuhao-tutor.com", "admin.wuhao-tutor.com", "docs.wuhao-tutor.com"]
        for domain in domains:
            self.generate_ssl_cert(domain)

        # 生成DH参数
        self.generate_dhparam()

        # 创建默认的HTTP认证用户
        self.create_htpasswd("admin")

        print("✅ 生产环境密钥设置完成")
        print("⚠️  请妥善保存生成的密钥和证书")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="五好伴学密钥管理工具")
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # 生成密钥命令
    generate_parser = subparsers.add_parser("generate", help="生成密钥")
    generate_parser.add_argument("secret", nargs="?", help="密钥名称（可选）")
    generate_parser.add_argument("--force", "-f", action="store_true", help="强制覆盖现有密钥")

    # 列出密钥命令
    subparsers.add_parser("list", help="列出所有密钥状态")

    # 验证密钥命令
    subparsers.add_parser("validate", help="验证密钥完整性")

    # 轮换密钥命令
    rotate_parser = subparsers.add_parser("rotate", help="轮换密钥")
    rotate_parser.add_argument("secret", help="要轮换的密钥名称")

    # SSL证书命令
    ssl_parser = subparsers.add_parser("ssl", help="生成SSL证书")
    ssl_parser.add_argument("domain", help="域名")
    ssl_parser.add_argument("--days", type=int, default=365, help="证书有效期（天）")

    # DH参数命令
    dhparam_parser = subparsers.add_parser("dhparam", help="生成DH参数文件")
    dhparam_parser.add_argument("--bits", type=int, default=2048, help="密钥长度")

    # HTTP认证命令
    htpasswd_parser = subparsers.add_parser("htpasswd", help="创建HTTP认证用户")
    htpasswd_parser.add_argument("username", help="用户名")
    htpasswd_parser.add_argument("--password", help="密码（可选，不提供则自动生成）")

    # 导出命令
    export_parser = subparsers.add_parser("export", help="导出密钥")
    export_parser.add_argument("--output", "-o", help="输出文件名")

    # 清理命令
    cleanup_parser = subparsers.add_parser("cleanup", help="清理旧密钥备份")
    cleanup_parser.add_argument("--days", type=int, default=30, help="保留天数")

    # 生产环境设置命令
    subparsers.add_parser("setup-prod", help="设置生产环境密钥")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    manager = SecretsManager()

    try:
        if args.command == "generate":
            if args.secret:
                success = manager.generate_secret(args.secret, args.force)
            else:
                success = manager.generate_all_secrets(args.force)
            sys.exit(0 if success else 1)

        elif args.command == "list":
            manager.list_secrets()

        elif args.command == "validate":
            success = manager.validate_secrets()
            sys.exit(0 if success else 1)

        elif args.command == "rotate":
            success = manager.rotate_secret(args.secret)
            sys.exit(0 if success else 1)

        elif args.command == "ssl":
            success = manager.generate_ssl_cert(args.domain, args.days)
            sys.exit(0 if success else 1)

        elif args.command == "dhparam":
            success = manager.generate_dhparam(args.bits)
            sys.exit(0 if success else 1)

        elif args.command == "htpasswd":
            success = manager.create_htpasswd(args.username, args.password)
            sys.exit(0 if success else 1)

        elif args.command == "export":
            success = manager.export_secrets(args.output)
            sys.exit(0 if success else 1)

        elif args.command == "cleanup":
            manager.cleanup_old_secrets(args.days)

        elif args.command == "setup-prod":
            manager.setup_production_secrets()

    except KeyboardInterrupt:
        print("\n⏹️  操作已取消")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 执行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
