# 域名切换执行检查清单

> **域名**: www.horsduroot.com  
> **目标服务器**: 121.199.173.244  
> **执行日期**: \***\*\_\_\_\_\*\***  
> **执行人**: liguoma

---

## 📋 执行前检查 (Pre-flight Checklist)

### 环境准备

- [ ] 新服务器后端服务运行正常

  ```bash
  ssh root@121.199.173.244
  systemctl status wuhao-tutor.service
  # 预期: active (running)
  ```

- [ ] 新服务器 Nginx 运行正常

  ```bash
  systemctl status nginx
  # 预期: active (running)
  ```

- [ ] 新服务器健康检查通过

  ```bash
  curl http://127.0.0.1:8000/health
  # 预期: {"status":"healthy","version":"0.2.1"}
  ```

- [ ] 防火墙已开放必要端口
  ```bash
  ufw status
  # 确认: 80/tcp, 443/tcp ALLOW
  ```

### 权限确认

- [ ] 拥有新服务器 root 权限

  ```bash
  ssh root@121.199.173.244 whoami
  # 预期: root
  ```

- [ ] 拥有阿里云域名管理权限

  - 登录: https://dns.console.aliyun.com/
  - 确认可以修改 horsduroot.com 的解析记录

- [ ] 拥有微信小程序后台管理权限
  - 登录: https://mp.weixin.qq.com/
  - 确认可以修改服务器域名配置

### 备份确认

- [ ] 已备份旧服务器配置

  ```bash
  ssh root@60.205.124.67
  tar -czf ~/backup-$(date +%Y%m%d).tar.gz \
    /etc/nginx/ \
    /path/to/wuhao-tutor/.env.production
  ```

- [ ] 已备份本地项目配置
  ```bash
  cd /Users/liguoma/my-devs/python/wuhao-tutor
  git status  # 确保无未提交的修改
  git commit -am "backup: before domain migration"
  ```

### 脚本准备

- [ ] 已下载最新代码

  ```bash
  cd /Users/liguoma/my-devs/python/wuhao-tutor
  git pull
  ```

- [ ] 脚本权限正确
  ```bash
  ls -la scripts/deploy/domain-migration.sh
  ls -la scripts/deploy/verify-domain-migration.sh
  # 确认有执行权限 (-rwxr-xr-x)
  ```

---

## 🚀 执行阶段检查

### Step 1: 上传脚本

- [ ] 脚本上传成功
  ```bash
  scp scripts/deploy/domain-migration.sh root@121.199.173.244:/tmp/
  # 预期: domain-migration.sh 100%
  ```

### Step 2: 执行自动化脚本

- [ ] SSH 登录成功

  ```bash
  ssh root@121.199.173.244
  ```

- [ ] 脚本执行开始

  ```bash
  sudo bash /tmp/domain-migration.sh
  # 记录开始时间: ____________
  ```

- [ ] 服务状态检查通过

  - ✓ wuhao-tutor 服务运行正常
  - ✓ Nginx 服务运行正常
  - ✓ 应用健康检查通过

- [ ] 配置文件备份成功

  - 备份目录: /root/nginx-backup-YYYYMMDD-HHMMSS

- [ ] Nginx 配置更新成功
  - ✓ 配置文件已更新 (`/etc/nginx/conf.d/wuhao-tutor.conf`)
  - ✓ Nginx 配置测试通过 (nginx -t)
  - ✓ Nginx 已重载

### Step 3: DNS 解析修改

- [ ] 登录阿里云控制台成功

  - URL: https://dns.console.aliyun.com/

- [ ] 找到域名 horsduroot.com

- [ ] 修改 www 记录

  - 记录类型: A
  - 主机记录: www
  - 旧值: 60.205.124.67
  - 新值: 121.199.173.244
  - TTL: 600
  - 修改时间: \***\*\_\_\_\_\*\***

- [ ] 修改 @ 记录

  - 记录类型: A
  - 主机记录: @
  - 旧值: 60.205.124.67
  - 新值: 121.199.173.244
  - TTL: 600
  - 修改时间: \***\*\_\_\_\_\*\***

