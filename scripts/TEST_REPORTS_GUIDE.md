# 测试报告管理说明

## 📋 测试报告位置

本项目的测试报告应存储在统一位置，便于查看和分析。

### 测试报告目录结构

```
test-results/
├── coverage/                    # 代码覆盖率报告
│   └── index.html               # HTML 覆盖率报告
├── performance/                 # 性能测试报告
│   ├── load-test-2025-11-13.json
│   └── profiling-report.html
├── integration/                 # 集成测试结果
│   ├── api-tests-2025-11-13.xml
│   └── api-tests-2025-11-13.json
├── unit/                        # 单元测试结果
│   ├── unit-tests-2025-11-13.xml
│   └── unit-tests-2025-11-13.json
└── latest-summary.json          # 最新测试摘要
```

---

## 🧪 生成测试报告

### 代码覆盖率报告

```bash
# 生成 HTML 覆盖率报告
make test-coverage

# 输出位置
htmlcov/index.html

# 查看报告
open htmlcov/index.html
```

### 集成测试报告

```bash
# 运行集成测试并生成报告
make test-integration

# 输出位置
test-results/integration/

# 报告格式
- JUnit XML (pytest-junit)
- JSON 报告 (pytest-json-report)
```

### 单元测试报告

```bash
# 运行单元测试并生成报告
make test-unit

# 输出位置
test-results/unit/
```

### 性能测试报告

```bash
# 运行性能测试
make test-performance

# 输出位置
test-results/performance/
```

---

## 📊 测试报告内容

### 覆盖率报告

**包含信息**：

- 整体代码覆盖率百分比（目标：≥ 80%）
- 文件级别覆盖率
- 函数级别覆盖率
- 缺失覆盖的代码行

**查看方式**：

```bash
# 生成并打开
make test-coverage
open htmlcov/index.html
```

### 测试结果汇总

**包含信息**：

- 测试总数
- 通过数 / 失败数 / 跳过数
- 执行时间
- 失败用例详情

**查看方式**：

```bash
# 查看 JSON 摘要
cat test-results/latest-summary.json | jq

# 查看最后测试输出
pytest tests/ -v --tb=short
```

---

## 🔄 自动化测试报告

### GitHub Actions 集成

在 `.github/workflows/` 中配置：

```yaml
- name: Generate Test Reports
  run: |
    make test-coverage
    pytest tests/ --json-report --json-report-file=test-results/report.json

- name: Upload Coverage
  uses: codecov/codecov-action@v3
  with:
    files: ./htmlcov/
```

### 本地开发

```bash
# 开发时快速测试
make test

# 全面测试（包括覆盖率）
make test-coverage

# 特定模块测试
pytest tests/unit/test_learning_service.py -v
```

---

## 📈 测试指标追踪

### 关键指标

| 指标           | 目标   | 当前 | 趋势 |
| -------------- | ------ | ---- | ---- |
| 总体覆盖率     | ≥ 80%  | 📊   | ↗️   |
| 单元测试通过率 | 100%   | 📊   | ↗️   |
| 集成测试通过率 | 100%   | 📊   | ↗️   |
| 平均执行时间   | < 300s | 📊   | ↘️   |
| 新代码覆盖率   | ≥ 85%  | 📊   | ↗️   |

### 追踪历史

```bash
# 创建历史比较脚本
./scripts/track-test-metrics.sh

# 输出示例
Date        Coverage    UnitTests    IntegrationTests
2025-11-10  78%         145/145 ✅   32/32 ✅
2025-11-11  79%         146/146 ✅   32/32 ✅
2025-11-12  80%         148/148 ✅   33/33 ✅
2025-11-13  81%         150/150 ✅   34/34 ✅
```

---

## 🗑️ 测试报告清理

### 自动清理策略

```bash
# 保留最近 30 天的报告
find test-results/ -name "*.json" -mtime +30 -delete

# 压缩旧报告
find test-results/ -name "*.json" -mtime +7 -exec gzip {} \;

# 保留最新的 5 个 HTML 报告
ls -t htmlcov/index.html.* | tail -n +6 | xargs rm
```

### 手动清理

```bash
# 清理所有测试报告
rm -rf test-results/ htmlcov/

# 清理特定类型
rm -rf test-results/integration/

# 仅保留最新汇总
find test-results -type f ! -name "latest-summary.json" -delete
```

---

## 📝 最佳实践

- ✅ 每次测试都生成报告
- ✅ 定期审查覆盖率趋势
- ✅ 为新代码编写测试
- ✅ 保留历史报告用于对比
- ✅ 在 CI/CD 中自动化报告生成
- ❌ 不要提交 test-results/ 到 Git（已 .gitignore）
- ❌ 不要忽视覆盖率下降
- 📊 定期分析测试失败原因

---

## 🎯 设置覆盖率门槛

在 `pyproject.toml` 中配置：

```toml
[tool.pytest.ini_options]
addopts = "--cov=src --cov-report=html --cov-report=term-missing --cov-fail-under=80"

[tool.coverage:run]
branch = true
omit = ["*/tests/*", "*/__init__.py"]

[tool.coverage:report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise NotImplementedError",
]
```

---

## 🚀 快速命令

```bash
# 生成所有报告
make test-coverage

# 查看覆盖率
open htmlcov/index.html

# 查看摘要
cat test-results/latest-summary.json | python -m json.tool

# 比较报告
diff test-results/previous-report.json test-results/latest-summary.json

# 清理旧报告
find test-results -mtime +30 -delete
```

---

**更新**：2025-11-13

**相关命令**：

- `make test` - 运行所有测试
- `make test-coverage` - 生成覆盖率报告
- `make test-unit` - 运行单元测试
- `make test-integration` - 运行集成测试

**相关文件**：

- `tests/conftest.py` - pytest 配置
- `pyproject.toml` - 测试工具配置
- `.github/workflows/` - CI/CD 配置
