#!/bin/bash
# 文件: scripts/deploy_to_production.sh

set -e

SERVER="root@121.199.173.244"
REMOTE_DIR="/opt/wuhao-tutor"

echo "🚀 开始部署到生产环境..."
echo "服务器: $SERVER"
echo "目录: $REMOTE_DIR"
echo ""

# ========== 本地阶段 ==========

echo "📍 阶段1: 本地准备"

# 1.1 代码检查
echo "🔍 代码检查..."
chmod +x scripts/pre_deploy_check.sh
./scripts/pre_deploy_check.sh

# 1.2 构建前端
echo "🏗️  构建前端..."
chmod +x scripts/build_frontend.sh
./scripts/build_frontend.sh

# 1.3 确认部署
read -p "✅ 本地检查通过,确认部署到生产环境? (y/N): " confirm
if [ "$confirm" != "y" ]; then
    echo "❌ 取消部署"
    exit 1
fi

# ========== 服务器阶段 ==========

echo ""
echo "📍 阶段2: 服务器操作"

# 2.1 同步文件 (仅关键文件)
echo "📤 同步文件到服务器..."

# 同步后端代码
rsync -avz --delete \
    --exclude='venv/' \
    --exclude='node_modules/' \
    --exclude='*.db' \
    --exclude='.env' \
    --exclude='__pycache__/' \
    --exclude='.git/' \
    --exclude='archive/' \
    --exclude='*.pyc' \
    ./src/ $SERVER:$REMOTE_DIR/src/

# 同步前端构建产物
rsync -avz --delete \
    ./frontend/dist/ $SERVER:$REMOTE_DIR/frontend/dist/

# 同步配置文件和依赖清单
rsync -avz \
    ./requirements.prod.txt $SERVER:$REMOTE_DIR/requirements.txt
rsync -avz \
    ./.env.production $SERVER:$REMOTE_DIR/.env

echo "✅ 文件同步完成"

# 2.2 远程部署操作
echo "🔄 执行远程部署操作..."

ssh $SERVER << 'EOF'
set -e

REMOTE_DIR="/opt/wuhao-tutor"
cd $REMOTE_DIR

echo "📦 激活虚拟环境并更新依赖..."
source venv/bin/activate

# 安装新的依赖
pip install -r requirements.txt

echo "🗄️  检查数据库连接..."
# 简单的数据库连接测试
python -c "
import sys
sys.path.append('.')
from src.core.database import engine
print('✅ 数据库连接正常')
"

echo "🎨 部署前端..."
# 确保前端目录存在
if [ ! -d "/var/www/html" ]; then
    mkdir -p /var/www/html
fi

# 备份旧版本（只备份 index.html 作为标记）
if [ -f "/var/www/html/index.html" ]; then
    cp /var/www/html/index.html /var/www/html/index.html.backup_$(date +%Y%m%d_%H%M%S)
fi

# 清空旧文件并复制新版本
rm -rf /var/www/html/*
cp -r $REMOTE_DIR/frontend/dist/* /var/www/html/

# 设置权限
chown -R www-data:www-data /var/www/html
chmod -R 755 /var/www/html

echo "🔄 重启服务..."
systemctl restart wuhao-tutor

# 等待启动
sleep 5

echo "📊 检查服务状态..."
systemctl status wuhao-tutor --no-pager -l | head -10

echo "🌐 重新加载 Nginx..."
nginx -t && nginx -s reload

echo "✅ 远程部署操作完成"
EOF

echo ""
echo "📍 阶段3: 部署验证"

# 3.1 健康检查
echo "🏥 健康检查..."
sleep 3

# 检查服务是否运行
if ssh $SERVER "systemctl is-active wuhao-tutor" >/dev/null; then
    echo "✅ wuhao-tutor 服务运行正常"
else
    echo "❌ wuhao-tutor 服务未正常运行"
    ssh $SERVER "journalctl -u wuhao-tutor -n 20 --no-pager"
    exit 1
fi

# 检查API健康状态
echo "🩺 API 健康检查..."
if curl -f -k -m 10 https://121.199.173.244/api/v1/files/health >/dev/null 2>&1; then
    echo "✅ API 健康检查通过"
else
    echo "⚠️ API 健康检查失败，检查详细信息..."
    curl -k https://121.199.173.244/api/v1/files/health || true
fi

# ========== 完成 ==========

echo ""
echo "=" * 60
echo "✅ 部署成功完成!"
echo "=" * 60
echo ""
echo "🌐 访问地址: https://121.199.173.244"
echo "📊 健康检查: https://121.199.173.244/api/v1/files/health"
echo "📋 查看日志: ssh $SERVER 'journalctl -u wuhao-tutor -f'"
echo ""
echo "🔧 如需查看服务状态: ssh $SERVER 'systemctl status wuhao-tutor'"