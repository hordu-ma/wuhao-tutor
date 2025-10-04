# 数据访问层指南 (DATA-ACCESS)

Last Updated: 2025-09-29
适用版本：后端 0.1.x 开发阶段
维护级别：核心（变更需在 PR 中说明影响面）

---

## 1. 文档定位

本文件定义五好伴学项目后端“数据访问层（DAL）”的角色、边界、模式、性能与演进方向，解决以下常见问题：

| 问题 | 查阅段落 |
|------|----------|
| 我应该在 Service 里直接写 SQL 吗？ | 2 / 3 |
| 如何新增复杂统计查询？ | 4 / 8 |
| 怎样避免 N+1 查询？ | 8 / 10 |
| 事务应该在哪一层控制？ | 7 |
| 如何设计批量操作？ | 6.4 |
| 学情分析的统计查询放哪里？ | 4.2 |
| 缓存会怎么接入？ | 9 |
| 性能监控如何关联查询？ | 10 |
| 测试仓储需要 mock 吗？ | 13 |

---

## 2. 分层定位与边界

| 层 | 职责 | 输入 | 输出 | 不应包含 |
|----|------|------|------|----------|
| API 层 | 路由/请求验证 | Pydantic 请求对象 | 标准响应包装 | 业务策略、直接 ORM 操作 |
| Service 层 | 业务流程/组合/跨仓储协调 | DTO / domain intent | DTO / Schema | 繁杂查询构造、原始 SQL |
| Repository 层 | 统一 CRUD + 复杂查询封装 | 字典/条件/标识 | ORM 模型实例/列表 | 业务流程判断 |
| ORM 模型 | 表结构与关系 | - | Python 对象 | 校验逻辑/流程决策 |

核心原则：
1. “Service 决策 + Repository 取数”
2. API 不感知 ORM 实体细节
3. 查询优化演进不影响 Service 调用签名
4. 单一出口：所有数据库访问由仓储层函数触发（测试与监控可注入观察）

---

## 3. 基础仓储：BaseRepository

### 3.1 目标
提供 80% 通用数据操作能力，避免在 Service 层重复编写：创建、获取、筛选、分页、更新、删除、批量操作。

### 3.2 典型方法（逻辑概念）
| 方法 | 功能 | 注意事项 |
|------|------|----------|
| create(data) | 创建单记录 | data 需是已清理字段 |
| bulk_create(list[data]) | 批量创建 | 建议控制批次（默认 ≤ 1000） |
| get_by_id(id) | 主键查询 | 返回 None 则由 Service 决策 |
| get_by_field(field, value) | 单字段唯一性场景 | 不做大小写转换 |
| get_all(filters, order_by, limit, offset) | 列表查询 | 支持 -field 降序（约定） |
| search(search_term, search_fields, limit) | LIKE / ILIKE 模糊查询 | 仅适用于文本性质字段 |
| update(id, update_data) | 局部更新 | Service 负责过滤不可更新字段 |
| bulk_update(list[{id, ...}]) | 批量局部更新 | 不做事务外部组合 |
| delete(id) | 硬删除或软删除（可扩展） | 软删除需继承扩展 |
| bulk_delete(ids) | 批量删除 | 建议审计需要前移确认 |
| exists(id) | 存在性快速检查 | 走主键索引 |
| count(filters) | 条件计数 | 大表慎用无索引字段 |

### 3.3 设计约束
- 泛型：`BaseRepository[ModelType]`
- 异步：所有方法 `async def`
- 不缓存：缓存层在上层（未来）适配
- 不吞异常：数据库异常向上抛出，由 Service 做上下文封装

### 3.4 安全约束
- 禁止接受用户原始 SQL 片段
- filters 仅允许字典 `{column_name: value}`，必要时在仓储内部白名单校验
- order_by 限定“列名或 -列名”模式，防 SQL 注入

---

## 4. 业务仓储：LearningRepository（示例扩展仓储）

### 4.1 适用场景
- 统计型查询（活跃度/题目数/正确率）
- 聚合 + 分组 + 时间窗口分析
- 多表关联 + 领域特有过滤语义
- 学情分析指标初步计算（非 AI 推断）

