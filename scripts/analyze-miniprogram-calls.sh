#!/bin/bash
# 提取小程序所有API调用清单
# 创建日期: 2025-10-26

echo "=== 提取小程序所有API调用 ==="

# 确保输出目录存在
mkdir -p docs/operations

# 搜索所有request调用（包括动态路径）
{
  # 方式1: 直接字符串路径
  grep -rh "request\.\(get\|post\|put\|delete\|patch\)" miniprogram/api/*.js \
    | grep -oE "'api/v1/[^']+'" \
    | sed "s/'//g"
  
  # 方式2: 模板字符串路径
  grep -rh "request\.\(get\|post\|put\|delete\|patch\)" miniprogram/api/*.js \
    | grep -oE '`api/v1/[^`]+`' \
    | sed 's/`//g' \
    | sed -E 's/\$\{[^}]+\}/:id/g'
  
  # 方式3: 在页面文件中的直接调用
  grep -rh "api\.\(baseUrl\)\?.*api/v1/" miniprogram/pages/**/*.js \
    | grep -oE "api/v1/[^'\"]+['\"]" \
    | sed -E "s/['\"]//g"
    
} | sort -u > docs/operations/miniprogram-api-calls.txt

echo "✅ 已导出 $(wc -l < docs/operations/miniprogram-api-calls.txt) 个小程序API调用"
echo "📄 文件位置: docs/operations/miniprogram-api-calls.txt"
echo ""
echo "前10个调用示例:"
head -10 docs/operations/miniprogram-api-calls.txt
