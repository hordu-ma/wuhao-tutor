# Vant Weapp 字体加载问题修复说明

## 问题描述
错误：`[Network layer in render layer error] Failed to load font http://at.alicdn.com/t/font_2553318_kfmm2polfg.woff?t=1694918397822`

## 原因
Vant Weapp 组件库使用阿里图标库的CDN字体文件，需要配置服务器域名白名单。

## 已修复
✅ 在 `project.config.json` 中添加了 `https://at.alicdn.com` 到 `downloadDomain`

## 生产环境配置
⚠️ 正式发布前需要在微信小程序后台配置服务器域名：

1. 登录 [微信公众平台](https://mp.weixin.qq.com)
2. 进入"开发" -> "开发管理" -> "开发设置"
3. 找到"服务器域名" -> "downloadFile合法域名"
4. 添加：`https://at.alicdn.com`

## 开发阶段临时方案
在微信开发者工具中：
1. 点击右上角"详情"
2. 勾选"不校验合法域名、web-view（业务域名）、TLS 版本以及 HTTPS 证书"

## 长期优化建议
考虑将字体文件本地化，避免依赖外部CDN：
- 下载 Vant 字体文件到项目
- 修改 `@vant/weapp/icon/index.wxss` 中的字体路径
- 这样可以提高加载速度和稳定性
