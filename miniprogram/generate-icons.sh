#!/bin/bash

# 五好伴学小程序 - TabBar 图标生成脚本
# 创建简单的占位符图标

ICON_DIR="assets/icons"
cd "$(dirname "$0")"

echo "🎨 开始创建 TabBar 占位符图标..."

# 检查 ImageMagick 是否安装
if ! command -v convert &> /dev/null; then
    echo "⚠️  ImageMagick 未安装"
    echo "📥 正在使用 macOS 内置工具创建图标..."
    
    # 使用 macOS sips 工具创建简单的灰色方块作为占位符
    # 创建一个 81x81 的 PNG 文件
    
    # 由于无法直接创建，我们下载示例图标
    echo ""
    echo "⚠️  无法自动生成图标，请手动下载图标文件"
    echo ""
    echo "📋 方案 1: 使用阿里巴巴图标库（推荐）"
    echo "   1. 访问: https://www.iconfont.cn/"
    echo "   2. 搜索并下载以下图标（PNG 格式，81x81 或 162x162）："
    echo "      - home (首页)"
    echo "      - document (作业)"
    echo "      - message (问答)"  
    echo "      - chart (报告)"
    echo "      - user (我的)"
    echo "   3. 保存到: $ICON_DIR/"
    echo ""
    echo "📋 方案 2: 使用微信官方示例"
    echo "   1. 下载微信小程序示例: https://github.com/wechat-miniprogram/miniprogram-demo"
    echo "   2. 复制 images 目录下的图标文件"
    echo ""
    echo "📋 方案 3: 临时使用文字 TabBar"
    echo "   修改 app.json，移除 iconPath 和 selectedIconPath 字段"
    echo "   （注意：这样 tabBar 只显示文字，没有图标）"
    echo ""
    echo "📁 所需文件清单:"
    echo "   $ICON_DIR/home.png"
    echo "   $ICON_DIR/home-active.png"
    echo "   $ICON_DIR/homework.png"
    echo "   $ICON_DIR/homework-active.png"
    echo "   $ICON_DIR/chat.png"
    echo "   $ICON_DIR/chat-active.png"
    echo "   $ICON_DIR/report.png"
    echo "   $ICON_DIR/report-active.png"
    echo "   $ICON_DIR/profile.png"
    echo "   $ICON_DIR/profile-active.png"
    echo ""
    
    # 创建 README
    cat > "$ICON_DIR/README.md" << 'ICONREADME'
# TabBar 图标说明

## 图标规格要求

- **尺寸**: 81px × 81px（推荐使用 162px × 162px 的 2 倍图）
- **格式**: PNG（支持透明背景）
- **颜色**: 
  - 普通状态：灰色 (#999999)
  - 选中状态：蓝色 (#1890ff)

## 快速获取图标

### 方法 1: 阿里巴巴图标库（iconfont）

1. 访问 https://www.iconfont.cn/
2. 注册/登录账号
3. 搜索以下关键词并下载 PNG 图标：
   - `home` 或 `首页` → home.png
   - `document` 或 `作业` 或 `file` → homework.png
   - `message` 或 `chat` 或 `对话` → chat.png
   - `chart` 或 `report` 或 `统计` → report.png
   - `user` 或 `profile` 或 `个人` → profile.png

4. 每个图标下载两次：
   - 灰色版本（普通状态）
   - 蓝色版本（选中状态）或使用 Photoshop/在线工具调色

### 方法 2: Flaticon

1. 访问 https://www.flaticon.com/
2. 搜索图标关键词
3. 下载免费的 PNG 图标
4. 调整颜色和大小

### 方法 3: 使用 Emoji 转图标（临时方案）

可以使用在线工具将 emoji 转换为 PNG：
- 🏠 → home.png
- 📝 → homework.png
- 💬 → chat.png
- 📊 → report.png
- 👤 → profile.png

## 图标命名规则

| 功能 | 普通状态 | 选中状态 |
|-----|---------|---------|
| 首页 | home.png | home-active.png |
| 作业 | homework.png | homework-active.png |
| 问答 | chat.png | chat-active.png |
| 报告 | report.png | report-active.png |
| 我的 | profile.png | profile-active.png |

## 在线图标编辑工具

- **Photopea** (免费在线 PS): https://www.photopea.com/
- **Remove.bg** (去背景): https://www.remove.bg/
- **TinyPNG** (压缩): https://tinypng.com/

## 注意事项

1. 确保图标背景透明
2. 图标主体居中
3. 颜色符合设计规范
4. 文件大小控制在 40KB 以内
ICONREADME
    
    echo "✅ 图标说明文件已创建: $ICON_DIR/README.md"
    echo ""
    echo "💡 提示: 请按照 README.md 中的说明准备图标文件"
    
    exit 1
fi

echo "✅ ImageMagick 已安装，开始生成占位符图标..."

# 生成灰色占位符图标（普通状态）
for icon in home homework chat report profile; do
    convert -size 162x162 xc:"#999999" \
            -gravity center \
            -pointsize 60 \
            -fill white \
            -annotate +0+0 "${icon:0:1}" \
            "$ICON_DIR/${icon}.png"
    echo "✅ 创建: ${icon}.png"
done

# 生成蓝色占位符图标（选中状态）
for icon in home homework chat report profile; do
    convert -size 162x162 xc:"#1890ff" \
            -gravity center \
            -pointsize 60 \
            -fill white \
            -annotate +0+0 "${icon:0:1}" \
            "$ICON_DIR/${icon}-active.png"
    echo "✅ 创建: ${icon}-active.png"
done

echo ""
echo "🎉 占位符图标创建完成！"
echo "📁 图标位置: $ICON_DIR/"
echo ""
echo "⚠️  这些是临时占位符图标，建议替换为正式设计的图标"
echo "📖 查看 $ICON_DIR/README.md 了解如何获取正式图标"
