"""
"""
设置用户为管理员角色
"""

import asyncio
import os
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

# 手动加载 .env.production 文件
from dotenv import load_dotenv
env_path = Path(__file__).parent.parent / '.env.production'
load_dotenv(env_path)

# 设置环境为生产环境
os.environ["ENVIRONMENT"] = "production"

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from src.core.config import get_settings
from src.models.user import User


async def set_admin_role(phone: str):
    """设置用户为管理员"""
    settings = get_settings()
    
    # 打印数据库 URL 验证（隐藏密码）
    db_url = settings.SQLALCHEMY_DATABASE_URI
    masked_url = db_url.split('@')[0].split('://')[0] + '://***:***@' + db_url.split('@')[1] if '@' in db_url else db_url
    print(f"🔗 连接数据库: {masked_url}")
    print(f"📋 环境: {os.getenv('ENVIRONMENT')}")
    
    # 创建数据库引擎和会话
    engine = create_async_engine(settings.SQLALCHEMY_DATABASE_URI, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
"""

import asyncio
import os
import sys
from pathlib import Path

# 设置环境为生产环境（必须在导入任何项目模块之前）
os.environ["ENVIRONMENT"] = "production"

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.core.config import get_settings
from src.models.user import User


async def set_admin_role(phone: str):
    """设置用户为管理员"""
    settings = get_settings()

    # 打印数据库 URL 验证（隐藏密码）
    db_url = settings.SQLALCHEMY_DATABASE_URI
    masked_url = (
        db_url.split("@")[0].split("://")[0] + "://***:***@" + db_url.split("@")[1]
        if "@" in db_url
        else db_url
    )
    print(f"🔗 连接数据库: {masked_url}")

    # 创建数据库引擎和会话
    engine = create_async_engine(settings.SQLALCHEMY_DATABASE_URI, echo=False)
    async_session = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        # 查询用户
        result = await session.execute(select(User).where(User.phone == phone))
        user = result.scalar_one_or_none()

        if not user:
            print(f"❌ 用户 {phone} 不存在")
            return False

        print(f"📋 用户信息:")
        print(f"  姓名: {user.name}")
        print(f"  手机号: {user.phone}")
        print(f"  当前角色: {user.role}")

        # 更新角色
        user.role = "admin"
        await session.commit()

        print(f"✅ 已将用户 {user.name} ({phone}) 设置为管理员")
        return True


async def main():
    if len(sys.argv) < 2:
        print("用法: python scripts/set_admin_role.py <手机号>")
        print("示例: python scripts/set_admin_role.py 13800000001")
        sys.exit(1)

    phone = sys.argv[1]
    await set_admin_role(phone)


if __name__ == "__main__":
    asyncio.run(main())
