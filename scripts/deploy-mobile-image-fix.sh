#!/bin/bash
# 移动端图片上传超时修复 - 快速部署脚本
# 日期: 2025-10-13

set -e  # 遇到错误立即退出

echo "🚀 开始部署移动端图片上传超时修复..."
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 项目路径
PROJECT_ROOT="/Users/liguoma/my-devs/python/wuhao-tutor"
FRONTEND_DIR="$PROJECT_ROOT/frontend"

# 1. 检查依赖
echo "📦 步骤 1/5: 检查依赖..."
cd "$FRONTEND_DIR"

if ! npm list browser-image-compression > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  browser-image-compression 未安装，正在安装...${NC}"
    npm install browser-image-compression
    echo -e "${GREEN}✅ 依赖安装完成${NC}"
else
    echo -e "${GREEN}✅ 依赖已存在${NC}"
fi
echo ""

# 2. 编译检查
echo "🔍 步骤 2/5: TypeScript 编译检查..."
npm run type-check || {
    echo -e "${RED}❌ TypeScript 编译检查失败${NC}"
    echo "请修复类型错误后重试"
    exit 1
}
echo -e "${GREEN}✅ 编译检查通过${NC}"
echo ""

# 3. 构建前端
echo "🔨 步骤 3/5: 构建前端生产版本..."
npm run build || {
    echo -e "${RED}❌ 前端构建失败${NC}"
    exit 1
}
echo -e "${GREEN}✅ 前端构建完成${NC}"
echo ""

# 4. 测试 Nginx 配置
echo "🔧 步骤 4/5: 测试 Nginx 配置..."
echo -e "${YELLOW}提示: 需要在服务器上执行以下命令：${NC}"
echo "  ssh root@121.199.173.244"
echo "  sudo nginx -t"
echo "  sudo systemctl reload nginx"
echo ""
read -p "是否已完成 Nginx 配置测试和重载？(y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}⚠️  请手动完成 Nginx 配置后继续部署${NC}"
    exit 0
fi
echo -e "${GREEN}✅ Nginx 配置已更新${NC}"
echo ""

# 5. 部署到生产
echo "🚀 步骤 5/5: 部署到生产环境..."
cd "$PROJECT_ROOT"
if [ -f "./scripts/deploy_to_production.sh" ]; then
    ./scripts/deploy_to_production.sh || {
        echo -e "${RED}❌ 部署失败${NC}"
        exit 1
    }
else
    echo -e "${YELLOW}⚠️  未找到部署脚本，请手动部署 dist 目录${NC}"
    echo "生产构建文件位于: $FRONTEND_DIR/dist"
fi
echo ""

# 完成
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ 部署完成！${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "📋 后续测试步骤："
echo "  1. 访问 https://121.199.173.244"
echo "  2. 使用桌面浏览器测试图片上传"
echo "  3. 使用 iOS Safari 测试图片上传（关键）"
echo "  4. 使用 Android Chrome 测试图片上传"
echo "  5. 观察控制台日志，确认压缩功能正常"
echo ""
echo "📊 监控要点："
echo "  - 压缩率应 > 60%"
echo "  - 上传时间应显著减少"
echo "  - 移动端上传成功率 > 95%"
echo ""
echo "📖 详细文档："
echo "  docs/fixes/2025-10-13-mobile-image-upload-timeout-fix.md"
echo ""
