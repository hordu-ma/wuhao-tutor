# 知识图谱与知识点掌握度优化开发建议（Phase 8.x）

> 面向后续迭代的技术方案建议，当前生产环境已启用 **方案 D（基于错题的动态聚合兜底）**，本文档不要求一次性全部完成，可按优先级逐步落地。

---

## 一、当前实现简要回顾

### 1. 现状概览

- **知识点掌握度主数据表**：`knowledge_mastery`
  - 设计目标：作为学科知识图谱、学习曲线、学情分析等的统一数据源。
  - 现状问题：生产环境中，部分用户的 `knowledge_mastery` 仍为空，导致知识图谱无法展示。
- **错题记录表**：`mistake_records`
  - 已确认能够稳定写入：含 `user_id`、`subject`、`title`、`knowledge_points` 等字段。
  - 英语错题已能正确标记 `subject=english`，并带有结构化 `knowledge_points` 列表。
- **知识图谱服务**：`KnowledgeGraphService.get_subject_knowledge_graph`
  - 原逻辑：只从 `knowledge_mastery` 查询，如无数据直接返回空图谱。
  - 当前状态：已实现 **方案 D 兜底**——当 `knowledge_mastery` 为空时，从 `mistake_records` 动态聚合知识点视图返回给前端。

### 2. 方案 D 的核心逻辑（已上线）

位置：`src/services/knowledge_graph_service.py` → `KnowledgeGraphService.get_subject_knowledge_graph`

- 步骤：
  1. 按 `user_id + subject(标准化)` 查询 `KnowledgeMastery`；
  2. 如无数据，则：
     - 按 `user_id + subject(标准化)` 查询 `MistakeRecord`；
     - 遍历每条错题的 `knowledge_points`（字符串列表），按知识点名称聚合 `mistake_count`；
     - 用 `SimpleNamespace` 构造一批“伪 `KnowledgeMastery` 记录”，统一走原有节点构建和掌握度分布逻辑；
     - 掌握度暂定固定值 `0.2`，代表“明显薄弱”。
- 前端效果：
  - 即使 `knowledge_mastery` 为空，只要有带 `knowledge_points` 的错题，知识图谱也能展示若干红色（薄弱）节点，而不是空白状态。

---

## 二、短期优化建议（Phase 8.8）

> 目标：在不大动架构的前提下，让 `knowledge_mastery` 真正稳定落地，并与方案 D 的聚合保持一致。

### 1. 明确事务边界与持久化责任

**问题来源猜测：**

- `LearningService._update_knowledge_mastery` 内部使用了 `db.add()` + `flush()`，但请求结束时的事务可能被上层 `get_db` 管理：
  - 某些路径下发生异常或提前返回，导致隐式 `rollback`；
  - 或者 Service 内部曾尝试 `commit`，与依赖注入的会话管理冲突。

**建议动作：**

1. 在 `src/core/database.py` 中确认 `get_db()` 的实现：
   - 建议采用统一模式：
     - 成功请求 → `commit()`；
     - 捕获异常 → `rollback()`；
     - Service 层与 Repository 层 **不主动 commit**，只 `flush()` 即可。
2. 全局搜索 `commit(`：
   - 确认所有 Service / Repository 内部是否有主动 `commit` 行为；
   - 逐步移除或收敛到事务协调器（例如统一放在 Service 聚合层）。

### 2. 收敛知识点掌握度写入路径

当前存在两类写入逻辑：

- `LearningService._update_knowledge_mastery`：根据批改错题更新。
- `KnowledgeGraphService._get_or_create_knowledge_mastery` / `update_knowledge_mastery_after_review`：根据复习/点评更新。

**建议动作：**

1. 抽象出一个统一的 `KnowledgeMasteryRepository` 或服务内私有方法：
   - 职责：
     - 根据 `user_id + subject + knowledge_point` 查询/创建记录；
     - 统一更新 `mistake_count`、`total_attempts`、`mastery_level` 等指标；
     - 仅做 `add()` / 字段更新，不负责 `commit()`。
2. `LearningService` 与 `KnowledgeGraphService` 统一通过该入口更新掌握度，避免重复实现与字段不一致。

### 3. 补充观测与排查工具

为避免“看不到到底写没写”的黑盒感，建议：

1. 在 `src/api/v1/endpoints/knowledge_graph.py` 增加一个只读诊断接口（管理员/调试用途）：
   - 输入：`user_id`（或当前用户）、`subject`；
   - 输出：原始 `KnowledgeMastery` 记录列表（不做任何加工）。
2. 在 `_update_knowledge_mastery` 内增加更细粒度日志：
   - 记录每个知识点的更新前后 `mistake_count` / `total_attempts` / `mastery_level`。
3. 对关键路径增加测试用例：
   - 单元测试：模拟一次批改，断言 `knowledge_mastery` 表新增/更新了记录；
   - 集成测试：通过 API 调用 + 测试数据库验证端到端效果。

---

## 三、中期优化建议（Phase 8.9）

