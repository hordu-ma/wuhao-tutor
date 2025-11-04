#!/bin/bash

# 微信小程序域名配置更新脚本
# 解决公式图片无法在真机显示的问题

echo "🔧 更新微信小程序域名配置..."

MINIPROGRAM_DIR="/Users/liguoma/my-devs/python/wuhao-tutor/miniprogram"
PROJECT_CONFIG="$MINIPROGRAM_DIR/project.config.json"

# 备份原配置
cp "$PROJECT_CONFIG" "$PROJECT_CONFIG.backup.$(date +%Y%m%d_%H%M%S)"

echo "📋 当前域名配置:"
echo "现有 downloadDomain:"
grep -A 1 '"downloadDomain"' "$PROJECT_CONFIG"

echo ""
echo "🔄 添加阿里云OSS域名到白名单..."

# 使用 jq 更新配置（如果没有 jq，则手动编辑）
if command -v jq >/dev/null 2>&1; then
    # 使用 jq 更新
    jq '.downloadDomain += ["https://wuhao-tutor-prod.oss-cn-hangzhou.aliyuncs.com"]' "$PROJECT_CONFIG" > "$PROJECT_CONFIG.tmp" && mv "$PROJECT_CONFIG.tmp" "$PROJECT_CONFIG"
    echo "✅ 使用 jq 成功更新配置"
else
    echo "⚠️  请手动添加以下域名到 project.config.json 的 downloadDomain 数组中:"
    echo "  \"https://wuhao-tutor-prod.oss-cn-hangzhou.aliyuncs.com\""
fi

echo ""
echo "📋 更新后的域名配置:"
echo "downloadDomain:"
grep -A 3 '"downloadDomain"' "$PROJECT_CONFIG"

echo ""
echo "✅ 配置更新完成！"
echo ""
echo "📱 接下来需要："
echo "1. 在微信开发者工具中重新编译"
echo "2. 重新上传到微信平台"
echo "3. 在手机端测试公式显示"
echo ""
echo "🔍 如果仍有问题，可能需要在微信公众平台后台添加服务器域名白名单"