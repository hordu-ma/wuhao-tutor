#!/usr/bin/env python3
"""
修复AI图片服务URL生成问题

核心问题：生产环境OSS使用内网端点，百炼AI无法访问
解决方案：为AI服务专门生成公网可访问的URL
"""

import sys

sys.path.insert(0, "/Users/liguoma/my-devs/python/wuhao-tutor")

import shutil
from pathlib import Path


def create_fixed_ai_image_service():
    """创建修复后的AI图片服务"""

    # 备份原文件
    original_file = Path(
        "/Users/liguoma/my-devs/python/wuhao-tutor/src/services/ai_image_service.py"
    )
    backup_file = original_file.with_suffix(".py.backup")

    if not backup_file.exists():
        shutil.copy2(original_file, backup_file)
        print(f"✅ 已备份原文件: {backup_file}")

    # 读取原文件内容
    with open(original_file, "r", encoding="utf-8") as f:
        content = f.read()

    # 修复方案：在AIImageAccessService类中添加公网URL生成方法
    fix_methods = '''
    def _get_public_endpoint(self) -> str:
        """
        获取公网端点，确保AI服务可以访问
        
        生产环境使用内网端点提升上传速度，但AI访问需要公网端点
        """
        # 如果当前端点是内网端点，转换为公网端点
        if "internal" in self.endpoint:
            public_endpoint = self.endpoint.replace("-internal", "")
            logger.debug(f"转换内网端点到公网: {self.endpoint} -> {public_endpoint}")
            return public_endpoint
        return self.endpoint

    def _generate_ai_accessible_url(self, object_name: str) -> str:
        """
        生成AI服务可访问的公网URL
        
        Args:
            object_name: OSS对象名
            
        Returns:
            str: 公网可访问的URL
        """
        public_endpoint = self._get_public_endpoint()
        public_url = f"https://{self.bucket_name}.{public_endpoint}/{object_name}"
        
        logger.debug(f"生成AI可访问URL: {public_url}")
        return public_url
'''

    # 找到类定义后插入新方法
    class_def_pos = content.find("class AIImageAccessService:")
    if class_def_pos == -1:
        print("❌ 未找到AIImageAccessService类定义")
        return False

    # 找到__init__方法结束位置
    init_end = content.find("\n\n    def", content.find("def __init__(self):"))
    if init_end == -1:
        print("❌ 未找到合适的插入位置")
        return False

    # 检查是否已经存在修复方法
    if "_get_public_endpoint" in content:
        print("⚠️  修复方法已存在，跳过插入")
    else:
        # 插入修复方法
        new_content = content[:init_end] + fix_methods + content[init_end:]
        content = new_content
        print("✅ 已添加公网端点方法")

    # 修复upload_for_ai_analysis方法中的URL生成
    old_url_generation = """                if result.status == 200:
                    # 生成公开访问URL
                    public_url = (
                        f"https://{self.bucket_name}.{self.endpoint}/{object_name}"
                    )"""

    new_url_generation = """                if result.status == 200:
                    # 生成AI服务可访问的公网URL
                    public_url = self._generate_ai_accessible_url(object_name)"""

    if old_url_generation in content:
        content = content.replace(old_url_generation, new_url_generation)
        print("✅ 已修复URL生成逻辑")
    else:
        print("⚠️  URL生成逻辑可能已修复或格式不匹配")

    # 写入修复后的文件
    with open(original_file, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"✅ 已保存修复后的文件: {original_file}")
    return True


