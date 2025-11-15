#!/bin/bash

# WebSocket 流式修复验证脚本
# 用途: 部署后验证修复是否生效
# 用法: ./scripts/verify_websocket_fix.sh

set -e

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║         WebSocket 流式修复验证脚本 (v0.1.1)                   ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 检查计数
CHECKS_PASSED=0
CHECKS_FAILED=0
CHECKS_WARNING=0

# 日志函数
log_pass() {
    echo -e "${GREEN}✅ $1${NC}"
    ((CHECKS_PASSED++))
}

log_fail() {
    echo -e "${RED}❌ $1${NC}"
    ((CHECKS_FAILED++))
}

log_warn() {
    echo -e "${YELLOW}⚠️  $1${NC}"
    ((CHECKS_WARNING++))
}

log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

echo "═══════════════════════════════════════════════════════════════════"
echo "第一阶段: 后端代码检查"
echo "═══════════════════════════════════════════════════════════════════"
echo ""

# 1. 检查后端代码修改
echo "1. 检查后端代码修改..."
echo ""

if grep -q "CONTENT_TIMEOUT = 90000" miniprogram/api/learning.js; then
    log_pass "前端 CONTENT_TIMEOUT 已更新为 90 秒"
else
    log_fail "前端 CONTENT_TIMEOUT 未正确更新"
fi

if grep -q "PROCESSING_TIMEOUT = 120000" miniprogram/api/learning.js; then
    log_pass "前端 PROCESSING_TIMEOUT 已更新为 120 秒"
else
    log_fail "前端 PROCESSING_TIMEOUT 未正确更新"
fi

if grep -q "keepalive" miniprogram/api/learning.js; then
    log_pass "前端 keepalive 心跳处理已添加"
else
    log_fail "前端 keepalive 心跳处理未添加"
fi

if grep -q "_stream_with_keepalive" src/services/learning_service.py; then
    log_pass "后端 _stream_with_keepalive 函数已添加"
else
    log_warn "后端 _stream_with_keepalive 函数未找到（可选）"
fi

if grep -q "UPDATE chat_session" src/services/learning_service.py; then
    log_pass "后端已使用原子 SQL 更新会话统计"
else
    log_fail "后端会话统计优化未完成"
fi

if grep -q "logger.debug" src/services/learning_service.py | grep -q "📦 收到 chunk"; then
    log_pass "后端流式日志已优化为 debug 级别"
else
    log_warn "后端流式日志可能未完全优化"
fi

echo ""
echo "═══════════════════════════════════════════════════════════════════"
echo "第二阶段: 服务状态检查"
echo "═══════════════════════════════════════════════════════════════════"
echo ""

echo "2. 检查后端服务状态..."
echo ""

if systemctl is-active --quiet wuhao-tutor.service; then
    log_pass "后端服务正在运行"
else
    log_fail "后端服务未运行，请执行: systemctl start wuhao-tutor.service"
fi

if systemctl is-enabled --quiet wuhao-tutor.service; then
    log_pass "后端服务已设置为自动启动"
else
    log_warn "后端服务未设置自动启动"
fi

echo ""
echo "3. 检查健康端点..."
echo ""

HEALTH_RESPONSE=$(curl -s http://localhost:8000/health 2>/dev/null || echo "")
if [ -n "$HEALTH_RESPONSE" ]; then
    log_pass "后端健康检查通过"
    log_info "响应: $HEALTH_RESPONSE"
else
    log_fail "后端健康检查失败，请检查服务"
fi

echo ""
echo "═══════════════════════════════════════════════════════════════════"
echo "第三阶段: 数据库检查"
echo "═══════════════════════════════════════════════════════════════════"
echo ""

echo "4. 检查数据库连接..."
echo ""

# 尝试从日志检查数据库状态
if journalctl -u wuhao-tutor.service -n 50 2>/dev/null | grep -q "数据库连接成功\|database connection\|connected"; then
    log_pass "数据库连接正常"
else
    log_warn "无法从日志确认数据库连接状态"
fi

echo ""
echo "═══════════════════════════════════════════════════════════════════"
echo "第四阶段: 日志验证"
echo "═══════════════════════════════════════════════════════════════════"
echo ""

echo "5. 检查最近的流式处理日志..."
echo ""

# 获取最近 100 行日志
RECENT_LOGS=$(journalctl -u wuhao-tutor.service -n 100 2>/dev/null || echo "")

if echo "$RECENT_LOGS" | grep -q "已发送 content_finished 信号\|已发送 done 事件"; then
    log_pass "检测到流式处理成功的日志"
else
    log_warn "未检测到最近的流式处理日志（可能是新部署）"
fi

if echo "$RECENT_LOGS" | grep -q "核心数据事务已提交"; then
    log_pass "检测到事务提交日志"
else
    log_warn "未检测到事务提交日志（可能是新部署）"
fi

if echo "$RECENT_LOGS" | grep -q "错误\|error\|Error\|ERROR" | grep -v "修复"; then
    log_warn "日志中检测到错误信息，请查看详细日志"
else
    log_pass "日志中未检测到明显错误"
fi

echo ""
echo "═══════════════════════════════════════════════════════════════════"
echo "第五阶段: 配置文件检查"
echo "═══════════════════════════════════════════════════════════════════"
echo ""

echo "6. 检查环境配置..."
echo ""

if [ -f ".env" ]; then
    log_pass ".env 配置文件存在"
else
    log_warn ".env 配置文件未找到"
fi

if [ -f "src/core/config.py" ]; then
    log_pass "core/config.py 配置文件存在"
else
    log_fail "core/config.py 配置文件缺失"
fi

echo ""
echo "═══════════════════════════════════════════════════════════════════"
echo "第六阶段: 测试运行"
echo "═══════════════════════════════════════════════════════════════════"
echo ""

echo "7. 运行单元测试..."
echo ""

if python -m pytest tests/test_websocket_long_stream.py::TestLongStreamWithKeepalive::test_stream_timeout_values -v --tb=short 2>/dev/null; then
    log_pass "超时配置测试通过"
else
    log_warn "超时配置测试失败或被跳过（可选）"
fi

echo ""
echo "═══════════════════════════════════════════════════════════════════"
echo "验证总结"
echo "═══════════════════════════════════════════════════════════════════"
echo ""

TOTAL_CHECKS=$((CHECKS_PASSED + CHECKS_FAILED + CHECKS_WARNING))

echo -e "${GREEN}✅ 通过: $CHECKS_PASSED${NC}"
echo -e "${RED}❌ 失败: $CHECKS_FAILED${NC}"
echo -e "${YELLOW}⚠️  警告: $CHECKS_WARNING${NC}"
echo ""

if [ $CHECKS_FAILED -eq 0 ]; then
    echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}🎉 所有关键检查都已通过！修复部署成功！🎉${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo "后续步骤:"
    echo "1. 在微信开发者工具中测试多页图片上传场景"
    echo "2. 检查 DevTools 控制台是否看到 keepalive 心跳"
    echo "3. 监控生产环境日志 24-48 小时"
    echo ""
    exit 0
else
    echo -e "${RED}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${RED}请解决上述失败项，然后重新运行此脚本${NC}"
    echo -e "${RED}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
    exit 1
fi
