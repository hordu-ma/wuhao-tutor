# WebSocket 流式接口错题自动识别修复总结

## 问题诊断

### 根本原因

1. **WebSocket 接口未触发错题识别**

   - 小程序使用 `/api/v1/learning/ws/ask` WebSocket 接口
   - 该接口调用 `ask_question_stream` 方法
   - 4 策略智能错题识别系统只在 `ask_question` 方法中实现
   - `ask_question_stream` 方法完全没有自动错题识别逻辑

2. **错题状态字段值错误**
   - `add_question_to_mistakes` 方法中 `mastery_status` 设置为 `"learning"`
   - 正确的枚举值应为: `not_mastered`, `reviewing`, `mastered`
   - 导致错题虽然创建成功，但无法被小程序端筛选查询到

## 修复方案

### 修复 1: WebSocket 流式接口添加错题识别（commit: bcce6cf）

```python
# src/services/learning_service.py - ask_question_stream 方法
# 在步骤9（更新学习分析）之后，步骤10（发送完成事件）之前添加：

# 🎯 9.5 智能错题自动创建（不阻塞流式响应）
mistake_created = False
mistake_info = None
try:
    mistake_result = await self._auto_create_mistake_if_needed(
        user_id, question, answer, request
    )
    if mistake_result:
        mistake_created = True
        mistake_info = mistake_result
        logger.info(
            f"✅ [流式] 错题自动创建成功: user_id={user_id}, "
            f"mistake_id={mistake_info.get('id')}, "
            f"category={mistake_info.get('category')}, "
            f"confidence={mistake_info.get('confidence')}"
        )
except Exception as mistake_err:
    logger.warning(f"[流式] 错题创建失败，但不影响问答: {str(mistake_err)}")

# 10. 发送完成事件
yield {
    "type": "done",
    "question_id": question_id,
    "answer_id": answer_id,
    "session_id": session_id,
    "usage": chunk.get("usage", {}),
    "full_content": full_answer_content,
    "mistake_created": mistake_created,  # 🎯 新增
    "mistake_info": mistake_info,  # 🎯 新增
}
```

**改动范围**：

- 文件：`src/services/learning_service.py`
- +23 行代码
- 复用现有的 `_auto_create_mistake_if_needed` 方法（4 策略系统）

### 修复 2: 错误的 mastery_status 字段值（commit: 1d77fe6）

```python
# src/services/learning_service.py - add_question_to_mistakes 方法
# 第 1347 行

# 修改前：
"mastery_status": "learning",  # ❌ 错误值

# 修改后：
"mastery_status": "not_mastered",  # ✅ 正确的枚举值
```

**数据库修复**：

```sql
UPDATE mistake_records
SET mastery_status = 'not_mastered'
WHERE mastery_status = 'learning' AND source = 'learning';
-- 已修复 2 条记录
```

## 验证结果

### 1. 日志验证

```bash
ssh root@121.199.173.244 'journalctl -u wuhao-tutor.service --since "5 minutes ago" --no-pager | grep "错题"'
```

**实际输出**：

```
🧠 智能错题识别: should_create=True, confidence=0.82, category=empty_question,
   reason=综合判断: 3/3 投票支持, 证据=[关键词(0.90), AI意图(0.70), 图片(0.85)]
✅ [流式] 错题自动创建成功: user_id=e10d8b6b-033a-4198-bb7b-99ff1d4d5ea8,
   mistake_id=7423a999-0abb-40e5-8868-ecee583dc263, category=empty_question
```

### 2. 数据库验证

```sql
SELECT id, source, title, mastery_status, created_at
FROM mistake_records
WHERE user_id = 'e10d8b6b-033a-4198-bb7b-99ff1d4d5ea8'
ORDER BY created_at DESC;
```

**结果**：

```
id: 7423a999-0abb-40e5-8868-ecee583dc263
source: learning
title: 图片中的题我不会
mastery_status: not_mastered  ✅ 已修复
created_at: 2025-11-03 14:18:20
```

## 测试步骤

### 1. 小程序端测试

1. 打开小程序"作业问答"功能
2. 上传一张题目图片，提问"这道题我不会做"
3. 等待 AI 回答完成
4. 切换到"错题本"标签页
5. **下拉刷新列表**（重要！）
6. 应该能看到新创建的错题记录

### 2. 监控日志

```bash
# 实时监控错题创建
ssh root@121.199.173.244 'journalctl -u wuhao-tutor.service -f | grep -E "流式|错题|mistake"'
```

### 3. 验证数据

```bash
# 查询最新错题
ssh root@121.199.173.244 '
PGPASSWORD=MA-keit13 psql \
  -h pgm-bp1ce0sp88j6ha90.pg.rds.aliyuncs.com \
  -U horsdu_ma -d wuhao_tutor -p 5432 \
  -c "SELECT id, source, title, mastery_status, created_at
      FROM mistake_records
      WHERE source = '\''learning'\''
      ORDER BY created_at DESC LIMIT 5;"
'
```

## 4 策略智能识别系统

### 策略详解

1. **关键词检测**（confidence: 0.6-0.9）

   - 高置信度关键词：不会做、怎么做、错了、求解、不理解
   - 中置信度关键词：这道题、解题步骤、帮我看看

2. **AI 意图识别**（confidence: 0.5-0.9）

   - 提取 AI 响应中的 JSON 元数据
   - 分析 `is_mistake_question` 字段
   - 启发式规则分析问题意图

3. **图片分析**（confidence: 0.7-0.9）

   - 图片 + 短文本（<20 字符）= 拍照题
   - 复用 Qwen-vl-max 视觉能力

4. **综合判断**（投票机制）
   - 至少 1 个证据置信度 ≥0.7，或
   - 至少 2 个证据投票支持
   - 最终置信度 = max(所有证据置信度)

### 配置项

```python
# src/core/config.py
AUTO_MISTAKE_DETECTION_ENABLED: bool = True  # 启用自动识别
AUTO_MISTAKE_MIN_CONFIDENCE: float = 0.7     # 最低置信度阈值
AUTO_MISTAKE_REQUIRE_IMAGE: bool = False     # 不强制要求图片
```

## 已知问题与注意事项

### ✅ 已解决

- [x] WebSocket 流式接口未触发错题识别
- [x] mastery_status 字段值错误
- [x] 已存在错误数据已修复（2 条记录）

### ⚠️ 注意事项

1. **小程序缓存**：用户需要下拉刷新错题列表
2. **时间差**：错题创建在 AI 回答完成后，非实时
3. **去重机制**：同一问题多次提问不会重复创建

### 📊 监控指标

- 错题创建成功率：通过日志 `✅ [流式] 错题自动创建成功` 监控
- 识别置信度分布：分析 `confidence` 字段
- 用户反馈：观察错题本中"误判"的错题数量

## 后续优化建议

1. **小程序端优化**

   - 在 AI 回答完成后自动刷新错题本
   - 显示错题创建成功的提示

2. **识别精度优化**

   - 收集误判案例，调整关键词库
   - 优化置信度阈值（当前 0.7）

3. **用户体验优化**
   - 添加"不是错题"的反馈按钮
   - 支持手动移除误判的错题

---

**最后更新**: 2025-11-03  
**修复版本**: commit 1d77fe6  
**测试状态**: ✅ 通过  
**生产状态**: ✅ 已部署
