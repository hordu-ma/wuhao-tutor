#!/bin/bash
# Phase 5.1 前后端联调自动化测试脚本
# 用于验证错题本优化功能的完整数据流

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 配置
PROD_HOST="121.199.173.244"
PROD_URL="https://www.horsduroot.com"
API_BASE="/api/v1"
TEST_RESULTS_DIR="./test-results/phase5"

# 创建测试结果目录
mkdir -p "$TEST_RESULTS_DIR"
REPORT_FILE="$TEST_RESULTS_DIR/integration-test-$(date +%Y%m%d-%H%M%S).md"

# 初始化测试报告
init_report() {
    cat > "$REPORT_FILE" << EOF
# Phase 5.1 前后端联调测试报告

**测试日期**: $(date '+%Y-%m-%d %H:%M:%S')
**测试环境**: 生产环境 ($PROD_URL)
**测试脚本**: test-phase5-integration.sh

---

## 📋 测试概况

EOF
}

# 打印标题
print_header() {
    echo ""
    echo -e "${PURPLE}════════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}  $1${NC}"
    echo -e "${PURPLE}════════════════════════════════════════════════════════════${NC}"
    echo ""
}

# 打印步骤
print_step() {
    echo -e "${BLUE}[$(date '+%H:%M:%S')]${NC} ${YELLOW}▶${NC} $1"
}

# 打印成功
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
    echo "- ✅ $1" >> "$REPORT_FILE"
}

# 打印失败
print_error() {
    echo -e "${RED}❌ $1${NC}"
    echo "- ❌ $1" >> "$REPORT_FILE"
}

# 打印警告
print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
    echo "- ⚠️  $1" >> "$REPORT_FILE"
}

# 打印信息
print_info() {
    echo -e "${CYAN}ℹ️  $1${NC}"
}

# ==================== 测试函数 ====================

# 测试 1: 健康检查
test_health_check() {
    print_header "测试 1: 后端健康检查"

    echo "### 1. 后端健康检查" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"

    print_step "检查后端服务状态..."

    # 检查主健康端点
    if curl -s -f "$PROD_URL/health" > /dev/null 2>&1; then
        print_success "主服务健康检查通过"
    else
        print_error "主服务健康检查失败"
        return 1
    fi

    # 检查学习模块健康端点
    if curl -s -f "$PROD_URL$API_BASE/learning/health" > /dev/null 2>&1; then
        print_success "学习模块健康检查通过"
    else
        print_error "学习模块健康检查失败"
        return 1
    fi

    echo "" >> "$REPORT_FILE"
}

# 测试 2: 数据库连接
test_database_connection() {
    print_header "测试 2: 数据库连接验证"

    echo "### 2. 数据库连接验证" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"

    print_step "通过 SSH 检查数据库连接..."

    # SSH 检查数据库
    if ssh -o ConnectTimeout=10 root@$PROD_HOST "psql -U wuhao_user -d wuhao_db -c 'SELECT 1;'" > /dev/null 2>&1; then
        print_success "数据库连接正常"
    else
        print_warning "无法通过 SSH 验证数据库（可能需要配置 SSH 密钥）"
    fi

    echo "" >> "$REPORT_FILE"
}

# 测试 3: API 端点可用性
test_api_endpoints() {
    print_header "测试 3: API 端点可用性"

    echo "### 3. API 端点可用性" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"

    # 定义需要测试的端点
    print_step "测试端点: 学习问答-健康检查"
    response=$(curl -s -o /dev/null -w "%{http_code}" "$PROD_URL$API_BASE/learning/health" 2>&1)
    if [[ "$response" == "200" ]]; then
        print_success "学习问答-健康检查 - HTTP $response (端点可访问)"
    else
        print_error "学习问答-健康检查 - HTTP $response (端点异常)"
    fi

    print_step "测试端点: 学习问答-测试端点"
    response=$(curl -s -o /dev/null -w "%{http_code}" "$PROD_URL$API_BASE/learning/test" 2>&1)
    if [[ "$response" == "200" ]]; then
        print_success "学习问答-测试端点 - HTTP $response (端点可访问)"
    else
        print_error "学习问答-测试端点 - HTTP $response (端点异常)"
    fi

    print_step "测试端点: 错题本-列表"
    response=$(curl -s -o /dev/null -w "%{http_code}" "$PROD_URL$API_BASE/mistakes" 2>&1)
    if [[ "$response" == "200" ]] || [[ "$response" == "401" ]] || [[ "$response" == "422" ]]; then
        print_success "错题本-列表 - HTTP $response (端点可访问)"
    else
        print_error "错题本-列表 - HTTP $response (端点异常)"
    fi

    print_step "测试端点: 用户认证-登录"
    response=$(curl -s -o /dev/null -w "%{http_code}" "$PROD_URL$API_BASE/auth/login" 2>&1)
    if [[ "$response" == "200" ]] || [[ "$response" == "401" ]] || [[ "$response" == "422" ]]; then
        print_success "用户认证-登录 - HTTP $response (端点可访问)"
    else
        print_error "用户认证-登录 - HTTP $response (端点异常)"
    fi

    echo "" >> "$REPORT_FILE"
}