### 4.2 常见能力（逻辑概念）
| 方法 | 功能 | 样例返回结构 |
|------|------|--------------|
| get_user_learning_stats(user_id, days) | 近 n 日答题/会话统计 | { total_questions, active_days, avg_session_length } |
| get_daily_activity_pattern(user_id, days) | 时间段分布 | { hour_buckets: { "08": 3, ... } } |
| get_knowledge_mastery_analysis(user_id, subject) | 知识掌握推断（占位） | { topic_scores: [{topic, score}], gaps: [...] } |
| get_session_with_qa_history(session_id, limit) | 组合会话与问答 | { session: {...}, history: [...] } |

### 4.3 设计原则
- 不在此层编码“推荐算法/权重策略” → 将来拆分“分析服务层”
- 聚合结果合理结构化（字典 / dataclass / 轻量 Pydantic 模型）
- 允许内部使用原生 SQL（需行内注释 + 性能说明 + 索引假设）

---

## 5. Query 构造模式与约束

| 场景 | 推荐做法 | 反例 |
|------|----------|------|
| 简单过滤 | 使用 BaseRepository.get_all | 在 Service 中手工拼 SQLAlchemy 条件 |
| 动态排序 | 解析排序字段 → 传入仓储 | 在 API 层直接构建 ORM 查询 |
| 模糊搜索 | 定义 search_fields 白名单 | 直接拼接 `%{term}%` 无字段校验 |
| 多条件组合 | 仓储方法内部封装 OR/AND | Service 层遍地 if 嵌套 |
| 批量 upsert | 暂不支持（需显式实现） | 手工循环调用 create/update |
| 统计 + 详情 | 两次查询或子查询优化 | N+1 次逐行查询 |

---

## 6. 数据写入策略

### 6.1 创建
- 单记录：简单映射字段
- 批量：分批写入（未来可用 bulk save / copy 优化）

### 6.2 更新
- 部分更新：仅允许白名单字段
- 防竞态：可在未来引入 `version` 字段（乐观锁）

### 6.3 删除
- 默认硬删除（可添加 `deleted_at / is_deleted` 实现软删除扩展）
- 审计需求场景：使用软删除 + 归档表

### 6.4 批量操作防踩坑
| 风险 | 说明 | 解决 |
|------|------|------|
| 事务过大 | 一次性更新过多行 | 分批提交 / 限制批次尺寸 |
| 锁膨胀 | 长事务导致行锁长期占用 | 拆分语义 / 缩短事务持有 |
| 内存暴涨 | 构造巨大 Python 列表 | 流式构造 / 生成器 |

---

## 7. 事务管理

### 7.1 原则
- 以“Service 调用仓储”级别为事务粒度（一个业务动作 = 一个事务）
- Repository 内部不主动开启独立事务（除非明确注释）
- 在 Service 层使用：
  ```python
  async with async_session() as session:
      repo = BaseRepository(Model, session)
      # 多步写入
      await repo.create(...)
      await repo.update(...)
      # session.commit() 由框架/调用端触发（视封装而定）
  ```

### 7.2 异常回滚
- 使用 `async_session` 上下文 → 异常自动 rollback
- 业务层捕获后，不再进行二次 commit

### 7.3 避免跨边界事务
不要在仓储内部嵌套另一个 session 或自行开启新连接。

---

## 8. 性能与查询优化策略（当前与规划）

| 问题类型 | 当前手段 | 规划 |
|----------|----------|------|
| N+1 查询 | 避免循环逐条 get；组合查询 | 引入 selectinload / joinedload |
| 慢查询检测 | 性能模块监听 & 阈值记录 | 指标外显 + 报警 |
| 统计类查询 | 手写聚合 | 物化视图（定时刷新） |
| 重复读 | 待缓存接入 | 分层缓存（会话/统计） |
| 分页 | limit/offset | cursor-based（避免深翻页） |
| 高频只读 | 直接 DB | 只读缓存层（Redis） |
| 大字段延迟加载 | ORM 默认 | 按需 lazy load / exclude 字段 |

### 8.1 典型优化建议
| 场景 | 建议 |
|------|------|
| 会话 + 历史整合 | 一次 join + 排序 + 限制数量 |
| 近 30 天活跃统计 | 预计算/缓存统计结果 |
| 高频模板数据 | 前置缓存（固定不变） |
| 分钟级重复查询 | QueryCache + TTL 300s（规划） |
| 复杂报表导出 | 后台任务生成 + 结果缓存 |

---

## 9. 缓存策略（规划草案）

