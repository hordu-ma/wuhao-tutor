#!/bin/bash

# 五好伴学小程序 - 快速上传部署脚本
# 使用前请确保：
# 1. 已安装微信开发者工具
# 2. 已在小程序后台配置服务器域名
# 3. 配置文件已更新为生产域名

set -e

echo "=========================================="
echo "五好伴学小程序 - 部署准备"
echo "=========================================="

# 进入小程序目录
cd "$(dirname "$0")/../miniprogram"

echo ""
echo "📋 步骤 1: 检查配置文件..."
echo "----------------------------------------"

# 检查 API 配置
if grep -q "https://www.horsduroot.com" config/index.js; then
  echo "✅ config/index.js - API 域名配置正确"
else
  echo "❌ config/index.js - API 域名需要更新为 https://www.horsduroot.com"
  exit 1
fi

# 检查项目配置
if grep -q "https://www.horsduroot.com" project.config.json; then
  echo "✅ project.config.json - 请求域名配置正确"
else
  echo "❌ project.config.json - 请求域名需要更新为 https://www.horsduroot.com"
  exit 1
fi

echo ""
echo "📦 步骤 2: 安装依赖..."
echo "----------------------------------------"
npm install

echo ""
echo "🔍 步骤 3: 代码质量检查..."
echo "----------------------------------------"

# 代码格式检查
if npm run lint; then
  echo "✅ 代码检查通过"
else
  echo "⚠️  代码检查有警告，请查看并修复"
fi

# TypeScript 类型检查
if npm run type-check; then
  echo "✅ 类型检查通过"
else
  echo "⚠️  类型检查有警告，请查看并修复"
fi

echo ""
echo "=========================================="
echo "✅ 预检查完成！"
echo "=========================================="
echo ""
echo "📱 下一步操作："
echo "----------------------------------------"
echo "1. 打开微信开发者工具"
echo "2. 导入项目（目录：$(pwd)）"
echo "3. 点击「工具」→「构建 npm」"
echo "4. 点击「预览」按钮，扫码真机测试"
echo "5. 测试以下核心功能："
echo "   - 微信登录"
echo "   - 作业问答（AI 对话）"
echo "   - 错题手册（增删改查）"
echo "   - 学习报告（数据展示）"
echo "   - 图片上传"
echo "   - 个人中心"
echo ""
echo "6. 功能测试通过后，点击「上传」按钮"
echo "   版本号：1.0.0"
echo "   项目备注：初始版本发布"
echo ""
echo "7. 登录小程序后台提交审核："
echo "   https://mp.weixin.qq.com/"
echo ""
echo "=========================================="
