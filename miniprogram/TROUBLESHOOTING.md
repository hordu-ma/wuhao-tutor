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

## 问题 2: tabBar 图标文件缺失 ✅ 已解决

### 错误信息

```
Error: app.json or theme.json["tabBar"]["list"][0]["iconPath"]: "assets/icons/home.png" not found
Error: app.json or theme.json["tabBar"]["list"][0]["selectedIconPath"]: "assets/icons/home-active.png" not found
...（其他图标文件）
```

### 原因分析

`app.json` 中配置的 tabBar 图标文件路径不存在。微信小程序的 tabBar 必须配置图标。

### 解决方案

**方法 1: 自动生成占位符图标（推荐用于快速开发）**

使用项目提供的 Python 脚本生成占位符图标：

```bash
cd /Users/liguoma/my-devs/python/wuhao-tutor
uv run python miniprogram/generate-icons.py
```

脚本会自动生成 10 个图标文件（5个功能 × 2个状态）：

- home.png / home-active.png - 首页
- homework.png / homework-active.png - 作业
- chat.png / chat-active.png - 问答
- report.png / report-active.png - 报告
- profile.png / profile-active.png - 我的

**方法 2: 手动准备图标**

1. **下载图标**（推荐来源）：
   - 阿里巴巴图标库：https://www.iconfont.cn/
   - Flaticon：https://www.flaticon.com/
   - Icons8：https://icons8.com/

2. **图标规格**：
   - 尺寸：81px × 81px（或 162px × 162px 的 2倍图）
   - 格式：PNG，支持透明背景
   - 颜色：普通状态 #999999，选中状态 #1890ff

3. **保存位置**：`miniprogram/assets/icons/`

**方法 3: 使用微信官方示例图标**

```bash
# 下载微信小程序官方示例
git clone https://github.com/wechat-miniprogram/miniprogram-demo.git
# 复制图标文件到项目
```

### 验证修复

```bash
# 检查图标文件
ls -lh miniprogram/assets/icons/*.png

# 应该看到 10 个 PNG 文件
```

---

## 问题 3: requiredPrivateInfos 配置冲突 ✅ 已解决

### 错误信息

```
Error: app.json: requiredPrivateInfos 'getFuzzyLocation' is mutually exclusive with 'getLocation'.
File: app.json
```

### 原因分析

在 `requiredPrivateInfos` 数组中，同时声明了 `getLocation`（精确定位）和 `getFuzzyLocation`（模糊定位），这两个 API 是**互斥的**，不能同时使用。

### API 说明

| API                | 说明     | 精度              | 隐私保护 | 使用场景         |
| ------------------ | -------- | ----------------- | -------- | ---------------- |
| `getLocation`      | 精确定位 | 高（±10米）       | 低       | 导航、打卡、外卖 |
| `getFuzzyLocation` | 模糊定位 | 低（约5公里范围） | 高       | 天气、推荐、统计 |

### 解决方案

根据应用类型选择合适的定位API：

**教育类应用（推荐使用模糊定位）**：

```json
{
  "requiredPrivateInfos": [
    "getFuzzyLocation", // ✅ 使用模糊定位
    "chooseLocation",
    "chooseAddress",
    "choosePoi"
  ]
}
```

**配送/打卡类应用（需要精确定位）**：

```json
{
  "requiredPrivateInfos": [
    "getLocation", // ✅ 使用精确定位
    "chooseLocation",
    "chooseAddress",
    "choosePoi"
  ]
}
```

### 我们的修复

五好伴学作为教育应用，不需要精确定位，已修改为使用 `getFuzzyLocation`。

---

## 问题 4: 后端 API 连接失败

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