- [ ] DNS 配置已保存

### Step 4: DNS 生效验证

- [ ] 本地 DNS 缓存已清除 (Mac)

  ```bash
  sudo dscacheutil -flushcache
  sudo killall -HUP mDNSResponder
  ```

- [ ] DNS 解析检查 (每 5 分钟检查一次)

  ```bash
  nslookup www.horsduroot.com
  ```

  | 检查时间      | 解析结果             | 状态 |
  | ------------- | -------------------- | ---- |
  | \_**\_:\_\_** | \***\*\_\_\_\_\*\*** | [ ]  |
  | \_**\_:\_\_** | \***\*\_\_\_\_\*\*** | [ ]  |
  | \_**\_:\_\_** | \***\*\_\_\_\_\*\*** | [ ]  |
  | \_**\_:\_\_** | \***\*\_\_\_\_\*\*** | [ ]  |

- [ ] DNS 生效确认
  - 预期结果: 121.199.173.244
  - 实际结果: \***\*\_\_\_\_\*\***
  - 生效时间: \***\*\_\_\_\_\*\***

### Step 5: SSL 证书配置

- [ ] Certbot 已安装

  ```bash
  certbot --version
  ```

- [ ] 邮箱地址已输入

  - 邮箱: \***\*\_\_\_\_\*\***

- [ ] SSL 证书申请成功

  - 域名: www.horsduroot.com, horsduroot.com
  - 颁发时间: \***\*\_\_\_\_\*\***
  - 到期时间: \***\*\_\_\_\_\*\***

- [ ] Nginx 配置自动更新

  - HTTPS (443) 配置已添加
  - HTTP (80) 自动跳转 HTTPS

- [ ] 证书自动续期测试通过
  ```bash
  certbot renew --dry-run
  ```

### Step 6: 应用配置更新

- [ ] 后端配置已更新

  - API_BASE_URL: https://www.horsduroot.com
  - FRONTEND_URL: https://www.horsduroot.com

- [ ] 应用服务已重启

  ```bash
  systemctl restart wuhao-tutor.service
  ```

- [ ] 应用启动成功
  ```bash
  systemctl status wuhao-tutor.service
  # 预期: active (running)
  ```

### Step 7: 脚本验证结果

- [ ] HTTP 跳转测试通过

  - 状态码: **\_\_** (预期: 301 或 302)

- [ ] HTTPS 访问测试通过

  - 状态码: **\_\_** (预期: 200)

- [ ] 健康检查测试通过

  - 响应: \***\*\_\_\_\_\*\***

- [ ] SSL 证书验证通过
  - 有效期至: \***\*\_\_\_\_\*\***

---

## 🧪 本地验证检查

### Step 8: 执行验证脚本

- [ ] 在本地 Mac 执行验证脚本

  ```bash
  cd /Users/liguoma/my-devs/python/wuhao-tutor
  bash scripts/deploy/verify-domain-migration.sh
  ```

- [ ] 测试结果记录

  | 测试项     | 状态              | 备注                 |
  | ---------- | ----------------- | -------------------- |
  | DNS 解析   | [ ] PASS [ ] FAIL | \***\*\_\_\_\_\*\*** |
  | HTTP 访问  | [ ] PASS [ ] FAIL | \***\*\_\_\_\_\*\*** |
  | HTTPS 访问 | [ ] PASS [ ] FAIL | \***\*\_\_\_\_\*\*** |
  | API 接口   | [ ] PASS [ ] FAIL | \***\*\_\_\_\_\*\*** |
  | 性能检查   | [ ] PASS [ ] FAIL | \***\*\_\_\_\_\*\*** |
  | 安全配置   | [ ] PASS [ ] FAIL | \***\*\_\_\_\_\*\*** |
  | 静态资源   | [ ] PASS [ ] FAIL | \***\*\_\_\_\_\*\*** |

- [ ] 测试通过率
  - 通过: \_\_\_\_ / 7
  - 失败: \_\_\_\_ / 7
  - 警告: \_\_\_\_ / 7