| 层次 | 适用数据 | 形式 | 失效策略 |
|------|----------|------|----------|
| 一级（进程内） | 短期高频（配置、小字典表） | LRU / 固定字典 | 定期刷新 |
| 二级（Redis） | 会话统计、热门主题、最近会话列表 | Key-Value / Hash | TTL + 主动失效 |
| 结果缓存 | 重复聚合查询 | 结果 JSON 序列化 | 定义 TTL + 参数哈希 |
| 预热缓存 | 模板/题库热数据 | 启动或调度加载 | 手动刷新 |

失效触发：
1. 写操作 → 精确删除相关 key
2. 定时刷新 → 定期全量/增量重建
3. 阈值清理 → 超出内存限制清扫低频

---

## 10. 慢查询与监控联动

| 监控项 | 来源 | 说明 |
|--------|------|------|
| 执行耗时 | SQLAlchemy 事件监听 | > 阈值（prod 0.5s）记录 |
| 查询类型统计 | 解析语句前缀（SELECT/UPDATE） | 频率分布 |
| 表热点分析 | 正则提取表名 | 用于索引评估 |
| 缓存命中率（规划） | QueryCache 包装 | 热点判断 |
| 异常占比 | 异常捕获位置 | 用于稳定性评估 |

“可观察性”文档补充：`OBSERVABILITY.md`（待接入 Prometheus Export）

---

## 11. 错误处理与异常分类

| 分类 | 典型异常 | 处理建议 |
|------|----------|----------|
| 数据不存在 | None 返回 | Service 层 → 转换为业务错误 |
| 唯一约束冲突 | IntegrityError | 用户重复行为提示 or 幂等处理 |
| 外键约束失败 | IntegrityError | 校验参数来源是否篡改 |
| 超时/连接失败 | OperationalError | 重试策略（只读场景） |
| 数据类型错误 | StatementError | 输入源 Schema 检查 |
| 乐观锁失败（规划） | VersionMismatch | 提示重试或刷新 |

禁止：
- 在仓储层捕获异常后返回假值（如返回 None 代替报错）

---

## 12. 命名与可维护性约定

| 元素 | 约定 |
|------|------|
| 仓储文件名 | `<domain>_repository.py` |
| 基础仓储 | `base_repository.py` |
| 扩展仓储类名 | `XxxRepository` |
| 统计方法前缀 | `get_ / compute_ / aggregate_` |
| 缓存方法（未来） | `cached_前缀` 或装饰器注解 |
| 批量方法 | `bulk_前缀` |
| 内部辅助（不供外部直接用） | `_internal_` 前缀 |

---

## 13. 测试策略

| 类型 | 范围 | 方式 |
|------|------|------|
| 单元测试 | BaseRepository 行为 | 使用内存 SQLite / fixtures |
| 集成测试 | 复杂统计 / 跨表 | 启动真实数据库（PostgreSQL） |
| 错误场景 | 唯一约束/外键 | 构造冲突数据 |
| 性能基线 | 大数据量查询 | 预填充 ≥ N 行测耗时 |
| 缓存命中（规划） | 模拟重复调用 | 对比无缓存版本 |

示例（伪概念）：
```
async def test_create_and_get(session):
    repo = BaseRepository(Model, session)
    obj = await repo.create({...})
    fetched = await repo.get_by_id(obj.id)
    assert fetched.id == obj.id
```

---

## 14. 示例调用（概念示例）

### 14.1 基础操作
```python
async def create_session(db, payload):
    from src.models.learning import ChatSession
    from src.repositories import BaseRepository

    repo = BaseRepository(ChatSession, db)
    return await repo.create({
        "user_id": payload.user_id,
        "title": payload.title,
        "status": "active"
    })
```

### 14.2 聚合统计
```python
async def get_learning_dashboard(db, user_id: str):
    from src.repositories.learning_repository import LearningRepository
    lr = LearningRepository(db)
    stats = await lr.get_user_learning_stats(user_id, days=30)
    pattern = await lr.get_daily_activity_pattern(user_id, days=30)
    return {
        "stats": stats,
        "activity_pattern": pattern
    }
```

### 14.3 批量更新（伪例）
```python
async def close_inactive_sessions(db, session_ids: list[str]):
    from src.repositories import BaseRepository
    from src.models.learning import ChatSession
    repo = BaseRepository(ChatSession, db)
    updates = [{"id": sid, "status": "closed"} for sid in session_ids]
    return await repo.bulk_update(updates)
```

