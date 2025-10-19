#!/bin/bash

# 五好伴学小程序 - 体验版快速发布脚本
# 用途：检查配置并指导体验版发布流程

set -e

echo "=========================================="
echo "五好伴学小程序 - 体验版发布助手"
echo "=========================================="
echo ""

# 进入小程序目录
cd "$(dirname "$0")/../miniprogram"

echo "📋 步骤 1: 检查配置文件..."
echo "----------------------------------------"

# 检查 API 配置
if grep -q "https://www.horsduroot.com" config/index.js; then
  echo "✅ config/index.js - API 域名配置正确"
else
  echo "❌ config/index.js - API 域名需要更新"
  exit 1
fi

# 检查项目配置
if grep -q "https://www.horsduroot.com" project.config.json; then
  echo "✅ project.config.json - 请求域名配置正确"
else
  echo "❌ project.config.json - 请求域名需要更新"
  exit 1
fi

echo ""
echo "📦 步骤 2: 安装/检查依赖..."
echo "----------------------------------------"
npm install

echo ""
echo "🔍 步骤 3: 代码质量检查..."
echo "----------------------------------------"
npm run lint || echo "⚠️  代码检查有警告，请查看"

echo ""
echo "=========================================="
echo "✅ 预检查完成！"
echo "=========================================="
echo ""
echo "📱 下一步：发布体验版"
echo "----------------------------------------"
echo ""
echo "第一步：添加体验成员（首次必做）"
echo "  1. 访问：https://mp.weixin.qq.com/"
echo "  2. 路径：管理 → 成员管理 → 体验成员"
echo "  3. 点击：添加成员"
echo "  4. 输入：测试用户的微信号"
echo "  5. 限制：最多 100 人"
echo ""
echo "第二步：上传代码"
echo "  1. 打开微信开发者工具"
echo "  2. 导入项目（当前目录：$(pwd)）"
echo "  3. 点击：工具 → 构建 npm（首次或有更新时）"
echo "  4. 点击：预览（扫码真机测试）"
echo "  5. 点击：上传"
echo "     版本号：1.0.0-beta.1"
echo "     备注：体验版测试 - 第一轮内测"
echo ""
echo "第三步：设置为体验版"
echo "  1. 登录：https://mp.weixin.qq.com/"
echo "  2. 路径：管理 → 版本管理"
echo "  3. 找到：刚上传的开发版本"
echo "  4. 点击：设为体验版"
echo ""
echo "第四步：分享给测试用户"
echo "  1. 在版本管理页面点击：体验版二维码"
echo "  2. 下载二维码图片"
echo "  3. 发送给测试成员"
echo "  4. 用户微信扫码即可访问"
echo ""
echo "=========================================="
echo "📚 相关文档"
echo "----------------------------------------"
echo "  体验版管理手册："
echo "  docs/miniprogram/experience-version-guide.md"
echo ""
echo "  测试指引文档："
echo "  docs/miniprogram/testing-guide.md"
echo ""
echo "  完整部署指南："
echo "  docs/deployment/miniprogram-deployment-guide.md"
echo ""
echo "=========================================="
echo ""
echo "💡 提示："
echo "  - 体验版无需审核，上传后立即可用"
echo "  - 只有添加的体验成员才能访问"
echo "  - 更新时版本号递增（beta.1 → beta.2）"
echo "  - 用户下次打开时自动更新到最新版"
echo ""
echo "🎯 准备好了吗？现在可以打开微信开发者工具开始上传！"
echo ""
