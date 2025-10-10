#!/bin/bash
# 文件: scripts/build_frontend.sh

set -e

echo "🏗️  构建前端..."

cd frontend

# 检查是否存在package.json
if [ ! -f "package.json" ]; then
    echo "❌ 未找到package.json"
    exit 1
fi

# 安装依赖
echo "📦 安装前端依赖..."
npm install

# 类型检查
echo "🔍 类型检查..."
npm run type-check

# 构建生产版本
echo "⚙️ 构建生产版本..."
npm run build

# 检查构建产物
if [ ! -d "dist" ]; then
    echo "❌ 前端构建失败"
    exit 1
fi

echo "✅ 前端构建完成: $(du -sh dist | cut -f1)"

cd ..