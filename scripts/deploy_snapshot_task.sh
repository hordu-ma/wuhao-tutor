#!/bin/bash
# 部署知识图谱快照定时任务到生产环境

set -e

echo "📦 部署知识图谱快照定时任务..."

# 服务器配置
SERVER="root@121.199.173.244"
REMOTE_DIR="/opt/wuhao-tutor"

# 1. 上传快照脚本
echo "ℹ️  上传快照脚本..."
# 确保 scripts 目录存在
ssh ${SERVER} "mkdir -p ${REMOTE_DIR}/scripts"
rsync -avz --progress \
    scripts/daily_snapshot.py \
    ${SERVER}:${REMOTE_DIR}/scripts/

# 确保脚本可执行
ssh ${SERVER} "chmod +x ${REMOTE_DIR}/scripts/daily_snapshot.py"
echo "✅ 快照脚本上传完成"

# 2. 上传systemd配置文件
echo "ℹ️  上传systemd配置..."
scp deploy/systemd/wuhao-snapshot.service ${SERVER}:/etc/systemd/system/
scp deploy/systemd/wuhao-snapshot.timer ${SERVER}:/etc/systemd/system/
echo "✅ systemd配置上传完成"

# 3. 重新加载systemd并启动定时器
echo "ℹ️  启动定时任务..."
ssh ${SERVER} << 'EOF'
    # 重新加载systemd配置
    systemctl daemon-reload
    
    # 启用并启动定时器
    systemctl enable wuhao-snapshot.timer
    systemctl start wuhao-snapshot.timer
    
    # 显示定时器状态
    echo ""
    echo "📊 定时器状态："
    systemctl status wuhao-snapshot.timer --no-pager
    
    echo ""
    echo "⏰ 下次执行时间："
    systemctl list-timers wuhao-snapshot.timer --no-pager
EOF

echo ""
echo "✅ 定时任务部署完成！"
echo ""
echo "ℹ️  管理命令："
echo "  - 查看定时器状态: ssh ${SERVER} 'systemctl status wuhao-snapshot.timer'"
echo "  - 查看服务状态:   ssh ${SERVER} 'systemctl status wuhao-snapshot.service'"
echo "  - 手动执行一次:   ssh ${SERVER} 'systemctl start wuhao-snapshot.service'"
echo "  - 查看执行日志:   ssh ${SERVER} 'journalctl -u wuhao-snapshot.service -n 50'"
echo "  - 停止定时器:     ssh ${SERVER} 'systemctl stop wuhao-snapshot.timer'"
echo "  - 禁用定时器:     ssh ${SERVER} 'systemctl disable wuhao-snapshot.timer'"
