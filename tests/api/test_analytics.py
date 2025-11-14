"""Analytics API测试模块"""

from datetime import datetime, timedelta
from typing import Any, Dict
from uuid import UUID, uuid4

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.analytics_service import AnalyticsService


class TestAnalyticsAPI:
    """Analytics API测试类"""

    @pytest_asyncio.fixture
    async def test_user_id(self) -> str:
        """创建测试用户ID"""
        return str(uuid4())

    @pytest_asyncio.fixture
    async def sample_homework_data(
        self, db_session: AsyncSession, test_user_id: str
    ) -> Dict[str, Any]:
        """创建示例作业数据"""
        # 由于我们使用的是内存数据库和Mock数据，这里返回基础结构
        return {
            "user_id": test_user_id,
            "subject": "math",
            "created_at": datetime.utcnow(),
        }

    @pytest.mark.asyncio
    async def test_get_learning_progress_success(
        self,
        test_client: TestClient,
        test_user_id: str,
        sample_homework_data: Dict[str, Any],
    ):
        """测试获取学习进度 - 成功场景"""

        # 模拟登录用户
        headers = {"Authorization": f"Bearer mock_token_{test_user_id}"}

        # 测试日粒度查询
        start_date = (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d")
        end_date = datetime.utcnow().strftime("%Y-%m-%d")

        response = test_client.get(
            f"/api/v1/analytics/learning-progress?start_date={start_date}&end_date={end_date}&granularity=daily",
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "summary" in data
        assert data["period"] == "daily"

    @pytest.mark.asyncio
    async def test_unauthorized_access(self, test_client: TestClient):
        """测试未授权访问"""

        response = test_client.get(
            "/api/v1/analytics/learning-progress?start_date=2023-01-01&end_date=2023-12-31"
        )

        assert response.status_code in [401, 403]


class TestAnalyticsService:
    """Analytics服务层测试类"""

    @pytest_asyncio.fixture
    async def analytics_service(self, db_session: AsyncSession) -> AnalyticsService:
        """创建analytics服务实例"""
        return AnalyticsService(db_session)

    @pytest_asyncio.fixture
    async def test_user_data(self) -> str:
        """创建测试用户数据"""
        return str(uuid4())

    @pytest.mark.asyncio
    async def test_get_learning_progress_empty_data(
        self, analytics_service: AnalyticsService, test_user_data: str
    ):
        """测试获取学习进度 - 空数据"""


        result = await analytics_service.get_learning_progress(
            user_id=UUID(test_user_data),
            start_date="2023-01-01",
            end_date="2023-01-31",
            granularity="daily",
        )

        assert "data" in result
        assert "summary" in result
        assert result["period"] == "daily"
        # 空数据情况下，应该返回空列表
        assert isinstance(result["data"], list)

    @pytest.mark.asyncio
    async def test_get_knowledge_points_mastery_empty(
        self, analytics_service: AnalyticsService, test_user_data: str
    ):
        """测试知识点掌握情况 - 空数据"""


        result = await analytics_service.get_knowledge_points_mastery(
            user_id=UUID(test_user_data)
        )

        assert "data" in result
        assert "summary" in result
        assert isinstance(result["data"], list)

    @pytest.mark.asyncio
    async def test_get_subject_statistics_empty(
        self, analytics_service: AnalyticsService, test_user_data: str
    ):
        """测试学科统计 - 空数据"""


        result = await analytics_service.get_subject_statistics(
            user_id=UUID(test_user_data), time_range="30d"
        )

        assert "data" in result
        assert "summary" in result
        assert isinstance(result["data"], list)
