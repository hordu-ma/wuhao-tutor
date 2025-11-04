#!/bin/bash

# 精准清理微信小程序无依赖文件
# 只移动analyse-data.json中标识的72个无依赖文件

echo "🚀 开始精准清理微信小程序无依赖文件..."

cd /Users/liguoma/my-devs/python/wuhao-tutor/miniprogram

# 创建备份目录
backup_dir="../backup/miniprogram-unused-$(date +%Y%m%d_%H%M%S)"
echo "📦 创建备份目录: $backup_dir"
mkdir -p "$backup_dir"

# 从analyse-data.json提取的72个无依赖文件列表
unused_files=(
    "miniprogram_npm/zrender/index.js"
    "miniprogram_npm/@vant/weapp/notify/index.js"
    "miniprogram_npm/@vant/weapp/notify/index.json"
    "miniprogram_npm/@vant/weapp/slider/index.wxs"
    "miniprogram_npm/tslib/index.js"
    "miniprogram_npm/@vant/weapp/field/types.js"
    "miniprogram_npm/@vant/weapp/notify/index.wxml"
    "miniprogram_npm/@vant/weapp/notify/index.wxs"
    "miniprogram_npm/regenerator-runtime/index.js"
    "miniprogram_npm/@vant/weapp/notify/index.wxss"
    "miniprogram_npm/mobx-miniprogram-bindings/index.js"
    "miniprogram_npm/@vant/weapp/notify/notify.js"
    "miniprogram_npm/mobx-miniprogram/index.js"
    "miniprogram_npm/echarts-for-weixin/index.js"
    "miniprogram_npm/echarts-for-weixin/index.json"
    "miniprogram_npm/echarts-for-weixin/index.wxml"
    "miniprogram_npm/echarts-for-weixin/index.wxss"
    "miniprogram_npm/echarts/index.js"
    "miniprogram_npm/@vant/weapp/share-sheet/index.js"
    "miniprogram_npm/@vant/weapp/share-sheet/index.json"
    "miniprogram_npm/@vant/weapp/dropdown-item/shared.js"
    "miniprogram_npm/@vant/weapp/share-sheet/index.wxml"
    "miniprogram_npm/@vant/weapp/share-sheet/index.wxs"
    "miniprogram_npm/@vant/weapp/share-sheet/index.wxss"
    "miniprogram_npm/@vant/weapp/share-sheet/options.js"
    "miniprogram_npm/@vant/weapp/share-sheet/options.json"
    "miniprogram_npm/@vant/weapp/share-sheet/options.wxml"
    "miniprogram_npm/@vant/weapp/share-sheet/options.wxs"
    "miniprogram_npm/@vant/weapp/dialog/dialog.js"
    "miniprogram_npm/@vant/weapp/share-sheet/options.wxss"
    "miniprogram_npm/@vant/weapp/definitions/index.js"
    "miniprogram_npm/@vant/weapp/count-down/index.js"
    "miniprogram_npm/@vant/weapp/index-bar/index.js"
    "miniprogram_npm/@vant/weapp/count-down/index.json"
    "miniprogram_npm/@vant/weapp/index-bar/index.json"
    "miniprogram_npm/@vant/weapp/count-down/index.wxml"
    "miniprogram_npm/@vant/weapp/index-bar/index.wxml"
    "miniprogram_npm/@vant/weapp/count-down/index.wxss"
    "miniprogram_npm/@vant/weapp/index-bar/index.wxss"
    "miniprogram_npm/@vant/weapp/tabbar-item/index.js"
    "miniprogram_npm/@vant/weapp/tabbar-item/index.json"
    "miniprogram_npm/@vant/weapp/count-down/utils.js"
    "miniprogram_npm/@vant/weapp/index-anchor/index.js"
    "miniprogram_npm/@vant/weapp/tabbar-item/index.wxml"
    "miniprogram_npm/@vant/weapp/index-anchor/index.json"
    "miniprogram_npm/@vant/weapp/tabbar-item/index.wxss"
    "miniprogram_npm/@vant/weapp/config-provider/index.js"
    "miniprogram_npm/@vant/weapp/index-anchor/index.wxml"
    "miniprogram_npm/@vant/weapp/config-provider/index.json"
    "miniprogram_npm/@vant/weapp/index-anchor/index.wxss"
    "miniprogram_npm/@vant/weapp/tabbar/index.js"
    "miniprogram_npm/@vant/weapp/config-provider/index.wxml"
    "miniprogram_npm/@vant/weapp/tabbar/index.json"
    "miniprogram_npm/@vant/weapp/config-provider/index.wxs"
    "miniprogram_npm/@vant/weapp/tabbar/index.wxml"
    "miniprogram_npm/@vant/weapp/tabbar/index.wxss"
    "miniprogram_npm/@vant/weapp/common/style/clearfix.wxss"
    "miniprogram_npm/@vant/weapp/common/style/ellipsis.wxss"
    "miniprogram_npm/@vant/weapp/common/style/hairline.wxss"
    "miniprogram_npm/@vant/weapp/common/style/var.wxss"
    "miniprogram_npm/@vant/weapp/common/style/mixins/clearfix.wxss"
    "miniprogram_npm/@vant/weapp/common/style/mixins/ellipsis.wxss"
    "miniprogram_npm/@vant/weapp/common/style/mixins/hairline.wxss"
    "miniprogram_npm/@vant/weapp/collapse-item/animate.js"
    "miniprogram_npm/@vant/weapp/collapse-item/index.js"
    "miniprogram_npm/@vant/weapp/collapse-item/index.json"
    "miniprogram_npm/@vant/weapp/collapse-item/index.wxml"
    "miniprogram_npm/@vant/weapp/collapse-item/index.wxss"
    "miniprogram_npm/@vant/weapp/collapse/index.js"
    "miniprogram_npm/@vant/weapp/collapse/index.json"
    "miniprogram_npm/@vant/weapp/collapse/index.wxml"
    "miniprogram_npm/@vant/weapp/collapse/index.wxss"
)

echo "📋 发现 ${#unused_files[@]} 个无依赖文件需要移动"

# 统计信息
moved_count=0
skipped_count=0

# 移动无依赖文件
for file in "${unused_files[@]}"; do
    if [ -f "$file" ]; then
        echo "🔄 移动文件: $file"
        
        # 创建目标目录结构
        target_dir="$backup_dir/$(dirname "$file")"
        mkdir -p "$target_dir"
        
        # 移动文件
        mv "$file" "$backup_dir/$file"
        
        ((moved_count++))
    else
        echo "⚠️  文件不存在，跳过: $file"
        ((skipped_count++))
    fi
done

# 移动后清理空目录
echo "🧹 清理空目录..."
find miniprogram_npm -type d -empty -delete 2>/dev/null || true

echo ""
echo "✅ 精准清理完成！"
echo "📊 统计信息:"
echo "   - 目标文件数: ${#unused_files[@]}"
echo "   - 成功移动: $moved_count"
echo "   - 跳过文件: $skipped_count" 
echo "   - 备份位置: $backup_dir"

# 显示目录大小变化
echo ""
echo "📐 目录大小:"
current_size=$(du -sh . | cut -f1)
echo "   - 当前大小: $current_size"

backup_size=$(du -sh "$backup_dir" | cut -f1)
echo "   - 备份大小: $backup_size"

echo ""
echo "🔍 验证编译状态..."
echo "请在微信开发者工具中验证小程序是否正常编译"