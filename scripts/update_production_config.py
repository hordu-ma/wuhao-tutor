#!/usr/bin/env python3
"""
生产环境配置更新脚本
更新现有配置文件中的占位符，生成真实的安全密钥
"""

import os
import re
import secrets
import string
from pathlib import Path


def generate_random_string(length: int = 32) -> str:
    """生成随机字符串"""
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def generate_jwt_secret() -> str:
    """生成JWT密钥"""
    return secrets.token_urlsafe(64)


def generate_password(length: int = 20) -> str:
    """生成强密码"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    password = "".join(secrets.choice(alphabet) for _ in range(length))
    return password


def generate_api_key() -> str:
    """生成API密钥"""
    return secrets.token_urlsafe(32)


def update_env_file(file_path: Path, replacements: dict) -> None:
    """更新环境配置文件"""
    if not file_path.exists():
        print(f"❌ 文件不存在: {file_path}")
        return

    content = file_path.read_text()
    original_content = content

    # 替换占位符
    for placeholder, real_value in replacements.items():
        content = content.replace(placeholder, real_value)

    # 如果内容有变化，则写入文件
    if content != original_content:
        # 备份原文件
        backup_path = file_path.with_suffix(file_path.suffix + ".backup")
        file_path.rename(backup_path)
        print(f"📝 备份原文件: {backup_path}")

        # 写入新文件
        file_path.write_text(content)
        os.chmod(file_path, 0o600)  # 设置安全权限
        print(f"✅ 更新配置文件: {file_path}")
    else:
        print(f"⏭️  无需更新: {file_path}")


def update_secrets_files(secrets_dir: Path, secrets_data: dict) -> None:
    """更新secrets目录中的密钥文件"""
    secrets_dir.mkdir(exist_ok=True)

    for filename, secret_value in secrets_data.items():
        file_path = secrets_dir / filename
        if not file_path.exists() or file_path.stat().st_size == 0:
            file_path.write_text(secret_value)
            os.chmod(file_path, 0o600)
            print(f"✅ 生成密钥文件: {file_path}")
        else:
            print(f"⏭️  密钥文件已存在: {file_path}")


def main():
    """主函数"""
    print("🔐 开始更新生产环境配置...")

    # 生成所有需要的密钥
    postgres_password = generate_password(24)
    redis_password = generate_password(20)
    jwt_secret = generate_jwt_secret()
    api_key = generate_api_key()
    encryption_key = generate_random_string(32)
    grafana_password = generate_password(16)

    # 定义占位符和实际值的映射
    replacements = {
        "CHANGE_ME_STRONG_PASSWORD": postgres_password,
        "CHANGE_ME_REDIS_PASSWORD": redis_password,
        "sA4bppW1-GYLPbhvouQESXDxBtOD06kuDyupLU7ll9GAeGhaAFp35sjN2F5GB14rRTCqmTvTkXYDeMvcBaFOaQ": jwt_secret,
        "CHANGE_ME_ACCESS_KEY_ID": "your_alicloud_access_key_id_here",
        "CHANGE_ME_ACCESS_KEY_SECRET": "your_alicloud_access_key_secret_here",
        "CHANGE_ME_OSS_ACCESS_KEY": "your_oss_access_key_id_here",
        "CHANGE_ME_OSS_SECRET_KEY": "your_oss_access_key_secret_here",
        "CHANGE_ME_SMS_ACCESS_KEY": "your_sms_access_key_id_here",
        "CHANGE_ME_SMS_SECRET_KEY": "your_sms_access_key_secret_here",
        "CHANGE_ME_WECHAT_APP_ID": "your_wechat_app_id_here",
        "CHANGE_ME_WECHAT_APP_SECRET": "your_wechat_app_secret_here",
        "CHANGE_ME_MINI_PROGRAM_APP_ID": "your_mini_program_app_id_here",
        "CHANGE_ME_MINI_PROGRAM_SECRET": "your_mini_program_app_secret_here",
        "CHANGE_ME_YOUR_APPLICATION_ID": "your_bailian_application_id_here",
        "sk-CHANGE_ME_YOUR_API_KEY": "your_bailian_api_key_here",
    }

    project_root = Path(__file__).parent.parent

    # 更新环境配置文件
    env_files = [".env.docker.production", ".env.prod"]

    for env_file in env_files:
        file_path = project_root / env_file
        update_env_file(file_path, replacements)

    # 更新secrets目录中的密钥文件
    secrets_dir = project_root / "secrets"
    secrets_data = {
        "jwt_secret.txt": jwt_secret,
        "postgres_password.txt": postgres_password,
        "redis_password.txt": redis_password,
        "grafana_password.txt": grafana_password,
        "api_key.txt": api_key,
        "encryption_key.txt": encryption_key,
    }

    update_secrets_files(secrets_dir, secrets_data)

    print("\\n🎉 配置更新完成！")
    print("\\n⚠️  重要提醒:")
    print("1. 原配置文件已备份为 .backup 后缀")
    print("2. 请手动填入以下阿里云配置:")
    print("   - BAILIAN_APPLICATION_ID 和 BAILIAN_API_KEY")
    print("   - ALICLOUD_ACCESS_KEY_ID 和 ALICLOUD_ACCESS_KEY_SECRET")
    print("   - OSS相关配置")
    print("   - 微信小程序配置（如果使用）")
    print("3. 生产环境部署前请验证所有配置")
    print("\\n📝 生成的密钥:")
    print(f"   数据库密码: {postgres_password}")
    print(f"   Redis密码: {redis_password}")
    print(f"   JWT密钥: {jwt_secret[:20]}...")
    print(f"   Grafana密码: {grafana_password}")


if __name__ == "__main__":
    main()
