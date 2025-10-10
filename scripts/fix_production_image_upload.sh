#!/bin/bash
# 生产环境OSS配置检查和修复脚本

echo "🔧 生产环境OSS配置检查和修复"
echo "=================================="

# 连接到生产服务器
PROD_SERVER="root@121.199.173.244"
PROD_PATH="/opt/wuhao-tutor"

echo "📡 连接到生产服务器..."

# 检查.env文件中的OSS配置
echo "🔍 检查当前OSS配置..."
ssh $PROD_SERVER "cd $PROD_PATH && grep -E '^OSS_' .env || echo '未找到OSS配置'"

echo ""
echo "📋 OSS配置要求："
echo "   OSS_BUCKET_NAME=wuhao-tutor"
echo "   OSS_ENDPOINT=oss-cn-hangzhou.aliyuncs.com  # 或 oss-cn-hangzhou-internal.aliyuncs.com"
echo "   OSS_ACCESS_KEY_ID=你的AccessKey"
echo "   OSS_ACCESS_KEY_SECRET=你的AccessKeySecret"

echo ""
echo "🛠️ 如果OSS配置缺失，请选择操作："
echo "   [1] 配置OSS存储（推荐）"
echo "   [2] 使用本地存储降级方案"
echo "   [3] 仅查看当前状态"

read -p "请选择操作 (1/2/3): " choice

case $choice in
    1)
        echo ""
        echo "📝 请提供OSS配置信息："
        read -p "OSS_ACCESS_KEY_ID: " oss_key_id
        read -s -p "OSS_ACCESS_KEY_SECRET: " oss_key_secret
        echo ""
        read -p "OSS_BUCKET_NAME [wuhao-tutor]: " oss_bucket
        oss_bucket=${oss_bucket:-wuhao-tutor}
        read -p "OSS_ENDPOINT [oss-cn-hangzhou.aliyuncs.com]: " oss_endpoint
        oss_endpoint=${oss_endpoint:-oss-cn-hangzhou.aliyuncs.com}

        echo ""
        echo "📤 配置OSS环境变量..."
        
        # 备份原配置
        ssh $PROD_SERVER "cd $PROD_PATH && cp .env .env.backup.$(date +%Y%m%d_%H%M%S)"
        
        # 更新OSS配置
        ssh $PROD_SERVER "cd $PROD_PATH && {
            sed -i '/^OSS_/d' .env
            echo 'OSS_BUCKET_NAME=$oss_bucket' >> .env
            echo 'OSS_ENDPOINT=$oss_endpoint' >> .env  
            echo 'OSS_ACCESS_KEY_ID=$oss_key_id' >> .env
            echo 'OSS_ACCESS_KEY_SECRET=$oss_key_secret' >> .env
        }"
        
        echo "✅ OSS配置已更新"
        ;;
        
    2)
        echo ""
        echo "📁 配置本地存储降级方案..."
        
        # 确保uploads目录存在且权限正确
        ssh $PROD_SERVER "cd $PROD_PATH && {
            mkdir -p uploads/ai_analysis
            chown -R www-data:www-data uploads/ 2>/dev/null || chown -R \$(whoami) uploads/
            chmod -R 755 uploads/
            ls -la uploads/
        }"
        
        # 更新BASE_URL配置
        ssh $PROD_SERVER "cd $PROD_PATH && {
            sed -i 's/BASE_URL=.*/BASE_URL=https:\/\/121.199.173.244/' .env
            grep BASE_URL .env || echo 'BASE_URL=https://121.199.173.244' >> .env
        }"
        
        echo "✅ 本地存储降级方案已配置"
        ;;
        
    3)
        echo ""
        echo "📊 当前系统状态："
        ssh $PROD_SERVER "cd $PROD_PATH && {
            echo '=== 环境配置 ==='
            grep -E '^(ENVIRONMENT|BASE_URL|OSS_)' .env
            echo ''
            echo '=== 上传目录状态 ==='
            ls -la uploads/ 2>/dev/null || echo '上传目录不存在'
            echo ''
            echo '=== 服务状态 ==='
            systemctl status wuhao-tutor | head -3
        }"
        ;;
        
    *)
        echo "❌ 无效选择"
        exit 1
        ;;
esac

if [[ $choice == 1 || $choice == 2 ]]; then
    echo ""
    echo "🔄 重启服务以应用配置..."
    ssh $PROD_SERVER "systemctl restart wuhao-tutor"
    
    echo "⏳ 等待服务启动..."
    sleep 5
    
    echo "🧪 测试服务健康状态..."
    curl -k -s https://121.199.173.244/api/v1/files/health | jq '.' || echo "健康检查失败"
    
    echo ""
    echo "✅ 配置完成！请测试图片上传功能"
    echo ""
    echo "🔍 故障排查："
    echo "   1. 查看服务日志: ssh $PROD_SERVER 'journalctl -u wuhao-tutor -f'"
    echo "   2. 测试上传: 使用前端界面上传图片"
    echo "   3. 运行诊断: python scripts/diagnose_image_upload.py"
fi

echo ""
echo "🎉 脚本执行完成"