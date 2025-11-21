"""
基础仓储模块
提供通用的数据访问层基类和方法
"""

from typing import Any, Dict, Generic, List, Optional, Type, TypeVar
from uuid import uuid4

from sqlalchemy import and_, delete, func, or_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase

from src.core.logging import get_logger

logger = get_logger(__name__)

# 泛型类型变量
ModelType = TypeVar("ModelType", bound=DeclarativeBase)


class BaseRepository(Generic[ModelType]):
    """
    基础仓储类
    提供通用的CRUD操作和查询方法
    """

    def __init__(self, model: Type[ModelType], db: AsyncSession):
        """
        初始化仓储

        Args:
            model: SQLAlchemy模型类
            db: 异步数据库会话
        """
        self.model = model
        self.db = db

    async def create(self, data: Dict[str, Any]) -> ModelType:
        """
        创建新记录

        Args:
            data: 创建数据

        Returns:
            创建的模型实例

        Raises:
            IntegrityError: 数据完整性约束违反
        """
        try:
            # 如果没有ID，生成UUID
            if hasattr(self.model, "id") and "id" not in data:
                data["id"] = str(uuid4())

            instance = self.model(**data)
            self.db.add(instance)
            await self.db.commit()
            await self.db.refresh(instance)

            logger.debug(
                f"Created {self.model.__name__} with id: {getattr(instance, 'id', 'N/A')}"
            )
            return instance

        except IntegrityError as e:
            await self.db.rollback()
            logger.error(f"Integrity error creating {self.model.__name__}: {e}")
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating {self.model.__name__}: {e}")
            raise

    async def get_by_id(self, record_id: str) -> Optional[ModelType]:
        """
        根据ID获取记录

        Args:
            record_id: 记录ID

        Returns:
            模型实例或None
        """
        try:
            stmt = select(self.model).where(self.model.id == record_id)
            result = await self.db.execute(stmt)
            instance = result.scalar_one_or_none()

            if instance:
                logger.debug(f"Found {self.model.__name__} with id: {record_id}")
            else:
                logger.debug(f"No {self.model.__name__} found with id: {record_id}")

            return instance

        except Exception as e:
            logger.error(f"Error getting {self.model.__name__} by id {record_id}: {e}")
            raise

    async def get_by_field(self, field: str, value: Any) -> Optional[ModelType]:
        """
        根据字段值获取记录

        Args:
            field: 字段名
            value: 字段值

        Returns:
            模型实例或None
        """
        try:
            field_attr = getattr(self.model, field)
            stmt = select(self.model).where(field_attr == value)
            result = await self.db.execute(stmt)
            instance = result.scalar_one_or_none()

            if instance:
                logger.debug(f"Found {self.model.__name__} with {field}: {value}")
            else:
                logger.debug(f"No {self.model.__name__} found with {field}: {value}")

            return instance

        except Exception as e:
            logger.error(f"Error getting {self.model.__name__} by {field}={value}: {e}")
            raise

    async def get_all(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        order_by: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[ModelType]:
        """
        获取所有记录

        Args:
            limit: 限制数量
            offset: 偏移量
            order_by: 排序字段
            filters: 过滤条件

        Returns:
            模型实例列表
        """
        try:
            stmt = select(self.model)

            # 应用过滤条件
            if filters:
                conditions = []
                for field, value in filters.items():
                    field_attr = getattr(self.model, field)
                    if isinstance(value, list):
                        conditions.append(field_attr.in_(value))
                    else:
                        conditions.append(field_attr == value)
                if conditions:
                    stmt = stmt.where(and_(*conditions))

            # 应用排序
            if order_by:
                if order_by.startswith("-"):
                    # 降序
                    order_field = order_by[1:]
                    field_attr = getattr(self.model, order_field)
                    stmt = stmt.order_by(field_attr.desc())
                else:
                    # 升序
                    field_attr = getattr(self.model, order_by)
                    stmt = stmt.order_by(field_attr.asc())

            # 应用分页
            if offset:
                stmt = stmt.offset(offset)
            if limit:
                stmt = stmt.limit(limit)

            result = await self.db.execute(stmt)
            instances = result.scalars().all()

            logger.debug(f"Found {len(instances)} {self.model.__name__} records")
            return list(instances)

        except Exception as e:
            logger.error(f"Error getting all {self.model.__name__}: {e}")
            raise

    async def update(self, record_id: str, data: Dict[str, Any]) -> Optional[ModelType]:
        """
        更新记录

        Args:
            record_id: 记录ID
            data: 更新数据

        Returns:
            更新后的模型实例或None
        """
        try:
            stmt = (
                update(self.model)
                .where(self.model.id == record_id)
                .values(**data)
                .returning(self.model)
            )

            result = await self.db.execute(stmt)
            await self.db.commit()

            instance = result.scalar_one_or_none()
            if instance:
                await self.db.refresh(instance)
                logger.debug(f"Updated {self.model.__name__} with id: {record_id}")
            else:
                logger.debug(
                    f"No {self.model.__name__} found to update with id: {record_id}"
                )

            return instance

        except IntegrityError as e:
            await self.db.rollback()
            logger.error(f"Integrity error updating {self.model.__name__}: {e}")
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(
                f"Error updating {self.model.__name__} with id {record_id}: {e}"
            )
            raise

    async def delete(self, record_id: str) -> bool:
        """
        删除记录

        Args:
            record_id: 记录ID

        Returns:
            是否删除成功
        """
        try:
            stmt = delete(self.model).where(self.model.id == record_id)
            result = await self.db.execute(stmt)
            await self.db.commit()

            deleted = result.rowcount > 0
            if deleted:
                logger.debug(f"Deleted {self.model.__name__} with id: {record_id}")
            else:
                logger.debug(
                    f"No {self.model.__name__} found to delete with id: {record_id}"
                )

            return deleted

        except Exception as e:
            await self.db.rollback()
            logger.error(
                f"Error deleting {self.model.__name__} with id {record_id}: {e}"
            )
            raise

    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        统计记录数量

        Args:
            filters: 过滤条件

        Returns:
            记录数量
        """
        try:
            stmt = select(func.count(self.model.id))

            # 应用过滤条件
            if filters:
                conditions = []
                for field, value in filters.items():
                    field_attr = getattr(self.model, field)
                    if isinstance(value, list):
                        conditions.append(field_attr.in_(value))
                    else:
                        conditions.append(field_attr == value)
                if conditions:
                    stmt = stmt.where(and_(*conditions))

            result = await self.db.execute(stmt)
            count = result.scalar()

            logger.debug(f"Counted {count} {self.model.__name__} records")
            return count or 0

        except Exception as e:
            logger.error(f"Error counting {self.model.__name__}: {e}")
            raise

    async def exists(self, record_id: str) -> bool:
        """
        检查记录是否存在

        Args:
            record_id: 记录ID

        Returns:
            是否存在
        """
        try:
            stmt = select(func.count(self.model.id)).where(self.model.id == record_id)
            result = await self.db.execute(stmt)
            count = result.scalar()

            exists = (count or 0) > 0
            logger.debug(f"{self.model.__name__} with id {record_id} exists: {exists}")

            return exists

        except Exception as e:
            logger.error(
                f"Error checking if {self.model.__name__} exists with id {record_id}: {e}"
            )
            raise

    async def bulk_create(self, data_list: List[Dict[str, Any]]) -> List[ModelType]:
        """
        批量创建记录

        Args:
            data_list: 创建数据列表

        Returns:
            创建的模型实例列表
        """
        try:
            instances = []
            for data in data_list:
                # 如果没有ID，生成UUID
                if hasattr(self.model, "id") and "id" not in data:
                    data["id"] = str(uuid4())
                instances.append(self.model(**data))

            self.db.add_all(instances)
            await self.db.commit()

            # 刷新所有实例
            for instance in instances:
                await self.db.refresh(instance)

            logger.debug(f"Bulk created {len(instances)} {self.model.__name__} records")
            return instances

        except IntegrityError as e:
            await self.db.rollback()
            logger.error(f"Integrity error bulk creating {self.model.__name__}: {e}")
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error bulk creating {self.model.__name__}: {e}")
            raise

    async def bulk_update(self, updates: List[Dict[str, Any]]) -> int:
        """
        批量更新记录

        Args:
            updates: 更新数据列表，每个字典必须包含'id'字段

        Returns:
            更新的记录数量
        """
        try:
            updated_count = 0
            for update_data in updates:
                record_id = update_data.pop("id")
                stmt = (
                    update(self.model)
                    .where(self.model.id == record_id)
                    .values(**update_data)
                )

                result = await self.db.execute(stmt)
                updated_count += result.rowcount

            await self.db.commit()
            logger.debug(f"Bulk updated {updated_count} {self.model.__name__} records")
            return updated_count

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error bulk updating {self.model.__name__}: {e}")
            raise

    async def bulk_delete(self, record_ids: List[str]) -> int:
        """
        批量删除记录

        Args:
            record_ids: 记录ID列表

        Returns:
            删除的记录数量
        """
        try:
            stmt = delete(self.model).where(self.model.id.in_(record_ids))
            result = await self.db.execute(stmt)
            await self.db.commit()

            deleted_count = result.rowcount
            logger.debug(f"Bulk deleted {deleted_count} {self.model.__name__} records")
            return deleted_count

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error bulk deleting {self.model.__name__}: {e}")
            raise

    async def search(
        self,
        search_term: str,
        search_fields: List[str],
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[ModelType]:
        """
        搜索记录

        Args:
            search_term: 搜索词
            search_fields: 搜索字段列表
            limit: 限制数量
            offset: 偏移量

        Returns:
            匹配的模型实例列表
        """
        try:
            conditions = []
            for field in search_fields:
                field_attr = getattr(self.model, field)
                conditions.append(field_attr.ilike(f"%{search_term}%"))

            stmt = select(self.model).where(or_(*conditions))

            if offset:
                stmt = stmt.offset(offset)
            if limit:
                stmt = stmt.limit(limit)

            result = await self.db.execute(stmt)
            instances = result.scalars().all()

            logger.debug(f"Search found {len(instances)} {self.model.__name__} records")
            return list(instances)

        except Exception as e:
            logger.error(f"Error searching {self.model.__name__}: {e}")
            raise