---

## 🌐 后端和前端配置更新

### Step 9: 更新后端配置

- [ ] 编辑后端环境变量

  ```bash
  ssh root@121.199.173.244
  vim /opt/wuhao-tutor/.env.production
  ```

  修改内容：

  - BASE_URL=https://www.horsduroot.com
  - BACKEND_CORS_ORIGINS='["https://www.horsduroot.com","http://www.horsduroot.com","https://horsduroot.com","http://horsduroot.com","https://121.199.173.244","http://121.199.173.244"]'

- [ ] 重启后端服务

  ```bash
  systemctl restart wuhao-tutor.service
  systemctl status wuhao-tutor.service
  ```

  - 服务启动成功: [ ]
  - 健康检查通过: [ ]

### Step 10: 前端配置（无需修改）

- [ ] 确认前端配置

  当前配置使用相对路径，自动适配域名和 IP 访问：

  位置：`/opt/wuhao-tutor/frontend/.env.production`

  ```bash
  VITE_API_BASE_URL=/api/v1
  ```

- [ ] 如需重新部署（可选）

  ```bash
  # 本地构建
  cd frontend && npm run build

  # 上传到服务器实际路径
  scp -r dist/* root@121.199.173.244:/var/www/html/
  ```

---

## 📱 小程序配置更新

### Step 11: 更新小程序配置

- [ ] 编辑小程序配置

  ```bash
  vim miniprogram/config/index.js
  ```

  - baseUrl: https://www.horsduroot.com
  - appId: wx2a8b340606664785 (确认正确)

- [ ] 检查其他配置文件
  ```bash
  grep -r "121.199.173.244" miniprogram/
  grep -r "60.205.124.67" miniprogram/
  ```
  - 发现需要修改的文件: \***\*\_\_\_\_\*\***

### Step 12: 微信小程序后台配置

- [ ] 登录微信公众平台

  - URL: https://mp.weixin.qq.com/

- [ ] 进入服务器域名配置

  - 路径: 开发管理 → 开发设置 → 服务器域名

- [ ] 添加 request 合法域名

  - 域名: https://www.horsduroot.com
  - 添加时间: \***\*\_\_\_\_\*\***

- [ ] 添加 uploadFile 合法域名

  - 域名: https://www.horsduroot.com
  - 添加时间: \***\*\_\_\_\_\*\***

- [ ] 添加 downloadFile 合法域名

  - 域名: https://www.horsduroot.com
  - 添加时间: \***\*\_\_\_\_\*\***

- [ ] 删除旧域名配置 (如有)

  - 删除: https://60.205.124.67 或其他旧配置

- [ ] 等待配置生效
  - 配置时间: \***\*\_\_\_\_\*\***
  - 预计生效: \***\*\_\_\_\_\*\*** (5-10 分钟后)

---

## ✅ 完整功能验证

### Step 12: Web 前端测试

- [ ] 浏览器访问首页

  - URL: https://www.horsduroot.com
  - SSL 证书: [ ] 有效 [ ] 警告
  - 页面加载: [ ] 正常 [ ] 异常

- [ ] 用户登录功能

  - 登录成功: [ ]
  - Token 获取: [ ]
  - 页面跳转: [ ]

- [ ] 作业问答功能

  - 发送文字消息: [ ]
  - 上传图片: [ ]
  - AI 响应: [ ]

- [ ] 错题手册功能

  - 查看错题列表: [ ]
  - 添加错题: [ ]
  - 今日复习: [ ]

- [ ] 学习记录功能

  - 查看统计数据: [ ]
  - 图表展示: [ ]

- [ ] 浏览器控制台检查
  - [ ] 无 JavaScript 错误
  - [ ] 无 CORS 错误
  - [ ] API 请求指向新域名

### Step 13: 小程序测试

- [ ] 微信开发者工具测试

  - 小程序启动: [ ] 正常 [ ] 异常
  - 网络请求: [ ] 成功 [ ] 失败
  - 域名检查: [ ] 无警告 [ ] 有警告

