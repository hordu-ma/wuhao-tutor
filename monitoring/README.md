# monitoring/ 目录

## 📁 目录结构

```
monitoring/
├── prometheus.yml          # Prometheus 配置文件
├── alertmanager/           # Alertmanager 配置
├── grafana/                # Grafana 配置
└── rules/                  # 告警规则
```

## 📝 各目录说明

### prometheus.yml

**用途**：Prometheus 监控系统的配置文件

- **功能**：

  - 定义监控目标（scrape targets）
  - 设置数据抓取间隔
  - 配置告警规则文件路径
  - 定义外部标签

- **常见配置项**：

  ```yaml
  global:
    scrape_interval: 15s # 抓取间隔
    evaluation_interval: 15s # 评估间隔

  scrape_configs:
    - job_name: 'wuhao-tutor'
      static_configs:
        - targets: ['localhost:8000']

  rule_files:
    - 'rules/*.yml' # 告警规则文件

  alerting:
    alertmanagers:
      - static_configs:
          - targets: ['localhost:9093']
  ```

- **修改频率**：低（仅当添加新的监控目标时）

### alertmanager/

**用途**：告警管理器配置

- **功能**：

  - 告警路由规则
  - 告警分组策略
  - 通知接收者配置
  - 告警模板

- **常见配置**：

  - Webhook 集成（Slack、钉钉、企业微信）
  - 邮件告警
  - SMS 告警
  - 告警去重和分组

- **文件类型**：YAML 配置文件

- **使用场景**：
  - 应用程序出现错误时发送告警
  - 性能指标超过阈值时通知
  - 告警分级和路由

### grafana/

**用途**：Grafana 可视化配置

- **功能**：

  - 仪表板配置（Dashboard）
  - 数据源配置
  - 告警面板配置
  - 用户和权限配置

- **常见文件**：

  - `dashboards.yml` - 仪表板配置
  - `datasources.yml` - 数据源配置
  - `provisioning/` - 自动配置目录

- **用途**：
  - 实时性能展示
  - 历史数据分析
  - 系统健康状态监控

### rules/

**用途**：Prometheus 告警规则

- **功能**：

  - 定义告警条件
  - 告警持续时间
  - 告警严重级别

- **规则示例**：

  ```yaml
  groups:
    - name: wuhao_alerts
      rules:
        - alert: HighErrorRate
          expr: rate(http_requests_total{status="500"}[5m]) > 0.05
          for: 5m
          labels:
            severity: critical
          annotations:
            summary: 'High error rate detected'
  ```

- **常见告警项**：
  - API 错误率过高
  - 数据库查询超时
  - 内存使用过多
  - 磁盘空间不足
  - 请求响应时间过长

## 🔄 监控架构

```
应用程序
    ↓
metrics (Prometheus format)
    ↓
Prometheus (prometheus.yml)
    ↓
告警规则 (rules/)
    ↓
Alertmanager (alertmanager/)
    ↓
通知渠道 (Slack、邮件等)

并行：
Grafana (grafana/)
    ↓
可视化展示
```

## 🛠️ 部署和运行

### 启动 Prometheus

```bash
prometheus --config.file=monitoring/prometheus.yml
```

### 启动 Alertmanager

```bash
alertmanager --config.file=monitoring/alertmanager/config.yml
```

### 启动 Grafana

```bash
docker run -d -p 3000:3000 grafana/grafana
# 然后加载配置：monitoring/grafana/
```

## 📌 最佳实践

- ✅ 定期审查告警规则的有效性
- ✅ 在仪表板上监控关键指标
- ✅ 为不同的告警级别配置不同的通知
- ✅ 记录告警触发的原因和处理方法
- ❌ 不要忽视或禁用重要告警
- 🔒 保护 Alertmanager 的敏感配置（API Key）

## 🔍 关键监控指标

### 应用程序级别

- HTTP 请求数和错误率
- API 响应时间分布
- 数据库查询性能
- 缓存命中率
- 业务逻辑错误

### 系统级别

- CPU 使用率
- 内存使用情况
- 磁盘 I/O
- 网络流量
- 进程运行状态

## 📚 相关文档

- [Prometheus 官方文档](https://prometheus.io/docs/)
- [Grafana 官方文档](https://grafana.com/docs/)
- [Alertmanager 官方文档](https://prometheus.io/docs/alerting/latest/overview/)

---

**更新**：2025-11-13

**维护人员**：DevOps Team
