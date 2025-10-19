#!/bin/bash

# 微信小程序代码包体积快速优化脚本
# 目标：将代码包从 2190KB 减小到 2048KB 以下

set -e

echo "=========================================="
echo "代码包体积优化 - 快速修复"
echo "=========================================="
echo ""

cd "$(dirname "$0")/../miniprogram"

echo "📊 当前问题："
echo "  主包大小：2190KB"
echo "  限制大小：2048KB"
echo "  超出：142KB"
echo ""

echo "✂️  优化方案 1：移除 ECharts（减少 1MB）"
echo "----------------------------------------"

if [ -f "components/ec-canvas/echarts.min.js" ]; then
  echo "发现 echarts.min.js (1MB)..."
  
  # 备份
  if [ ! -f "components/ec-canvas/echarts.min.js.removed" ]; then
    mv components/ec-canvas/echarts.min.js components/ec-canvas/echarts.min.js.removed
    echo "✅ 已移除 echarts.min.js（备份为 .removed）"
  else
    echo "⚠️  echarts.min.js 已经被移除"
  fi
else
  echo "⚠️  echarts.min.js 未找到"
fi

echo ""
echo "📝 说明："
echo "  - 学习报告页面的图表将暂时无法显示"
echo "  - 后续可以使用轻量级图表库（如 wxcharts）"
echo "  - 或者使用小程序原生组件实现简单图表"
echo ""

echo "=========================================="
echo "✅ 优化完成！"
echo "=========================================="
echo ""
echo "📱 下一步："
echo "  1. 在微信开发者工具中重新编译"
echo "  2. 检查代码包大小（应该 < 1.2MB）"
echo "  3. 测试功能（学习报告页面可能需要调整）"
echo "  4. 上传代码"
echo ""

echo "🔄 如需恢复 ECharts："
echo "  mv components/ec-canvas/echarts.min.js.removed components/ec-canvas/echarts.min.js"
echo ""

echo "💡 替代方案："
echo "  1. 使用 wx-charts（轻量级，约 50KB）"
echo "  2. 使用小程序 Canvas API 手绘图表"
echo "  3. 使用后端生成图表图片（最轻量）"
echo ""
