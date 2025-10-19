#!/bin/bash

################################################################################
# 域名切换验证脚本
#
# 执行位置: 本地 Mac 或任何可访问互联网的机器
# 使用方式: bash verify-domain-migration.sh
# 作者: Auto-generated
# 日期: 2025-10-19
################################################################################

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 配置
DOMAIN="www.horsduroot.com"
ROOT_DOMAIN="horsduroot.com"
TARGET_IP="121.199.173.244"
OLD_IP="60.205.124.67"

# 统计变量
PASSED=0
FAILED=0
WARNING=0

# 日志函数
log_test() {
    echo -e "${BLUE}[TEST]${NC} $1"
}

log_pass() {
    echo -e "${GREEN}[PASS]${NC} $1"
    ((PASSED++))
}

log_fail() {
    echo -e "${RED}[FAIL]${NC} $1"
    ((FAILED++))
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
    ((WARNING++))
}

# 分隔线
separator() {
    echo ""
    echo "=============================================="
    echo ""
}

# 测试 1: DNS 解析
test_dns() {
    separator
    log_test "测试 1: DNS 解析验证"
    
    # 测试 www 域名
    WWW_IP=$(nslookup $DOMAIN 2>/dev/null | grep -A1 "Name:" | tail -1 | awk '{print $2}')
    if [[ "$WWW_IP" == "$TARGET_IP" ]]; then
        log_pass "$DOMAIN 解析正确: $WWW_IP"
    elif [[ "$WWW_IP" == "$OLD_IP" ]]; then
        log_fail "$DOMAIN 仍解析到旧 IP: $WWW_IP (预期: $TARGET_IP)"
    else
        log_warn "$DOMAIN 解析到未知 IP: $WWW_IP (预期: $TARGET_IP)"
    fi
    
    # 测试根域名
    ROOT_IP=$(nslookup $ROOT_DOMAIN 2>/dev/null | grep -A1 "Name:" | tail -1 | awk '{print $2}')
    if [[ "$ROOT_IP" == "$TARGET_IP" ]]; then
        log_pass "$ROOT_DOMAIN 解析正确: $ROOT_IP"
    elif [[ "$ROOT_IP" == "$OLD_IP" ]]; then
        log_fail "$ROOT_DOMAIN 仍解析到旧 IP: $ROOT_IP (预期: $TARGET_IP)"
    else
        log_warn "$ROOT_DOMAIN 解析到未知 IP: $ROOT_IP (预期: $TARGET_IP)"
    fi
    
    # 检查 DNS 传播
    log_test "检查全球 DNS 传播情况..."
    echo "  访问 https://www.whatsmydns.net/#A/$DOMAIN 查看详情"
}

