#!/usr/bin/env python3
"""
知识图谱API集成测试脚本
测试所有知识图谱相关的API端点
"""

import asyncio
import json
from datetime import datetime
from typing import Any, Dict

import httpx

# 生产环境API基础URL
BASE_URL = "https://wuhao.guomaspace.com/api/v1"

# 测试账号token (需要替换为真实token)
# 从生产环境获取: 登录小程序后从本地存储中获取
TEST_TOKEN = ""


# 如果没有token,可以通过此函数获取
async def get_test_token() -> str:
    """通过测试账号登录获取token"""
    print("⚠️ 请先登录小程序,从本地存储中获取token")
    print("或者使用以下命令获取:")
    print("ssh root@121.199.173.244")
    print("cd /opt/wuhao-tutor")
    print("python3 scripts/server_create_test_accounts.py --list")
    return ""


class KnowledgeGraphAPITester:
    """知识图谱API测试器"""

    def __init__(self, base_url: str, token: str):
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        self.results = []

    async def test_endpoint(
        self, name: str, method: str, path: str, params: Dict[str, Any] | None = None
    ) -> Dict[str, Any]:
        """测试单个API端点"""
        url = f"{self.base_url}{path}"

        print(f"\n{'='*60}")
        print(f"🧪 测试: {name}")
        print(f"📍 {method} {url}")
        if params:
            print(f"📦 参数: {json.dumps(params, ensure_ascii=False, indent=2)}")

        try:
            async with httpx.AsyncClient() as client:
                if method == "GET":
                    response = await client.get(
                        url, headers=self.headers, params=params, timeout=10.0
                    )
                elif method == "POST":
                    response = await client.post(
                        url, headers=self.headers, json=params, timeout=10.0
                    )
                else:
                    raise ValueError(f"不支持的HTTP方法: {method}")

                # 解析响应
                result = {
                    "name": name,
                    "status_code": response.status_code,
                    "success": response.status_code == 200,
                    "response": None,
                    "error": None,
                }

                if response.status_code == 200:
                    try:
                        data = response.json()
                        result["response"] = data
                        print(f"✅ 成功 (Status: {response.status_code})")
                        print(f"📄 响应数据:")
                        print(json.dumps(data, ensure_ascii=False, indent=2))
                    except json.JSONDecodeError:
                        result["success"] = False
                        result["error"] = "响应不是有效的JSON"
                        print(f"❌ 失败: {result['error']}")
                else:
                    result["success"] = False
                    result["error"] = response.text
                    print(f"❌ 失败 (Status: {response.status_code})")
                    print(f"错误信息: {response.text}")

                self.results.append(result)
                return result

        except Exception as e:
            result = {
                "name": name,
                "status_code": 0,
                "success": False,
                "response": None,
                "error": str(e),
            }
            print(f"❌ 异常: {e}")
            self.results.append(result)
            return result

    async def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始知识图谱API集成测试")
        print(f"📅 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🌐 API地址: {self.base_url}")

        # Test 1: 获取知识点列表
        await self.test_endpoint(
            name="获取知识点列表",
            method="GET",
            path="/knowledge-graph/knowledge-points",
            params={"subject": "数学", "min_count": 1},
        )

        # Test 2: 获取知识图谱快照
        await self.test_endpoint(
            name="获取知识图谱快照",
            method="GET",
            path="/knowledge-graph/snapshot",
            params={"subject": "数学"},
        )

        # Test 3: 获取薄弱知识链
        await self.test_endpoint(
            name="获取薄弱知识链",
            method="GET",
            path="/knowledge-graph/weak-chains",
            params={"subject": "数学", "limit": 5},
        )

        # Test 4: 获取智能复习推荐
        await self.test_endpoint(
            name="获取智能复习推荐",
            method="GET",
            path="/knowledge-graph/review-recommendations",
            params={"subject": "数学", "limit": 10},
        )

        # Test 5: 按知识点筛选错题列表
        await self.test_endpoint(
            name="按知识点筛选错题",
            method="GET",
            path="/mistakes",
            params={"subject": "数学", "page": 1, "page_size": 10},
        )

        # 打印测试总结
        self.print_summary()

    def print_summary(self):
        """打印测试总结"""
        print(f"\n{'='*60}")
        print("📊 测试总结")
        print(f"{'='*60}")

        total = len(self.results)
        success = sum(1 for r in self.results if r["success"])
        failed = total - success

        print(f"总测试数: {total}")
        print(f"✅ 成功: {success}")
        print(f"❌ 失败: {failed}")
        print(f"成功率: {(success/total*100):.1f}%")

        if failed > 0:
            print("\n失败的测试:")
            for r in self.results:
                if not r["success"]:
                    print(f"  ❌ {r['name']}: {r['error']}")

        print(f"\n{'='*60}")


async def main():
    """主函数"""
    global TEST_TOKEN

    # 检查token
    if not TEST_TOKEN:
        print("❌ 错误: 请先设置TEST_TOKEN")
        print("\n获取Token的方法:")
        print("1. 登录微信小程序")
        print("2. 打开微信开发者工具")
        print("3. 在Console中执行: wx.getStorageSync('token')")
        print("4. 复制token到本脚本的TEST_TOKEN变量")
        return

    # 创建测试器
    tester = KnowledgeGraphAPITester(BASE_URL, TEST_TOKEN)

    # 运行测试
    await tester.run_all_tests()


if __name__ == "__main__":
    # 设置提示
    print("=" * 60)
    print("知识图谱API集成测试工具")
    print("=" * 60)
    print("\n📝 使用说明:")
    print("1. 编辑本文件,设置TEST_TOKEN变量")
    print("2. 运行: python3 scripts/test_knowledge_graph_api.py")
    print("3. 查看测试结果")
    print("\n" + "=" * 60 + "\n")

    # 运行测试
    asyncio.run(main())
