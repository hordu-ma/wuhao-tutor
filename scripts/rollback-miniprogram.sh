#!/bin/bash

# 微信小程序文件回滚脚本
# 恢复刚才移动的文件

MINIPROGRAM_DIR="/Users/liguoma/my-devs/python/wuhao-tutor/miniprogram"
BACKUP_DIR="/Users/liguoma/my-devs/python/wuhao-tutor/backup/miniprogram-npm-cleanup-20251104"

echo "🔄 开始回滚微信小程序文件..."
echo "📁 小程序目录: $MINIPROGRAM_DIR"
echo "📁 备份目录: $BACKUP_DIR"

cd "$MINIPROGRAM_DIR"

# 检查备份目录是否存在
if [ ! -d "$BACKUP_DIR" ]; then
    echo "❌ 备份目录不存在: $BACKUP_DIR"
    exit 1
fi

echo "📦 恢复 miniprogram_npm 目录..."
if [ -d "$BACKUP_DIR/miniprogram_npm" ]; then
    mv "$BACKUP_DIR/miniprogram_npm" ./
    echo "✅ miniprogram_npm 已恢复"
else
    echo "⚠️  未找到 miniprogram_npm 备份"
fi

echo "📦 恢复 node_modules 目录..."
if [ -d "$BACKUP_DIR/node_modules" ]; then
    mv "$BACKUP_DIR/node_modules" ./
    echo "✅ node_modules 已恢复"
else
    echo "⚠️  未找到 node_modules 备份"
fi

echo "📦 恢复 tests 目录..."
if [ -d "$BACKUP_DIR/tests" ]; then
    mv "$BACKUP_DIR/tests" ./
    echo "✅ tests 目录已恢复"
else
    echo "⚠️  未找到 tests 备份"
fi

echo "📦 恢复 examples 目录..."
if [ -d "$BACKUP_DIR/examples" ]; then
    mv "$BACKUP_DIR/examples" ./
    echo "✅ examples 目录已恢复"
else
    echo "⚠️  未找到 examples 备份"
fi

echo "📋 恢复开发配置文件..."
CONFIG_FILES=(
    ".eslintrc.js"
    ".prettierrc"
    ".prettierignore"  
    "tsconfig.json"
    "package-lock.json"
    "README.md"
    "generate-avatars.py"
)

for file in "${CONFIG_FILES[@]}"; do
    if [ -f "$BACKUP_DIR/$file" ]; then
        cp "$BACKUP_DIR/$file" ./
        echo "  ✅ 恢复 $file"
    else
        echo "  ⚠️  未找到 $file 备份"
    fi
done

echo ""
echo "✅ 回滚完成！"
echo ""
echo "📊 当前目录大小:"
du -sh .
echo ""
echo "🔧 建议重新构建npm包:"
echo "   npm install"
echo "   npm run build:npm"