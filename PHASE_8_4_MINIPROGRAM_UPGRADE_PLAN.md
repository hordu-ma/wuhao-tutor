# Phase 8.4-8.5：知识图谱学科隔离 - 小程序端升级开发计划

> 📍 **当前阶段**: Phase 8.4-8.5（知识图谱优化 - 小程序前端升级）  
> ⏱️ **预计工期**: 1 小时 40 分钟  
> 📅 **创建日期**: 2025-11-14  
> 🔗 **相关文档**: [DEVELOPMENT_CONTEXT.md](./docs/DEVELOPMENT_CONTEXT.md)

---

## 📊 背景与目标

### 当前状态

**已完成部分（Phase 8.1-8.3）**:

- ✅ **8.1** Service 层学科隔离逻辑 - 完成
- ✅ **8.2** API 层学科隔离接口 - 完成
  - 新接口：`GET /api/v1/knowledge-graph/graphs/{subject}`
  - 响应 Schema：`SubjectKnowledgeGraphResponse`
- ✅ **8.3** 删除错题实时同步 - 完成
  - `delete_mistake()` 方法已升级，自动触发快照更新

**待完成部分（本次开发）**:

- ❌ **8.4** 小程序 API 调用升级（预计 1.5h）
- ❌ **8.5** 实时更新机制优化（预计 0.5h）

### 核心问题

当前小程序端存在的问题：

1. ⚠️ 调用的是旧接口 `/knowledge-graph/mastery`（已废弃）
2. ⚠️ 未使用新的学科隔离接口 `/graphs/{subject}`
3. ⚠️ 学科切换时发送中文名称（需转换为英文枚举）
4. ⚠️ 页面 `onShow()` 未实现自动刷新（删除错题后需手动刷新）

### 开发目标

1. **API 升级**：迁移到新的学科隔离接口
2. **数据兼容**：支持新旧两种 API 格式（平滑过渡）
3. **学科转换**：中文学科名 → 英文枚举映射
4. **实时刷新**：删除错题后自动更新知识图谱

---

## 📋 详细任务分解

### 任务 1：添加中英文学科转换工具方法 ⭐⭐

**预计时间**: 10 分钟  
**优先级**: 高（其他任务依赖此方法）

#### 修改文件

- 📁 `miniprogram/subpackages/charts/pages/knowledge-graph/index.js`

#### 实现位置

在 `Page({})` 内部，`onLoad()` 方法之前添加

#### 代码实现

```javascript
/**
 * 中文学科名称转英文枚举
 * @param {string} chineseSubject - 中文学科名（如"数学"）
 * @returns {string} 英文学科枚举（如"math"）
 */
convertSubjectToEnglish(chineseSubject) {
  const mapping = {
    '数学': 'math',
    '语文': 'chinese',
    '英语': 'english',
    '物理': 'physics',
    '化学': 'chemistry',
    '生物': 'biology',
    '历史': 'history',
    '地理': 'geography',
    '政治': 'politics',
  };
  return mapping[chineseSubject] || 'math'; // 默认返回数学
},
```

#### 验收标准

- [ ] 支持 9 个学科映射
- [ ] 有默认值（math）防止未知学科报错
- [ ] 注释清晰（JSDoc 格式）

---

### 任务 2：添加新 API 方法到 mistakes.js ⭐⭐⭐

**预计时间**: 15 分钟  
**优先级**: 高

#### 修改文件

- 📁 `miniprogram/api/mistakes.js`

#### 实现位置

在文件末尾，`module.exports` 或最后一个方法之后添加

#### 代码实现

```javascript
/**
 * 获取学科知识图谱（新版接口，支持学科隔离）
 * @param {Object} params - 参数对象
 * @param {string} params.subject - 学科英文名（math/chinese/english/physics/chemistry/biology/history/geography/politics）
 * @param {Object} config - 请求配置（可选）
 * @returns {Promise} API响应
 *
 * @example
 * mistakesApi.getSubjectKnowledgeGraph({ subject: 'math' })
 */
getSubjectKnowledgeGraph(params, config = {}) {
  return request.get(
    `knowledge-graph/graphs/${params.subject}`,
    {},
    { showLoading: false, ...config }
  );
},
```

#### 新旧接口对比

