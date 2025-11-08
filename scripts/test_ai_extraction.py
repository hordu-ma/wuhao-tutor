#!/usr/bin/env python3
"""
测试AI结构化提取功能

用途：验证从问答对话中提取题目的准确性

运行：python scripts/test_ai_extraction.py
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import Optional

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))


async def test_extraction():
    """测试AI结构化提取"""
    # 加载生产环境配置
    from dotenv import load_dotenv

    env_file = os.getenv("ENV_FILE", ".env.production")
    load_dotenv(env_file)
    print(f"✅ 已加载环境配置: {env_file}")
    print(f"✅ 百炼API Key: {os.getenv('BAILIAN_API_KEY', 'NOT_SET')[:20]}...")

    from src.services.bailian_service import BailianService

    # 初始化服务（使用环境变量配置）
    bailian_service = BailianService()

    # 创建一个简单的测试类来调用提取方法
    class TestExtractor:
        def __init__(self, bailian_service):
            self.bailian_service = bailian_service

        async def _extract_structured_question(
            self,
            user_question: str,
            ai_answer: str,
            image_urls: Optional[list] = None,
            subject: Optional[str] = None,
        ) -> dict:
            """直接复制LearningService中的提取方法"""
            try:
                # 构建提示词
                prompt = f"""你是一个专业的K12教育题目解析专家。请从以下学生与老师的问答对话中，提取出**结构化的题目信息**。

**学生提问：**
{user_question}

**老师回答：**
{ai_answer}

**任务要求：**
1. 分离学生的提问语句（如"老师我不会"、"帮我看看"）和真正的题目内容
2. 提取题目主体（如果学生没有明确给出题目，从老师回答中推断）
3. 提取标准答案
4. 提取详细解析
5. 识别涉及的知识点（2-5个）
6. 判断题目类型和难度

**输出格式（严格JSON）：**
```json
{{
  "question_content": "纯净的题目内容（去除学生的求助语句）",
  "correct_answer": "标准答案",
  "explanation": "详细解析过程",
  "knowledge_points": ["知识点1", "知识点2"],
  "difficulty_level": 2,
  "question_type": "选择题/填空题/解答题/判断题/应用题",
  "extraction_success": true,
  "confidence": 0.9
}}
```

**特殊情况处理：**
- 如果学生只上传图片没有文字，question_content填写"图片题目（需OCR识别）"
- 如果无法提取完整题目，设置 extraction_success=false，confidence降低
- 知识点必须具体明确，不要用"数学知识"这种泛泛的说法
- 难度等级：1=基础，2=中等，3=困难，4=挑战，5=竞赛"""

                if subject:
                    prompt += f"\n\n**学科：** {subject}"

                if image_urls and len(image_urls) > 0:
                    prompt += f"\n\n**注意：** 学生上传了 {len(image_urls)} 张图片，题目可能在图片中"

                # 调用百炼AI
                response = await self.bailian_service.chat_completion(
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,
                )

                # 解析响应
                response_text = (
                    response.content if hasattr(response, "content") else str(response)
                )

                # 提取JSON部分
                import re

                json_match = re.search(
                    r"```json\s*(\{.*?\})\s*```", response_text, re.DOTALL
                )
                if json_match:
                    json_str = json_match.group(1)
                else:
                    json_str = response_text.strip()

                import json

                result = json.loads(json_str)

                return result

            except Exception as e:
                print(f"AI提取失败: {e}")
                import traceback

                traceback.print_exc()
                return {
                    "question_content": user_question[:200],
                    "correct_answer": "详见解析",
                    "explanation": ai_answer[:500],
                    "knowledge_points": ["未识别"],
                    "difficulty_level": 2,
                    "question_type": "解答题",
                    "extraction_success": False,
                    "confidence": 0.5,
                    "fallback": True,
                }

    extractor = TestExtractor(bailian_service)

    # 测试用例1：带有"老师我不会"的提问
    test_case_1 = {
        "user_question": "老师，我不会做这道题：求二次函数 y=x²-4x+3 的对称轴和顶点坐标",
        "ai_answer": """这道题考查二次函数的性质。

**题目分析：**
已知二次函数 y = x² - 4x + 3

**解题步骤：**

1. 求对称轴：
   对称轴公式 x = -b/(2a)
   其中 a=1, b=-4
   x = -(-4)/(2×1) = 2

2. 求顶点坐标：
   将x=2代入原式：
   y = 2² - 4×2 + 3 = 4 - 8 + 3 = -1
   
**答案：**
- 对称轴：x = 2
- 顶点坐标：(2, -1)

**涉及知识点：**
- 二次函数对称轴公式
- 二次函数顶点坐标
- 配方法
""",
        "subject": "数学",
    }

    # 测试用例2：纯题目提问
    test_case_2 = {
        "user_question": "解方程：2x + 5 = 13",
        "ai_answer": """这是一个一元一次方程。

**解题步骤：**
2x + 5 = 13
2x = 13 - 5
2x = 8
x = 4

**答案：** x = 4

**知识点：** 一元一次方程、移项、同除
""",
        "subject": "数学",
    }

    # 测试用例3：图片题目
    test_case_3 = {
        "user_question": "[图片]",
        "ai_answer": """从图片中可以看到这是一道几何题。

题目：已知三角形ABC中，AB=AC，角A=40°，求角B和角C。

**解答：**
因为AB=AC（等腰三角形）
所以角B=角C

又因为角A+角B+角C=180°
40° + 角B + 角B = 180°
2×角B = 140°
角B = 70°

**答案：** 角B=70°，角C=70°

**知识点：** 等腰三角形性质、三角形内角和
""",
        "subject": "数学",
        "image_urls": ["https://example.com/image1.jpg"],
    }

    print("=" * 80)
    print("AI结构化提取测试")
    print("=" * 80)

    # 测试所有用例
    for i, test_case in enumerate([test_case_1, test_case_2, test_case_3], 1):
        print(f"\n{'=' * 80}")
        print(f"测试用例 {i}")
        print(f"{'=' * 80}")
        print(f"\n📝 用户提问：\n{test_case['user_question']}")
        print(f"\n🤖 AI回答：\n{test_case['ai_answer'][:200]}...")

        try:
            result = await extractor._extract_structured_question(
                user_question=test_case["user_question"],
                ai_answer=test_case["ai_answer"],
                image_urls=test_case.get("image_urls"),
                subject=test_case.get("subject"),
            )

            print(f"\n✅ 提取结果：")
            print(f"  - 提取成功: {result.get('extraction_success')}")
            print(f"  - 置信度: {result.get('confidence'):.2f}")
            print(f"  - 题目类型: {result.get('question_type')}")
            print(f"  - 难度等级: {result.get('difficulty_level')}")
            print(f"\n📄 纯净题目内容：")
            print(f"  {result.get('question_content')}")
            print(f"\n💡 标准答案：")
            print(f"  {result.get('correct_answer')}")
            print(f"\n📚 知识点：")
            for kp in result.get("knowledge_points", []):
                print(f"  - {kp}")
            print(f"\n📖 解析（前100字）：")
            print(f"  {result.get('explanation', '')[:100]}...")

            if result.get("fallback"):
                print(f"\n⚠️ 注意：使用了降级提取（AI提取失败）")

        except Exception as e:
            print(f"\n❌ 提取失败: {e}")
            import traceback

            traceback.print_exc()

    print(f"\n{'=' * 80}")
    print("测试完成")
    print(f"{'=' * 80}")


if __name__ == "__main__":
    asyncio.run(test_extraction())
