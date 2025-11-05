# 阶段 3 完成：首页智能推荐功能

## 实施方案

✅ **采用方案 A 的方案 1**：

- 使用现有知识图谱推荐算法
- 前端 24 小时缓存
- 显示 3 条推荐
- 点击仅提示，不跳转

---

## 实现内容

### 1. 后端 API（新增）

**文件**: `src/api/v1/endpoints/analytics.py`

**新增接口**: `GET /api/v1/analytics/homepage/recommendations`

**核心逻辑**:

```python
1. 统计用户主要学科（从错题记录）
2. 调用 KnowledgeGraphService.recommend_review_path()
3. 返回3条推荐，包含：
   - id: 推荐ID（基于日期）
   - title: "{知识点名称} 复习"
   - content: 推荐理由
   - icon: 图标（star-o, fire-o, like-o）
   - color: 颜色（#ff9800, #f44336, #2196f3）
   - knowledge_point_id: 知识点ID
   - priority: 优先级分数
```

**推荐算法**（复用现有）:

- **掌握度因子**：优先推荐掌握度低的知识点
- **遗忘曲线因子**：基于最后练习时间计算遗忘风险
- **前置知识权重**：错误率高的补前置知识
- **关联链薄弱因子**：识别知识链薄弱环节

**降级策略**:

- 如果用户无错题数据，返回 3 条默认推荐
- 如果算法失败，返回通用学习建议

---

### 2. 前端 API 客户端（修改）

**文件**: `miniprogram/utils/api.js`

**新增方法**: `analysis.getHomepageRecommendations()`

**缓存策略**:

```javascript
{
  enableCache: true,
  cache: {
    ttl: 24 * 60 * 60 * 1000,  // 24小时
    tags: ['homepage', 'recommendations']
  }
}
```

**更新机制**:

- 首次加载：调用后端 API
- 24 小时内：使用缓存数据
- 24 小时后：自动过期，重新请求
- 用户主动刷新：清除缓存，重新加载

---

### 3. 前端首页逻辑（修改）

**文件**: `miniprogram/pages/index/index.js`

**修改方法**: `loadRecommendations()`

**变更内容**:

- ❌ 删除：Mock 数据生成逻辑（约 120 行）
- ✅ 新增：调用真实 API
- ✅ 新增：响应格式解析（两层结构）
- ✅ 新增：错误降级处理

**响应处理**:

```javascript
// 第一层：微信小程序响应
response.statusCode === 200
response.data

// 第二层：后端API响应
response.data.success === true
response.data.data // 推荐数组
```

**点击行为**:

```javascript
onRecommendationTap(e) {
  // 仅显示提示，不跳转
  wx.showToast({
    title: '知识点推荐',
    icon: 'none'
  });
}
```

---

## 技术特性

### 每日更新机制

**前端缓存方式**（当前实现）:

- ✅ 缓存 Key 包含 API 路径
- ✅ TTL: 24 小时
- ✅ 自动过期
- ⚠️ 不保证 0 点准时更新（取决于首次访问时间）

**优化方向**（后续可选）:

- 后端 Redis 缓存
- Key 格式：`homepage:rec:{user_id}:{date}`
- 每日 0 点自动失效

### 数据来源

推荐内容**完全来自用户错题本**：

1. `MistakeRecord` 表：用户的错题记录
2. `KnowledgeMastery` 表：知识点掌握度追踪
3. `MistakeKnowledgePoint` 表：错题-知识点关联

**知识点提取**（已有功能）:

- AI 反馈中的知识点字段
- 百炼 AI 自动分析
- 规则化知识点库匹配

### 推荐优先级

**算法权重**:

```
priority = (
  (1 - mastery_level) * 0.4 +      # 掌握度低 40%
  prerequisite_weight * 0.3 +      # 前置知识 30%
  forgetting_risk * 0.2 +          # 遗忘风险 20%
  related_chain_weak * 0.1         # 关联链薄弱 10%
)
```

---

## 测试步骤

### 1. 后端测试

```bash
# 启动后端服务
cd /Users/liguoma/my-devs/python/wuhao-tutor
uv run uvicorn src.main:app --reload

# 测试API（需要登录Token）
curl -X GET "http://localhost:8000/api/v1/analytics/homepage/recommendations" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**预期响应**:

```json
{
  "success": true,
  "data": [
    {
      "id": "rec_2025-11-05_0",
      "title": "二次函数 复习",
      "content": "掌握度较低，建议巩固此知识点",
      "icon": "star-o",
      "color": "#ff9800",
      "knowledge_point_id": "...",
      "priority": 0.85
    }
    // ... 最多3条
  ],
  "message": "获取首页推荐成功"
}
```

### 2. 前端测试

**步骤**:

1. 打开微信开发者工具
2. 编译小程序
3. 登录用户账号
4. 查看首页"为您推荐"区域

**预期效果**:

- ✅ 显示 3 条推荐卡片
- ✅ 每条包含图标、标题、内容
- ✅ 点击显示"知识点推荐"提示
- ✅ 控制台无错误
- ✅ 控制台日志显示 API 调用成功

**控制台日志**:

```
📌 [推荐] API响应: { data: {...}, statusCode: 200 }
📌 [推荐] 后端响应: { success: true, data: [...] }
📌 [推荐] 设置推荐: [...]
```

### 3. 缓存测试

**验证 24 小时缓存**:

1. 首次加载：查看 Network 请求
2. 刷新页面：无新请求（使用缓存）
3. 清除缓存：`storage.js:132` 清除
4. 再次刷新：触发新请求

---

## 数据流程图

```
用户首页加载
    ↓
loadUserData()
    ↓
loadRecommendations()
    ↓
api.analysis.getHomepageRecommendations()
    ↓
[缓存检查] 24小时内？
    ├─ 是 → 返回缓存数据
    └─ 否 → 调用后端API
           ↓
    GET /analytics/homepage/recommendations
           ↓
    1. 查询用户主要学科
    2. 调用知识图谱推荐算法
    3. 转换为首页格式
           ↓
    返回3条推荐
           ↓
    前端解析响应
           ↓
    setData({ recommendations })
           ↓
    页面渲染推荐卡片
```

---

## 已知限制

1. **非精确 0 点更新**：缓存基于首次访问时间+24h
2. **单学科推荐**：当前仅推荐主要学科的知识点
3. **无错题时显示默认**：新用户会看到通用建议

---

## 后续优化方向

### 短期（1-2 周）

- [ ] 多学科混合推荐
- [ ] 推荐理由个性化（基于具体错误）
- [ ] 点击跳转到错题本筛选

### 中期（1-2 月）

- [ ] Redis 后端缓存（0 点准时更新）
- [ ] A/B 测试不同推荐算法
- [ ] 推荐点击率统计

### 长期（3-6 月）

- [ ] 协同过滤推荐
- [ ] 深度学习推荐模型
- [ ] 个性化学习路径规划

---

## 文件变更清单

### 后端

- ✅ `src/api/v1/endpoints/analytics.py` +150 行（新增接口）

### 前端

- ✅ `miniprogram/utils/api.js` +15 行（新增 API 方法）
- ✅ `miniprogram/pages/index/index.js` -85 行（删除 Mock）+40 行（真实 API）

### 文档

- ✅ `HOMEPAGE_STAGE3_RECOMMENDATIONS.md` 本文档

---

**实施时间**: 2025-11-05  
**状态**: ✅ 开发完成，待测试  
**下一步**: 用户测试验证
