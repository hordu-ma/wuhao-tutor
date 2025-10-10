#!/usr/bin/env python3
"""
修复百炼VL模型图片访问问题

问题诊断：
1. 生产环境OSS使用内网端点 (oss-cn-hangzhou-internal.aliyuncs.com)
2. 百炼AI服务无法访问内网OSS地址
3. 需要为AI服务生成公网可访问的OSS URL

解决方案：
1. 在AI图片服务中检测环境并使用公网端点
2. 确保生成的图片URL使用公网域名
3. 测试修复后的URL能否被百炼AI访问
"""

import sys

sys.path.insert(0, "/Users/liguoma/my-devs/python/wuhao-tutor")

from src.core.config import get_settings


def analyze_oss_config():
    """分析当前OSS配置"""
    settings = get_settings()

    print("🔍 当前OSS配置分析:")
    print(f"   Bucket: {settings.OSS_BUCKET_NAME}")
    print(f"   Endpoint: {settings.OSS_ENDPOINT}")
    print(f"   Access Key: {(settings.OSS_ACCESS_KEY_ID or '')[:10]}...")

    # 检查是否为内网端点
    is_internal = "internal" in settings.OSS_ENDPOINT
    print(f"   是否内网端点: {'是' if is_internal else '否'}")

    if is_internal:
        # 生成对应的公网端点
        public_endpoint = settings.OSS_ENDPOINT.replace("-internal", "")
        print(f"   对应公网端点: {public_endpoint}")

        # 生成示例URL对比
        sample_object = "ai_analysis/user123/20241010_123456_abcdef.jpg"
        internal_url = f"https://{settings.OSS_BUCKET_NAME}.{settings.OSS_ENDPOINT}/{sample_object}"
        public_url = (
            f"https://{settings.OSS_BUCKET_NAME}.{public_endpoint}/{sample_object}"
        )

        print(f"\n📎 URL对比:")
        print(f"   内网URL (AI无法访问): {internal_url}")
        print(f"   公网URL (AI可以访问): {public_url}")

        return {
            "has_issue": True,
            "current_endpoint": settings.OSS_ENDPOINT,
            "public_endpoint": public_endpoint,
            "bucket": settings.OSS_BUCKET_NAME,
        }
    else:
        print("   ✅ 当前已使用公网端点")
        return {"has_issue": False}


def generate_fix_code():
    """生成修复代码"""

    fix_code = '''
# 在 src/services/ai_image_service.py 中添加公网URL生成方法

def _get_public_endpoint(self) -> str:
    """获取公网端点，确保AI服务可以访问"""
    # 如果当前端点是内网端点，转换为公网端点
    if "internal" in self.endpoint:
        return self.endpoint.replace("-internal", "")
    return self.endpoint

def _generate_public_url(self, object_name: str) -> str:
    """生成公网可访问的URL"""
    public_endpoint = self._get_public_endpoint()
    return f"https://{self.bucket_name}.{public_endpoint}/{object_name}"

# 在 upload_for_ai_analysis 方法中使用公网URL
if result.status == 200:
    # 使用公网端点生成URL，确保AI服务可以访问
    public_url = self._generate_public_url(object_name)
    
    logger.info(
        f"AI图片上传成功: user={user_id}, object={object_name}, "
        f"public_url={public_url}, size={len(content)}"
    )
'''

    return fix_code


def main():
    """主函数"""
    print("🚀 百炼VL模型图片访问问题修复工具")
    print("=" * 50)

    # 分析配置
    analysis = analyze_oss_config()

    if analysis["has_issue"]:
        print("\n❌ 发现问题: OSS使用内网端点，百炼AI无法访问")
        print("\n🔧 修复步骤:")
        print("1. 修改AI图片服务，为AI生成公网URL")
        print("2. 保持上传使用内网端点（提升传输速度）")
        print("3. 返回给前端的ai_accessible_url使用公网地址")
        print("4. 测试百炼AI能否正常访问修复后的URL")

        print("\n📝 需要应用的代码修复:")
        print(generate_fix_code())

        print("\n⚡ 立即修复: 运行以下命令")
        print("   python scripts/fix_ai_image_url.py")

    else:
        print("\n✅ OSS配置正常，问题可能在其他地方")
        print("\n🔍 其他可能的原因:")
        print("1. 百炼平台VL模型配置问题")
        print("2. 图片格式不支持")
        print("3. OSS bucket权限设置问题")
        print("4. 网络连接问题")


if __name__ == "__main__":
    main()
