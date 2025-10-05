#!/usr/bin/env python3
"""
五好伴学小程序 - TabBar 图标生成器
使用 PIL (Pillow) 生成简单的占位符图标
"""

try:
    import os

    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("❌ 未安装 Pillow 库")
    print("📥 正在安装 Pillow...")
    import subprocess

    subprocess.check_call(["pip3", "install", "pillow"])
    import os

    from PIL import Image, ImageDraw, ImageFont

# 图标配置
ICON_SIZE = 162  # 2倍图
ICONS = {"home": "🏠", "homework": "📝", "chat": "💬", "report": "📊", "profile": "👤"}

# 颜色配置
COLOR_NORMAL = "#999999"
COLOR_ACTIVE = "#1890ff"


def hex_to_rgb(hex_color):
    """将十六进制颜色转换为RGB"""
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))


def create_icon(filename, color, emoji):
    """创建图标"""
    # 创建图像
    img = Image.new("RGBA", (ICON_SIZE, ICON_SIZE), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)

    # 绘制圆形背景
    rgb = hex_to_rgb(color)
    draw.ellipse([20, 20, ICON_SIZE - 20, ICON_SIZE - 20], fill=rgb + (255,))

    # 添加文字（emoji 或首字母）
    try:
        # 尝试使用系统字体
        font = ImageFont.truetype("/System/Library/Fonts/Apple Color Emoji.ttc", 80)
    except:
        try:
            font = ImageFont.truetype(
                "/System/Library/Fonts/Supplemental/Arial Unicode.ttf", 60
            )
        except:
            font = ImageFont.load_default()

    # 绘制文字
    text = emoji
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (ICON_SIZE - text_width) / 2
    y = (ICON_SIZE - text_height) / 2 - 10

    draw.text((x, y), text, fill=(255, 255, 255, 255), font=font)

    # 保存图标
    img.save(filename, "PNG")
    print(f"✅ 创建: {filename}")


def main():
    # 确保目录存在
    icon_dir = "assets/icons"
    os.makedirs(icon_dir, exist_ok=True)

    print("🎨 开始生成 TabBar 图标...\n")

    # 生成所有图标
    for name, emoji in ICONS.items():
        # 普通状态
        create_icon(f"{icon_dir}/{name}.png", COLOR_NORMAL, emoji)
        # 选中状态
        create_icon(f"{icon_dir}/{name}-active.png", COLOR_ACTIVE, emoji)

    print(f"\n🎉 所有图标生成完成！")
    print(f"📁 图标位置: {icon_dir}/")
    print("\n⚠️  这些是临时占位符图标，建议后续替换为专业设计的图标")


if __name__ == "__main__":
    main()
