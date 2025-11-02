#!/bin/bash

# 小程序滚动修复 - 快速回滚脚本
# 使用方法: chmod +x rollback-scroll-fix.sh && ./rollback-scroll-fix.sh

set -e

echo "========================================="
echo "小程序滚动修复 - 回滚工具"
echo "========================================="
echo ""

# 检查 Git 状态
if ! git status > /dev/null 2>&1; then
    echo "❌ 错误: 当前目录不是 Git 仓库"
    exit 1
fi

# 显示最近的提交
echo "📋 最近的提交记录:"
git log --oneline -5
echo ""

# 提示用户确认
read -p "⚠️  确认要回滚滚动修复吗？这将撤销所有滚动优化变更。(y/N): " confirm

if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
    echo "❌ 已取消回滚操作"
    exit 0
fi

echo ""
echo "🔄 开始回滚..."

# 回滚文件变更
echo "📝 还原 index.js..."
git checkout HEAD~1 -- miniprogram/pages/learning/index/index.js

echo "📝 还原 index.wxml..."
git checkout HEAD~1 -- miniprogram/pages/learning/index/index.wxml

echo "🗑️  删除临时文档..."
rm -f SCROLL_FIX_SUMMARY.md
rm -f SCROLL_FIX_TESTING.md

echo ""
echo "✅ 回滚完成！"
echo ""
echo "📌 下一步操作:"
echo "1. 在微信开发者工具中重新编译"
echo "2. 测试验证回滚是否成功"
echo "3. 如需重新应用修复，运行 git stash pop"
echo ""
echo "🔗 提示: 回滚的变更已暂存，运行 'git status' 查看"
