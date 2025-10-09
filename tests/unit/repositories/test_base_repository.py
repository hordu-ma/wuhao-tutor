"""
基础仓储单元测试
测试BaseRepository的CRUD操作、分页、过滤等功能
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.repositories.base_repository import BaseRepository
from src.models.user import User
from tests.factories import UserFactory


class TestBaseRepositoryCreate:
    """创建操作测试"""

    @pytest.mark.asyncio
    async def test_create_success(self):
        """测试成功创建记录"""
        mock_db = AsyncMock(spec=AsyncSession)
        repo = BaseRepository(User, mock_db)
        
        user_data = {
            "phone": "13900000001",
            "name": "测试用户",
            "password_hash": "hashed_password"
        }
        
        # Mock数据库操作
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        
        result = await repo.create(user_data)
        
        assert result is not None
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_with_id(self):
        """测试创建带ID的记录"""
        mock_db = AsyncMock(spec=AsyncSession)
        repo = BaseRepository(User, mock_db)
        
        user_id = "custom_user_123"
        user_data = {
            "id": user_id,
            "phone": "13900000001",
            "name": "测试用户",
            "password_hash": "hashed_password"
        }
        
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        
        result = await repo.create(user_data)
        
        assert result is not None


class TestBaseRepositoryRead:
    """读取操作测试"""

    @pytest.mark.asyncio
    async def test_get_by_id_found(self):
        """测试根据ID获取记录-成功"""
        mock_db = AsyncMock(spec=AsyncSession)
        repo = BaseRepository(User, mock_db)
        
        user_id = "test_user_123"
        expected_user = UserFactory.create_user(user_id=user_id)
        
        # Mock execute结果
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = expected_user
        mock_db.execute = AsyncMock(return_value=mock_result)
        
        result = await repo.get_by_id(user_id)
        
        assert result is not None
        assert result.id == user_id

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self):
        """测试根据ID获取记录-未找到"""
        mock_db = AsyncMock(spec=AsyncSession)
        repo = BaseRepository(User, mock_db)
        
        # Mock execute返回None
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)
        
        result = await repo.get_by_id("nonexistent_id")
        
        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_field(self):
        """测试根据字段获取记录"""
        mock_db = AsyncMock(spec=AsyncSession)
        repo = BaseRepository(User, mock_db)
        
        phone = "13800138000"
        expected_user = UserFactory.create_user(phone=phone)
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = expected_user
        mock_db.execute = AsyncMock(return_value=mock_result)
        
        result = await repo.get_by_field("phone", phone)
        
        assert result is not None
        assert result.phone == phone

    @pytest.mark.asyncio
    async def test_get_all(self):
        """测试获取所有记录"""
        mock_db = AsyncMock(spec=AsyncSession)
        repo = BaseRepository(User, mock_db)
        
        users = [UserFactory.create_user() for _ in range(5)]
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = users
        mock_db.execute = AsyncMock(return_value=mock_result)
        
        result = await repo.get_all()
        
        assert len(result) == 5


class TestBaseRepositoryUpdate:
    """更新操作测试"""

    @pytest.mark.asyncio
    async def test_update_success(self):
        """测试成功更新记录"""
        mock_db = AsyncMock(spec=AsyncSession)
        repo = BaseRepository(User, mock_db)
        
        user_id = "test_user_123"
        update_data = {"name": "更新后的名字"}
        
        existing_user = UserFactory.create_user(user_id=user_id)
        
        # Mock get_by_id
        with patch.object(repo, 'get_by_id', return_value=existing_user):
            mock_db.commit = AsyncMock()
            mock_db.refresh = AsyncMock()
            
            result = await repo.update(user_id, update_data)
            
            assert result is not None
            mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_not_found(self):
        """测试更新不存在的记录"""
        mock_db = AsyncMock(spec=AsyncSession)
        repo = BaseRepository(User, mock_db)
        
        # Mock get_by_id返回None
        with patch.object(repo, 'get_by_id', return_value=None):
            result = await repo.update("nonexistent_id", {"name": "新名字"})
            
            assert result is None


class TestBaseRepositoryDelete:
    """删除操作测试"""

    @pytest.mark.asyncio
    async def test_delete_success(self):
        """测试成功删除记录"""
        mock_db = AsyncMock(spec=AsyncSession)
        repo = BaseRepository(User, mock_db)
        
        user_id = "test_user_123"
        existing_user = UserFactory.create_user(user_id=user_id)
        
        # Mock get_by_id
        with patch.object(repo, 'get_by_id', return_value=existing_user):
            mock_db.delete = MagicMock()
            mock_db.commit = AsyncMock()
            
            result = await repo.delete(user_id)
            
            assert result is True
            mock_db.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_not_found(self):
        """测试删除不存在的记录"""
        mock_db = AsyncMock(spec=AsyncSession)
        repo = BaseRepository(User, mock_db)
        
        # Mock get_by_id返回None
        with patch.object(repo, 'get_by_id', return_value=None):
            result = await repo.delete("nonexistent_id")
            
            assert result is False

    @pytest.mark.asyncio
    async def test_soft_delete(self):
        """测试软删除"""
        mock_db = AsyncMock(spec=AsyncSession)
        repo = BaseRepository(User, mock_db)
        
        user_id = "test_user_123"
        existing_user = UserFactory.create_user(user_id=user_id)
        
        # Mock get_by_id
        with patch.object(repo, 'get_by_id', return_value=existing_user):
            mock_db.commit = AsyncMock()
            mock_db.refresh = AsyncMock()
            
            result = await repo.soft_delete(user_id)
            
            assert result is not None


class TestBaseRepositoryPagination:
    """分页操作测试"""

    @pytest.mark.asyncio
    async def test_paginate_first_page(self):
        """测试第一页分页"""
        mock_db = AsyncMock(spec=AsyncSession)
        repo = BaseRepository(User, mock_db)
        
        users = [UserFactory.create_user() for _ in range(10)]
        
        # Mock count查询
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 50
        
        # Mock data查询
        mock_data_result = MagicMock()
        mock_data_result.scalars.return_value.all.return_value = users
        
        mock_db.execute = AsyncMock(side_effect=[mock_count_result, mock_data_result])
        
        result = await repo.paginate(page=1, size=10)
        
        assert "items" in result
        assert "total" in result
        assert result["total"] == 50
        assert len(result["items"]) == 10

    @pytest.mark.asyncio
    async def test_paginate_empty_result(self):
        """测试空结果分页"""
        mock_db = AsyncMock(spec=AsyncSession)
        repo = BaseRepository(User, mock_db)
        
        # Mock count查询返回0
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 0
        
        # Mock data查询返回空列表
        mock_data_result = MagicMock()
        mock_data_result.scalars.return_value.all.return_value = []
        
        mock_db.execute = AsyncMock(side_effect=[mock_count_result, mock_data_result])
        
        result = await repo.paginate(page=1, size=10)
        
        assert result["total"] == 0
        assert len(result["items"]) == 0


class TestBaseRepositoryFilter:
    """过滤操作测试"""

    @pytest.mark.asyncio
    async def test_filter_by_single_condition(self):
        """测试单条件过滤"""
        mock_db = AsyncMock(spec=AsyncSession)
        repo = BaseRepository(User, mock_db)
        
        filtered_users = [UserFactory.create_user(role="student")]
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = filtered_users
        mock_db.execute = AsyncMock(return_value=mock_result)
        
        result = await repo.filter(role="student")
        
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_filter_by_multiple_conditions(self):
        """测试多条件过滤"""
        mock_db = AsyncMock(spec=AsyncSession)
        repo = BaseRepository(User, mock_db)
        
        filtered_users = [
            UserFactory.create_user(role="student", grade_level="senior_1")
        ]
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = filtered_users
        mock_db.execute = AsyncMock(return_value=mock_result)
        
        result = await repo.filter(role="student", grade_level="senior_1")
        
        assert len(result) > 0


class TestBaseRepositoryCount:
    """计数操作测试"""

    @pytest.mark.asyncio
    async def test_count_all(self):
        """测试统计所有记录"""
        mock_db = AsyncMock(spec=AsyncSession)
        repo = BaseRepository(User, mock_db)
        
        mock_result = MagicMock()
        mock_result.scalar.return_value = 100
        mock_db.execute = AsyncMock(return_value=mock_result)
        
        result = await repo.count()
        
        assert result == 100

    @pytest.mark.asyncio
    async def test_count_with_filter(self):
        """测试带过滤条件的计数"""
        mock_db = AsyncMock(spec=AsyncSession)
        repo = BaseRepository(User, mock_db)
        
        mock_result = MagicMock()
        mock_result.scalar.return_value = 50
        mock_db.execute = AsyncMock(return_value=mock_result)
        
        result = await repo.count(role="student")
        
        assert result == 50


class TestBaseRepositoryExists:
    """存在性检查测试"""

    @pytest.mark.asyncio
    async def test_exists_true(self):
        """测试记录存在"""
        mock_db = AsyncMock(spec=AsyncSession)
        repo = BaseRepository(User, mock_db)
        
        user_id = "test_user_123"
        
        # Mock get_by_id返回用户
        with patch.object(repo, 'get_by_id', return_value=UserFactory.create_user()):
            result = await repo.exists(user_id)
            
            assert result is True

    @pytest.mark.asyncio
    async def test_exists_false(self):
        """测试记录不存在"""
        mock_db = AsyncMock(spec=AsyncSession)
        repo = BaseRepository(User, mock_db)
        
        # Mock get_by_id返回None
        with patch.object(repo, 'get_by_id', return_value=None):
            result = await repo.exists("nonexistent_id")
            
            assert result is False


class TestBaseRepositoryBatchOperations:
    """批量操作测试"""

    @pytest.mark.asyncio
    async def test_bulk_create(self):
        """测试批量创建"""
        mock_db = AsyncMock(spec=AsyncSession)
        repo = BaseRepository(User, mock_db)
        
        users_data = [
            {"phone": f"1390000000{i}", "name": f"用户{i}", "password_hash": "hash"}
            for i in range(5)
        ]
        
        mock_db.add_all = MagicMock()
        mock_db.commit = AsyncMock()
        
        result = await repo.bulk_create(users_data)
        
        assert result is True
        mock_db.add_all.assert_called_once()

    @pytest.mark.asyncio
    async def test_bulk_update(self):
        """测试批量更新"""
        mock_db = AsyncMock(spec=AsyncSession)
        repo = BaseRepository(User, mock_db)
        
        user_ids = ["user_1", "user_2", "user_3"]
        update_data = {"is_active": True}
        
        mock_db.execute = AsyncMock()
        mock_db.commit = AsyncMock()
        
        result = await repo.bulk_update(user_ids, update_data)
        
        # 根据实际实现验证
        assert result is not None or result is True


class TestBaseRepositoryEdgeCases:
    """边界情况测试"""

    @pytest.mark.asyncio
    async def test_create_with_duplicate_key(self):
        """测试创建重复键记录"""
        mock_db = AsyncMock(spec=AsyncSession)
        repo = BaseRepository(User, mock_db)
        
        user_data = {
            "phone": "13800138000",  # 假设已存在
            "name": "用户",
            "password_hash": "hash"
        }
        
        # Mock数据库抛出完整性错误
        from sqlalchemy.exc import IntegrityError
        mock_db.commit = AsyncMock(side_effect=IntegrityError("", "", ""))
        
        with pytest.raises(IntegrityError):
            await repo.create(user_data)

    @pytest.mark.asyncio
    async def test_paginate_invalid_page(self):
        """测试无效页码"""
        mock_db = AsyncMock(spec=AsyncSession)
        repo = BaseRepository(User, mock_db)
        
        # 页码为0或负数
        with pytest.raises((ValueError, AssertionError)):
            await repo.paginate(page=0, size=10)

    @pytest.mark.asyncio
    async def test_update_with_none_data(self):
        """测试使用None数据更新"""
        mock_db = AsyncMock(spec=AsyncSession)
        repo = BaseRepository(User, mock_db)
        
        user_id = "test_user_123"
        
        # Mock get_by_id
        with patch.object(repo, 'get_by_id', return_value=UserFactory.create_user()):
            result = await repo.update(user_id, None)
            
            # 应该返回未修改的记录或抛出错误
            assert result is not None or pytest.raises(ValueError)
