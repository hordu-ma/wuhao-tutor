# 移动端兼容性修复 - 快速参考

## ⚡ 快速开始

### 1️⃣ 构建（在有 Node.js 的机器上）

```bash
cd /data/workspace/wuhao-tutor/frontend
npm install
npm run build
```

### 2️⃣ 验证构建产物

```bash
/data/workspace/wuhao-tutor/scripts/verify_legacy_build.sh
```

预期输出：
```
✓ Legacy Plugin 配置正确
✓ 构建产物包含现代和兼容两套代码
```

### 3️⃣ 部署到生产

```bash
cd /data/workspace/wuhao-tutor
./scripts/deploy_to_production.sh
```

### 4️⃣ 测试验证

访问兼容性检测页面：
```
https://121.199.173.244/check-compatibility.html
```

预期评分：> 90%

## 📋 配置摘要

### package.json 新增依赖

```json
{
  "devDependencies": {
    "@vitejs/plugin-legacy": "^5.3.0",
    "terser": "^5.27.0"
  }
}
```

### vite.config.ts 关键配置

```typescript
import legacy from '@vitejs/plugin-legacy'

// plugins 数组中添加
legacy({
  targets: ['iOS >= 11', 'Android >= 5', 'Chrome >= 49'],
  polyfills: [
    'es.promise',
    'es.object.entries',
    'es.object.values',
    'es.array.includes',
    'es.string.includes',
  ],
  renderLegacyChunks: true,
  modernPolyfills: false,
})

// build.target 修改为
build: {
  target: 'es2015',
  // ...
}
```

## 🎯 验收标准

### ✅ 技术验收

- [ ] `npm run build` 成功
- [ ] `dist/assets/` 包含 `*-legacy-*.js` 文件
- [ ] `dist/assets/` 包含 `polyfills-legacy-*.js` 文件
- [ ] `dist/index.html` 包含 `nomodule` 脚本标签

### ✅ 功能验收

**桌面端（无回归）**
- [ ] Chrome/Edge/Firefox 最新版正常
- [ ] 作业问答功能正常
- [ ] Console 无错误

**移动端（兼容性修复）**
- [ ] iOS Safari 11+ 正常
- [ ] Android Chrome 49+ 正常
- [ ] 作业问答功能正常
- [ ] Console 无错误

## 🔧 常用命令

### 本地开发

```bash
cd frontend
npm run dev
# 访问 http://localhost:5173
```

### 类型检查

```bash
npm run type-check
```

### 构建并验证

```bash
npm run build && ../scripts/verify_legacy_build.sh
```

### 查看构建日志（检查 Legacy）

```bash
npm run build | grep -i "legacy"
```

预期看到：`Building legacy bundle for production...`

## 📊 浏览器支持矩阵

| 浏览器 | 最低版本 | 说明 |
|--------|---------|------|
| iOS Safari | 11+ | 支持 Promise、Fetch、ES6 Classes |
| Android Chrome | 49+ | 支持 ES6 基础语法、Proxy |
| Android WebView | 5.0+ | 基础 ES5 支持 |
| Chrome | 87+ | 完整 ES2020 支持 |
| Safari | 14+ | 完整 ES2020 支持 |
| Edge | 88+ | 完整 ES2020 支持 |

**覆盖率**: 99.5%+

## 🐛 故障排查

### 问题 1: 构建失败

**症状**: `npm run build` 报错

**解决**:
```bash
# 清理缓存
rm -rf node_modules package-lock.json
npm install

# 检查依赖版本
npm list @vitejs/plugin-legacy terser
```

### 问题 2: 没有生成 legacy 文件

**症状**: `dist/assets/` 没有 `*-legacy-*.js`

**检查**:
1. 确认 `vite.config.ts` 正确导入和配置 `legacy` 插件
2. 确认构建模式为 production：`NODE_ENV=production npm run build`
3. 查看构建日志是否有错误

### 问题 3: 移动端仍然报错

**检查**:
1. 清除浏览器缓存
2. 访问 `/check-compatibility.html` 查看评分
3. 使用 Eruda 查看 Console 错误
4. 确认服务器正确部署了 legacy 文件

### 问题 4: 桌面端性能下降

**检查**:
1. 使用 Chrome DevTools Lighthouse 测试
2. 查看 Network 面板，确认只加载 `type="module"` 脚本
3. 检查文件大小是否异常

## 📞 技术支持

### 日志位置

- **构建日志**: `npm run build` 输出
- **浏览器日志**: DevTools Console
- **服务器日志**: `/var/log/nginx/error.log`

### 关键文件

- **配置**: `frontend/vite.config.ts`
- **依赖**: `frontend/package.json`
- **验证脚本**: `scripts/verify_legacy_build.sh`
- **兼容性检测**: `frontend/public/check-compatibility.html`
- **实施文档**: `docs/mobile-browser-compatibility-implementation.md`

## 🔗 相关资源

- [Vite Legacy Plugin 文档](https://github.com/vitejs/vite/tree/main/packages/plugin-legacy)
- [Browserslist 查询](https://browsersl.ist/)
- [Can I Use](https://caniuse.com/)
- [设计文档](./mobile-browser-compatibility-design.md)

---

**最后更新**: 2025-10-13  
**维护者**: 五好伴学开发团队
