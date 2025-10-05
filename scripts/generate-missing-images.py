#!/usr/bin/env python3
"""
生成小程序缺失的图标和图片
"""

import os

from PIL import Image, ImageDraw, ImageFont


def create_icon(size, bg_color, emoji, filename):
    """创建带 emoji 的图标"""
    img = Image.new("RGB", (size, size), color=bg_color)
    draw = ImageDraw.Draw(img)

    # 绘制圆形背景
    draw.ellipse(
        [10, 10, size - 10, size - 10], fill=bg_color, outline="white", width=3
    )

    # 尝试添加文本（emoji）
    try:
        font_size = int(size * 0.4)
        try:
            font = ImageFont.truetype(
                "/System/Library/Fonts/Apple Color Emoji.ttc", font_size
            )
        except:
            font = ImageFont.load_default()

        # 计算文本位置（居中）
        bbox = draw.textbbox((0, 0), emoji, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        position = ((size - text_width) // 2, (size - text_height) // 2 - 5)

        draw.text(position, emoji, fill="white", font=font)
    except Exception as e:
        print(f"警告: 无法添加 emoji，使用简单图形: {e}")
        # 回退方案：绘制简单的几何图形
        draw.rectangle(
            [size // 4, size // 4, 3 * size // 4, 3 * size // 4], fill="white"
        )

    img.save(filename)
    print(f"✅ 创建图标: {filename}")


def create_placeholder_image(width, height, text, filename):
    """创建占位图片"""
    img = Image.new("RGB", (width, height), color="#e0e0e0")
    draw = ImageDraw.Draw(img)

    # 绘制边框
    draw.rectangle([0, 0, width - 1, height - 1], outline="#999999", width=2)

    # 绘制对角线
    draw.line([0, 0, width, height], fill="#999999", width=1)
    draw.line([0, height, width, 0], fill="#999999", width=1)

    # 添加文本
    try:
        font_size = 24
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
        except:
            font = ImageFont.load_default()

        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        position = ((width - text_width) // 2, (height - text_height) // 2)

        # 绘制文本背景
        padding = 10
        draw.rectangle(
            [
                position[0] - padding,
                position[1] - padding,
                position[0] + text_width + padding,
                position[1] + text_height + padding,
            ],
            fill="white",
        )

        draw.text(position, text, fill="#333333", font=font)
    except Exception as e:
        print(f"警告: 无法添加文本: {e}")

    img.save(filename)
    print(f"✅ 创建占位图: {filename}")


def main():
    # 获取小程序根目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)

    # 图标目录
    icons_dir = os.path.join(project_root, "miniprogram", "assets", "icons")
    images_dir = os.path.join(project_root, "miniprogram", "assets", "images")

    # 确保目录存在
    os.makedirs(icons_dir, exist_ok=True)
    os.makedirs(images_dir, exist_ok=True)

    print("🚀 开始生成缺失的图片资源...\n")

    # 生成图标
    icons_to_create = [
        ("login.png", "#1890ff", "🔐"),
        ("demo.png", "#52c41a", "🎮"),
    ]

    for filename, color, emoji in icons_to_create:
        filepath = os.path.join(icons_dir, filename)
        create_icon(200, color, emoji, filepath)

    # 生成图片
    images_to_create = [
        ("default-avatar.png", 200, 200, "Avatar"),
        ("empty-user.png", 300, 300, "Empty"),
    ]

    for filename, width, height, text in images_to_create:
        filepath = os.path.join(images_dir, filename)
        create_placeholder_image(width, height, text, filepath)

    print("\n✅ 所有图片资源生成完成!")
    print(f"📁 图标位置: {icons_dir}")
    print(f"📁 图片位置: {images_dir}")


if __name__ == "__main__":
    main()
