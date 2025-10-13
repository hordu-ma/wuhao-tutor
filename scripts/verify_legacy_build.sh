#!/bin/bash
# 文件: scripts/verify_legacy_build.sh
# 用途: 验证 Legacy Plugin 构建产物

set -e

echo "🔍 验证 Legacy 构建产物"
echo "======================="

FRONTEND_DIR="/data/workspace/wuhao-tutor/frontend"
DIST_DIR="$FRONTEND_DIR/dist"
ASSETS_DIR="$DIST_DIR/assets"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查 dist 目录
if [ ! -d "$DIST_DIR" ]; then
    echo -e "${RED}❌ 未找到 dist 目录${NC}"
    echo "   请先执行构建: cd frontend && npm run build"
    exit 1
fi

echo -e "${GREEN}✓${NC} dist 目录存在"

# 检查 assets 目录
if [ ! -d "$ASSETS_DIR" ]; then
    echo -e "${RED}❌ 未找到 assets 目录${NC}"
    exit 1
fi

echo -e "${GREEN}✓${NC} assets 目录存在"

# 检查 legacy 文件
echo ""
echo "📦 检查 Legacy 文件..."
echo "----------------------"

LEGACY_FILES=$(find "$ASSETS_DIR" -name "*-legacy-*.js" 2>/dev/null | wc -l)

if [ "$LEGACY_FILES" -eq 0 ]; then
    echo -e "${RED}❌ 未找到 legacy 文件${NC}"
    echo "   Legacy Plugin 可能未正确配置或构建失败"
    exit 1
fi

echo -e "${GREEN}✓${NC} 找到 $LEGACY_FILES 个 legacy 文件"

# 列出 legacy 文件及大小
echo ""
echo "Legacy 文件列表:"
find "$ASSETS_DIR" -name "*-legacy-*.js" -exec ls -lh {} \; | awk '{print "  - " $9 " (" $5 ")"}'

# 检查 polyfills-legacy 文件
echo ""
echo "🔧 检查 Polyfills..."
echo "-------------------"

POLYFILLS_FILE=$(find "$ASSETS_DIR" -name "polyfills-legacy-*.js" 2>/dev/null)

if [ -z "$POLYFILLS_FILE" ]; then
    echo -e "${YELLOW}⚠${NC}  未找到 polyfills-legacy-*.js"
    echo "   可能使用了内联 polyfills（某些配置下正常）"
else
    POLYFILLS_SIZE=$(ls -lh "$POLYFILLS_FILE" | awk '{print $5}')
    echo -e "${GREEN}✓${NC} Polyfills 文件: $POLYFILLS_SIZE"
    
    # 检查 polyfills 文件大小
    POLYFILLS_SIZE_KB=$(du -k "$POLYFILLS_FILE" | cut -f1)
    if [ "$POLYFILLS_SIZE_KB" -gt 100 ]; then
        echo -e "${YELLOW}⚠${NC}  Polyfills 文件较大 (${POLYFILLS_SIZE_KB}KB > 100KB)"
        echo "   建议检查 vite.config.ts 中的 polyfills 配置"
    fi
fi

# 检查 index.html
echo ""
echo "📄 检查 index.html..."
echo "--------------------"

INDEX_HTML="$DIST_DIR/index.html"

if [ ! -f "$INDEX_HTML" ]; then
    echo -e "${RED}❌ 未找到 index.html${NC}"
    exit 1
fi

# 检查是否包含 legacy 脚本标签
if grep -q "nomodule" "$INDEX_HTML"; then
    echo -e "${GREEN}✓${NC} index.html 包含 nomodule 脚本标签"
else
    echo -e "${RED}❌ index.html 不包含 nomodule 脚本标签${NC}"
    echo "   Legacy Plugin 可能未正确注入脚本"
    exit 1
fi

# 检查现代脚本
if grep -q 'type="module"' "$INDEX_HTML"; then
    echo -e "${GREEN}✓${NC} index.html 包含 type=\"module\" 脚本标签"
else
    echo -e "${YELLOW}⚠${NC}  index.html 不包含 type=\"module\" 脚本标签"
fi

# 统计文件大小
echo ""
echo "📊 构建产物统计"
echo "---------------"

TOTAL_SIZE=$(du -sh "$DIST_DIR" | cut -f1)
ASSETS_SIZE=$(du -sh "$ASSETS_DIR" | cut -f1)

echo "  总大小: $TOTAL_SIZE"
echo "  Assets 大小: $ASSETS_SIZE"

# 统计 JS 文件
JS_COUNT=$(find "$ASSETS_DIR" -name "*.js" | wc -l)
MODERN_COUNT=$(find "$ASSETS_DIR" -name "*.js" ! -name "*-legacy-*.js" | wc -l)
LEGACY_COUNT=$(find "$ASSETS_DIR" -name "*-legacy-*.js" | wc -l)

echo "  JS 文件总数: $JS_COUNT"
echo "  - 现代浏览器: $MODERN_COUNT"
echo "  - 兼容浏览器: $LEGACY_COUNT"

# 检查主要 vendor 文件
echo ""
echo "🎯 关键 Vendor 文件"
echo "------------------"

VENDORS=(
    "vue-vendor"
    "element-vendor"
    "utils-vendor"
    "pinia-vendor"
    "chart-vendor"
)

for vendor in "${VENDORS[@]}"; do
    VENDOR_FILE=$(find "$ASSETS_DIR" -name "${vendor}-*.js" 2>/dev/null | head -1)
    if [ -n "$VENDOR_FILE" ]; then
        VENDOR_SIZE=$(ls -lh "$VENDOR_FILE" | awk '{print $5}')
        echo -e "${GREEN}✓${NC} $vendor: $VENDOR_SIZE"
    else
        echo -e "${YELLOW}⚠${NC}  $vendor: 未找到（可能被合并）"
    fi
done

# 检查 CSS 文件
echo ""
echo "🎨 CSS 文件"
echo "----------"

CSS_COUNT=$(find "$ASSETS_DIR" -name "*.css" | wc -l)
echo "  CSS 文件数: $CSS_COUNT"

if [ "$CSS_COUNT" -gt 0 ]; then
    find "$ASSETS_DIR" -name "*.css" -exec ls -lh {} \; | awk '{print "  - " $9 " (" $5 ")"}'
fi

# 最终总结
echo ""
echo "✅ 验证总结"
echo "=========="

if [ "$LEGACY_FILES" -gt 0 ] && grep -q "nomodule" "$INDEX_HTML"; then
    echo -e "${GREEN}✓ Legacy Plugin 配置正确${NC}"
    echo -e "${GREEN}✓ 构建产物包含现代和兼容两套代码${NC}"
    echo ""
    echo "📋 下一步操作:"
    echo "  1. 部署到生产: ./scripts/deploy_to_production.sh"
    echo "  2. 验证移动端: 使用旧版 iOS/Android 浏览器测试"
    echo "  3. 监控错误率: 检查生产环境 JS 错误"
else
    echo -e "${RED}❌ 验证失败，请检查配置${NC}"
    exit 1
fi
