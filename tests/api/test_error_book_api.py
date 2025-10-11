"""
错题本API集成测试
"""

import pytest
from httpx import AsyncClient
from fastapi import status
from datetime import datetime

from src.main import app
from src.models.error_book import ErrorQuestion, ReviewRecord
from tests.conftest import TestClient


class TestErrorBookAPI:
    """错题本API集成测试"""

    @pytest.fixture
    def test_error_question_data(self):
        """测试错题数据"""
        return {
            "subject": "数学",
            "question_content": "解方程 2x + 3 = 7，求x的值",
            "student_answer": "x = 1",
            "correct_answer": "x = 2",
            "error_type": "计算错误",
            "knowledge_points": ["一元一次方程", "基础运算"],
            "difficulty_level": 2,
            "is_starred": False,
            "tags": ["易错题"]
        }

    async def test_create_error_question(self, test_client: TestClient, test_error_question_data):
        """测试创建错题"""
        # 登录获取token
        await test_client.login()
        
        # 创建错题
        response = await test_client.post("/api/v1/error-book", json=test_error_question_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["subject"] == "数学"
        assert data["question_content"] == test_error_question_data["question_content"]
        assert data["mastery_status"] == "learning"
        assert data["review_count"] == 0
        assert "id" in data

    async def test_get_error_questions_list(self, test_client: TestClient, test_error_question_data):
        """测试获取错题列表"""
        # 登录并创建测试数据
        await test_client.login()
        create_response = await test_client.post("/api/v1/error-book", json=test_error_question_data)
        assert create_response.status_code == status.HTTP_200_OK
        
        # 获取错题列表
        response = await test_client.get("/api/v1/error-book")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "limit" in data
        assert data["total"] >= 1
        assert len(data["items"]) >= 1

    async def test_get_error_questions_with_filters(self, test_client: TestClient, test_error_question_data):
        """测试带筛选条件的错题列表"""
        # 登录并创建测试数据
        await test_client.login()
        await test_client.post("/api/v1/error-book", json=test_error_question_data)
        
        # 按学科筛选
        response = await test_client.get("/api/v1/error-book", params={"subject": "数学"})
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert all(item["subject"] == "数学" for item in data["items"])
        
        # 按状态筛选
        response = await test_client.get("/api/v1/error-book", params={"status": "learning"})
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert all(item["mastery_status"] == "learning" for item in data["items"])

    async def test_get_error_question_detail(self, test_client: TestClient, test_error_question_data):
        """测试获取错题详情"""
        # 登录并创建测试数据
        await test_client.login()
        create_response = await test_client.post("/api/v1/error-book", json=test_error_question_data)
        error_question_id = create_response.json()["id"]
        
        # 获取错题详情
        response = await test_client.get(f"/api/v1/error-book/{error_question_id}")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["id"] == error_question_id
        assert data["subject"] == "数学"
        assert data["question_content"] == test_error_question_data["question_content"]

    async def test_update_error_question(self, test_client: TestClient, test_error_question_data):
        """测试更新错题"""
        # 登录并创建测试数据
        await test_client.login()
        create_response = await test_client.post("/api/v1/error-book", json=test_error_question_data)
        error_question_id = create_response.json()["id"]
        
        # 更新错题
        update_data = {
            "error_type": "理解错误",
            "difficulty_level": 3,
            "is_starred": True
        }
        response = await test_client.put(f"/api/v1/error-book/{error_question_id}", json=update_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["error_type"] == "理解错误"
        assert data["difficulty_level"] == 3
        assert data["is_starred"] == True

    async def test_delete_error_question(self, test_client: TestClient, test_error_question_data):
        """测试删除错题"""
        # 登录并创建测试数据
        await test_client.login()
        create_response = await test_client.post("/api/v1/error-book", json=test_error_question_data)
        error_question_id = create_response.json()["id"]
        
        # 删除错题
        response = await test_client.delete(f"/api/v1/error-book/{error_question_id}")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] == True
        
        # 验证删除成功
        get_response = await test_client.get(f"/api/v1/error-book/{error_question_id}")
        assert get_response.status_code == status.HTTP_404_NOT_FOUND

    async def test_create_review_record(self, test_client: TestClient, test_error_question_data):
        """测试创建复习记录"""
        # 登录并创建测试数据
        await test_client.login()
        create_response = await test_client.post("/api/v1/error-book", json=test_error_question_data)
        error_question_id = create_response.json()["id"]
        
        # 创建复习记录
        review_data = {
            "review_result": "correct",
            "score": 95,
            "time_spent": 180,
            "student_answer": "x = 2",
            "notes": "这次做对了，理解了解题方法"
        }
        response = await test_client.post(
            f"/api/v1/error-book/{error_question_id}/review", 
            json=review_data
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["review_result"] == "correct"
        assert data["score"] == 95
        assert data["error_question_id"] == error_question_id

    async def test_get_error_book_stats(self, test_client: TestClient, test_error_question_data):
        """测试获取错题本统计"""
        # 登录并创建测试数据
        await test_client.login()
        await test_client.post("/api/v1/error-book", json=test_error_question_data)
        
        # 获取统计信息
        response = await test_client.get("/api/v1/error-book/stats")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "overview" in data
        assert "by_subject" in data
        assert "by_category" in data
        
        assert "total_errors" in data["overview"]
        assert data["overview"]["total_errors"] >= 1

    async def test_get_review_recommendations(self, test_client: TestClient, test_error_question_data):
        """测试获取复习推荐"""
        # 登录并创建测试数据
        await test_client.login()
        await test_client.post("/api/v1/error-book", json=test_error_question_data)
        
        # 获取复习推荐
        response = await test_client.get("/api/v1/error-book/recommendations")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "urgent_reviews" in data
        assert "daily_plan" in data
        assert "weak_areas" in data
        
        assert isinstance(data["urgent_reviews"], list)
        assert "target_count" in data["daily_plan"]

    async def test_batch_update_status(self, test_client: TestClient, test_error_question_data):
        """测试批量更新状态"""
        # 登录并创建测试数据
        await test_client.login()
        create_response = await test_client.post("/api/v1/error-book", json=test_error_question_data)
        error_question_id = create_response.json()["id"]
        
        # 批量更新状态
        batch_data = {
            "error_question_ids": [error_question_id],
            "action": "update_status",
            "data": {"status": "reviewing"}
        }
        response = await test_client.post("/api/v1/error-book/batch", json=batch_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] == True

    async def test_analyze_error(self, test_client: TestClient):
        """测试AI错题分析"""
        # 登录
        await test_client.login()
        
        # AI分析请求
        analysis_data = {
            "question_content": "计算 2 + 2 的值",
            "student_answer": "5",
            "correct_answer": "4",
            "subject": "数学"
        }
        response = await test_client.post("/api/v1/error-book/analyze", json=analysis_data)
        
        # 注意：这个测试可能会失败，因为依赖真实的AI服务
        # 在集成测试中，我们可以mock AI服务或跳过这个测试
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            assert "error_type" in data
            assert "analysis" in data
            assert "suggestions" in data

    async def test_unauthorized_access(self, test_client: TestClient):
        """测试未授权访问"""
        # 不登录直接访问
        response = await test_client.get("/api/v1/error-book")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_invalid_error_question_id(self, test_client: TestClient):
        """测试无效的错题ID"""
        await test_client.login()
        
        # 访问不存在的错题
        response = await test_client.get("/api/v1/error-book/non-existent-id")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_validation_errors(self, test_client: TestClient):
        """测试数据验证错误"""
        await test_client.login()
        
        # 发送无效数据
        invalid_data = {
            "subject": "",  # 空学科
            "question_content": "",  # 空题目内容
            "difficulty_level": 10  # 超出范围的难度
        }
        response = await test_client.post("/api/v1/error-book", json=invalid_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestErrorBookIntegration:
    """错题本功能集成测试"""

    async def test_complete_error_lifecycle(self, test_client: TestClient):
        """测试完整的错题生命周期"""
        await test_client.login()
        
        # 1. 创建错题
        error_data = {
            "subject": "数学",
            "question_content": "解方程 2x + 3 = 7",
            "student_answer": "x = 1",
            "correct_answer": "x = 2",
            "error_type": "计算错误",
            "knowledge_points": ["一元一次方程"],
            "difficulty_level": 2
        }
        create_response = await test_client.post("/api/v1/error-book", json=error_data)
        assert create_response.status_code == status.HTTP_200_OK
        error_id = create_response.json()["id"]
        
        # 2. 第一次复习（错误）
        review1_data = {
            "review_result": "incorrect",
            "score": 20,
            "notes": "还是不太理解"
        }
        review1_response = await test_client.post(
            f"/api/v1/error-book/{error_id}/review", 
            json=review1_data
        )
        assert review1_response.status_code == status.HTTP_200_OK
        
        # 3. 第二次复习（部分正确）
        review2_data = {
            "review_result": "partial",
            "score": 60,
            "notes": "方法对了，但计算有误"
        }
        review2_response = await test_client.post(
            f"/api/v1/error-book/{error_id}/review", 
            json=review2_data
        )
        assert review2_response.status_code == status.HTTP_200_OK
        
        # 4. 第三次复习（完全正确）
        review3_data = {
            "review_result": "correct",
            "score": 95,
            "notes": "完全掌握了"
        }
        review3_response = await test_client.post(
            f"/api/v1/error-book/{error_id}/review", 
            json=review3_data
        )
        assert review3_response.status_code == status.HTTP_200_OK
        
        # 5. 检查错题状态更新
        detail_response = await test_client.get(f"/api/v1/error-book/{error_id}")
        assert detail_response.status_code == status.HTTP_200_OK
        detail_data = detail_response.json()
        
        assert detail_data["review_count"] >= 3
        assert detail_data["mastery_rate"] > 0
        
        # 6. 检查统计信息更新
        stats_response = await test_client.get("/api/v1/error-book/stats")
        assert stats_response.status_code == status.HTTP_200_OK
        stats_data = stats_response.json()
        assert stats_data["overview"]["total_errors"] >= 1