#!/bin/bash
# 提取后端所有API端点清单
# 创建日期: 2025-10-26

echo "=== 提取后端所有API端点 ==="

# 确保输出目录存在
mkdir -p docs/operations

# 搜索所有@router装饰器
grep -rh "@router\." src/api/v1/endpoints/*.py \
  | grep -E "(get|post|put|patch|delete)\(" \
  | sed -E 's/.*@router\.(get|post|put|patch|delete)\(["\']([^"\']+)["\'].*/\1|\2/' \
  | sort -u \
  > docs/operations/backend-endpoints.txt

echo "✅ 已导出 $(wc -l < docs/operations/backend-endpoints.txt) 个后端端点"
echo "📄 文件位置: docs/operations/backend-endpoints.txt"
echo ""
echo "前10个端点示例:"
head -10 docs/operations/backend-endpoints.txt
