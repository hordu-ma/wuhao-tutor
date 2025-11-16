# 五好伴学系统全面审查报告

## Todo 清单
- [x] 1. 梳理项目结构与依赖版本
- [x] 2. 审阅后端/前端/小程序/运维实现细节
- [x] 3. 汇总问题与建议并输出审查报告

## 变更摘要
```
变更类型: 文档
风险评估: 中
```

## 验证命令
```/dev/null/commands.sh#L1-4
make lint
make test
npm run lint --prefix frontend
```

## 回滚方案
```/dev/null/rollback.sh#L1-3
git checkout HEAD -- gpt_suggestion.md
# 或
git revert <commit-hash>
```

---

## 1. 执行摘要
- 架构分层（API→Service→Repository→Model）遵循良好，异步链路、限流、安全头等基础设施已上线。
- 依赖阿里云百炼、OSS、ASR、OCR 等外部服务，需重点监控调用成本与故障降级。
- 测试覆盖率与监控体系具备雏形，但端到端测试、CI 强约束、AI Mock 仍待补齐。

---

## 2. 后端 (FastAPI / Python)
| 维度 | 现状 | 风险 | 建议 |
| --- | --- | --- | --- |
| 分层与依赖 | `src/api`→`services`→`repositories`→`models`，`BaseRepository` 泛型化；`LearningService`、`MistakeService` 封装 AI 逻辑 | 业务扩展时 Service 体量易膨胀 | 引入 `ServiceResult`/`UseCase` 模式，将 AI/缓存/监控注入式管理 |
| 安全与限流 | `SecurityHeadersMiddleware`、`RateLimitMiddleware`、Token Bucket + Sliding Window | 多节点部署下限流为进程级 | 迁移到 Redis 计数器，提供统一的 `RateLimitRuleStore` |
| AI 调用 | `bailian_service` 支持重试、超时、日志；`LearningService` 内建作业批改、错题自动生成 | 缺少熔断、成本追踪、灰度模型切换 | 增加调用熔断器、Prometheus 指标、模型版本配置化；在 `AIContext` 里记录 token 消耗 |
| 数据层 | AsyncSession + selectinload；`BaseRepository` 统一 CRUD | 热表（question/answer/mistake）索引策略未知 | 补充复合索引审计脚本，配合慢查询日志输出结构化 JSON |
| 监控 | `PerformanceMonitoringMiddleware`、`cleanup_old_metrics` | 监控数据未统一输出 (Prometheus/OpenTelemetry) | 引入 `metrics_exporter`，把中间件指标写入 Prometheus 网关 |

---

## 3. 前端 (Vue3 + TS + Element Plus)
- **工程化**：Vite + TypeScript + Pinia + ESLint/Prettier/Vitest；全局错误处理、认证恢复集中在 `main.ts`。
- **交互性能**：ECharts/KaTeX、大量 AI 请求需加骨架屏、请求终止（AbortController）和并发限流。
- **质量保障**：建议
  1. 在 CI 中强制 `npm run lint && npm run test:coverage`；
  2. 增设 Playwright/ Cypress 端到端脚本覆盖「登录→问答→错题→复习」。
- **安全**：对上传、富文本渲染做二次校验；增加 CSP 报警通道，监控第三方脚本失效。

---

## 4. 微信小程序
- **配置**：`project.config.json` 开启 URL 白名单、按需编译；`requestDomain` 仅指向生产，需要拆分 dev/staging。
- **网络层**：建议统一请求签名与重试策略；对语音/图片上传加入哈希校验与大小预检查。
- **体验**：AI 分析过程引入 Loading/重试提示，减少用户无反馈等待。

---

## 5. DevOps / 运行
- **部署脚本**：`scripts/deploy.sh` 涵盖 SSH 检查、env 校验、systemd 修复、前后端同步、健康检查；需确认依赖管理（uv vs pip）一致，避免重复装包。
- **监控与日志**：建议
  1. 采集 systemd、Nginx、Uvicorn、AI 调用日志到集中平台（ELK/Loki）；
  2. 设定 AI 费用、Redis 连接池、DB TPS 的阈值告警；
  3. 定期演练 `cleanup` 协程崩溃或未执行的兜底策略。
- **CI/CD**：若尚未启用，可配置：
  - 后端：`make lint && make test`
  - 前端：`npm run lint && npm run test:coverage`
  - 小程序：微信 CLI 校验
  并在合入前要求测试报告与覆盖率阈值。

---

## 6. 测试与质量
- `tests/` 已含 `api/services/repositories/performance`，但应：
  1. 增加 AI Mock（固定响应/错误）以脱离外部依赖；
  2. 引入性能基准测试，记录 AI 问答/错题算法 P95；
  3. 添加 Chaos 场景：Redis 宕机、百炼 API 降速、OSS 不可用；
  4. 将覆盖率阈值写入 CI（如 `pytest --cov --cov-fail-under=80`）。

---

## 7. 风险与改进优先级
| 时间 | 重点 | 说明 |
| --- | --- | --- |
| 短期 (≤1月) | Redis 分布式限流、AI 熔断与降级、OSS 上传安全审计、端到端测试落地 | 直接降低高频风险 |
| 中期 (1-3月) | Prometheus/Grafana/Loki 统一观测、AI 成本仪表、PGVector/推荐系统 POC、预发布灰度流程 | 支撑功能扩展与稳定性 |
| 长期 (3-6月) | A/B 测试框架、RAG 模块、威胁建模与渗透测试、移动端原生计划 | 面向产品演进与安全治理 |

---

## 8. 后续行动
1. 若需具体整改方案（如 RateLimiter Redis 化、AI 熔断器实现、Playwright 脚本示例），请按优先级逐项授权。
2. 建议结合实时指标、用户反馈、成本数据定期复盘本报告内容，保持动态调优。