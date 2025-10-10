#!/bin/bash
# 文件: scripts/deploy/rollback.sh

set -e

SERVER="root@121.199.173.244"
REMOTE_DIR="/opt/wuhao-tutor"

echo "⏪ 开始回滚生产环境..."

# 检查备份版本
echo "🔍 检查可用备份版本..."

ssh $SERVER << 'EOF'
BACKUP_DIR="/var/www"
echo "可用的前端备份版本:"
ls -la $BACKUP_DIR/ | grep wuhao-tutor_backup || echo "未找到前端备份"

REPO_DIR="/opt/wuhao-tutor"
cd $REPO_DIR
echo ""
echo "Git 历史版本 (最近5个):"
git log --oneline -5
EOF

# 获取用户选择
echo ""
read -p "请选择回滚方式 [git/backup]: " rollback_type

if [ "$rollback_type" = "git" ]; then
    read -p "请输入要回滚到的 commit hash: " commit_hash
    
    ssh $SERVER << EOF
    cd $REMOTE_DIR
    echo "🔄 回滚到 commit: $commit_hash"
    git checkout $commit_hash
    
    # 重新安装依赖 (可能有变化)
    source venv/bin/activate
    pip install -r requirements.txt
    
    # 重启服务
    systemctl restart wuhao-tutor
    
    echo "✅ Git回滚完成"
EOF

elif [ "$rollback_type" = "backup" ]; then
    ssh $SERVER << 'EOF'
    BACKUP_DIR="/var/www"
    LATEST_BACKUP=$(ls -td $BACKUP_DIR/wuhao-tutor_backup_* 2>/dev/null | head -1)
    
    if [ -z "$LATEST_BACKUP" ]; then
        echo "❌ 未找到备份版本"
        exit 1
    fi
    
    echo "🔄 恢复备份: $LATEST_BACKUP"
    
    # 备份当前版本
    if [ -d "/var/www/wuhao-tutor" ]; then
        mv /var/www/wuhao-tutor /var/www/wuhao-tutor_current_$(date +%Y%m%d_%H%M%S)
    fi
    
    # 恢复备份
    cp -r $LATEST_BACKUP /var/www/wuhao-tutor
    chown -R www-data:www-data /var/www/wuhao-tutor
    
    # 重启Nginx
    nginx -s reload
    
    echo "✅ 备份恢复完成"
EOF

else
    echo "❌ 无效的回滚方式"
    exit 1
fi

echo ""
echo "⏪ 回滚完成! 请检查服务状态:"
echo "🌐 https://121.199.173.244"