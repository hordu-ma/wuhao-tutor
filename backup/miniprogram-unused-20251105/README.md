# 无依赖代码文件备份

**备份时间**: 2025-11-05  
**总文件数**: 83  
**成功移动**: 83

## 文件分类统计

| 类型    | 数量 | 说明                |
| ------- | ---- | ------------------- |
| `.js`   | 32   | JavaScript 代码文件 |
| `.json` | 14   | JSON 配置文件       |
| `.wxml` | 13   | 微信小程序模板文件  |
| `.wxss` | 19   | 微信小程序样式文件  |
| `.wxs`  | 5    | 微信脚本文件        |

## 主要内容

### 1. Towxml 相关

- `towxml.config.js` - Towxml 配置文件（已禁用）

### 2. 未使用的 vant 组件

- `collapse` / `collapse-item` - 折叠面板
- `count-down` - 倒计时
- `notify` - 消息通知
- `share-sheet` - 分享面板
- `tabbar` / `tabbar-item` - 标签栏
- `index-bar` / `index-anchor` - 索引栏
- `config-provider` - 全局配置

### 3. Echarts 图表库

- `echarts/index.js` - **3.3MB** 主文件
- `echarts-for-weixin/` - 微信小程序适配
- `zrender/index.js` - **667KB** 渲染引擎

### 4. 其他 npm 包

- `mobx-miniprogram` / `mobx-miniprogram-bindings` - 状态管理
- `fs-extra` / `graceful-fs` - 文件系统（Node.js）
- `jsonfile` / `universalify` - 工具库
- `tslib` / `regenerator-runtime` - 运行时支持

### 5. 自定义工具

- `utils/formula-debugger.js` - 公式调试工具

### 6. 组件

- `components/ec-canvas/` - Echarts 画布组件（未使用）

## ⚠️ 重要说明

1. **这些文件在当前版本中没有被引用**，根据微信开发者工具的依赖分析结果移除
2. **节省空间**：总大小约 **4.3MB**，主要是 echarts.js (3.3MB) 和 zrender.js (667KB)
3. **已备份**：所有文件已安全保存在此目录，需要时可以恢复
4. **不影响功能**：移除这些文件不会影响小程序的正常运行

## 恢复方法

如果需要恢复某个文件：

```bash
# 从备份目录复制回 miniprogram
cp backup/miniprogram-unused-20251105/<file_path> miniprogram/<file_path>
```

## 删除建议

**建议保留此备份目录**，观察一段时间后（如 1-2 周）确认没有问题再删除。

---

**生成工具**: analyse-data.json (微信开发者工具依赖分析)  
**备份目录**: `/Users/liguoma/my-devs/python/wuhao-tutor/backup/miniprogram-unused-20251105`
