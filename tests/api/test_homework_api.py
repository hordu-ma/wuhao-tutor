"""
作业API端点测试
测试作业模板、提交、批改等功能
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from io import BytesIO

from tests.factories import HomeworkFactory, UserFactory, RequestFactory


class TestHomeworkHealth:
    """作业模块健康检查测试"""

    def test_homework_health_check(self, test_client: TestClient):
        """测试作业模块健康检查"""
        response = test_client.get("/api/v1/homework/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["module"] == "homework"


class TestHomeworkTemplates:
    """作业模板API测试"""

    def test_create_template_success(self, test_client: TestClient):
        """测试创建作业模板成功"""
        template_data = {
            "title": "数学练习题",
            "subject": "math",
            "homework_type": "daily",
            "difficulty": "medium",
            "description": "这是一个测试作业模板"
        }
        
        with patch("src.api.v1.endpoints.homework.HomeworkService") as mock_service:
            mock_instance = MagicMock()
            mock_homework = HomeworkFactory.create_homework(**template_data)
            mock_instance.create_homework_template = AsyncMock(return_value=mock_homework)
            mock_service.return_value = mock_instance
            
            response = test_client.post(
                "/api/v1/homework/templates",
                json=template_data,
                headers={"Authorization": "Bearer valid_token"}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["title"] == template_data["title"]

    def test_get_templates_list(self, test_client: TestClient):
        """测试获取作业模板列表"""
        with patch("src.api.v1.endpoints.homework.HomeworkService") as mock_service:
            mock_instance = MagicMock()
            mock_templates = [
                HomeworkFactory.create_homework(title=f"作业{i}")
                for i in range(3)
            ]
            mock_instance.get_homework_templates = AsyncMock(return_value=mock_templates)
            mock_service.return_value = mock_instance
            
            response = test_client.get(
                "/api/v1/homework/templates",
                headers={"Authorization": "Bearer valid_token"}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 3

    def test_get_template_by_id(self, test_client: TestClient):
        """测试根据ID获取作业模板"""
        template_id = "test_homework_123"
        
        with patch("src.api.v1.endpoints.homework.HomeworkService") as mock_service:
            mock_instance = MagicMock()
            mock_homework = HomeworkFactory.create_homework(homework_id=template_id)
            mock_instance.get_homework_by_id = AsyncMock(return_value=mock_homework)
            mock_service.return_value = mock_instance
            
            response = test_client.get(
                f"/api/v1/homework/templates/{template_id}",
                headers={"Authorization": "Bearer valid_token"}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["id"] == template_id

    def test_get_template_not_found(self, test_client: TestClient):
        """测试获取不存在的作业模板"""
        template_id = "nonexistent_id"
        
        with patch("src.api.v1.endpoints.homework.HomeworkService") as mock_service:
            mock_instance = MagicMock()
            mock_instance.get_homework_by_id = AsyncMock(return_value=None)
            mock_service.return_value = mock_instance
            
            response = test_client.get(
                f"/api/v1/homework/templates/{template_id}",
                headers={"Authorization": "Bearer valid_token"}
            )
        
        assert response.status_code == 404


class TestHomeworkSubmissions:
    """作业提交API测试"""

    def test_submit_homework_success(self, test_client: TestClient):
        """测试成功提交作业"""
        submission_data = RequestFactory.create_homework_submission_request()
        
        with patch("src.api.v1.endpoints.homework.HomeworkService") as mock_service:
            mock_instance = MagicMock()
            mock_submission = HomeworkFactory.create_homework_submission(
                homework_id=submission_data["homework_id"]
            )
            mock_instance.submit_homework = AsyncMock(return_value=mock_submission)
            mock_service.return_value = mock_instance
            
            response = test_client.post(
                "/api/v1/homework/submissions",
                json=submission_data,
                headers={"Authorization": "Bearer valid_token"}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert "id" in data["data"]

    def test_submit_homework_with_file(self, test_client: TestClient):
        """测试带文件的作业提交"""
        # 创建模拟文件
        file_content = b"test file content"
        files = {
            "file": ("test.pdf", BytesIO(file_content), "application/pdf")
        }
        form_data = {
            "homework_id": "test_homework_123",
            "submission_title": "测试提交"
        }
        
        with patch("src.api.v1.endpoints.homework.HomeworkService") as mock_service:
            mock_instance = MagicMock()
            mock_submission = HomeworkFactory.create_homework_submission(
                homework_id=form_data["homework_id"],
                file_url="https://example.com/test.pdf"
            )
            mock_instance.submit_homework_with_file = AsyncMock(return_value=mock_submission)
            mock_service.return_value = mock_instance
            
            response = test_client.post(
                "/api/v1/homework/submit",
                data=form_data,
                files=files,
                headers={"Authorization": "Bearer valid_token"}
            )
        
        assert response.status_code in [200, 201]

    def test_get_submissions_list(self, test_client: TestClient):
        """测试获取作业提交列表"""
        with patch("src.api.v1.endpoints.homework.HomeworkService") as mock_service:
            mock_instance = MagicMock()
            mock_submissions = [
                HomeworkFactory.create_homework_submission(submission_title=f"提交{i}")
                for i in range(5)
            ]
            mock_instance.get_submissions = AsyncMock(return_value={
                "items": mock_submissions,
                "total": 5,
                "page": 1,
                "size": 10
            })
            mock_service.return_value = mock_instance
            
            response = test_client.get(
                "/api/v1/homework/submissions",
                headers={"Authorization": "Bearer valid_token"}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]["items"]) == 5

    def test_get_submissions_with_filter(self, test_client: TestClient):
        """测试带过滤条件的作业提交列表"""
        with patch("src.api.v1.endpoints.homework.HomeworkService") as mock_service:
            mock_instance = MagicMock()
            mock_submissions = [
                HomeworkFactory.create_homework_submission(status="reviewed")
            ]
            mock_instance.get_submissions = AsyncMock(return_value={
                "items": mock_submissions,
                "total": 1,
                "page": 1,
                "size": 10
            })
            mock_service.return_value = mock_instance
            
            response = test_client.get(
                "/api/v1/homework/submissions?status=reviewed",
                headers={"Authorization": "Bearer valid_token"}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["items"][0]["status"] == "reviewed"

    def test_get_submission_by_id(self, test_client: TestClient):
        """测试根据ID获取作业提交"""
        submission_id = "test_submission_123"
        
        with patch("src.api.v1.endpoints.homework.HomeworkService") as mock_service:
            mock_instance = MagicMock()
            mock_submission = HomeworkFactory.create_homework_submission(submission_id=submission_id)
            mock_instance.get_submission_by_id = AsyncMock(return_value=mock_submission)
            mock_service.return_value = mock_instance
            
            response = test_client.get(
                f"/api/v1/homework/submissions/{submission_id}",
                headers={"Authorization": "Bearer valid_token"}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["id"] == submission_id


class TestHomeworkReview:
    """作业批改API测试"""

    def test_grade_homework_success(self, test_client: TestClient):
        """测试成功批改作业"""
        submission_id = "test_submission_123"
        
        with patch("src.api.v1.endpoints.homework.HomeworkService") as mock_service:
            mock_instance = MagicMock()
            mock_submission = HomeworkFactory.create_homework_submission(
                submission_id=submission_id,
                status="reviewed",
                total_score=85.0
            )
            mock_instance.grade_homework = AsyncMock(return_value=mock_submission)
            mock_service.return_value = mock_instance
            
            response = test_client.post(
                f"/api/v1/homework/submissions/{submission_id}/grade",
                headers={"Authorization": "Bearer valid_token"}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["status"] == "reviewed"
        assert data["data"]["total_score"] == 85.0

    def test_grade_homework_ai_error(self, test_client: TestClient):
        """测试AI批改失败"""
        submission_id = "test_submission_123"
        
        with patch("src.api.v1.endpoints.homework.HomeworkService") as mock_service:
            from src.core.exceptions import ServiceError
            mock_instance = MagicMock()
            mock_instance.grade_homework = AsyncMock(
                side_effect=ServiceError("AI服务暂时不可用")
            )
            mock_service.return_value = mock_instance
            
            response = test_client.post(
                f"/api/v1/homework/submissions/{submission_id}/grade",
                headers={"Authorization": "Bearer valid_token"}
            )
        
        assert response.status_code == 500

    def test_regrade_homework(self, test_client: TestClient):
        """测试重新批改作业"""
        submission_id = "test_submission_123"
        
        with patch("src.api.v1.endpoints.homework.HomeworkService") as mock_service:
            mock_instance = MagicMock()
            mock_submission = HomeworkFactory.create_homework_submission(
                submission_id=submission_id,
                status="reviewed",
                total_score=90.0
            )
            mock_instance.regrade_homework = AsyncMock(return_value=mock_submission)
            mock_service.return_value = mock_instance
            
            response = test_client.post(
                f"/api/v1/homework/submissions/{submission_id}/regrade",
                headers={"Authorization": "Bearer valid_token"}
            )
        
        assert response.status_code == 200


class TestHomeworkStats:
    """作业统计API测试"""

    def test_get_homework_stats(self, test_client: TestClient):
        """测试获取作业统计"""
        with patch("src.api.v1.endpoints.homework.HomeworkService") as mock_service:
            mock_instance = MagicMock()
            mock_stats = {
                "total_submissions": 50,
                "reviewed_count": 40,
                "average_score": 85.5,
                "pending_count": 10
            }
            mock_instance.get_homework_stats = AsyncMock(return_value=mock_stats)
            mock_service.return_value = mock_instance
            
            response = test_client.get(
                "/api/v1/homework/stats",
                headers={"Authorization": "Bearer valid_token"}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["total_submissions"] == 50
        assert data["data"]["average_score"] == 85.5

    def test_get_homework_stats_with_date_range(self, test_client: TestClient):
        """测试带日期范围的作业统计"""
        with patch("src.api.v1.endpoints.homework.HomeworkService") as mock_service:
            mock_instance = MagicMock()
            mock_stats = {
                "total_submissions": 20,
                "reviewed_count": 18,
                "average_score": 88.0,
                "pending_count": 2
            }
            mock_instance.get_homework_stats = AsyncMock(return_value=mock_stats)
            mock_service.return_value = mock_instance
            
            response = test_client.get(
                "/api/v1/homework/stats?start_date=2024-01-01&end_date=2024-01-31",
                headers={"Authorization": "Bearer valid_token"}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert "total_submissions" in data["data"]


class TestHomeworkPagination:
    """作业分页API测试"""

    def test_get_submissions_pagination(self, test_client: TestClient):
        """测试作业提交分页"""
        with patch("src.api.v1.endpoints.homework.HomeworkService") as mock_service:
            mock_instance = MagicMock()
            mock_submissions = [
                HomeworkFactory.create_homework_submission()
                for _ in range(10)
            ]
            mock_instance.get_submissions = AsyncMock(return_value={
                "items": mock_submissions,
                "total": 100,
                "page": 1,
                "size": 10,
                "pages": 10
            })
            mock_service.return_value = mock_instance
            
            response = test_client.get(
                "/api/v1/homework/submissions?page=1&size=10",
                headers={"Authorization": "Bearer valid_token"}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["page"] == 1
        assert data["data"]["size"] == 10
        assert data["data"]["total"] == 100

    def test_get_submissions_invalid_page(self, test_client: TestClient):
        """测试无效的页码"""
        response = test_client.get(
            "/api/v1/homework/submissions?page=-1",
            headers={"Authorization": "Bearer valid_token"}
        )
        
        assert response.status_code == 422  # Validation error


class TestHomeworkEdgeCases:
    """作业边界情况测试"""

    def test_submit_homework_without_template(self, test_client: TestClient):
        """测试提交作业但模板不存在"""
        submission_data = RequestFactory.create_homework_submission_request(
            homework_id="nonexistent_homework"
        )
        
        with patch("src.api.v1.endpoints.homework.HomeworkService") as mock_service:
            from src.core.exceptions import ValidationError
            mock_instance = MagicMock()
            mock_instance.submit_homework = AsyncMock(
                side_effect=ValidationError("作业模板不存在")
            )
            mock_service.return_value = mock_instance
            
            response = test_client.post(
                "/api/v1/homework/submissions",
                json=submission_data,
                headers={"Authorization": "Bearer valid_token"}
            )
        
        assert response.status_code == 400

    def test_grade_already_reviewed_homework(self, test_client: TestClient):
        """测试批改已批改的作业"""
        submission_id = "already_reviewed"
        
        with patch("src.api.v1.endpoints.homework.HomeworkService") as mock_service:
            mock_instance = MagicMock()
            mock_submission = HomeworkFactory.create_homework_submission(
                submission_id=submission_id,
                status="reviewed"
            )
            mock_instance.grade_homework = AsyncMock(return_value=mock_submission)
            mock_service.return_value = mock_instance
            
            response = test_client.post(
                f"/api/v1/homework/submissions/{submission_id}/grade",
                headers={"Authorization": "Bearer valid_token"}
            )
        
        # 应该允许重新批改或返回已批改结果
        assert response.status_code in [200, 409]

    def test_get_stats_no_data(self, test_client: TestClient):
        """测试统计数据为空的情况"""
        with patch("src.api.v1.endpoints.homework.HomeworkService") as mock_service:
            mock_instance = MagicMock()
            mock_stats = {
                "total_submissions": 0,
                "reviewed_count": 0,
                "average_score": 0,
                "pending_count": 0
            }
            mock_instance.get_homework_stats = AsyncMock(return_value=mock_stats)
            mock_service.return_value = mock_instance
            
            response = test_client.get(
                "/api/v1/homework/stats",
                headers={"Authorization": "Bearer valid_token"}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["total_submissions"] == 0
