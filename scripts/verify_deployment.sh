#!/bin/bash
# 部署验证脚本 - 全面检查生产环境状态

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

HOST="${1:-121.199.173.244}"
TIMEOUT=10

echo -e "${BLUE}🔍 开始验证五好伴学生产环境部署...${NC}"
echo -e "${BLUE}目标主机: $HOST${NC}"

# 健康检查函数
check_service() {
    local name="$1"
    local url="$2"
    local expected_status="${3:-200}"
    
    echo -ne "${YELLOW}检查 $name...${NC}"
    
    if response=$(curl -s -w "%{http_code}" --connect-timeout $TIMEOUT "$url" -o /dev/null 2>/dev/null); then
        if [ "$response" = "$expected_status" ]; then
            echo -e " ${GREEN}✅ 正常 ($response)${NC}"
            return 0
        else
            echo -e " ${RED}❌ 异常 ($response)${NC}"
            return 1
        fi
    else
        echo -e " ${RED}❌ 无法连接${NC}"
        return 1
    fi
}

# 检查端口是否开放
check_port() {
    local name="$1"
    local port="$2"
    
    echo -ne "${YELLOW}检查 $name 端口 $port...${NC}"
    
    if nc -z -w$TIMEOUT "$HOST" "$port" 2>/dev/null; then
        echo -e " ${GREEN}✅ 开放${NC}"
        return 0
    else
        echo -e " ${RED}❌ 关闭${NC}"
        return 1
    fi
}

# 记录检查结果
declare -a passed_checks=()
declare -a failed_checks=()

record_result() {
    if [ $? -eq 0 ]; then
        passed_checks+=("$1")
    else
        failed_checks+=("$1")
    fi
}

echo ""
echo -e "${BLUE}📊 核心服务检查${NC}"
echo "----------------------------------------"

# 1. 应用API健康检查
check_service "应用API" "http://$HOST:8000/health"
record_result "应用API"

# 2. API文档
check_service "API文档" "http://$HOST:8000/docs"
record_result "API文档"

# 3. 根路径
check_service "应用根路径" "http://$HOST:8000/"
record_result "应用根路径"

echo ""
echo -e "${BLUE}🔧 监控服务检查${NC}"
echo "----------------------------------------"

# 4. Prometheus
check_service "Prometheus" "http://$HOST:9090/-/healthy"
record_result "Prometheus"

# 5. Grafana
check_service "Grafana" "http://$HOST:3000/api/health"
record_result "Grafana"

# 6. AlertManager
check_service "AlertManager" "http://$HOST:9093/-/healthy"
record_result "AlertManager"

echo ""
echo -e "${BLUE}📈 监控指标检查${NC}"
echo "----------------------------------------"

# 7. Node Exporter
check_service "Node Exporter" "http://$HOST:9100/metrics"
record_result "Node Exporter"

# 8. PostgreSQL Exporter
check_service "PostgreSQL Exporter" "http://$HOST:9187/metrics"
record_result "PostgreSQL Exporter"

# 9. Redis Exporter
check_service "Redis Exporter" "http://$HOST:9121/metrics"
record_result "Redis Exporter"

# 10. Nginx Exporter
check_service "Nginx Exporter" "http://$HOST:9113/metrics"
record_result "Nginx Exporter"

# 11. cAdvisor
check_service "cAdvisor" "http://$HOST:8080/containers/"
record_result "cAdvisor"

echo ""
echo -e "${BLUE}🌐 网络端口检查${NC}"
echo "----------------------------------------"

# 端口检查
check_port "HTTP" 80
record_result "HTTP端口"

check_port "HTTPS" 443
record_result "HTTPS端口"

check_port "API" 8000
record_result "API端口"

check_port "Grafana" 3000
record_result "Grafana端口"

check_port "Prometheus" 9090
record_result "Prometheus端口"

echo ""
echo -e "${BLUE}🔐 HTTPS检查${NC}"
echo "----------------------------------------"

