#!/bin/bash
# 文件: scripts/pre_deploy_check.sh

set -e

echo "🔍 开始部署前检查..."

# 1. 检查关键文件存在性
echo "📋 检查关键文件..."

required_files=(
    "src/main.py"
    "src/core/config.py"
    "src/services/bailian_service.py"
    "src/services/ai_image_service.py"
    "frontend/src/api/file.ts"
    ".env.production"
)

for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        echo "❌ 缺少关键文件: $file"
        exit 1
    fi
done

# 2. 检查 .env 文件未被提交
if git ls-files --error-unmatch .env >/dev/null 2>&1; then
    echo "❌ 错误: .env 文件不应提交到Git"
    exit 1
fi

# 3. 检查是否有未提交的关键修改
if ! git diff --quiet HEAD -- src/ frontend/src/; then
    echo "⚠️ 警告: 存在未提交的代码修改"
    git status --porcelain | grep -E "^(M|A|D)" | head -5
    echo ""
    read -p "是否继续部署? (y/N): " confirm
    if [ "$confirm" != "y" ]; then
        echo "❌ 部署已取消"
        exit 1
    fi
fi

# 4. 检查Python语法
echo "🐍 检查Python语法..."
python -m py_compile src/main.py
python -m py_compile src/services/ai_image_service.py

echo "✅ 所有关键文件完整"
echo "✅ 代码验证通过,可以安全部署到生产环境"