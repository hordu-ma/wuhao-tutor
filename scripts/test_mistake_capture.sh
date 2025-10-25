#!/bin/bash

# 测试错题捕获功能
# 验证关键词扩展是否生效

echo "🧪 =========================================="
echo "🧪 测试错题捕获功能"
echo "🧪 =========================================="
echo ""

# 生产环境API地址
API_URL="https://horsduroot.com/api/v1/learning/ask"

# 测试用户token（需要先登录获取）
# 这里使用占位符，实际使用时需要替换为真实token
TEST_TOKEN="${TEST_TOKEN:-your_token_here}"

echo "📋 测试场景1: 包含关键词「不会」"
echo "   输入: 999+999这道题不会"
echo ""

# 测试请求（需要真实token）
cat << EOF > /tmp/test_request.json
{
  "content": "999+999这道题不会",
  "subject": "math",
  "use_context": true,
  "include_history": false
}
EOF

echo "📤 发送测试请求..."
echo ""

# 如果有token，发送真实请求
if [ "$TEST_TOKEN" != "your_token_here" ]; then
  curl -X POST "$API_URL" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $TEST_TOKEN" \
    -d @/tmp/test_request.json \
    | jq '.mistake_created, .mistake_info'
else
  echo "⚠️  未提供TEST_TOKEN，跳过真实请求测试"
  echo "   使用方式: TEST_TOKEN=your_token ./scripts/test_mistake_capture.sh"
fi

echo ""
echo "📋 测试场景2: 查看生产环境日志"
echo ""

ssh root@121.199.173.244 'journalctl -u wuhao-tutor.service -n 50 --no-pager | grep -E "(检测到|错题|mistake)" || echo "暂无相关日志"'

echo ""
echo "✅ =========================================="
echo "✅ 测试完成"
echo "✅ =========================================="
echo ""
echo "💡 提示："
echo "   1. 在小程序中测试输入：999+999这道题不会"
echo "   2. 查看Console日志中的API响应"
echo "   3. 检查 mistake_created 字段是否为 true"
echo "   4. 验证错题本列表是否新增记录"
echo ""