# 测试 2: HTTP 访问和跳转
test_http() {
    separator
    log_test "测试 2: HTTP 访问和 HTTPS 跳转"
    
    # 测试 HTTP 跳转
    HTTP_RESPONSE=$(curl -s -I -L http://$DOMAIN 2>&1)
    HTTP_CODE=$(echo "$HTTP_RESPONSE" | grep "HTTP/" | head -1 | awk '{print $2}')
    
    if echo "$HTTP_RESPONSE" | grep -q "301\|302"; then
        log_pass "HTTP 自动跳转 HTTPS (状态码: $HTTP_CODE)"
    else
        log_warn "HTTP 响应状态码: $HTTP_CODE (预期: 301 或 302)"
    fi
    
    # 检查跳转目标
    LOCATION=$(echo "$HTTP_RESPONSE" | grep -i "Location:" | head -1 | awk '{print $2}' | tr -d '\r')
    if [[ "$LOCATION" == https://$DOMAIN* ]] || [[ "$LOCATION" == https://$ROOT_DOMAIN* ]]; then
        log_pass "跳转目标正确: $LOCATION"
    else
        log_warn "跳转目标: $LOCATION (请检查是否正确)"
    fi
}

# 测试 3: HTTPS 访问
test_https() {
    separator
    log_test "测试 3: HTTPS 访问和 SSL 证书"
    
    # 测试 HTTPS 连接
    HTTPS_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://$DOMAIN)
    if [[ "$HTTPS_CODE" == "200" ]]; then
        log_pass "HTTPS 访问正常 (状态码: $HTTPS_CODE)"
    else
        log_fail "HTTPS 访问失败 (状态码: $HTTPS_CODE)"
    fi
    
    # 测试 SSL 证书
    if command -v openssl &> /dev/null; then
        CERT_INFO=$(echo | openssl s_client -servername $DOMAIN -connect $DOMAIN:443 2>/dev/null | openssl x509 -noout -dates 2>/dev/null)
        
        if [[ -n "$CERT_INFO" ]]; then
            NOT_BEFORE=$(echo "$CERT_INFO" | grep "notBefore" | cut -d= -f2)
            NOT_AFTER=$(echo "$CERT_INFO" | grep "notAfter" | cut -d= -f2)
            
            log_pass "SSL 证书有效"
            echo "  颁发时间: $NOT_BEFORE"
            echo "  到期时间: $NOT_AFTER"
            
            # 检查证书颁发者
            CERT_ISSUER=$(echo | openssl s_client -servername $DOMAIN -connect $DOMAIN:443 2>/dev/null | openssl x509 -noout -issuer 2>/dev/null | cut -d= -f2-)
            echo "  颁发者: $CERT_ISSUER"
        else
            log_fail "无法获取 SSL 证书信息"
        fi
    else
        log_warn "未安装 openssl，跳过证书检查"
    fi
}

# 测试 4: API 接口
test_api() {
    separator
    log_test "测试 4: API 接口验证"
    
    # 测试健康检查
    HEALTH_RESPONSE=$(curl -s https://$DOMAIN/health)
    if echo "$HEALTH_RESPONSE" | grep -q "healthy\|ok\|success"; then
        log_pass "健康检查接口正常: $HEALTH_RESPONSE"
    else
        log_fail "健康检查接口异常: $HEALTH_RESPONSE"
    fi
    
    # 测试 API 文档
    DOCS_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://$DOMAIN/docs)
    if [[ "$DOCS_CODE" == "200" ]]; then
        log_pass "API 文档访问正常 (https://$DOMAIN/docs)"
    else
        log_warn "API 文档访问异常 (状态码: $DOCS_CODE)"
    fi
    
    # 测试 OpenAPI Schema
    OPENAPI_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://$DOMAIN/openapi.json)
    if [[ "$OPENAPI_CODE" == "200" ]]; then
        log_pass "OpenAPI Schema 访问正常"
    else
        log_warn "OpenAPI Schema 访问异常 (状态码: $OPENAPI_CODE)"
    fi
}

# 测试 5: 性能检查
test_performance() {
    separator
    log_test "测试 5: 性能检查"
    
    # 测试响应时间
    RESPONSE_TIME=$(curl -s -o /dev/null -w "%{time_total}" https://$DOMAIN/health)
    RESPONSE_MS=$(echo "$RESPONSE_TIME * 1000" | bc)
    
    if (( $(echo "$RESPONSE_TIME < 1.0" | bc -l) )); then
        log_pass "响应时间: ${RESPONSE_MS} ms (优秀)"
    elif (( $(echo "$RESPONSE_TIME < 3.0" | bc -l) )); then
        log_pass "响应时间: ${RESPONSE_MS} ms (良好)"
    else
        log_warn "响应时间: ${RESPONSE_MS} ms (较慢，建议优化)"
    fi
    
    # 测试 TTFB (Time To First Byte)
    TTFB=$(curl -s -o /dev/null -w "%{time_starttransfer}" https://$DOMAIN)
    TTFB_MS=$(echo "$TTFB * 1000" | bc)
    echo "  首字节时间 (TTFB): ${TTFB_MS} ms"
    
    # 测试 DNS 解析时间
    DNS_TIME=$(curl -s -o /dev/null -w "%{time_namelookup}" https://$DOMAIN)
    DNS_MS=$(echo "$DNS_TIME * 1000" | bc)
    echo "  DNS 解析时间: ${DNS_MS} ms"
}

# 测试 6: 安全检查
test_security() {
    separator
    log_test "测试 6: 安全配置检查"
    
    # 检查安全响应头
    HEADERS=$(curl -s -I https://$DOMAIN)
    
    # Strict-Transport-Security
    if echo "$HEADERS" | grep -qi "Strict-Transport-Security"; then
        log_pass "HSTS 已启用"
    else
        log_warn "HSTS 未启用 (建议配置)"
    fi
    
    # X-Frame-Options
    if echo "$HEADERS" | grep -qi "X-Frame-Options"; then
        log_pass "X-Frame-Options 已配置"
    else
        log_warn "X-Frame-Options 未配置 (建议添加)"
    fi
    
    # X-Content-Type-Options
    if echo "$HEADERS" | grep -qi "X-Content-Type-Options"; then
        log_pass "X-Content-Type-Options 已配置"
    else
        log_warn "X-Content-Type-Options 未配置 (建议添加)"
    fi
    
    # 检查 TLS 版本
    TLS_VERSION=$(echo | openssl s_client -servername $DOMAIN -connect $DOMAIN:443 2>/dev/null | grep "Protocol" | awk '{print $3}')
    if [[ "$TLS_VERSION" == "TLSv1.2" ]] || [[ "$TLS_VERSION" == "TLSv1.3" ]]; then
        log_pass "TLS 版本: $TLS_VERSION (安全)"
    else
        log_warn "TLS 版本: $TLS_VERSION (建议升级)"
    fi
}

# 测试 7: 静态资源
test_static_resources() {
    separator
    log_test "测试 7: 静态资源访问"
    
    # 测试静态文件路径
    STATIC_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://$DOMAIN/static/)
    if [[ "$STATIC_CODE" == "200" ]] || [[ "$STATIC_CODE" == "403" ]] || [[ "$STATIC_CODE" == "404" ]]; then
        log_pass "静态文件路径可访问 (状态码: $STATIC_CODE)"
    else
        log_warn "静态文件路径异常 (状态码: $STATIC_CODE)"
    fi
}

# 测试 8: 旧服务器流量检查
test_old_server() {
    separator
    log_test "测试 8: 旧服务器流量检查"
    
    echo "  提示: 请 SSH 登录旧服务器 ($OLD_IP) 检查访问日志"
    echo ""
    echo "  执行命令:"
    echo "    ssh root@$OLD_IP"
    echo "    tail -n 100 /var/log/nginx/access.log"
    echo ""
    echo "  预期结果: 24-48 小时后应无新访问记录"
    log_warn "此项需要手动检查"
}

# 生成测试报告
generate_report() {
    separator
    echo ""
    echo "=========================================="
    echo "          测试报告汇总"
    echo "=========================================="
    echo ""
    echo "  通过: ${GREEN}$PASSED${NC}"
    echo "  失败: ${RED}$FAILED${NC}"
    echo "  警告: ${YELLOW}$WARNING${NC}"
    echo ""
    
    if [[ $FAILED -eq 0 ]]; then
        echo -e "${GREEN}✓ 域名切换成功！${NC}"
        echo ""
        echo "  访问地址: https://$DOMAIN"
        echo "  API 文档: https://$DOMAIN/docs"
        echo ""
        echo "后续操作:"
        echo "  1. 更新小程序服务器域名配置"
        echo "  2. 重新构建并部署前端"
        echo "  3. 监控错误日志 24-48 小时"
        echo "  4. 停止旧服务器"
    else
        echo -e "${RED}✗ 域名切换存在问题，请检查失败项${NC}"
        echo ""
        echo "排查建议:"
        echo "  1. 查看新服务器错误日志: tail -f /var/log/nginx/error.log"
        echo "  2. 检查 DNS 解析是否生效: nslookup $DOMAIN"
        echo "  3. 检查 SSL 证书: https://www.ssllabs.com/ssltest/analyze.html?d=$DOMAIN"
        echo "  4. 参考文档: docs/deployment/domain-migration-guide.md"
    fi
    
    echo ""
    separator
}

# 主函数
main() {
    echo ""
    echo "=========================================="
    echo "  域名切换验证脚本"
    echo "  目标域名: $DOMAIN"
    echo "  执行时间: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "=========================================="
    
    test_dns
    test_http
    test_https
    test_api
    test_performance
    test_security
    test_static_resources
    test_old_server
    generate_report
}

# 执行主函数
main "$@"