| 维度     | 旧接口                             | 新接口                                 |
| -------- | ---------------------------------- | -------------------------------------- |
| 路径     | `/knowledge-graph/mastery`         | `/knowledge-graph/graphs/{subject}`    |
| 参数     | `{ subject: '数学' }` (Query 参数) | `{ subject: 'math' }` (Path 参数)      |
| 响应格式 | `{ items: [...] }`                 | `{ nodes: [...], weak_chains: [...] }` |
| 学科支持 | 单学科或全部                       | 严格单学科隔离                         |

#### 验收标准

- [ ] 方法签名正确（参数、返回值）
- [ ] JSDoc 注释完整（包含示例）
- [ ] 导出模块中包含此方法
- [ ] showLoading 默认为 false（避免频繁弹窗）

---

### 任务 3：修改 loadSnapshot() 调用新接口 ⭐⭐⭐

**预计时间**: 20 分钟  
**优先级**: 高

#### 修改文件

- 📁 `miniprogram/subpackages/charts/pages/knowledge-graph/index.js`

#### 实现位置

修改 `loadSnapshot()` 方法（约 Lines 93-150）

#### 修改策略

1. 调用 `convertSubjectToEnglish()` 转换学科名
2. 使用新的 `getSubjectKnowledgeGraph()` API 方法
3. 保留旧代码注释（便于回滚）

#### 代码实现

```javascript
async loadSnapshot() {
  try {
    console.log('开始加载知识图谱，当前学科:', this.data.selectedSubject);

    // 🆕 转换中文学科名为英文枚举
    const subjectEn = this.convertSubjectToEnglish(this.data.selectedSubject);
    console.log('学科转换:', this.data.selectedSubject, '→', subjectEn);

    // 🆕 调用新版学科隔离API
    const response = await mistakesApi.getSubjectKnowledgeGraph({
      subject: subjectEn,
    });

    // 旧代码（注释保留，向后兼容）
    // const response = await mistakesApi.getKnowledgeGraphSnapshot({
    //   subject: this.data.selectedSubject,
    // });

    console.log('知识图谱数据加载成功:', response);

    if (response && response.data) {
      const formattedData = this.formatSnapshotData(response.data);

      if (formattedData) {
        this.setData({
          snapshot: formattedData,
          isEmpty: !formattedData.knowledge_points || formattedData.knowledge_points.length === 0,
        });

        // 如果有数据，渲染图表
        if (!this.data.isEmpty) {
          if (this.data.viewMode === 'graph') {
            this.renderChart();
          }
        }
      } else {
        this.setData({
          isEmpty: true,
        });
      }
    } else {
      this.setData({
        isEmpty: true,
      });
    }
  } catch (error) {
    console.error('加载知识图谱失败:', error);
    wx.showToast({
      title: '加载失败',
      icon: 'none',
    });
    this.setData({
      isEmpty: true,
    });
  }
},
```

#### 验收标准

- [ ] 调用新 API 方法
- [ ] 使用英文学科名（经过转换）
- [ ] 保留旧代码注释（向后兼容）
- [ ] 错误处理保持不变
- [ ] Console 日志清晰（包含转换过程）

---

### 任务 4：数据格式适配（兼容新旧格式）⭐⭐⭐

**预计时间**: 30 分钟  
**优先级**: 高（核心兼容性保障）

#### 修改文件

- 📁 `miniprogram/subpackages/charts/pages/knowledge-graph/index.js`

#### 实现位置

修改 `formatSnapshotData()` 方法（约 Lines 155-197）

#### 新旧格式对比

**旧格式（/mastery 接口）**:

```json
{
  "items": [
    {
      "knowledge_point": "二次函数",
      "mastery_level": 0.65,
      "mistake_count": 3,
      "correct_count": 5,
      "total_attempts": 8
    }
  ],
  "total_count": 10,
  "average_mastery": 0.72,
  "subject": "数学"
}
```

**新格式（/graphs/{subject} 接口）**:

```json
{
  "subject": "math",
  "nodes": [
    {
      "id": "uuid-xxx",
      "name": "二次函数",
      "mastery": 0.65,
      "mistake_count": 3,
      "correct_count": 5,
      "total_attempts": 8
    }
  ],
  "weak_chains": [
    {
      "knowledge_point": "二次函数",
      "mastery_level": 0.3,
      "related_points": ["一元二次方程"]
    }
  ],
  "mastery_distribution": {
    "weak": 2,
    "learning": 5,
    "mastered": 3
  },
  "total_points": 10,
  "avg_mastery": 0.72,
  "recommendations": [
    {
      "knowledge_point": "二次函数",
      "reason": "掌握度低于50%",
      "priority": "high"
    }
  ]
}
```

