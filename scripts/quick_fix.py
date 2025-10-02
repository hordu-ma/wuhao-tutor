#!/usr/bin/env python3
"""
快速修复登录问题的简单脚本
创建基本的SQLite数据库和测试用户
"""

import sqlite3
import hashlib
import secrets
import uuid
from datetime import datetime
import os

def hash_password(password: str) -> str:
    """使用PBKDF2算法哈希密码"""
    salt = secrets.token_hex(16)
    password_hash = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000
    )
    return f"{salt}:{password_hash.hex()}"

def main():
    # 删除现有数据库
    db_path = "wuhao_tutor_dev.db"
    if os.path.exists(db_path):
        os.remove(db_path)
        print("✅ 已删除现有数据库")

    # 创建数据库连接
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # 创建users表 - 简化版，兼容SQLAlchemy
        cursor.execute("""
        CREATE TABLE users (
            id TEXT PRIMARY KEY,
            phone TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            wechat_openid TEXT,
            wechat_unionid TEXT,
            name TEXT NOT NULL,
            nickname TEXT,
            avatar_url TEXT,
            school TEXT,
            grade_level TEXT,
            class_name TEXT,
            institution TEXT,
            parent_contact TEXT,
            parent_name TEXT,
            role TEXT DEFAULT 'student',
            is_active INTEGER DEFAULT 1,
            is_verified INTEGER DEFAULT 1,
            study_subjects TEXT,
            study_goals TEXT,
            notification_enabled INTEGER DEFAULT 1,
            last_login_at TEXT,
            login_count INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # 创建user_sessions表 - 简化版
        cursor.execute("""
        CREATE TABLE user_sessions (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            device_id TEXT,
            device_type TEXT,
            access_token_jti TEXT NOT NULL UNIQUE,
            refresh_token_jti TEXT NOT NULL UNIQUE,
            expires_at TEXT NOT NULL,
            is_revoked INTEGER DEFAULT 0,
            ip_address TEXT,
            user_agent TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """)

        print("✅ 数据库表创建成功")

        # 创建测试用户
        current_time = datetime.utcnow().isoformat()

        test_users = [
            {
                'id': str(uuid.uuid4()),
                'phone': '13800138000',
                'password_hash': hash_password('123456'),
                'name': '测试学生',
                'nickname': '小测',
                'role': 'student',
                'school': '测试中学',
                'grade_level': 'junior_2',
                'class_name': '初二(1)班',
            },
            {
                'id': str(uuid.uuid4()),
                'phone': '13800138001',
                'password_hash': hash_password('123456'),
                'name': '测试老师',
                'nickname': '张老师',
                'role': 'teacher',
                'school': '测试中学',
            }
        ]

        for user in test_users:
            cursor.execute("""
            INSERT INTO users (
                id, phone, password_hash, name, nickname, role, school,
                grade_level, class_name, is_active, is_verified,
                notification_enabled, login_count, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 1, 1, 0, ?, ?)
            """, (
                user['id'], user['phone'], user['password_hash'],
                user['name'], user['nickname'], user['role'],
                user['school'], user.get('grade_level'), user.get('class_name'),
                current_time, current_time
            ))

        conn.commit()
        print("✅ 测试用户创建成功")
        print("📱 学生账号: 13800138000 / 123456")
        print("👨‍🏫 教师账号: 13800138001 / 123456")

    except Exception as e:
        conn.rollback()
        print(f"❌ 创建失败: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    main()
