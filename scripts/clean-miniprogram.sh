#!/bin/bash

# 微信小程序无依赖文件清理脚本
# 将无依赖的第三方包文件移动到backup文件夹

MINIPROGRAM_DIR="/Users/liguoma/my-devs/python/wuhao-tutor/miniprogram"
BACKUP_DIR="/Users/liguoma/my-devs/python/wuhao-tutor/backup/miniprogram-npm-cleanup-$(date +%Y%m%d)"

echo "🧹 开始清理微信小程序无依赖文件..."
echo "📁 小程序目录: $MINIPROGRAM_DIR"
echo "📁 备份目录: $BACKUP_DIR"

# 创建备份目录
mkdir -p "$BACKUP_DIR"

cd "$MINIPROGRAM_DIR"

# 1. 备份并删除 miniprogram_npm 目录（这些是构建产物，可以重新构建）
if [ -d "miniprogram_npm" ]; then
    echo "📦 移动 miniprogram_npm 目录到备份位置..."
    mv miniprogram_npm "$BACKUP_DIR/"
    echo "✅ miniprogram_npm 已移动到备份目录"
fi

# 2. 备份并删除 node_modules 目录（开发依赖，不需要上传）
if [ -d "node_modules" ]; then
    echo "📦 移动 node_modules 目录到备份位置..."
    mv node_modules "$BACKUP_DIR/"
    echo "✅ node_modules 已移动到备份目录"
fi

# 3. 备份其他可能的无用文件
echo "🔍 检查其他可能的无用文件..."

# 删除各种缓存和临时文件
find . -name ".DS_Store" -type f -delete 2>/dev/null || true
find . -name "*.log" -type f -delete 2>/dev/null || true
find . -name ".eslintcache" -type f -delete 2>/dev/null || true

# 备份开发配置文件（这些通常不需要上传）
DEV_FILES=(
    ".eslintrc.js"
    ".prettierrc"
    ".prettierignore"  
    "tsconfig.json"
    "package-lock.json"
    "README.md"
    "generate-avatars.py"
)

echo "📋 备份开发配置文件..."
for file in "${DEV_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "  📄 备份 $file"
        cp "$file" "$BACKUP_DIR/"
        rm "$file"
    fi
done

# 4. 备份测试目录
if [ -d "tests" ]; then
    echo "📦 移动 tests 目录到备份位置..."
    mv tests "$BACKUP_DIR/"
    echo "✅ tests 目录已移动到备份目录"
fi

# 5. 备份examples目录
if [ -d "examples" ]; then
    echo "📦 移动 examples 目录到备份位置..."
    mv examples "$BACKUP_DIR/"
    echo "✅ examples 目录已移动到备份目录"
fi

echo ""
echo "✅ 清理完成！"
echo ""
echo "📊 备份文件位置: $BACKUP_DIR"
echo "📝 已移动的内容:"
echo "   - miniprogram_npm/ (第三方包构建产物)"
echo "   - node_modules/ (开发依赖)"
echo "   - tests/ (测试文件)"
echo "   - examples/ (示例文件)"
echo "   - 各种开发配置文件"
echo ""
echo "🔄 如需恢复npm包，请运行:"
echo "   cd $MINIPROGRAM_DIR"
echo "   npm install"
echo "   npm run build:npm"
echo ""
echo "📱 现在可以重新上传小程序到微信平台了！"