#### 字段映射表

| 含义       | 旧格式字段        | 新格式字段             |
| ---------- | ----------------- | ---------------------- |
| 节点列表   | `items`           | `nodes`                |
| 知识点名称 | `knowledge_point` | `name`                 |
| 掌握度     | `mastery_level`   | `mastery`              |
| 总数       | `total_count`     | `total_points`         |
| 平均掌握度 | `average_mastery` | `avg_mastery`          |
| 薄弱知识链 | ❌ 无             | `weak_chains`          |
| 掌握度分布 | ❌ 无             | `mastery_distribution` |
| 复习推荐   | ❌ 无             | `recommendations`      |

#### 代码实现

```javascript
/**
 * 格式化快照数据（兼容新旧两种API格式）
 * @param {Object} snapshot - API响应数据
 * @returns {Object|null} 格式化后的数据，失败返回null
 */
formatSnapshotData(snapshot) {
  if (!snapshot) {
    console.warn('快照数据为空');
    return null;
  }

  // 🆕 新版 /graphs/{subject} API 格式（优先）
  if (snapshot.nodes && Array.isArray(snapshot.nodes)) {
    console.log('✅ 检测到新版API格式，nodes数量:', snapshot.nodes.length);

    const knowledge_points = snapshot.nodes.map(node => ({
      name: node.name || '',
      mastery_level: node.mastery || 0,        // 注意字段名变化: mastery
      mistake_count: node.mistake_count || 0,
      correct_count: node.correct_count || 0,
      total_attempts: node.total_attempts || 0,
      id: node.id || '',                       // 🆕 节点ID
    }));

    return {
      subject: snapshot.subject || '',
      knowledge_points,
      total_mistakes: snapshot.total_points || 0,
      average_mastery: snapshot.avg_mastery || 0,
      // 🆕 新增字段（增强功能）
      weak_chains: snapshot.weak_chains || [],
      mastery_distribution: snapshot.mastery_distribution || {},
      recommendations: snapshot.recommendations || [],
    };
  }

  // 向后兼容：旧版 /mastery API 格式
  if (snapshot.items && Array.isArray(snapshot.items)) {
    console.log('⚠️ 检测到旧版API格式，items数量:', snapshot.items.length);

    const knowledge_points = snapshot.items.map(item => ({
      name: item.knowledge_point || '',
      mastery_level: item.mastery_level || 0,  // 旧格式字段名
      mistake_count: item.mistake_count || 0,
      correct_count: item.correct_count || 0,
      total_attempts: item.total_attempts || 0,
    }));

    return {
      subject: snapshot.subject || '',
      knowledge_points,
      total_mistakes: snapshot.total_count || 0,
      average_mastery: snapshot.average_mastery || 0,
      // 旧格式无这些字段
      weak_chains: [],
      mastery_distribution: {},
      recommendations: [],
    };
  }

  console.error('❌ 未知的快照数据格式，无法解析:', snapshot);
  return null;
}
```

#### 验收标准

- [ ] 优先适配新格式（nodes）
- [ ] 完全兼容旧格式（items）
- [ ] 字段映射正确（mastery vs mastery_level）
- [ ] 包含新增字段（weak_chains、mastery_distribution、recommendations）
- [ ] 有详细 Console 日志（区分新旧格式）
- [ ] 错误处理完善（未知格式返回 null）

---

### 任务 5：添加页面生命周期刷新逻辑 ⭐⭐

**预计时间**: 10 分钟  
**优先级**: 中

#### 修改文件

- 📁 `miniprogram/subpackages/charts/pages/knowledge-graph/index.js`

#### 实现位置

修改 `onShow()` 方法（约 Lines 73-75）

#### 使用场景

用户从知识图谱页面跳转到错题列表 → 删除某个错题 → 返回知识图谱页面 → **自动刷新显示最新数据**

#### 代码实现

```javascript
onShow() {
  console.log('📍 知识图谱页面显示');

  // 🆕 如果不是首次加载（已有数据），则刷新
  // 使用场景: 从错题列表删除错题后返回此页面
  if (this.data.snapshot) {
    console.log('🔄 检测到已有数据，触发增量刷新');
    this.loadData(); // 重新加载数据
  } else {
    console.log('🆕 首次加载，跳过刷新（将在onLoad中加载）');
  }
},
```

