#!/bin/bash

# 更新阿里云百炼API密钥脚本
# 使用方法: ./update_api_key.sh <new_api_key>

if [ $# -ne 1 ]; then
    echo "用法: $0 <新的API密钥>"
    echo "例如: $0 sk-xxxxxxxxxxxxxxxxxx"
    exit 1
fi

NEW_API_KEY="$1"

# 验证密钥格式
if [[ ! "$NEW_API_KEY" =~ ^sk- ]]; then
    echo "❌ 错误: API密钥必须以 'sk-' 开头"
    exit 1
fi

echo "🔄 更新阿里云百炼API密钥..."

# 更新生产环境配置
ssh root@121.199.173.244 "cd /opt/wuhao-tutor && sed -i 's/BAILIAN_API_KEY=.*/BAILIAN_API_KEY=$NEW_API_KEY/' .env.production"

echo "✅ 配置文件已更新"

# 重启服务
echo "🔄 重启后端服务..."
ssh root@121.199.173.244 'systemctl restart wuhao-tutor.service'

echo "⏳ 等待服务启动..."
sleep 5

# 验证服务状态
echo "🔍 验证服务状态..."
if ssh root@121.199.173.244 'systemctl is-active --quiet wuhao-tutor.service'; then
    echo "✅ 服务已成功重启"
else
    echo "❌ 服务启动失败，请检查日志"
    exit 1
fi

# 测试API密钥
echo "🧪 测试新API密钥..."
TEST_RESULT=$(ssh root@121.199.173.244 "curl -s -H 'Authorization: Bearer $NEW_API_KEY' -H 'Content-Type: application/json' -X POST https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions -d '{\"model\":\"qwen-plus\",\"messages\":[{\"role\":\"user\",\"content\":\"你好\"}]}'")

if echo "$TEST_RESULT" | grep -q '"choices"'; then
    echo "✅ 新API密钥验证成功！"
    echo "🎉 密钥更新完成，作业问答功能已恢复"
else
    echo "❌ 新API密钥验证失败"
    echo "响应: $TEST_RESULT"
    exit 1
fi