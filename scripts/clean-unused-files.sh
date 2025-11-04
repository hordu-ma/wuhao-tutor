#!/bin/bash

# 精准清理微信小程序无依赖文件脚本
# 基于微信开发者工具的依赖分析结果

MINIPROGRAM_DIR="/Users/liguoma/my-devs/python/wuhao-tutor/miniprogram"
BACKUP_DIR="/Users/liguoma/my-devs/python/wuhao-tutor/backup/unused-files-$(date +%Y%m%d-%H%M%S)"

echo "🔍 开始精准清理微信小程序无依赖文件..."
echo "📁 小程序目录: $MINIPROGRAM_DIR"
echo "📁 备份目录: $BACKUP_DIR"

# 创建备份目录
mkdir -p "$BACKUP_DIR"

cd "$MINIPROGRAM_DIR"

# 统计清理前的文件
echo "📊 分析当前文件结构..."

# 1. 查找并备份@vant/weapp组件库中可能未使用的组件
echo "🔍 分析@vant/weapp组件库..."
if [ -d "miniprogram_npm/@vant/weapp" ]; then
    # 获取项目中实际使用的vant组件
    echo "📋 检查项目中使用的Vant组件..."
    
    # 扫描所有.js, .json, .wxml文件中引用的vant组件
    USED_COMPONENTS=$(find pages components -name "*.js" -o -name "*.json" -o -name "*.wxml" 2>/dev/null | xargs grep -h "@vant/weapp" 2>/dev/null | grep -o "@vant/weapp/[^'\"]*" | sed 's|@vant/weapp/||' | sort -u)
    
    echo "✅ 发现使用的Vant组件:"
    echo "$USED_COMPONENTS"
    
    # 找出所有可用的vant组件
    ALL_VANT_COMPONENTS=$(ls miniprogram_npm/@vant/weapp/ | grep -v "^common$" | grep -v "^lib$")
    
    echo "📦 备份未使用的Vant组件..."
    mkdir -p "$BACKUP_DIR/miniprogram_npm/@vant/weapp"
    
    for component in $ALL_VANT_COMPONENTS; do
        # 检查这个组件是否被使用
        if ! echo "$USED_COMPONENTS" | grep -q "^$component$"; then
            if [ -d "miniprogram_npm/@vant/weapp/$component" ]; then
                echo "  📦 备份未使用组件: $component"
                mv "miniprogram_npm/@vant/weapp/$component" "$BACKUP_DIR/miniprogram_npm/@vant/weapp/"
            fi
        fi
    done
fi

# 2. 备份echarts中未使用的文件
echo "🔍 分析echarts文件..."
if [ -d "miniprogram_npm/echarts" ]; then
    mkdir -p "$BACKUP_DIR/miniprogram_npm/echarts"
    
    # 检查是否使用了echarts
    ECHARTS_USED=$(find pages components -name "*.js" 2>/dev/null | xargs grep -l "echarts" 2>/dev/null | wc -l)
    
    if [ "$ECHARTS_USED" -eq 0 ]; then
        echo "📦 备份未使用的echarts库..."
        mv miniprogram_npm/echarts/* "$BACKUP_DIR/miniprogram_npm/echarts/" 2>/dev/null || true
    else
        # 只备份可能未使用的部分（如example, test等）
        for dir in miniprogram_npm/echarts/*/; do
            dirname=$(basename "$dir")
            if [[ "$dirname" =~ ^(example|test|demo|doc)$ ]]; then
                echo "  📦 备份echarts示例: $dirname"
                mv "$dir" "$BACKUP_DIR/miniprogram_npm/echarts/" 2>/dev/null || true
            fi
        done
    fi
fi

# 3. 备份其他第三方库中的示例和测试文件
echo "🔍 清理第三方库示例文件..."
find miniprogram_npm -type d -name "example*" -o -name "demo*" -o -name "test*" -o -name "spec*" | while read dir; do
    if [ -d "$dir" ]; then
        echo "  📦 备份示例/测试目录: $dir"
        relative_path=${dir#miniprogram_npm/}
        mkdir -p "$BACKUP_DIR/miniprogram_npm/$(dirname "$relative_path")"
        mv "$dir" "$BACKUP_DIR/miniprogram_npm/$(dirname "$relative_path")/"
    fi
done

# 4. 备份可能的重复或未使用的index.js文件
echo "🔍 分析重复的index.js文件..."
find miniprogram_npm -name "index.js" -size -1k | while read file; do
    # 备份小于1KB的index.js文件（可能是空文件或只有简单导出）
    if [ -f "$file" ] && [ $(wc -c < "$file") -lt 100 ]; then
        echo "  📦 备份可能无用的小文件: $file"
        relative_path=${file#miniprogram_npm/}
        mkdir -p "$BACKUP_DIR/miniprogram_npm/$(dirname "$relative_path")"
        mv "$file" "$BACKUP_DIR/miniprogram_npm/$(dirname "$relative_path")/"
    fi
done

# 5. 清理不必要的声明文件和映射文件
echo "🔍 清理类型声明和映射文件..."
find miniprogram_npm -name "*.d.ts" -o -name "*.map" -o -name "*.md" | while read file; do
    if [ -f "$file" ]; then
        echo "  📦 备份声明/映射文件: $file"
        relative_path=${file#miniprogram_npm/}
        mkdir -p "$BACKUP_DIR/miniprogram_npm/$(dirname "$relative_path")"
        mv "$file" "$BACKUP_DIR/miniprogram_npm/$(dirname "$relative_path")/"
    fi
done

# 6. 统计结果
echo ""
echo "✅ 清理完成！"
echo ""
echo "📊 清理统计:"
BACKUP_SIZE=$(du -sh "$BACKUP_DIR" 2>/dev/null | cut -f1)
CURRENT_SIZE=$(du -sh . 2>/dev/null | cut -f1)
BACKUP_FILES=$(find "$BACKUP_DIR" -type f | wc -l)

echo "   📁 备份文件数量: $BACKUP_FILES"
echo "   💾 备份文件大小: $BACKUP_SIZE"
echo "   📁 当前目录大小: $CURRENT_SIZE"
echo ""
echo "🗂️  备份位置: $BACKUP_DIR"
echo ""
echo "📝 如需恢复，请运行:"
echo "   cp -r $BACKUP_DIR/* ."
echo ""
echo "🔄 如需重新构建npm包:"
echo "   npm run build:npm"