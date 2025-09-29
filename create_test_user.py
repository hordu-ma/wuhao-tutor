#!/usr/bin/env python3
"""
创建测试用户脚本
用于开发和测试环境初始化数据库和用户
"""

import asyncio
import hashlib
import sqlite3
import uuid
from datetime import datetime
from typing import Dict, Any


def create_tables():
    """创建数据库表"""
    conn = sqlite3.connect('wuhao_tutor_dev.db')
    cursor = conn.cursor()

    # 创建用户表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            phone TEXT UNIQUE NOT NULL,
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
            is_verified INTEGER DEFAULT 0,
            study_subjects TEXT,
            study_goals TEXT,
            notification_enabled INTEGER DEFAULT 1,
            last_login_at TEXT,
            login_count INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    ''')

    # 创建用户会话表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_sessions (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            device_id TEXT,
            device_type TEXT,
            access_token_jti TEXT UNIQUE NOT NULL,
            refresh_token_jti TEXT UNIQUE NOT NULL,
            expires_at TEXT NOT NULL,
            is_revoked INTEGER DEFAULT 0,
            ip_address TEXT,
            user_agent TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    # 创建作业表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS homework (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            title TEXT NOT NULL,
            content TEXT,
            file_url TEXT,
            file_name TEXT,
            file_type TEXT,
            status TEXT DEFAULT 'pending',
            score INTEGER,
            feedback TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    conn.commit()
    conn.close()
    print("✅ 数据库表创建完成")


def hash_password(password: str) -> str:
    """使用PBKDF2对密码进行哈希"""
    import secrets
    salt = secrets.token_hex(16)
    password_hash = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000
    )
    return f"{salt}:{password_hash.hex()}"


def create_test_users():
    """创建测试用户"""
    conn = sqlite3.connect('wuhao_tutor_dev.db')
    cursor = conn.cursor()

    current_time = datetime.utcnow().isoformat()

    # 测试用户数据
    users: list[Dict[str, Any]] = [
        {
            'id': str(uuid.uuid4()),
            'phone': '13800138000',
            'password': '123456',
            'name': '测试学生',
            'role': 'student',
            'school': '测试中学',
            'grade_level': 'junior_2',
            'class_name': '初二(1)班',
        },
        {
            'id': str(uuid.uuid4()),
            'phone': '13800138001',
            'password': '123456',
            'name': '测试老师',
            'role': 'teacher',
            'school': '测试中学',
            'institution': '测试教育机构',
        },
        {
            'id': str(uuid.uuid4()),
            'phone': '13800138002',
            'password': 'admin123',
            'name': '系统管理员',
            'role': 'admin',
        }
    ]

    for user_data in users:
        password = user_data.pop('password')
        password_hash = hash_password(password)

        user_data['password_hash'] = password_hash
        user_data['is_active'] = 1
        user_data['is_verified'] = 1
        user_data['notification_enabled'] = 1
        user_data['login_count'] = 0
        user_data['created_at'] = current_time
        user_data['updated_at'] = current_time

        try:
            # 检查用户是否已存在
            cursor.execute('SELECT id FROM users WHERE phone = ?', (user_data['phone'],))
            existing_user = cursor.fetchone()

            if existing_user:
                print(f"⚠️  用户 {user_data['phone']} ({user_data['name']}) 已存在，跳过创建")
                continue

            # 插入用户数据
            columns = ', '.join(user_data.keys())
            placeholders = ', '.join(['?' for _ in user_data])
            query = f'INSERT INTO users ({columns}) VALUES ({placeholders})'

            cursor.execute(query, list(user_data.values()))
            print(f"✅ 创建用户: {user_data['name']} ({user_data['phone']}) - {user_data['role']}")

        except sqlite3.Error as e:
            print(f"❌ 创建用户失败 {user_data['name']}: {e}")

    conn.commit()
    conn.close()


def verify_users():
    """验证用户创建结果"""
    conn = sqlite3.connect('wuhao_tutor_dev.db')
    cursor = conn.cursor()

    cursor.execute('SELECT phone, name, role FROM users ORDER BY role, phone')
    users = cursor.fetchall()

    if users:
        print("\n📋 数据库中的用户:")
        print("-" * 50)
        for phone, name, role in users:
            print(f"  {phone} | {name:12} | {role}")
        print("-" * 50)
        print(f"总计: {len(users)} 个用户")
    else:
        print("❌ 没有找到用户数据")

    conn.close()


def test_password_verification():
    """测试密码验证"""
    def verify_password(password: str, password_hash: str) -> bool:
        try:
            salt, stored_hash = password_hash.split(':')
            calculated_hash = hashlib.pbkdf2_hmac(
                'sha256',
                password.encode('utf-8'),
                salt.encode('utf-8'),
                100000
            )
            return calculated_hash.hex() == stored_hash
        except ValueError:
            return False

    conn = sqlite3.connect('wuhao_tutor_dev.db')
    cursor = conn.cursor()

    # 测试第一个用户的密码
    cursor.execute('SELECT phone, password_hash FROM users WHERE phone = ?', ('13800138000',))
    result = cursor.fetchone()

    if result:
        phone, password_hash = result
        test_result = verify_password('123456', password_hash)
        print(f"\n🔐 密码验证测试:")
        print(f"  用户: {phone}")
        print(f"  测试密码: 123456")
        print(f"  验证结果: {'✅ 通过' if test_result else '❌ 失败'}")
    else:
        print("❌ 未找到测试用户")

    conn.close()


def main():
    """主函数"""
    print("🚀 开始初始化测试数据...")

    try:
        # 创建表
        create_tables()

        # 创建测试用户
        create_test_users()

        # 验证结果
        verify_users()

        # 测试密码验证
        test_password_verification()

        print("\n✅ 测试数据初始化完成!")
        print("\n📖 测试用户信息:")
        print("  学生账号: 13800138000 / 123456")
        print("  教师账号: 13800138001 / 123456")
        print("  管理员账号: 13800138002 / admin123")

    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
