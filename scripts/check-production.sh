#!/bin/bash
# 快速验证生产环境状态

set -e

SERVER="121.199.173.244"
DOMAIN="horsduroot.com"

echo "=========================================="
echo "五好伴学 - 生产环境状态检查"
echo "=========================================="
echo

# 1. 检查后端服务
echo "📍 1. 后端服务状态"
if ssh root@${SERVER} "systemctl is-active --quiet wuhao-tutor.service"; then
    echo "   ✅ 服务运行中"
    ssh root@${SERVER} "systemctl status wuhao-tutor.service --no-pager | head -3"
else
    echo "   ❌ 服务未运行"
    exit 1
fi
echo

# 2. 检查后端 API
echo "📍 2. 后端 API 健康检查"
if curl -s "https://${DOMAIN}/api/v1/health" | grep -q "ok"; then
    echo "   ✅ API 响应正常"
else
    echo "   ❌ API 无响应"
fi
echo

# 3. 检查前端
echo "📍 3. 前端页面检查"
if curl -s -o /dev/null -w "%{http_code}" "https://${DOMAIN}" | grep -q "200"; then
    echo "   ✅ 前端页面正常"
else
    echo "   ❌ 前端页面异常"
fi
echo

# 4. 检查 SSL 证书
echo "📍 4. SSL 证书检查"
CERT_DAYS=$(echo | openssl s_client -servername ${DOMAIN} -connect ${DOMAIN}:443 2>/dev/null | openssl x509 -noout -checkend 0 2>/dev/null && echo "✅ 证书有效" || echo "⚠️  证书即将过期")
echo "   ${CERT_DAYS}"
echo

# 5. 检查磁盘空间
echo "📍 5. 磁盘空间"
ssh root@${SERVER} "df -h / | tail -1 | awk '{print \"   使用: \" \$5 \" (剩余: \" \$4 \")\"}'"
echo

# 6. 检查内存使用
echo "📍 6. 内存使用"
ssh root@${SERVER} "free -h | grep Mem | awk '{print \"   已用: \" \$3 \" / 总共: \" \$2}'"
echo

echo "=========================================="
echo "✅ 检查完成"
echo "=========================================="
