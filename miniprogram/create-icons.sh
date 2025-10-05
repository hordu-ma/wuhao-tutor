#!/bin/bash

# 创建简单的占位符图标（使用 ImageMagick 或直接复制现有图片）
# 这里我们先创建一个说明文件

cat > assets/icons/README.md << 'ICONREADME'
# TabBar 图标说明

## 所需图标列表

每个图标需要两个版本：
- 普通状态（灰色）
- 选中状态（蓝色）

### 图标规格
- 尺寸：81px × 81px
- 格式：PNG（支持透明背景）
- 建议使用 2 倍图（162px × 162px）

### 所需图标文件

1. **home.png** / **home-active.png** - 首页图标
2. **homework.png** / **homework-active.png** - 作业图标  
3. **chat.png** / **chat-active.png** - 问答图标
4. **report.png** / **report-active.png** - 报告图标
5. **profile.png** / **profile-active.png** - 我的图标

## 临时解决方案

在图标制作完成前，可以：
1. 使用在线图标生成工具：https://www.iconfont.cn/
2. 从开源图标库下载：https://www.flaticon.com/
3. 使用微信官方示例图标

## 快速获取图标

访问 https://www.iconfont.cn/ 搜索并下载以下图标：
- home / 首页
- homework / 作业 / 文档
- chat / 对话 / 消息
- report / 报告 / 图表
- profile / 用户 / 个人中心
ICONREADME

echo "图标说明文件已创建"