- [ ] 真机测试 (iOS)

  - 小程序打开: [ ]
  - 登录功能: [ ]
  - 作业问答: [ ]
  - 图片上传: [ ]
  - 错题本: [ ]

- [ ] 真机测试 (Android)
  - 小程序打开: [ ]
  - 登录功能: [ ]
  - 作业问答: [ ]
  - 图片上传: [ ]
  - 错题本: [ ]

---

## 📊 监控和观察

### Step 14: 日志监控

- [ ] 新服务器日志监控 (持续 1 小时)

  ```bash
  ssh root@121.199.173.244
  tail -f /var/log/nginx/access.log
  tail -f /var/log/nginx/error.log
  ```

  - 访问量: \***\*\_\_\_\_\*\***
  - 错误数: \***\*\_\_\_\_\*\***
  - 异常情况: \***\*\_\_\_\_\*\***

- [ ] 旧服务器流量检查
  ```bash
  ssh root@60.205.124.67
  tail -f /var/log/nginx/access.log
  ```
  - 最后访问时间: \***\*\_\_\_\_\*\***
  - 访问量趋势: [ ] 递减 [ ] 不变 [ ] 递增

### Step 15: 性能检查

- [ ] API 响应时间

  ```bash
  curl -s -o /dev/null -w "%{time_total}" https://www.horsduroot.com/health
  ```

  - 响应时间: **\_\_** 秒 (预期 <1 秒)

- [ ] 首页加载时间
  - 浏览器 Network 选项卡查看
  - 加载时间: **\_\_** 秒 (预期 <3 秒)

---

## 🎯 最终验收

### 验收标准确认

- [ ] 所有核心功能正常工作
- [ ] 无关键错误日志
- [ ] 性能指标符合预期
- [ ] 用户体验良好
- [ ] SSL 证书有效
- [ ] 域名解析正确

### 完成时间记录

- 开始时间: \***\*\_\_\_\_\*\***
- 结束时间: \***\*\_\_\_\_\*\***
- 总耗时: **\_\_** 小时 **\_\_** 分钟

### 遇到的问题记录

1. 问题: \***\*\_\_\_\_\*\***
   解决方案: \***\*\_\_\_\_\*\***
   耗时: \***\*\_\_\_\_\*\***

2. 问题: \***\*\_\_\_\_\*\***
   解决方案: \***\*\_\_\_\_\*\***
   耗时: \***\*\_\_\_\_\*\***

3. 问题: \***\*\_\_\_\_\*\***
   解决方案: \***\*\_\_\_\_\*\***
   耗时: \***\*\_\_\_\_\*\***

---

## 📝 后续观察计划

### 24 小时内

- [ ] 每 2 小时检查一次错误日志
- [ ] 监控旧服务器流量变化
- [ ] 收集用户反馈（如有）

### 48 小时后

- [ ] 确认旧服务器无流量
- [ ] 备份旧服务器配置
- [ ] 考虑停止旧服务器服务

### 1 周后

- [ ] 验证 SSL 证书自动续期配置
- [ ] 更新项目文档
- [ ] 归档切换记录

---

## 🚨 回滚记录（如需要）

### 回滚原因

---

### 回滚操作

- [ ] DNS 解析已回滚

  - www.horsduroot.com → 60.205.124.67
  - horsduroot.com → 60.205.124.67
  - 回滚时间: \***\*\_\_\_\_\*\***

- [ ] 配置已恢复
- [ ] 服务已验证

### 问题分析

---

### 再次切换计划

---

---

## ✨ 签名确认

**执行人**: liguoma  
**执行日期**: \***\*\_\_\_\_\*\***  
**验收结果**: [ ] 成功 [ ] 部分成功 [ ] 失败  
**备注**: \***\*\_\_\_\_\*\***

---

**文档版本**: v1.0  
**创建时间**: 2025-10-19  
**相关文档**: [域名迁移索引](./DOMAIN_MIGRATION_INDEX.md)
