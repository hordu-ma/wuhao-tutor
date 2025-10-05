# 🐛 常见问题排查指南

## 问题 1: theme.json 编译错误 ✅ 已解决

### 错误信息

```
Error: theme.json: light.tabBar field needs to be string
Error: theme.json: dark.tabBar field needs to be string
```

### 原因分析

`theme.json` 文件中错误地包含了 `tabBar` 配置对象。根据微信小程序规范，`theme.json` **只能包含以下字段**：

**允许的字段**：

- `navigationBarBackgroundColor` - 导航栏背景颜色
- `navigationBarTextStyle` - 导航栏文字颜色（black/white）
- `navigationBarTitleText` - 导航栏标题文字
- `backgroundColor` - 窗口背景色
- `backgroundTextStyle` - 下拉背景字体、loading 图的样式（dark/light）
- `backgroundColorTop` - 顶部窗口背景色（iOS）
- `backgroundColorBottom` - 底部窗口背景色（iOS）

**不允许的字段**：

- ❌ `tabBar` - 这个配置应该在 `app.json` 中

### 解决方案

**修改前** (`theme.json`)：

```json
{
  "light": {
    "navigationBarBackgroundColor": "#1890ff",
    "tabBar": {
      // ❌ 错误：不应该在这里
      "color": "#999999",
      "selectedColor": "#1890ff"
    }
  }
}
```

**修改后** (`theme.json`)：

```json
{
  "light": {
    "navigationBarBackgroundColor": "#1890ff",
    "navigationBarTextStyle": "white",
    "navigationBarTitleText": "五好伴学",
    "backgroundColor": "#f5f5f5",
    "backgroundTextStyle": "light",
    "backgroundColorTop": "#ffffff",
    "backgroundColorBottom": "#ffffff"
  },
  "dark": {
    "navigationBarBackgroundColor": "#1f1f1f",
    "navigationBarTextStyle": "white",
    "navigationBarTitleText": "五好伴学",
    "backgroundColor": "#000000",
    "backgroundTextStyle": "dark",
    "backgroundColorTop": "#1f1f1f",
    "backgroundColorBottom": "#1f1f1f"
  }
}
```

**tabBar 的正确位置** (`app.json`)：

```json
{
  "pages": [...],
  "window": {...},
  "tabBar": {  // ✅ 正确：tabBar 应该在 app.json 中
    "color": "#999999",
    "selectedColor": "#1890ff",
    "backgroundColor": "#ffffff",
    "borderStyle": "black",
    "list": [...]
  }
}
```

### 验证修复

修改完成后：

1. 保存文件
2. 微信开发者工具会自动重新编译
3. BUILD 面板的错误应该消失
4. 模拟器应该正常显示

---

## 问题 2: 后端 API 连接失败

### 错误信息

```
request:fail
net::ERR_CONNECTION_REFUSED
```

### 解决方案

1. **检查后端服务是否运行**：

   ```bash
   lsof -ti:8000
   # 应该返回进程 ID，如果没有输出说明后端未启动
   ```

2. **启动后端服务**：

   ```bash
   cd /Users/liguoma/my-devs/python/wuhao-tutor
   ./scripts/start-dev.sh
   ```

3. **检查 API 配置**：

   ```bash
   cat miniprogram/config/index.js | grep baseUrl
   # 应该显示: baseUrl: 'http://localhost:8000'
   ```

4. **在开发者工具中关闭域名校验**：
   - 详情 → 本地设置
   - ✅ 勾选 "不校验合法域名..."

---

## 问题 3: npm 包安装失败

### 错误信息

```
npm ERR! code ENOENT
npm ERR! syscall open
```

### 解决方案

```bash
cd /Users/liguoma/my-devs/python/wuhao-tutor/miniprogram

# 清除缓存
rm -rf node_modules package-lock.json

# 重新安装
npm install

# 在微信开发者工具中：工具 → 构建 npm
```

---

## 问题 4: 页面空白或无法显示

### 可能原因

1. **页面路径配置错误**
   - 检查 `app.json` 中的 `pages` 数组
   - 确保页面文件夹包含 4 个文件：`.js`, `.json`, `.wxml`, `.wxss`

2. **JavaScript 语法错误**
   - 打开 Console 面板查看错误信息
   - 检查页面的 `.js` 文件是否有语法错误

3. **网络请求失败**
   - 检查 Network 面板
   - 确认后端 API 是否正常响应

### 调试步骤

```bash
# 1. 检查页面文件完整性
ls -la pages/index/

# 应该看到:
# index.js
# index.json
# index.wxml
# index.wxss

# 2. 检查 app.json 配置
cat app.json | grep "pages/index/index"

# 3. 查看后端健康检查
curl http://localhost:8000/api/v1/health
```

---

## 问题 5: 真机预览时无法访问后端

### 错误信息

```
request:fail url not in domain list
```

### 解决方案

1. **开发环境（临时）**：
   - 使用电脑的局域网 IP 地址

   ```javascript
   // config/index.js
   api: {
     baseUrl: 'http://192.168.1.100:8000'; // 改为你的电脑 IP
   }
   ```

2. **获取电脑 IP**：

   ```bash
   ifconfig | grep "inet " | grep -v 127.0.0.1
   ```

3. **生产环境**：
   - 在微信公众平台配置服务器域名
   - 使用 HTTPS 域名

---

## 快速诊断清单

遇到问题时，按顺序检查：

- [ ] 后端服务在 8000 端口运行？`lsof -ti:8000`
- [ ] 开发者工具关闭了域名校验？详情 → 本地设置
- [ ] `theme.json` 配置正确（不包含 tabBar）？
- [ ] `app.json` 配置完整（包含 pages, tabBar）？
- [ ] Console 面板有 JavaScript 错误？
- [ ] Network 面板显示请求状态？
- [ ] npm 包已正确安装？`ls node_modules`

---

## 获取帮助

- **微信开放文档**: https://developers.weixin.qq.com/miniprogram/dev/framework/
- **项目文档**: `/docs/miniprogram/`
- **开发调试指南**: `miniprogram/开发调试指南.md`

---

**最后更新**: 2025-10-05
