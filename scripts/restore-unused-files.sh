#!/bin/bash

# 恢复微信小程序无依赖文件的脚本
# 如果清理后发现编译问题，可以使用此脚本恢复

echo "🔄 恢复微信小程序无依赖文件..."

cd /Users/liguoma/my-devs/python/wuhao-tutor

# 查找最新的备份目录
backup_dir=$(ls -1 backup/miniprogram-unused-* | tail -1)

if [ -z "$backup_dir" ]; then
    echo "❌ 未找到备份目录"
    exit 1
fi

echo "📦 使用备份目录: $backup_dir"

# 恢复文件
echo "🔄 恢复无依赖文件..."
cp -r "$backup_dir/miniprogram_npm"/* "miniprogram/miniprogram_npm/"

echo "✅ 恢复完成！"
echo "📊 当前目录大小:"
du -sh miniprogram

echo ""
echo "🔍 请在微信开发者工具中验证编译状态"