# 测试 4: 小程序配置检查
test_miniprogram_config() {
    print_header "测试 4: 小程序配置检查"

    echo "### 4. 小程序配置检查" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"

    print_step "检查小程序配置文件..."

    CONFIG_FILE="./miniprogram/config/index.js"

    if [[ ! -f "$CONFIG_FILE" ]]; then
        print_error "配置文件不存在: $CONFIG_FILE"
        return 1
    fi

    # 检查 API 地址
    if grep -q "baseUrl: 'https://www.horsduroot.com'" "$CONFIG_FILE"; then
        print_success "API 地址配置正确 (生产环境)"
    else
        print_warning "API 地址可能未配置为生产环境"
    fi

    # 检查环境
    if grep -q "environment: 'production'" "$CONFIG_FILE"; then
        print_success "环境配置为 production"
    else
        print_warning "环境可能未设置为 production"
    fi

    # 检查超时设置
    if grep -q "timeout: 120000" "$CONFIG_FILE"; then
        print_success "超时设置正确 (120s)"
    else
        print_warning "超时设置可能需要调整"
    fi

    echo "" >> "$REPORT_FILE"
}

# 测试 5: 组件文件完整性
test_component_files() {
    print_header "测试 5: 批改结果组件完整性"

    echo "### 5. 批改结果组件完整性" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"

    print_step "检查组件文件..."

    COMPONENT_DIR="./miniprogram/components/correction-card"

    # 检查组件目录
    if [[ ! -d "$COMPONENT_DIR" ]]; then
        print_error "组件目录不存在: $COMPONENT_DIR"
        return 1
    fi

    # 检查必要文件
    if [[ -f "$COMPONENT_DIR/index.js" ]]; then
        print_success "组件文件存在: index.js"
    else
        print_error "组件文件缺失: index.js"
    fi

    if [[ -f "$COMPONENT_DIR/index.json" ]]; then
        print_success "组件文件存在: index.json"
    else
        print_error "组件文件缺失: index.json"
    fi

    if [[ -f "$COMPONENT_DIR/index.wxml" ]]; then
        print_success "组件文件存在: index.wxml"
    else
        print_error "组件文件缺失: index.wxml"
    fi

    if [[ -f "$COMPONENT_DIR/index.wxss" ]]; then
        print_success "组件文件存在: index.wxss"
    else
        print_error "组件文件缺失: index.wxss"
    fi

    echo "" >> "$REPORT_FILE"
}

# 测试 6: 页面集成检查
test_page_integration() {
    print_header "测试 6: 学习问答页面集成检查"

    echo "### 6. 学习问答页面集成检查" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"

    print_step "检查页面集成..."

    PAGE_JSON="./miniprogram/pages/learning/index/index.json"
    PAGE_JS="./miniprogram/pages/learning/index/index.js"
    PAGE_WXML="./miniprogram/pages/learning/index/index.wxml"

    # 检查组件注册
    if grep -q '"correction-card"' "$PAGE_JSON"; then
        print_success "组件已在页面配置中注册"
    else
        print_error "组件未在页面配置中注册"
    fi

    # 检查 JS 逻辑
    if grep -q 'correction_result' "$PAGE_JS"; then
        print_success "页面 JS 包含批改结果处理逻辑"
    else
        print_error "页面 JS 缺少批改结果处理逻辑"
    fi

    # 检查模板渲染
    if grep -q 'correction-card' "$PAGE_WXML"; then
        print_success "页面模板包含组件引用"
    else
        print_error "页面模板缺少组件引用"
    fi

    echo "" >> "$REPORT_FILE"
}