# HTTPS检查 (自签名证书会失败，这是正常的)
echo -ne "${YELLOW}检查HTTPS证书...${NC}"
if curl -k -s --connect-timeout $TIMEOUT "https://$HOST/health" >/dev/null 2>&1; then
    echo -e " ${GREEN}✅ HTTPS可访问 (自签名证书)${NC}"
    passed_checks+=("HTTPS")
else
    echo -e " ${YELLOW}⚠️  HTTPS不可用 (需要配置证书)${NC}"
    failed_checks+=("HTTPS")
fi

echo ""
echo -e "${BLUE}💾 数据库连接检查${NC}"
echo "----------------------------------------"

# 尝试通过API检查数据库连接
echo -ne "${YELLOW}检查数据库连接...${NC}"
if response=$(curl -s "http://$HOST:8000/health" | grep -o '"database.*"' 2>/dev/null); then
    if echo "$response" | grep -q "healthy\|ok\|connected"; then
        echo -e " ${GREEN}✅ 数据库连接正常${NC}"
        passed_checks+=("数据库连接")
    else
        echo -e " ${RED}❌ 数据库连接异常${NC}"
        failed_checks+=("数据库连接")
    fi
else
    echo -e " ${YELLOW}⚠️  无法获取数据库状态${NC}"
    failed_checks+=("数据库连接")
fi

echo ""
echo -e "${BLUE}📊 检查结果汇总${NC}"
echo "========================================"

total_checks=$((${#passed_checks[@]} + ${#failed_checks[@]}))
pass_rate=$(( ${#passed_checks[@]} * 100 / total_checks ))

echo -e "${GREEN}✅ 通过检查: ${#passed_checks[@]}/$total_checks${NC}"
echo -e "${RED}❌ 失败检查: ${#failed_checks[@]}/$total_checks${NC}"
echo -e "${BLUE}📈 通过率: $pass_rate%${NC}"

if [ ${#passed_checks[@]} -gt 0 ]; then
    echo ""
    echo -e "${GREEN}✅ 通过的检查项：${NC}"
    for check in "${passed_checks[@]}"; do
        echo -e "  • $check"
    done
fi

if [ ${#failed_checks[@]} -gt 0 ]; then
    echo ""
    echo -e "${RED}❌ 失败的检查项：${NC}"
    for check in "${failed_checks[@]}"; do
        echo -e "  • $check"
    done
fi

echo ""
echo -e "${BLUE}🎯 部署状态评估${NC}"
echo "========================================"

if [ "$pass_rate" -ge 90 ]; then
    echo -e "${GREEN}🎉 部署状态: 优秀 (≥90%)${NC}"
    echo -e "${GREEN}   生产环境已就绪！${NC}"
    exit_code=0
elif [ "$pass_rate" -ge 70 ]; then
    echo -e "${YELLOW}⚠️  部署状态: 良好 (70-89%)${NC}"
    echo -e "${YELLOW}   部分服务需要调整${NC}"
    exit_code=0
elif [ "$pass_rate" -ge 50 ]; then
    echo -e "${YELLOW}⚠️  部署状态: 一般 (50-69%)${NC}"
    echo -e "${YELLOW}   建议检查失败项目${NC}"
    exit_code=1
else
    echo -e "${RED}❌ 部署状态: 需要修复 (<50%)${NC}"
    echo -e "${RED}   部署存在重大问题${NC}"
    exit_code=1
fi

echo ""
echo -e "${BLUE}📝 后续建议${NC}"
echo "========================================"
echo -e "1. 配置域名和正式SSL证书"
echo -e "2. 设置监控告警邮箱"
echo -e "3. 配置定时数据库备份"
echo -e "4. 添加百炼AI服务密钥"
echo -e "5. 配置微信小程序信息"

echo ""
echo -e "${BLUE}🔗 快速访问链接${NC}"
echo "========================================"
echo -e "主应用: http://$HOST:8000"
echo -e "API文档: http://$HOST:8000/docs"
echo -e "监控面板: http://$HOST:3000"
echo -e "指标收集: http://$HOST:9090"

exit $exit_code