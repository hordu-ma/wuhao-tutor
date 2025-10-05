# 🚀 下一步开发行动计划

> **更新时间**: 2025-10-05  
> **策略**: RAG 后置开发，优先交付快速价值  
> **当前状态**: 第一批开发准备启动

---

## 📋 立即执行 (本周 Week 1)

### 1️⃣ 知识点提取优化 (TD-002) - 🔥 最高优先级

**目标**: 替换关键词匹配为 NLP/LLM 提取  
**预估工时**: 24 小时 (3 天)  
**截止日期**: 2025-10-08

#### 任务分解

- [ ] Day 1: 设计知识点提取架构 (规则 + AI 混合)

  - 调研 jieba 分词库
  - 测试百炼 API 知识点提取效果
  - 设计学科知识点词典结构

- [ ] Day 2: 实现知识点提取服务

  - 开发 `KnowledgeExtractionService`
  - 实现规则匹配逻辑
  - 实现 AI 提取逻辑
  - 实现结果融合和去重

- [ ] Day 3: 测试和优化
  - 准备 100 道测试题目
  - 人工标注知识点
  - 计算提取准确率 (目标 > 80%)
  - 调优算法参数

#### 关键文件

```
src/services/knowledge_extraction_service.py  (新建)
data/knowledge_dict/                          (新建目录)
  ├── math_grade_9.json
  ├── chinese_grade_9.json
  └── english_grade_9.json
tests/unit/test_knowledge_extraction.py       (新建)
```

#### 验收标准

- ✅ 知识点提取准确率 > 80%
- ✅ 平均提取时间 < 500ms
- ✅ 支持数学/语文/英语三科
- ✅ 置信度评分机制完善

---

## 📅 本月计划 (Week 1-4)

### Week 1 (10/06 - 10/12)

- **知识点提取优化** (3 天) ← 当前任务
- **知识图谱数据准备** (2 天)
  - 收集人教版教材目录
  - 整理教育部课程标准
  - 下载开源知识图谱数据

### Week 2 (10/13 - 10/19)

- **知识图谱数据导入** (2 天)
  - 开发导入脚本
  - 导入数学学科数据 (500+ 知识点)
  - 验证数据关联关系
- **答案质量评估** (1 天)
  - 实现多维度评分
  - 支持人工反馈

### Week 3 (10/20 - 10/26)

- **流式响应实现** (2 天)
  - 后端 SSE 接口
  - 前端打字机效果
- **请求缓存机制** (1 天)
  - Redis 缓存层
  - 相似度匹配

### Week 4 (10/27 - 11/02)

- **错题本功能** (2 天)
  - 数据模型
  - 复习提醒算法
  - 前端页面
- **学情分析优化** (2 天)
  - 遗忘曲线算法
  - 时间衰减权重

---

## 🎯 本周具体任务 (Day by Day)

### 周一 (10/06)

**上午**:

- [ ] 阅读百炼 API 文档，测试知识点提取效果
- [ ] 安装 jieba 分词库: `uv add jieba`
- [ ] 创建项目结构:
  ```bash
  mkdir -p src/services/knowledge
  mkdir -p data/knowledge_dict
  mkdir -p tests/unit/knowledge
  ```

**下午**:

- [ ] 设计 `KnowledgeExtractionService` 接口
- [ ] 实现基础的规则匹配逻辑
- [ ] 编写单元测试框架

### 周二 (10/07)

**上午**:

- [ ] 实现百炼 API 调用逻辑
- [ ] 实现结果融合算法

**下午**:

- [ ] 准备测试数据 (20 道数学题)
- [ ] 人工标注知识点
- [ ] 测试提取准确率

### 周三 (10/08)

**全天**:

- [ ] 扩大测试集 (100 道题)
- [ ] 调优算法参数
- [ ] 编写文档和 README
- [ ] 提交代码，准备进入下一任务

---

## 📖 参考资源

### 技术文档

- [jieba 中文分词](https://github.com/fxsjy/jieba)
- [百炼 API 文档](https://help.aliyun.com/document_detail/2712195.html)
- [知识图谱构建指南](docs/guide/knowledge-graph.md)

### 数据资源

- 人教版教材目录: http://www.pep.com.cn/
- 教育部课程标准: http://www.moe.gov.cn/
- K12 开源知识图谱: https://github.com/search?q=K12+knowledge+graph

### 项目文档

- [开发路线图](docs/DEVELOPMENT_ROADMAP.md) - 完整计划
- [项目状况分析](docs/PROJECT_DEVELOPMENT_STATUS.md) - 技术债务
- [AI 助手上下文](AI-CONTEXT.md) - 核心信息

---

## ✅ 今日行动清单 (2025-10-05 晚)

### 准备工作 (1 小时)

- [ ] 通读开发路线图文档
- [ ] 确认环境配置正常: `uv run python scripts/diagnose.py`
- [ ] 安装 jieba: `uv add jieba`
- [ ] 创建项目目录结构

### 技术预研 (2 小时)

- [ ] 测试 jieba 分词效果

  ```python
  import jieba
  text = "求二次函数 y = x^2 - 4x + 3 的顶点坐标"
  words = jieba.cut(text)
  print(list(words))
  ```

- [ ] 测试百炼 API 知识点提取
  ```python
  prompt = "从题目中提取数学知识点: 求二次函数..."
  response = await bailian_service.chat_completion(...)
  ```

### 设计工作 (1 小时)

- [ ] 绘制知识点提取流程图
- [ ] 设计知识点词典 JSON 格式
- [ ] 编写 `KnowledgeExtractionService` 接口定义

---

## 🔔 提醒事项

### 重要原则

1. ✅ **每天提交代码**: 保持小步快跑，持续集成
2. ✅ **测试先行**: 先写测试，再写实现
3. ✅ **文档同步**: 代码和文档同步更新
4. ✅ **性能监控**: 关注提取时间，避免阻塞

### Git 提交规范

```bash
# 示例
git add src/services/knowledge_extraction_service.py
git commit -m "feat(knowledge): 实现知识点提取服务基础框架"

git add data/knowledge_dict/math_grade_9.json
git commit -m "data(knowledge): 添加数学九年级知识点词典"

git add tests/unit/test_knowledge_extraction.py
git commit -m "test(knowledge): 添加知识点提取单元测试"
```

### 每日站会问题

1. 昨天完成了什么?
2. 今天计划做什么?
3. 遇到什么阻碍?

---

## 📞 需要帮助?

### 技术问题

- 查看 [AI-CONTEXT.md](AI-CONTEXT.md) § 常见问题排查
- 运行诊断脚本: `uv run python scripts/diagnose.py`

### 设计问题

- 参考 [开发路线图](docs/DEVELOPMENT_ROADMAP.md) 详细方案
- 参考 [项目状况分析](docs/PROJECT_DEVELOPMENT_STATUS.md) 架构设计

### 其他问题

- 邮箱: maliguo@outlook.com
- 项目 Issues: GitHub Issues

---

**🔥 让我们开始吧！第一步：知识点提取优化！**

**目标**: Week 3 前完成第一批开发，快速交付价值！
