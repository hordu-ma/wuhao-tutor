#!/usr/bin/env python3
"""
生成五好伴学的默认头像和空用户头像
- default-avatar.png: 默认用户头像（未上传头像时使用）
- empty-user.png: 空状态占位图
"""

import os

from PIL import Image, ImageDraw, ImageFont


def create_default_avatar(output_path, size=200):
    """
    创建默认用户头像
    - 渐变蓝色背景
    - 白色用户图标（简约人形）
    """
    # 创建图像
    img = Image.new("RGB", (size, size), color="white")
    draw = ImageDraw.Draw(img)

    # 绘制渐变蓝色圆形背景
    for i in range(size):
        for j in range(size):
            # 计算距离中心的距离
            dx = i - size // 2
            dy = j - size // 2
            distance = (dx * dx + dy * dy) ** 0.5

            if distance <= size // 2:
                # 渐变色计算
                ratio = distance / (size // 2)
                r = int(24 + (64 - 24) * ratio)
                g = int(144 + (169 - 144) * ratio)
                b = int(255 + (255 - 255) * ratio)
                img.putpixel((i, j), (r, g, b))

    # 绘制白色用户图标
    # 头部（圆形）
    head_radius = size // 6
    head_center_y = size // 2 - size // 8
    draw.ellipse(
        [
            size // 2 - head_radius,
            head_center_y - head_radius,
            size // 2 + head_radius,
            head_center_y + head_radius,
        ],
        fill="white",
    )

    # 身体（半圆形/梯形）
    body_top = head_center_y + head_radius + size // 20
    body_width = size // 3
    body_height = size // 4

    # 绘制身体轮廓
    body_points = [
        (size // 2 - body_width // 3, body_top),
        (size // 2 + body_width // 3, body_top),
        (size // 2 + body_width // 2, body_top + body_height),
        (size // 2 - body_width // 2, body_top + body_height),
    ]
    draw.polygon(body_points, fill="white")

    # 保存图片
    img.save(output_path, "PNG")
    print(f"✅ 默认头像已生成: {output_path}")
    print(f"   尺寸: {size}x{size} 像素")
    print(f"   样式: 渐变蓝色背景 + 白色用户图标")


def create_empty_user_avatar(output_path, size=200):
    """
    创建空用户占位图
    - 浅灰色背景
    - 深灰色虚线轮廓
    - 简约用户图标
    """
    # 创建图像
    img = Image.new("RGB", (size, size), color="#f5f5f5")
    draw = ImageDraw.Draw(img)

    # 绘制圆形背景
    draw.ellipse([0, 0, size, size], fill="#f0f0f0", outline="#d9d9d9", width=2)

    # 绘制虚线圆圈（装饰）
    inner_margin = size // 10
    for angle in range(0, 360, 15):
        import math

        radius = size // 2 - inner_margin
        x1 = size // 2 + int(radius * math.cos(math.radians(angle)))
        y1 = size // 2 + int(radius * math.sin(math.radians(angle)))
        x2 = size // 2 + int(radius * math.cos(math.radians(angle + 5)))
        y2 = size // 2 + int(radius * math.sin(math.radians(angle + 5)))
        draw.line([x1, y1, x2, y2], fill="#bfbfbf", width=2)

    # 绘制灰色用户图标
    icon_color = "#999999"

    # 头部
    head_radius = size // 7
    head_center_y = size // 2 - size // 10
    draw.ellipse(
        [
            size // 2 - head_radius,
            head_center_y - head_radius,
            size // 2 + head_radius,
            head_center_y + head_radius,
        ],
        fill=icon_color,
    )

    # 身体
    body_top = head_center_y + head_radius + size // 25
    body_width = size // 3
    body_height = size // 5

    body_points = [
        (size // 2 - body_width // 3, body_top),
        (size // 2 + body_width // 3, body_top),
        (size // 2 + body_width // 2, body_top + body_height),
        (size // 2 - body_width // 2, body_top + body_height),
    ]
    draw.polygon(body_points, fill=icon_color)

    # 保存图片
    img.save(output_path, "PNG")
    print(f"✅ 空用户头像已生成: {output_path}")
    print(f"   尺寸: {size}x{size} 像素")
    print(f"   样式: 浅灰色背景 + 虚线装饰 + 灰色用户图标")


if __name__ == "__main__":
    # 生成头像
    assets_dir = os.path.join(os.path.dirname(__file__), "assets/images")

    # 确保目录存在
    os.makedirs(assets_dir, exist_ok=True)

    # 生成默认头像
    default_avatar_path = os.path.join(assets_dir, "default-avatar.png")
    create_default_avatar(default_avatar_path, size=200)

    # 生成空用户头像
    empty_user_path = os.path.join(assets_dir, "empty-user.png")
    create_empty_user_avatar(empty_user_path, size=200)

    print("\n🎨 头像生成完成！")
