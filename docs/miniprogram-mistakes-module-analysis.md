# 小程序错题本模块 - 代码实现详解

> **文档版本**: v1.0  
> **生成时间**: 2025-10-20  
> **涉及模块**: 错题手册 (Mistakes Module)

---

## 📋 模块架构概览

### 文件结构

```
miniprogram/
├── api/mistakes.js                    # 错题 API 封装 (320行)
├── utils/ebbinghaus.js                # 艾宾浩斯算法 (256行)
├── pages/mistakes/
│   ├── list/                          # 错题列表 (532行)
│   ├── detail/                        # 错题详情
│   ├── add/                           # 添加错题 (143行)
│   └── today-review/                  # 今日复习 (63行)
└── components/mistake-card/           # 错题卡片组件 (240行)
```

---

## 🧠 核心算法：艾宾浩斯遗忘曲线

### 复习间隔时间表

```javascript
const REVIEW_INTERVALS = [
  1, // 第1次: 1天后
  2, // 第2次: 2天后
  4, // 第3次: 4天后
  7, // 第4次: 7天后
  15, // 第5次: 15天后
  30, // 第6次: 30天后
  60, // 第7次: 60天后
  90, // 第8次: 90天后
]
```

### 掌握状态定义

```javascript
const MASTERY_STATUS = {
  NOT_MASTERED: 'not_mastered', // 未掌握
  REVIEWING: 'reviewing', // 复习中
  MASTERED: 'mastered', // 已掌握 (连续3次答对 + 正确率≥80%)
}
```

### 核心算法逻辑

```javascript
// 1. 计算下次复习时间
calculateNextReviewDate(reviewCount, lastReviewDate, isCorrect)
  ├─ 答错 → reviewCount 重置为 0，从第1天间隔重新开始
  ├─ 答对 → 按 REVIEW_INTERVALS 数组取间隔天数
  └─ 返回计算后的日期

// 2. 判断掌握状态
getMasteryStatus(reviewCount, correctCount, correctRate)
  ├─ reviewCount === 0 → NOT_MASTERED
  ├─ correctCount ≥ 3 && correctRate ≥ 80 → MASTERED
  └─ 其他 → REVIEWING

// 3. 更新复习记录
updateReviewRecord(mistake, isCorrect)
  ├─ 更新计数器 (reviewCount, correctCount, correctAttempts)
  ├─ 计算正确率
  ├─ 调用 calculateNextReviewDate()
  ├─ 调用 getMasteryStatus()
  └─ 返回更新后的错题对象
```

---

## 📡 API 层设计

### 主要接口

| 接口                   | 方法   | 端点                            | 功能                           |
| ---------------------- | ------ | ------------------------------- | ------------------------------ |
| `getMistakeList`       | GET    | `/mistakes`                     | 获取错题列表（支持分页、筛选） |
| `getMistakeDetail`     | GET    | `/mistakes/:id`                 | 获取错题详情                   |
| `createMistake`        | POST   | `/mistakes`                     | 创建错题                       |
| `updateMistake`        | PUT    | `/mistakes/:id`                 | 更新错题                       |
| `deleteMistake`        | DELETE | `/mistakes/:id`                 | 删除错题                       |
| `getTodayReview`       | GET    | `/mistakes/today-review`        | 获取今日复习任务               |
| `completeReview`       | POST   | `/mistakes/:id/complete-review` | 提交复习结果                   |
| `getMistakeStatistics` | GET    | `/mistakes/statistics`          | 获取统计数据                   |

### 筛选参数

```javascript
getMistakeList({
  page: 1,
  page_size: 20,
  mastery_status: 'not_mastered' | 'reviewing' | 'mastered',
  subject: '数学' | '英语' | ...,
  difficulty_level: 1 | 2 | 3,
  keyword: '搜索关键词'
})
```

---

## 📄 页面功能详解

### 1. 错题列表页 (`list/index.js`)

**核心功能**:

- ✅ Tab 切换（全部/未掌握/复习中/已掌握）
- ✅ 多维度筛选（科目、难度）
- ✅ 关键词搜索
- ✅ 下拉刷新 + 上拉加载更多
- ✅ 卡片点击跳转详情

**数据加载流程**:

