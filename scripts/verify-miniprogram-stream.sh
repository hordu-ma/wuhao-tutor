#!/bin/bash
# 微信小程序流式响应验证脚本

echo "========================================="
echo "微信小程序 SSE 流式响应验证脚本"
echo "========================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 验证步骤
echo -e "${YELLOW}📋 验证清单:${NC}"
echo ""

# 1. 检查后端端点
echo -e "${YELLOW}1️⃣  检查后端 SSE 端点${NC}"
echo "   测试命令: curl -X POST https://horsduroot.com/api/v1/learning/ask-stream \\"
echo "              -H 'Content-Type: application/json' \\"
echo "              -H 'Authorization: Bearer YOUR_TOKEN' \\"
echo "              -d '{\"content\":\"1+1=?\"}'"
echo ""

# 2. 检查前端代码
echo -e "${YELLOW}2️⃣  检查前端代码修改${NC}"
echo "   ✅ miniprogram/api/learning.js - askQuestionStream() 方法已添加"
echo "   ✅ miniprogram/pages/learning/index/index.js - sendMessage() 已更新"
echo ""

# 3. 微信开发者工具测试
echo -e "${YELLOW}3️⃣  微信开发者工具测试步骤${NC}"
echo "   a) 打开微信开发者工具"
echo "   b) 打开项目: wuhao-tutor/miniprogram"
echo "   c) 编译小程序"
echo "   d) 打开控制台（Console 面板）"
echo "   e) 进入学习页面"
echo "   f) 发送一个问题（例如: '1+1等于几？'）"
echo ""

# 4. 验证关键日志
echo -e "${YELLOW}4️⃣  验证控制台日志（必须看到以下内容）${NC}"
echo "   ✅ [SSE Stream] 开始流式请求: https://..."
echo "   ✅ [SSE Chunk] {type: 'content', content: '1', ...}"
echo "   ✅ [SSE Chunk] {type: 'content', content: '+', ...}"
echo "   ✅ [SSE Chunk] {type: 'content', content: '1', ...}"
echo "   ✅ [Stream Chunk] ... (多个)"
echo "   ✅ [Stream Complete] {question: {...}, answer: {...}}"
echo ""

# 5. 验证用户体验
echo -e "${YELLOW}5️⃣  验证用户体验（页面表现）${NC}"
echo "   ✅ 问题发送后，立即显示 AI 消息占位符"
echo "   ✅ < 2 秒内开始逐字显示内容（非一次性显示）"
echo "   ✅ 内容实时累积，自动滚动到底部"
echo "   ✅ Markdown 格式实时渲染（粗体、代码块等）"
echo "   ✅ 完成后消息状态变为 'received'"
echo ""

# 6. 常见问题排查
echo -e "${YELLOW}6️⃣  常见问题排查${NC}"
echo "   ❌ 如果看不到 [SSE Chunk] 日志:"
echo "      → 检查是否调用了 askQuestionStream() 而非 askQuestion()"
echo "      → 检查微信开发者工具基础库版本 >= 2.20.1"
echo "      → 检查网络请求是否被拦截（Network 面板）"
echo ""
echo "   ❌ 如果内容一次性显示（非流式）:"
echo "      → 检查 onChunkReceived 回调是否触发"
echo "      → 检查 setData() 是否在回调中调用"
echo "      → 检查是否使用了节流导致更新延迟"
echo ""
echo "   ❌ 如果首字响应时间 > 5 秒:"
echo "      → 检查后端日志是否正常流式返回"
echo "      → 检查网络延迟（Network 面板）"
echo "      → 测试后端 API 是否正常工作"
echo ""

# 7. 测试 token
echo -e "${YELLOW}7️⃣  测试账号信息${NC}"
echo "   账号: 13800000001"
echo "   密码: password123"
echo "   Token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
echo ""

# 8. 回滚方案
echo -e "${YELLOW}8️⃣  如果需要紧急回滚${NC}"
echo "   修改: miniprogram/pages/learning/index/index.js 第 784 行"
echo "   替换: await api.learning.askQuestionStream(...)"
echo "   为:   await api.learning.askQuestion(requestParams)"
echo ""

echo "========================================="
echo -e "${GREEN}✅ 准备就绪！请在微信开发者工具中开始测试${NC}"
echo "========================================="
echo ""

# 可选：自动打开文档
if command -v open &> /dev/null; then
  echo "📖 打开修复文档？(y/n)"
  read -r response
  if [[ "$response" =~ ^[Yy]$ ]]; then
    open "docs/solutions/miniprogram-sse-stream-fix.md"
  fi
fi