#### 与 onPullDownRefresh 的区别

| 方法                  | 触发时机           | 使用场景           | 实现状态    |
| --------------------- | ------------------ | ------------------ | ----------- |
| `onShow()`            | 页面显示时自动触发 | 返回页面时自动刷新 | 🆕 本次新增 |
| `onPullDownRefresh()` | 用户手动下拉触发   | 手动刷新           | ✅ 已实现   |

#### 验收标准

- [ ] 页面显示时检查是否有已加载数据
- [ ] 有数据时触发刷新（调用 `loadData()`）
- [ ] 首次加载时跳过（避免重复加载）
- [ ] Console 日志清晰（区分首次/刷新）

---

### 任务 6：联调测试（小程序端验证）⭐⭐⭐

**预计时间**: 15 分钟  
**优先级**: 高（验证所有改动）

#### 测试环境准备

**1. 启动后端开发服务器**

```bash
cd /Users/liguoma/my-devs/python/wuhao-tutor

# 方式1: 使用Makefile
make dev

# 方式2: 直接运行
uv run python src/main.py
```

**2. 配置小程序开发者工具**

- 打开项目路径：`/Users/liguoma/my-devs/python/wuhao-tutor/miniprogram`
- 确认后端地址：`http://localhost:8000` 或 `http://127.0.0.1:8000`
- 检查网络配置：开发者工具 → 详情 → 本地设置 → 不校验合法域名

#### 测试场景清单

##### 场景 1：学科切换测试 ⭐⭐⭐

**步骤**:

1. 进入"知识图谱"页面
2. 切换学科：数学 → 语文 → 英语 → 物理
3. 观察数据是否正确加载

**验证点**:

- [ ] 每次切换后数据重新加载
- [ ] Console 显示学科转换日志：`学科转换: 数学 → math`
- [ ] 图谱节点数量变化（不同学科知识点数量不同）
- [ ] 无报错信息

**预期日志**:

```
开始加载知识图谱，当前学科: 数学
学科转换: 数学 → math
✅ 检测到新版API格式，nodes数量: 5
知识图谱数据加载成功: {...}
```

---

##### 场景 2：新版 API 格式验证 ⭐⭐⭐

**步骤**:

1. 打开"知识图谱"页面
2. 打开开发者工具 Console
3. 查看数据加载日志

**验证点**:

- [ ] Console 显示：`✅ 检测到新版API格式，nodes数量: X`
- [ ] 图谱渲染正确（节点、连线）
- [ ] 统计数据显示正确（总知识点数、平均掌握度）
- [ ] 新增字段生效（薄弱知识链、掌握度分布等）

**预期响应数据**:

```json
{
  "subject": "math",
  "nodes": [...],
  "weak_chains": [...],
  "mastery_distribution": {"weak": 2, "learning": 3, "mastered": 1},
  "total_points": 6,
  "avg_mastery": 0.68,
  "recommendations": [...]
}
```

---

##### 场景 3：删除错题后自动刷新 ⭐⭐⭐

**步骤**:

1. 进入"知识图谱"页面，记录当前知识点数量（如 6 个）
2. 点击某个知识点，跳转到关联的错题列表
3. 删除其中一个错题
4. 返回知识图谱页面

**验证点**:

- [ ] 返回时自动触发刷新（无需手动下拉）
- [ ] Console 显示：`🔄 检测到已有数据，触发增量刷新`
- [ ] 知识点数据已更新（掌握度提升或知识点数量变化）
- [ ] 图谱重新渲染

**预期日志**:

```
📍 知识图谱页面显示
🔄 检测到已有数据，触发增量刷新
开始加载知识图谱，当前学科: 数学
学科转换: 数学 → math
✅ 检测到新版API格式，nodes数量: 5  ← 数量从6变为5
```

---

##### 场景 4：下拉刷新测试 ⭐⭐

**步骤**:

1. 进入"知识图谱"页面
2. 手动下拉页面

**验证点**:

- [ ] 出现下拉刷新动画
- [ ] 数据重新加载
- [ ] 刷新完成后动画消失
- [ ] 数据显示正确

**预期行为**:

- 下拉 → 显示加载动画 → 调用 `loadData()` → 动画消失