```javascript
loadMistakesList(reset)
  ├─ reset=true → 重置页码和列表
  ├─ 构建请求参数（包含筛选条件）
  ├─ 调用 mistakesApi.getMistakeList()
  ├─ 兼容多种响应格式
  └─ 更新 mistakesList、total、hasMore
```

---

### 2. 错题详情页 (`detail/index.js`)

**功能**:

- ✅ 查看模式：显示题目、答案、解析
- ✅ 复习模式：提交复习结果（答对/答错）
- ✅ 显示复习历史和下次复习时间
- ✅ 删除错题（带确认弹窗）

---

### 3. 添加错题页 (`add/index.js`)

**表单字段**:

```javascript
formData: {
  subject: '',              // 必填
  difficulty_level: 2,      // 默认中等
  question_content: '',     // 必填
  student_answer: '',       // 可选
  correct_answer: '',       // 必填
  explanation: ''           // 可选
}
```

**表单验证**:

- ✅ 科目、题目内容、正确答案为必填项
- ✅ 提交成功后返回列表页

---

### 4. 今日复习页 (`today-review/index.js`)

**功能**:

- ✅ 显示今日需要复习的错题列表
- ✅ 点击卡片进入复习模式
- ✅ 从详情页返回后自动刷新

---

## 🧩 组件设计

### Mistake Card 组件

**属性**:

```javascript
properties: {
  mistake: Object,           // 错题数据
  mode: String,              // 'list' | 'review' | 'detail'
  showActions: Boolean       // 是否显示操作按钮
}
```

**核心方法**:

- `getDifficultyText(level)` - 难度文本映射
- `getMasteryStatusText(status)` - 掌握状态文本
- `getNextReviewText(date)` - 下次复习时间显示
- `formatTime(time)` - 相对时间格式化（今天、昨天、X 天前）

**触发事件**:

- `tap` - 卡片点击
- `review` - 开始复习
- `delete` - 删除错题
- `edit` - 编辑错题

---

## 🔄 数据流

```
用户操作
  ↓
页面/组件
  ↓
API Layer (mistakes.js)
  ↓
网络层 (request.js)
  ↓
后端 API (/api/v1/mistakes)
  ↓
响应数据
  ↓
艾宾浩斯算法处理 (可选)
  ↓
setData() 更新视图
```

---

## ⚠️ 现存问题与优化建议

### 问题清单

1. **算法前后端分离不彻底**

   - 前端 `ebbinghaus.js` 与后端算法重复
   - 建议：前端仅做展示，复习逻辑完全由后端计算

2. **缺少离线缓存**

   - 网络故障时无法查看已加载的错题
   - 建议：使用 `wx.setStorageSync()` 缓存列表数据

3. **复习提醒功能缺失**

   - 无小程序订阅消息提醒今日复习任务
   - 建议：集成微信订阅消息 API

4. **批量导入未实现**

   - API 定义了 `batchImportMistakes` 但前端无入口
   - 建议：添加"扫描识别错题"功能（OCR）

5. **统计图表缺失**
   - `getMistakeStatistics` API 未在页面中使用
   - 建议：添加学习报告页，使用 ECharts 可视化

---

## 🚀 优化建议

### 性能优化

1. **虚拟列表**

   - 当错题数量 >100 时，使用 `recycle-view` 减少渲染

2. **图片懒加载**

   - 错题卡片中的题目图片使用 `lazy-load`

3. **请求防抖**
   - 搜索输入使用 `debounce` 减少 API 调用

### 功能增强

1. **AI 生成解析**

   - 利用百炼智能体自动生成错题解析

2. **错题分享**

   - 生成错题卡片图片，分享至微信好友

3. **学习报告**
   - 每周/每月复习报告推送

---

## 📊 代码统计

| 模块         | 代码行数  | 复杂度 |
| ------------ | --------- | ------ |
| API 层       | 320       | 中     |
| 算法核心     | 256       | 高     |
| 列表页       | 532       | 高     |
| 详情页       | ~200      | 中     |
| 添加页       | 143       | 低     |
| 今日复习页   | 63        | 低     |
| 错题卡片组件 | 240       | 中     |
| **总计**     | **~1754** | -      |

---

**文档作者**: AI Assistant  
**最后更新**: 2025-10-20  
**项目**: 五好伴学 - 微信小程序