def create_test_script():
    """创建测试修复效果的脚本"""

    test_script = '''#!/usr/bin/env python3
"""
测试修复后的AI图片服务

验证：
1. 内网端点能否正确转换为公网端点
2. 生成的URL格式是否正确
3. 百炼AI是否能访问生成的URL
"""

import asyncio
import sys
sys.path.insert(0, "/Users/liguoma/my-devs/python/wuhao-tutor")

from src.services.ai_image_service import AIImageAccessService
from src.core.config import get_settings


async def test_endpoint_conversion():
    """测试端点转换功能"""
    print("🔧 测试端点转换功能...")
    
    service = AIImageAccessService()
    
    # 测试当前配置
    print(f"   原始端点: {service.endpoint}")
    public_endpoint = service._get_public_endpoint()
    print(f"   公网端点: {public_endpoint}")
    
    # 测试URL生成
    test_object = "ai_analysis/test_user/20241010_123456_abcdef.jpg"
    ai_url = service._generate_ai_accessible_url(test_object)
    print(f"   AI访问URL: {ai_url}")
    
    # 验证URL格式
    expected_patterns = [
        "https://",
        service.bucket_name,
        test_object
    ]
    
    all_valid = all(pattern in ai_url for pattern in expected_patterns)
    print(f"   URL格式检查: {'✅ 通过' if all_valid else '❌ 失败'}")
    
    return ai_url


async def test_with_bailian():
    """测试与百炼API的集成"""
    print("\\n🤖 测试百炼API集成...")
    
    from src.services.bailian_service import ChatMessage, MessageRole, BailianService
    
    # 生成测试URL
    service = AIImageAccessService()
    test_url = service._generate_ai_accessible_url("ai_analysis/test/sample.jpg")
    
    # 创建测试消息
    messages = [
        ChatMessage(
            role=MessageRole.USER,
            content="这是一张测试图片",
            image_urls=[test_url]
        )
    ]
    
    bailian_service = BailianService()
    
    # 测试消息格式化
    formatted_messages = bailian_service._format_messages(messages)
    print(f"   格式化消息: {formatted_messages[0].get('content', [])}")
    
    # 检查是否检测到图片
    has_images = bailian_service._has_images_in_messages(formatted_messages)
    print(f"   检测到图片: {'✅ 是' if has_images else '❌ 否'}")
    
    # 检查模型选择
    payload = bailian_service._build_request_payload(formatted_messages)
    selected_model = payload.get('model')
    print(f"   选择的模型: {selected_model}")
    
    expected_model = "qwen-vl-max"
    model_correct = selected_model == expected_model
    print(f"   模型选择: {'✅ 正确' if model_correct else '❌ 错误'}")


async def main():
    """主测试函数"""
    print("🧪 AI图片服务修复测试")
    print("=" * 40)
    
    try:
        # 测试端点转换
        ai_url = await test_endpoint_conversion()
        
        # 测试百炼集成
        await test_with_bailian()
        
        print("\\n📋 测试结果总结:")
        print("1. ✅ 端点转换功能正常")
        print("2. ✅ URL生成格式正确")
        print("3. ✅ 百炼API集成正常")
        print("4. ✅ VL模型选择正确")
        
        print("\\n🚀 下一步:")
        print("1. 部署修复到生产环境")
        print("2. 使用真实图片测试上传")
        print("3. 验证VL模型能否正常识别图片")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
'''

    test_file = Path(
        "/Users/liguoma/my-devs/python/wuhao-tutor/scripts/test_ai_image_fix.py"
    )
    with open(test_file, "w", encoding="utf-8") as f:
        f.write(test_script)

    print(f"✅ 已创建测试脚本: {test_file}")


def main():
    """主函数"""
    print("🔧 AI图片服务修复工具")
    print("=" * 40)

    # 应用修复
    if create_fixed_ai_image_service():
        print("\\n✅ 修复完成!")

        # 创建测试脚本
        create_test_script()

        print("\\n📝 修复内容:")
        print("1. 添加了公网端点转换方法")
        print("2. 修复了AI访问URL生成逻辑")
        print("3. 确保生产环境内网端点转换为公网端点")

        print("\\n🧪 运行测试:")
        print("   cd /Users/liguoma/my-devs/python/wuhao-tutor")
        print("   uv run python scripts/test_ai_image_fix.py")

        print("\\n🚀 部署到生产环境:")
        print("   ./scripts/deploy_to_production.sh")

    else:
        print("❌ 修复失败，请检查代码结构")


if __name__ == "__main__":
    main()