---

##### 场景 5：错误处理测试 ⭐

**步骤**:

1. 断开后端服务器（或修改 API 地址为错误地址）
2. 刷新知识图谱页面

**验证点**:

- [ ] 显示友好错误提示："加载失败"
- [ ] Console 显示错误日志：`加载知识图谱失败: ...`
- [ ] 页面状态切换为空状态（`isEmpty: true`）
- [ ] 不崩溃，可以继续操作

---

##### 场景 6：多机型兼容性测试 ⭐

**步骤**:

1. 在开发者工具中切换不同机型（iPhone、Android）
2. 测试以上所有场景

**验证点**:

- [ ] iOS 模拟器正常
- [ ] Android 模拟器正常
- [ ] 不同屏幕尺寸下 UI 正常

---

#### 回归测试清单

**已有功能不受影响**:

- [ ] 图谱/列表视图切换正常
- [ ] ECharts 力导向图渲染正常
- [ ] 节点大小/颜色按掌握度变化
- [ ] 点击节点跳转到错题列表
- [ ] 页面标题显示正确
- [ ] 无内存泄漏（多次切换后性能正常）

---

#### 性能指标

| 指标         | 目标值 | 验证方式                    |
| ------------ | ------ | --------------------------- |
| API 响应时间 | <500ms | 开发者工具 Network 面板     |
| 页面加载时间 | <1s    | 从进入到渲染完成            |
| 学科切换响应 | <800ms | 点击切换到数据显示          |
| 内存占用     | <50MB  | 开发者工具 Performance 面板 |

---

#### 问题记录模板

如发现问题，请记录：

```markdown
**问题编号**: P8.4-001
**严重程度**: 高/中/低
**测试场景**: 场景 X
**问题描述**:
**复现步骤**:

1.
2.
3. **预期结果**:
   **实际结果**:
   **错误日志**:
   **解决方案**:
   **验证状态**: 待修复/已修复/已验证
```

---

## 📦 交付清单

完成后应有以下变更：

```
miniprogram/
├── api/
│   └── mistakes.js                              [修改] +20行
│       └── getSubjectKnowledgeGraph()           [新增] 新API方法
│
└── subpackages/charts/pages/knowledge-graph/
    └── index.js                                 [修改] +95行
        ├── convertSubjectToEnglish()            [新增] 学科转换（15行）
        ├── loadSnapshot()                       [修改] 调用新API（+10行）
        ├── formatSnapshotData()                 [修改] 兼容新旧格式（+60行）
        └── onShow()                             [修改] 自动刷新（+10行）
```

**统计**:

- 修改文件数：2 个
- 新增代码：约 115 行
- 修改代码：约 20 行
- 删除代码：0 行（保持向后兼容）

---

## ⏱️ 时间安排

### 总体时间表

| 任务                      | 预计时间           | 累计时间 | 优先级 |
| ------------------------- | ------------------ | -------- | ------ |
| 任务 1: 学科转换工具      | 10 分钟            | 10 分钟  | ⭐⭐   |
| 任务 2: 添加 API 方法     | 15 分钟            | 25 分钟  | ⭐⭐⭐ |
| 任务 3: 修改 loadSnapshot | 20 分钟            | 45 分钟  | ⭐⭐⭐ |
| 任务 4: 数据格式适配      | 30 分钟            | 75 分钟  | ⭐⭐⭐ |
| 任务 5: 页面刷新逻辑      | 10 分钟            | 85 分钟  | ⭐⭐   |
| 任务 6: 联调测试          | 15 分钟            | 100 分钟 | ⭐⭐⭐ |
| **总计**                  | **1 小时 40 分钟** |          |        |

### 推荐执行顺序

```
第1步（10分钟）
└─ 任务1: convertSubjectToEnglish()        [基础工具]
    ↓
第2步（15分钟）
└─ 任务2: getSubjectKnowledgeGraph()       [API封装]
    ↓
第3步（20分钟）
└─ 任务3: 修改loadSnapshot()               [调用升级]
    ↓
第4步（30分钟）
└─ 任务4: formatSnapshotData()             [数据适配]
    ↓
第5步（10分钟）
└─ 任务5: onShow()自动刷新                 [体验优化]
    ↓
第6步（15分钟）
└─ 任务6: 联调测试                          [全面验证]
```

**执行策略**:

- **顺序执行**：前 5 个任务有依赖关系，必须按顺序完成
- **持续集成**：每完成一个任务立即测试，避免问题累积
- **增量提交**：每完成 1-2 个任务提交一次代码

---

## 🎯 验收标准

### 功能验收

- [ ] **学科切换**：9 个学科都能正常切换并加载数据
- [ ] **新 API 调用**：使用 `/graphs/{subject}` 接口
- [ ] **数据兼容**：同时支持新旧两种 API 格式
- [ ] **学科转换**：中文 → 英文映射正确
- [ ] **自动刷新**：删除错题后返回页面自动更新
- [ ] **下拉刷新**：手动刷新功能正常
- [ ] **错误处理**：网络异常时有友好提示
- [ ] **性能达标**：API 响应 <500ms，页面加载 <1s

### 代码质量

- [ ] **注释完整**：所有新增方法有 JSDoc 注释
- [ ] **日志清晰**：关键步骤有 Console 日志输出
- [ ] **向后兼容**：保留旧代码注释，便于回滚
- [ ] **无硬编码**：学科映射使用配置对象
- [ ] **错误处理**：所有异步操作有 try-catch

### 测试覆盖

- [ ] 6 个测试场景全部通过
- [ ] 回归测试无问题
- [ ] 多机型兼容性验证
- [ ] 性能指标达标

---

## 🚨 风险与注意事项

### 潜在风险

1. **API 响应格式变化**

   - **风险**：后端接口响应字段可能与文档不一致
   - **缓解**：formatSnapshotData() 中加强容错，所有字段使用 `||` 提供默认值

2. **学科枚举不匹配**

   - **风险**：前端映射的学科名与后端枚举不一致
   - **缓解**：参考后端 `SubjectType` 定义，保持一致

3. **旧版 API 依赖**

   - **风险**：其他页面可能还在使用旧接口
   - **缓解**：本次只修改知识图谱页面，不影响其他模块

4. **缓存问题**
   - **风险**：小程序缓存旧数据导致测试混乱
   - **缓解**：测试前清除缓存（开发者工具 → 清缓存 → 全部清除）

### 注意事项

1. **不要删除旧代码**：保留注释，便于回滚
2. **不要修改其他方法**：只改动指定的 5 个方法
3. **不要修改样式**：本次不涉及 UI 调整
4. **先测试后提交**：每个任务完成后立即测试
5. **保持日志输出**：便于问题排查

---

## 📚 相关文档

### 项目文档

- [DEVELOPMENT_CONTEXT.md](./docs/DEVELOPMENT_CONTEXT.md) - 完整开发上下文
- [MISTAKE_EXTRACTION_OPTIMIZATION.md](./docs/MISTAKE_EXTRACTION_OPTIMIZATION.md) - 错题本优化方案

### API 文档

- Swagger UI: http://localhost:8000/docs
- 新接口文档: `/api/v1/knowledge-graph/graphs/{subject}`
- Schema 定义: `src/schemas/knowledge_graph.py`

### 后端代码

- API 层: `src/api/v1/endpoints/knowledge_graph.py` (Lines 32-106)
- Service 层: `src/services/knowledge_graph_service.py` (Lines 285-501)
- Schema: `src/schemas/knowledge_graph.py` (Lines 377-426)

### 前端代码

- 知识图谱页面: `miniprogram/subpackages/charts/pages/knowledge-graph/`
- API 封装: `miniprogram/api/mistakes.js`
- 工具库: `miniprogram/utils/request.js`

---

## 🔄 后续计划

### Phase 8.6-8.7（可选优化）

完成 8.4-8.5 后，可继续进行：

- **8.6** 性能优化（1h）

  - 数据库索引优化
  - 前端缓存机制
  - 图表渲染优化

- **8.7** 生产环境验证（1h）
  - PostgreSQL 迁移测试
  - 生产数据备份
  - 灰度发布

### Phase 9：错题本批改功能测试（后续）

根据原计划，Phase 8 完成后应进入：

- 错题本批改功能的单元测试
- 集成测试
- Prompt 测试

---

## 📝 变更记录

| 版本 | 日期       | 变更内容                         | 作者         |
| ---- | ---------- | -------------------------------- | ------------ |
| v1.0 | 2025-11-14 | 初始版本，Phase 8.4-8.5 开发计划 | AI Assistant |

---

**准备就绪，等待执行确认。** 🚀
