#!/usr/bin/env python3
"""
直接创建用户脚本（非交互式）
用于快速创建指定用户
"""
import asyncio
import secrets
import string
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.core.config import get_settings
from src.services.user_service import UserService


def generate_secure_password(length: int = 10) -> str:
    """生成安全的随机密码（包含大写、小写和数字）"""
    while True:
        password = "".join(
            secrets.choice(string.ascii_letters + string.digits) for _ in range(length)
        )
        
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        
        if has_upper and has_lower and has_digit:
            return password


async def create_user_direct():
    """直接创建用户"""
    phone = "15662660599"
    name = "李国马"  # 可以修改姓名
    
    # 加载生产环境配置
    load_dotenv(".env.production")
    settings = get_settings()
    database_url = settings.SQLALCHEMY_DATABASE_URI
    
    print(f"🔧 连接数据库: {database_url.split('@')[-1]}")  # 只显示数据库地址部分
    
    engine = create_async_engine(database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    try:
        async with async_session() as session:
            user_service = UserService(session)
            
            # 检查手机号是否已存在
            try:
                existing_user = await user_service.user_repo.get_by_field("phone", phone)
                if existing_user:
                    print(f"❌ 手机号 {phone} 已存在")
                    print(f"   用户ID: {existing_user.id}")
                    print(f"   姓名: {existing_user.name}")
                    print(f"   状态: {'激活' if existing_user.is_active else '未激活'}")
                    return
            except Exception as e:
                print(f"⚠️  检查用户时出错: {str(e)}")
            
            # 生成密码
            password = generate_secure_password(10)
            
            # 创建用户
            password_hash = user_service._hash_password(password)
            
            user_data = {
                "phone": phone,
                "password_hash": password_hash,
                "name": name,
                "nickname": name,
                "role": "student",
                "is_active": True,
                "is_verified": True,
                "login_count": 0,
            }
            
            user = await user_service.user_repo.create(user_data)
            
            print("\n" + "=" * 60)
            print("✅ 用户账号创建成功！")
            print("=" * 60)
            print(f"👤 用户ID: {user.id}")
            print(f"📱 手机号: {user.phone}")
            print(f"👤 姓名: {user.name}")
            print(f"🔐 密码: {password}")
            print(f"📧 角色: {user.role}")
            print(f"✅ 状态: {'激活' if user.is_active else '未激活'}")
            print(f"📅 创建时间: {user.created_at}")
            print("=" * 60)
            
    except Exception as e:
        print(f"❌ 创建用户失败: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(create_user_direct())