> 目标：让 `knowledge_mastery` 成为真正的单一事实源（SSOT），方案 D 只作为临时兜底或过渡逻辑。

### 1. 从错题聚合回写 KnowledgeMastery

既然方案 D 已经能够基于错题动态聚合出知识点视图，可以反过来利用这条路径做一次“回填”：

1. 新增后台任务 / 管理员接口，例如：`POST /knowledge-graph/rebuild-mastery-from-mistakes`：
   - 支持按 `user_id` & `subject` 维度重建；
   - 使用与方案 D 类似的聚合逻辑：
     - 遍历 `mistake_records`，按 `knowledge_point` 聚合 `mistake_count`；
     - 将结果写入/更新 `knowledge_mastery`；
     - 掌握度计算可沿用当前简化公式：
       - 例如：`mastery = max(0.1, 1 / (1 + alpha * mistake_count))`。
2. 回填完成后：
   - 优先从 `knowledge_mastery` 读取知识图谱；
   - 方案 D 的兜底逻辑只在“新用户且尚未有回填”的极少数场景触发。

### 2. 优化掌握度与趋势计算

当前掌握度设计偏“静态”，可以引入更多维度：

- 因素：错题次数、最近练习时间、是否复习正确、题目难度等；
- 示例公式（可迭代调整，不需要一次到位）：
  - 基础掌握度：`base = correct_attempts / max(1, total_attempts)`；
  - 惩罚错题：`penalty = 1 / (1 + beta * mistake_count)`；
  - 时间衰减：`decay = exp(-lambda * days_since_last_practice)`；
  - 最终：`mastery = clip(base * penalty * decay, 0, 1)`。

与此同时，可以让：

- `trend` 字段真正反映最近 N 次练习的变化（improving / stable / declining）。

### 3. 统一 subject / knowledge_point 的规范

- 将 `subject` 存储统一为英文枚举（`english` / `math` / `chinese` 等）或中文枚举，避免双向映射混乱；
- 对 `knowledge_point` 引入标准化字典 `KnowledgeNode`：
  - 字段：`id`、`name`、`subject`、`aliases` 等；
  - `KnowledgeMastery` 中引用 `knowledge_node_id`，保证前台展示和统计的一致性。

---

## 四、长期规划建议（Phase 9.x）

> 目标：让知识图谱成为多源融合的“学习知识图”，不仅仅依赖错题。

### 1. 多源输入融合

- 来源包括：
  - 作业批改错题（当前已接入）；
  - 正确作答题目（识别“巩固/已掌握”区域）；
  - 主动复习行为（自测、错题重做）；
  - AI 主动推送的练习或小测。

### 2. 知识图谱结构深化

- 在 `knowledge_nodes` 中显式维护：
  - 先修关系 prerequisite（A → B）；
  - 同层关联 relation（同一单元/知识组）；
  - 可从教材章节 / 现有知识树导入。
- 基于图结构：
  - 识别“薄弱链”：从低掌握度节点沿先修链向上追溯；
  - 为推荐服务提供更智能的路径规划（从基础到进阶）。

### 3. 快照与时间维度

- 利用 `UserKnowledgeGraphSnapshot` 记录阶段性图谱：
  - 每日/每周生成一份快照；
  - 支持回看“过去 7 天 / 30 天”的进步曲线；
  - 为家长端/教师端提供趋势报告基础数据。

---

## 五、建议的落地顺序

1. **优先级 P0（已完成 / 进行中）**

   - [x] 方案 D：基于错题的动态聚合兜底（已在 `get_subject_knowledge_graph` 中实现）。
   - [ ] 修正事务边界与 `knowledge_mastery` 持久化路径，确保新数据能稳定写入。

2. **优先级 P1（下一阶段建议）**

   - [ ] 抽象统一的 KnowledgeMastery 更新入口，消除重复逻辑；
   - [ ] 增加诊断接口与测试用例，保证可观测性与回归安全。

3. **优先级 P2（回填与算法优化）**

   - [ ] 基于现有错题数据批量回填 `knowledge_mastery`；
   - [ ] 优化掌握度算法与趋势字段，提升图谱表达力。

4. **优先级 P3（结构化知识与多源融合）**
   - [ ] 建立稳定的知识点字典与关系图；
   - [ ] 引入多源行为数据，沉淀为更完整的“学习知识图”。

---

## 六、给开发/运维的执行建议

- 在每次调整知识点掌握度逻辑后，务必：
  1. 先在 **测试环境** 用固定用户跑一套“图片作业 → 批改 → 错题 → 知识图谱”全链路；
  2. 用 SQL 明确检查：
     - `mistake_records` 中有英语错题且 `knowledge_points` 正确；
     - `knowledge_mastery` 中对应知识点记录已新增/更新；
  3. 再通过小程序前端确认：
     - 英语知识图谱出现节点，颜色、大小与预期一致；
     - 切换用户不会污染或串号。
- 生产环境调整建议走 **灰度策略**：
  - 先在少量内部账号开启新逻辑；
  - 观察 3 ～ 7 天的日志与用户行为，再全量开放。