---

## 15. 重构/演进指引

| 场景 | 行动 |
|------|------|
| 查询方法重复出现在多个 Service | 抽取到专用仓储 |
| Service 中出现 for + 多次 get_by_id | 设计批量查询或 JOIN |
| 原生 SQL 越界增长 | 封装到仓储，并评估建索引 |
| 聚合耗时 > 目标 | 加入缓存或预计算表 |
| 统计口径不一致 | 统一接口文档 + 单元测试锁定 |
| 事务跨多个 Service | 引入 Facade 组合或领域服务 |

---

## 16. 与其它文档的关系

| 主题 | 去向 |
|------|------|
| 架构分层总览 | `ARCHITECTURE.md` |
| API 输出结构 | `api/models.md` |
| 学情分析指标语义 | （规划）`LEARNING-ANALYTICS.md` |
| 缓存命中率指标 | `OBSERVABILITY.md` |
| 安全控制（避免数据外泄） | `SECURITY.md` |
| 迁移/DDL 变更流程 | `MIGRATION.md` |

---

## 17. 常见反模式（Avoid List）

| 反模式 | 危害 | 替代 |
|--------|------|------|
| 在 Service 层写复杂 SQL | 逻辑分散、不可测试 | 仓储封装 |
| 返回 ORM 实例给 API | 泄露内部结构 | 转换为 Schema |
| 在仓储里拼接不校验的排序字段 | 注入风险 | 白名单验证 |
| 捕获异常并返回 None | 模糊语义 | 抛出让上层处理 |
| 写操作后不 commit 且跨函数传递 session | 容易导致悬挂事务 | 限定作用域 |
| 为规避 N+1 用一次性加载所有数据 | 内存暴涨 | 分页 / 分段加载 |
| 滥用缓存不设失效策略 | 脏数据 / 难调试 | 设计 TTL + 精确失效 |
| 批量处理逐行 update | O(n) round-trip | bulk_update / 合并更新 |

---

## 18. 未来演进路线 (Roadmap Draft)

| 阶段 | 目标 | 内容 |
|------|------|------|
| Phase A | 结构稳定 | 补全文档 + 查询审计 |
| Phase B | 基线性能 | 慢查询集中治理 + 指标可视化 |
| Phase C | 缓存引入 | 一级/二级缓存策略验证 |
| Phase D | 数据分析增强 | 物化视图 & 分析聚合 |
| Phase E | 拆分 | 高负载模块（分析/AI日志）抽离 |
| Phase F | 成熟化 | 建立查询模式基线与自动建议 |

---

## 19. 维护规范

| 场景 | 要求 |
|------|------|
| 新增仓储方法 | 有 docstring + 指出复杂度 |
| 引入原生 SQL | 注释说明：用途 / 假设 / 依赖索引 |
| 统计方法变更 | 回顾前端影响 + 更新测试 |
| 缓存策略更新 | 更新本文件第 9 节 |
| 性能退化 | 先采集数据 → 再评估重构 |
| 废弃方法 | 标记 @deprecated + 保留 2 个小版本周期 |

---

## 20. FAQ（快速参考）

| 问题 | 答案 |
|------|------|
| 需要组合两个仓储的方法？ | 在 Service 层组合调用，必要时新建“聚合仓储” |
| 能否直接在 API 层调用 BaseRepository？ | 否，保持业务隔离 |
| 为什么不做自动缓存？ | 缓存策略需领域语义，防止误缓存脏数据 |
| 统计逻辑放在哪？ | 初期在业务仓储，后期大规模迁独立分析模块 |
| 如何模拟 DB 错误测试？ | 使用故意破坏数据 / monkeypatch session.execute |
| 为什么没有 Upsert? | 需求未出现，避免提前抽象（可逐案定制） |

---

## 21. 变更记录（占位）

| 日期 | 变更 | 描述 | 负责人 |
|------|------|------|--------|
| 2025-09-29 | 初稿 | 文档结构建立 | 文档重构组 |
| (待填写) | ... | ... | ... |

---

## 22. 反馈

如发现：
- 文档与代码脱节
- 统计口径不一致
- 复杂查询无注释
- 性能热点无归档

请创建 Issue（标签：`data-access`）或提交 PR，附：
1. 场景/问题描述
2. 现状与预期差异
3. 风险与影响面
4. 建议方案（可选）

---

（END）
