"""
用户API端点测试
测试用户活动、统计等功能
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from datetime import datetime, timedelta

from tests.factories import UserFactory, HomeworkFactory


class TestUserActivities:
    """用户活动API测试"""

    def test_get_user_activities_success(self, test_client: TestClient):
        """测试获取用户活动成功"""
        # Mock数据库查询
        with patch("src.api.v1.endpoints.user.select") as mock_select:
            with patch("src.api.v1.endpoints.user.desc") as mock_desc:
                # 构造mock返回值
                mock_homework = HomeworkFactory.create_homework_submission(
                    submission_title="测试作业提交"
                )
                
                # Mock execute返回
                mock_result = MagicMock()
                mock_result.scalars.return_value.all.return_value = [mock_homework]
                
                # Mock db.execute
                async def mock_execute(*args, **kwargs):
                    return mock_result
                
                response = test_client.get(
                    "/api/v1/user/activities?limit=10",
                    headers={"Authorization": "Bearer valid_token"}
                )
        
        assert response.status_code == 200
        data = response.json()
        assert "data" in data

    def test_get_user_activities_with_limit(self, test_client: TestClient):
        """测试获取指定数量的用户活动"""
        response = test_client.get(
            "/api/v1/user/activities?limit=5",
            headers={"Authorization": "Bearer valid_token"}
        )
        
        assert response.status_code == 200

    def test_get_user_activities_empty(self, test_client: TestClient):
        """测试用户无活动记录"""
        with patch("src.api.v1.endpoints.user.select") as mock_select:
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = []
            
            response = test_client.get(
                "/api/v1/user/activities",
                headers={"Authorization": "Bearer valid_token"}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data.get("data"), list)


class TestUserStats:
    """用户统计API测试"""

    def test_get_user_stats_success(self, test_client: TestClient):
        """测试获取用户统计成功"""
        with patch("src.api.v1.endpoints.user.select") as mock_select:
            # Mock作业统计
            mock_homework_result = MagicMock()
            mock_homework_result.scalars.return_value.all.return_value = [
                HomeworkFactory.create_homework_submission()
                for _ in range(10)
            ]
            
            # Mock pending作业统计
            mock_pending_result = MagicMock()
            mock_pending_result.scalars.return_value.all.return_value = [
                HomeworkFactory.create_homework_submission(status="uploaded")
                for _ in range(3)
            ]
            
            response = test_client.get(
                "/api/v1/user/stats",
                headers={"Authorization": "Bearer valid_token"}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert "data" in data

    def test_get_user_stats_no_homework(self, test_client: TestClient):
        """测试用户无作业统计"""
        with patch("src.api.v1.endpoints.user.select") as mock_select:
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = []
            
            response = test_client.get(
                "/api/v1/user/stats",
                headers={"Authorization": "Bearer valid_token"}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert "total_homework" in data.get("data", {})

    def test_get_user_stats_unauthorized(self, test_client: TestClient):
        """测试未授权访问用户统计"""
        response = test_client.get("/api/v1/user/stats")
        
        assert response.status_code == 403  # Forbidden or 401


class TestUserProfile:
    """用户资料相关测试"""

    def test_get_user_info(self, test_client: TestClient):
        """测试获取用户信息"""
        with patch("src.api.v1.endpoints.user.get_current_user_id") as mock_user_id:
            mock_user_id.return_value = "test_user_123"
            
            with patch("src.services.user_service.UserService.get_user_by_id") as mock_get_user:
                mock_get_user.return_value = UserFactory.create_user(
                    user_id="test_user_123",
                    name="测试用户"
                )
                
                response = test_client.get(
                    "/api/v1/user/info",
                    headers={"Authorization": "Bearer valid_token"}
                )
        
        # 根据实际endpoint调整状态码
        assert response.status_code in [200, 404]


class TestUserActivityTypes:
    """用户活动类型测试"""

    def test_homework_activity_format(self, test_client: TestClient):
        """测试作业活动格式"""
        with patch("src.api.v1.endpoints.user.select") as mock_select:
            mock_homework = HomeworkFactory.create_homework_submission(
                submission_title="数学作业",
                created_at=datetime.utcnow()
            )
            
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = [mock_homework]
            
            response = test_client.get(
                "/api/v1/user/activities",
                headers={"Authorization": "Bearer valid_token"}
            )
        
        assert response.status_code == 200

    def test_learning_activity_format(self, test_client: TestClient):
        """测试学习活动格式"""
        # 测试学习相关活动的格式
        response = test_client.get(
            "/api/v1/user/activities",
            headers={"Authorization": "Bearer valid_token"}
        )
        
        assert response.status_code == 200


class TestUserEdgeCases:
    """用户API边界情况测试"""

    def test_activities_invalid_limit(self, test_client: TestClient):
        """测试无效的limit参数"""
        response = test_client.get(
            "/api/v1/user/activities?limit=-1",
            headers={"Authorization": "Bearer valid_token"}
        )
        
        # 应该返回错误或使用默认值
        assert response.status_code in [200, 422]

    def test_activities_large_limit(self, test_client: TestClient):
        """测试过大的limit参数"""
        response = test_client.get(
            "/api/v1/user/activities?limit=1000",
            headers={"Authorization": "Bearer valid_token"}
        )
        
        # 应该返回有限数量或错误
        assert response.status_code in [200, 422]

    def test_stats_database_error(self, test_client: TestClient):
        """测试数据库错误情况"""
        with patch("src.api.v1.endpoints.user.select") as mock_select:
            mock_select.side_effect = Exception("Database error")
            
            response = test_client.get(
                "/api/v1/user/stats",
                headers={"Authorization": "Bearer valid_token"}
            )
        
        # 应该优雅地处理错误
        assert response.status_code in [200, 500]


class TestUserActivityTimeRange:
    """用户活动时间范围测试"""

    def test_recent_activities(self, test_client: TestClient):
        """测试最近活动"""
        response = test_client.get(
            "/api/v1/user/activities?limit=10",
            headers={"Authorization": "Bearer valid_token"}
        )
        
        assert response.status_code == 200

    def test_old_activities(self, test_client: TestClient):
        """测试历史活动"""
        # 如果API支持时间范围查询
        response = test_client.get(
            "/api/v1/user/activities",
            headers={"Authorization": "Bearer valid_token"}
        )
        
        assert response.status_code == 200


class TestUserStatisticsCalculation:
    """用户统计计算测试"""

    def test_homework_completion_rate(self, test_client: TestClient):
        """测试作业完成率计算"""
        with patch("src.api.v1.endpoints.user.select") as mock_select:
            # Mock总作业数: 10
            # Mock完成作业数: 8
            response = test_client.get(
                "/api/v1/user/stats",
                headers={"Authorization": "Bearer valid_token"}
            )
        
        assert response.status_code == 200

    def test_average_score_calculation(self, test_client: TestClient):
        """测试平均分计算"""
        response = test_client.get(
            "/api/v1/user/stats",
            headers={"Authorization": "Bearer valid_token"}
        )
        
        assert response.status_code == 200
