#!/bin/bash
# scripts/diagnose_mobile_cache_issue.sh
# 移动端缓存问题诊断工具

set -e

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔍 移动端缓存问题诊断工具${NC}"
echo "=============================="
echo ""

# 1. 检查本地构建
echo -e "${YELLOW}1️⃣ 检查本地构建产物${NC}"
if [ -d "frontend/dist/assets" ]; then
    echo -e "${GREEN}✅ 构建目录存在${NC}"
    JS_COUNT=$(ls -1 frontend/dist/assets/*.js 2>/dev/null | wc -l | tr -d ' ')
    echo "   JS文件数量: $JS_COUNT"
    LATEST_FILE=$(ls -lt frontend/dist/assets/*.js 2>/dev/null | head -1 | awk '{print $9, $6, $7, $8}')
    echo "   最新文件: $LATEST_FILE"
    
    # 检查关键词
    if grep -r "错题手册" frontend/dist/assets/*.js > /dev/null 2>&1; then
        echo -e "${GREEN}✅ 本地构建包含新功能（错题手册）${NC}"
    else
        echo -e "${RED}❌ 本地构建不包含新功能${NC}"
        echo -e "${YELLOW}   建议: 执行 cd frontend && npm run build${NC}"
    fi
    
    if grep -r "作业问答" frontend/dist/assets/*.js > /dev/null 2>&1; then
        echo -e "${GREEN}✅ 本地构建包含新功能（作业问答）${NC}"
    else
        echo -e "${RED}❌ 本地构建不包含新功能（作业问答）${NC}"
    fi
else
    echo -e "${RED}❌ 构建目录不存在，请先执行构建${NC}"
    echo -e "${YELLOW}   执行: cd frontend && npm run build${NC}"
fi
echo ""

# 2. 检查生产服务器
echo -e "${YELLOW}2️⃣ 检查生产服务器文件${NC}"
SERVER_CHECK=$(ssh root@121.199.173.244 2>&1 << 'EOF'
if [ -d "/var/www/html/assets" ]; then
    echo "DIR_EXISTS:true"
    ls -1 /var/www/html/assets/*.js 2>/dev/null | wc -l
    ls -lt /var/www/html/assets/*.js 2>/dev/null | head -1 | awk '{print $9, $6, $7, $8}'
    
    if grep -r "错题手册" /var/www/html/assets/*.js > /dev/null 2>&1; then
        echo "HAS_MISTAKE:true"
    else
        echo "HAS_MISTAKE:false"
    fi
    
    if grep -r "作业问答" /var/www/html/assets/*.js > /dev/null 2>&1; then
        echo "HAS_QA:true"
    else
        echo "HAS_QA:false"
    fi
else
    echo "DIR_EXISTS:false"
fi
EOF
)

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ 无法连接到生产服务器${NC}"
    echo -e "${YELLOW}   请确认 SSH 配置正确${NC}"
else
    if echo "$SERVER_CHECK" | grep -q "DIR_EXISTS:true"; then
        echo -e "${GREEN}✅ 服务器文件目录存在${NC}"
        
        JS_COUNT=$(echo "$SERVER_CHECK" | sed -n '2p' | tr -d ' ')
        echo "   JS文件数量: $JS_COUNT"
        
        LATEST=$(echo "$SERVER_CHECK" | sed -n '3p')
        echo "   最新文件: $LATEST"
        
        if echo "$SERVER_CHECK" | grep -q "HAS_MISTAKE:true"; then
            echo -e "${GREEN}✅ 服务器包含新功能（错题手册）${NC}"
        else
            echo -e "${RED}❌ 服务器不包含新功能（错题手册）${NC}"
            echo -e "${YELLOW}   建议: 重新部署 ./scripts/deploy_to_production.sh${NC}"
        fi
        
        if echo "$SERVER_CHECK" | grep -q "HAS_QA:true"; then
            echo -e "${GREEN}✅ 服务器包含新功能（作业问答）${NC}"
        else
            echo -e "${RED}❌ 服务器不包含新功能（作业问答）${NC}"
        fi
    else
        echo -e "${RED}❌ 服务器文件目录不存在${NC}"
        echo -e "${YELLOW}   建议: 执行首次部署${NC}"
    fi
fi
echo ""

# 3. 检查 Nginx 配置
echo -e "${YELLOW}3️⃣ 检查 Nginx 缓存配置${NC}"
NGINX_CONFIG=$(ssh root@121.199.173.244 2>&1 << 'EOF'
grep -A 3 "location.*\.(js|css" /etc/nginx/conf.d/wuhao-tutor.conf | grep -E "expires|Cache-Control"
EOF
)

if [ $? -eq 0 ]; then
    echo "$NGINX_CONFIG"
    
    if echo "$NGINX_CONFIG" | grep -q "expires 1y"; then
        echo -e "${YELLOW}⚠️  检测到长缓存配置 (1年)${NC}"
        echo -e "${YELLOW}   这可能导致移动端浏览器缓存旧版本${NC}"
        echo -e "${YELLOW}   建议: 修改 nginx/conf.d/wuhao-tutor.conf${NC}"
    fi
    
    if echo "$NGINX_CONFIG" | grep -q "immutable"; then
        echo -e "${YELLOW}⚠️  检测到 immutable 缓存标记${NC}"
        echo -e "${YELLOW}   浏览器会认为文件永远不变${NC}"
    fi
else
    echo -e "${RED}❌ 无法读取 Nginx 配置${NC}"
fi
echo ""

# 4. 测试 HTTP 响应（在服务器端执行）
echo -e "${YELLOW}4️⃣ 测试 HTTP 响应头${NC}"

CACHE_TEST=$(ssh root@121.199.173.244 2>&1 << 'EOF'
# 测试 index.html
echo "INDEX_CACHE_TEST:"
curl -sI http://localhost/ 2>/dev/null | grep -i -E "cache-control|expires" || echo "No cache headers"

echo ""
echo "JS_CACHE_TEST:"
# 测试 JS 文件
JS_FILE=$(ls /var/www/html/assets/*.js 2>/dev/null | head -1)
if [ -n "$JS_FILE" ]; then
    JS_FILENAME=$(basename "$JS_FILE")
    curl -sI "http://localhost/assets/$JS_FILENAME" 2>/dev/null | grep -i -E "cache-control|expires" || echo "No cache headers"
fi
EOF
)

if [ $? -eq 0 ]; then
    echo "index.html 缓存策略:"
    INDEX_RESULT=$(echo "$CACHE_TEST" | sed -n '/INDEX_CACHE_TEST:/,/^$/p' | grep -v INDEX_CACHE_TEST)
    echo "$INDEX_RESULT"
    
    if echo "$INDEX_RESULT" | grep -qi "no-cache"; then
        echo -e "${GREEN}✅ index.html 配置为不缓存${NC}"
    elif echo "$INDEX_RESULT" | grep -qi "No cache headers"; then
        echo -e "${YELLOW}⚠️  index.html 没有缓存头配置${NC}"
    else
        echo -e "${RED}❌ index.html 可能被缓存${NC}"
    fi
    echo ""
    
    echo "JS 文件缓存策略:"
    JS_RESULT=$(echo "$CACHE_TEST" | sed -n '/JS_CACHE_TEST:/,//p' | grep -v JS_CACHE_TEST | grep -v "^$")
    echo "$JS_RESULT"
    
    if echo "$JS_RESULT" | grep -qi "max-age=31536000"; then
        echo -e "${YELLOW}⚠️  JS 文件缓存1年，可能导致更新延迟${NC}"
    fi
else
    echo -e "${RED}❌ 无法测试 HTTP 响应头${NC}"
fi
echo ""

# 5. 文件对比
echo -e "${YELLOW}5️⃣ 本地与服务器文件对比${NC}"
if [ -d "frontend/dist/assets" ]; then
    LOCAL_JS=$(ls -1 frontend/dist/assets/*.js 2>/dev/null | head -1 | xargs basename)
    REMOTE_JS=$(ssh root@121.199.173.244 "ls -1 /var/www/html/assets/*.js 2>/dev/null | head -1" 2>/dev/null | xargs basename)
    
    if [ -n "$LOCAL_JS" ] && [ -n "$REMOTE_JS" ]; then
        if [ "$LOCAL_JS" == "$REMOTE_JS" ]; then
            echo -e "${GREEN}✅ 本地和服务器文件名一致${NC}"
            echo "   文件: $LOCAL_JS"
        else
            echo -e "${YELLOW}⚠️  本地和服务器文件名不同${NC}"
            echo "   本地: $LOCAL_JS"
            echo "   服务器: $REMOTE_JS"
            echo -e "${YELLOW}   建议: 重新部署${NC}"
        fi
    fi
fi
echo ""

# 6. 生成诊断报告
echo "=============================="
echo -e "${BLUE}📋 诊断报告总结${NC}"
echo "=============================="
echo ""

# 判断问题类型
ISSUE_TYPE="unknown"

if echo "$SERVER_CHECK" | grep -q "HAS_MISTAKE:false"; then
    ISSUE_TYPE="not_deployed"
    echo -e "${RED}🔴 问题类型: 服务器文件未更新${NC}"
    echo ""
    echo "📝 解决步骤:"
    echo "1. 确认本地已构建最新版本"
    echo "   cd frontend && npm run build"
    echo ""
    echo "2. 执行部署脚本"
    echo "   ./scripts/deploy_to_production.sh"
    echo ""
    echo "3. 验证部署成功"
    echo "   ./scripts/diagnose_mobile_cache_issue.sh"
    
elif echo "$NGINX_CONFIG" | grep -q "expires 1y"; then
    ISSUE_TYPE="cache_config"
    echo -e "${YELLOW}🟡 问题类型: Nginx 缓存配置过激进${NC}"
    echo ""
    echo "📝 解决步骤:"
    echo "1. 短期方案: 让用户清除浏览器缓存"
    echo "   iOS Safari: 设置 → Safari → 清除历史记录与网站数据"
    echo "   Android Chrome: 设置 → 隐私 → 清除浏览数据"
    echo "   微信: 设置 → 通用 → 存储空间 → 清理缓存"
    echo ""
    echo "2. 长期方案: 优化 Nginx 配置"
    echo "   修改文件: nginx/conf.d/wuhao-tutor.conf"
    echo "   参考文档: docs/fixes/MOBILE_CACHE_ISSUE_ANALYSIS.md"
    echo "   执行: ssh root@121.199.173.244 'systemctl reload nginx'"
    
else
    ISSUE_TYPE="deployed"
    echo -e "${GREEN}🟢 服务器文件已更新${NC}"
    echo ""
    echo "📝 用户解决方案:"
    echo "问题原因: 手机浏览器缓存了旧版本的 JS/CSS 文件"
    echo ""
    echo "清除缓存方法:"
    echo ""
    echo "【iOS Safari】"
    echo "  设置 → Safari → 清除历史记录与网站数据"
    echo "  或: 长按刷新按钮 → 选择'清除缓存并重新加载'"
    echo ""
    echo "【Android Chrome】"
    echo "  菜单 → 设置 → 隐私设置 → 清除浏览数据"
    echo "  勾选'缓存的图像和文件' → 清除数据"
    echo ""
    echo "【微信内置浏览器】"
    echo "  我 → 设置 → 通用 → 存储空间 → 清理缓存"
    echo "  退出微信重新进入"
    echo ""
    echo "【快速方案】"
    echo "  使用隐私/无痕模式访问网站"
    echo "  或在地址栏后加: ?_t=$(date +%s)"
fi

echo ""
echo "=============================="
echo -e "${BLUE}📚 相关文档${NC}"
echo "=============================="
echo "详细分析报告: docs/fixes/MOBILE_CACHE_ISSUE_ANALYSIS.md"
echo "Nginx 优化配置: 见分析报告 '层次2' 部分"
echo "部署流程优化: 见分析报告 '层次3' 部分"
echo ""

# 保存诊断结果到文件
REPORT_FILE="diagnostic_report_$(date +%Y%m%d_%H%M%S).txt"
{
    echo "移动端缓存问题诊断报告"
    echo "生成时间: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "=============================="
    echo ""
    echo "问题类型: $ISSUE_TYPE"
    echo ""
    echo "服务器检查结果:"
    echo "$SERVER_CHECK"
    echo ""
    echo "Nginx 配置:"
    echo "$NGINX_CONFIG"
} > "$REPORT_FILE"

echo -e "${GREEN}✅ 诊断报告已保存: $REPORT_FILE${NC}"
