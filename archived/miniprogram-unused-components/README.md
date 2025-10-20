# 小程序未使用组件备份

## 📁 备份说明

本文件夹存放从 `miniprogram/components` 中移除的未使用组件。

### 🗂️ 备份结构

```
backup-YYYYMMDD/
├── api-status/           # API 状态显示组件
├── correction-result/    # 批改结果显示组件
├── error-boundary/       # 错误边界组件
└── network-status/       # 网络状态组件
```

## 📅 备份记录

### 2025-10-20

- **原因**：微信开发者工具检测到这些组件未被任何页面使用
- **操作**：从 miniprogram 中移除，减小小程序包体积
- **备份位置**：`backup-20251020/`
- **组件列表**：
  - api-status
  - correction-result
  - error-boundary
  - network-status

## 🔄 恢复方法

如果需要恢复某个组件，执行：

```bash
# 恢复单个组件（以 api-status 为例）
cp -r archived/miniprogram-unused-components/backup-YYYYMMDD/api-status miniprogram/components/

# 恢复所有组件
cp -r archived/miniprogram-unused-components/backup-YYYYMMDD/* miniprogram/components/
```

## ⚠️ 注意事项

1. 这些组件虽然当前未使用，但功能完整，可能在未来版本中需要
2. 删除前已确认没有页面引用这些组件
3. 备份文件夹不会被 Git 忽略，会随代码仓库一起保存

## 📝 组件功能说明

- **api-status**: 用于显示 API 调用状态（加载中、成功、失败等）
- **correction-result**: 用于展示作业批改结果
- **error-boundary**: 错误边界组件，用于捕获和处理组件错误
- **network-status**: 网络状态提示组件
