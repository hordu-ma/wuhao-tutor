#!/bin/bash

echo "🔍 当前生产环境API密钥状态检查"

# 显示当前配置
echo "📋 当前配置:"
ssh root@121.199.173.244 'cd /opt/wuhao-tutor && grep BAILIAN .env.production'

echo ""
echo "🧪 测试当前密钥:"
# 获取当前密钥
CURRENT_KEY=$(ssh root@121.199.173.244 'cd /opt/wuhao-tutor && grep BAILIAN_API_KEY .env.production | cut -d= -f2')

# 测试密钥
TEST_RESULT=$(ssh root@121.199.173.244 "curl -s -H 'Authorization: Bearer $CURRENT_KEY' -H 'Content-Type: application/json' -X POST https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions -d '{\"model\":\"qwen-plus\",\"messages\":[{\"role\":\"user\",\"content\":\"你好\"}]}'")

if echo "$TEST_RESULT" | grep -q '"choices"'; then
    echo "✅ API密钥有效"
else
    echo "❌ API密钥无效"
    echo "错误信息: $TEST_RESULT"
    echo ""
    echo "📝 请按以下步骤获取新密钥:"
    echo "1. 登录阿里云控制台"
    echo "2. 进入百炼大模型服务"
    echo "3. 查看/重新生成API密钥"
    echo "4. 使用新密钥运行: ./scripts/update_api_key.sh sk-新密钥"
fi

echo ""
echo "🔗 阿里云百炼控制台: https://bailian.console.aliyun.com/"