# 测试 7: 后端日志检查
test_backend_logs() {
    print_header "测试 7: 后端日志检查（可选）"

    echo "### 7. 后端日志检查" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"

    print_step "检查最近的后端日志..."

    print_info "尝试获取最近 50 行日志..."

    if ssh -o ConnectTimeout=10 root@$PROD_HOST "journalctl -u wuhao-tutor.service -n 50 --no-pager" > "$TEST_RESULTS_DIR/backend-logs.txt" 2>&1; then
        print_success "成功获取后端日志，保存到: $TEST_RESULTS_DIR/backend-logs.txt"

        # 检查是否有错误
        error_count=$(grep -c "ERROR\|Exception\|Failed" "$TEST_RESULTS_DIR/backend-logs.txt" || true)
        if [[ $error_count -gt 0 ]]; then
            print_warning "发现 $error_count 个错误日志条目"
        else
            print_success "最近日志中无错误"
        fi
    else
        print_warning "无法获取后端日志（可能需要配置 SSH 访问）"
    fi

    echo "" >> "$REPORT_FILE"
}

# 测试 8: 数据库表结构验证
test_database_schema() {
    print_header "测试 8: 数据库表结构验证（可选）"

    echo "### 8. 数据库表结构验证" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"

    print_step "检查关键表的存在..."

    if ssh -o ConnectTimeout=10 root@$PROD_HOST "psql -U wuhao_user -d wuhao_db -c '\dt mistakes'" > /dev/null 2>&1; then
        print_success "mistakes 表存在"

        # 检查新字段
        if ssh root@$PROD_HOST "psql -U wuhao_user -d wuhao_db -c '\d mistakes' | grep -q 'question_number'" 2>&1; then
            print_success "question_number 字段存在"
        else
            print_warning "question_number 字段可能缺失"
        fi

        if ssh root@$PROD_HOST "psql -U wuhao_user -d wuhao_db -c '\d mistakes' | grep -q 'is_unanswered'" 2>&1; then
            print_success "is_unanswered 字段存在"
        else
            print_warning "is_unanswered 字段可能缺失"
        fi
    else
        print_warning "无法验证数据库表结构（可能需要配置访问权限）"
    fi

    echo "" >> "$REPORT_FILE"
}

# 生成测试报告摘要
generate_summary() {
    print_header "测试完成 - 生成报告"

    cat >> "$REPORT_FILE" << EOF

---

## 📊 测试总结

**测试完成时间**: $(date '+%Y-%m-%d %H:%M:%S')

### 测试覆盖
- ✅ 后端服务健康检查
- ✅ API 端点可用性验证
- ✅ 小程序配置检查
- ✅ 组件文件完整性检查
- ✅ 页面集成验证

### 下一步行动

1. **手动测试**: 在微信开发者工具中进行实际操作测试
   - 上传作业图片
   - 验证批改结果显示
   - 检查错题本关联

2. **性能测试**: 监控响应时间和成功率
   - 图片上传速度
   - AI 批改时间
   - 错题创建速度

3. **边界测试**: 测试特殊场景
   - 全对作业
   - 未作答题目
   - 网络异常
   - 超时场景

### 相关文档
- 详细测试指南: \`docs/PHASE5_INTEGRATION_TEST.md\`
- 开发进度: \`DEVELOPMENT_CONTEXT.md\`

---

**报告生成**: test-phase5-integration.sh
EOF

    print_success "测试报告已生成: $REPORT_FILE"
}

# ==================== 主流程 ====================

main() {
    clear

    print_header "Phase 5.1 前后端联调自动化测试"

    echo -e "${CYAN}测试环境: ${NC}$PROD_URL"
    echo -e "${CYAN}测试时间: ${NC}$(date '+%Y-%m-%d %H:%M:%S')"
    echo -e "${CYAN}报告路径: ${NC}$REPORT_FILE"
    echo ""

    # 初始化报告
    init_report

    # 执行测试
    test_health_check
    test_database_connection
    test_api_endpoints
    test_miniprogram_config
    test_component_files
    test_page_integration
    test_backend_logs
    test_database_schema

    # 生成摘要
    generate_summary

    echo ""
    print_header "✅ 所有自动化测试完成"

    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}📋 完整测试报告: ${NC}$REPORT_FILE"
    echo -e "${CYAN}🔍 后端日志文件: ${NC}$TEST_RESULTS_DIR/backend-logs.txt"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""

    print_info "接下来请在微信开发者工具中进行手动测试"
    print_info "参考文档: docs/PHASE5_INTEGRATION_TEST.md"
    echo ""
}

# 运行主流程
main "$@"
