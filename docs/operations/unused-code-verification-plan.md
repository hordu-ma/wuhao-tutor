# 后端代码使用情况验证方案

> **目标**: 系统性分析小程序端(miniprogram)对后端 API 的实际调用情况，识别未使用代码
>
> **创建日期**: 2025-10-26
>
> **验证范围**: 后端 `src/` 目录 vs 小程序端 `miniprogram/` 目录

---

## 📊 一、验证方法论

### 方法 1️⃣: 静态代码追踪法（推荐首选）

**原理**: 通过代码搜索建立后端 API 端点与前端调用的映射关系

**步骤**:

1. **提取后端所有 API 端点** (从 `src/api/v1/endpoints/*.py`)
2. **提取小程序所有 API 调用** (从 `miniprogram/api/*.js` 和页面文件)
3. **双向匹配分析**，标记未匹配项
4. **人工复核**关键端点

**优势**: 快速、准确、可自动化
**劣势**: 可能遗漏动态调用场景

---

### 方法 2️⃣: 动态日志分析法（生产验证）

**原理**: 在生产环境收集真实用户请求日志

**步骤**:

1. **启用 API 访问日志**记录（30 天窗口期）
2. **统计端点调用频次**
3. **标记零调用端点**
4. **结合用户行为分析**（可能是功能未上线而非代码无用）

**优势**: 100%真实数据
**劣势**: 需要时间、新功能会误判

---

### 方法 3️⃣: 依赖图分析法（深度验证）

**原理**: 分析代码依赖关系，找出孤立模块

**步骤**:

1. **构建后端模块依赖图**（Service → Repository → Model）
2. **追踪 API 端点到 Service 的调用链**
3. **标记无 API 入口的 Service/Repository**
4. **检查是否为后台任务/定时任务使用**

**优势**: 找到深层未使用代码
**劣势**: 复杂度高、需要工具支持

---

## 🔍 二、当前系统模块清单

### 后端模块分类

| 类别         | 模块名称      | 文件位置                                       | 关键 API 端点          |
| ------------ | ------------- | ---------------------------------------------- | ---------------------- |
| **核心业务** | 作业批改      | `src/services/homework_service.py`             | `/api/v1/homework/*`   |
| **核心业务** | 学习问答      | `src/services/learning_service.py`             | `/api/v1/learning/*`   |
| **核心业务** | 错题手册      | `src/services/mistake_service.py`              | `/api/v1/mistakes/*`   |
| **核心业务** | 用户管理      | `src/services/user_service.py`                 | `/api/v1/users/*`      |
| **辅助功能** | 学情分析      | `src/services/analytics_service.py`            | `/api/v1/analytics/*`  |
| **辅助功能** | 答案质量评估  | `src/services/answer_quality_service.py`       | 无直接端点 ⚠️          |
| **辅助功能** | 知识点提取    | `src/services/knowledge/extraction_service.py` | 无直接端点 ⚠️          |
| **基础设施** | 文件上传      | `src/utils/file_upload.py`                     | `/api/v1/files/*`      |
| **基础设施** | 百炼 AI 服务  | `src/services/bailian_service.py`              | 无直接端点（内部调用） |
| **已废弃?**  | 微信服务      | `src/services/wechat_service.py`               | `/api/v1/wechat/*` ⚠️  |
| **已废弃?**  | 作业 API 服务 | `src/services/homework_api_service.py`         | 可能重复 ⚠️            |
| **已废弃?**  | 目标管理      | `src/api/v1/endpoints/goals.py`                | `/api/v1/goals/*` ⚠️   |

### 小程序前端模块清单

| 前端模块 | 文件位置                      | 调用的后端 API           |
| -------- | ----------------------------- | ------------------------ |
| 作业提交 | `miniprogram/api/homework.js` | ✅ `/api/v1/homework/*`  |
| 学习问答 | `miniprogram/api/learning.js` | ✅ `/api/v1/learning/*`  |
| 错题手册 | `miniprogram/api/mistakes.js` | ✅ `/api/v1/mistakes/*`  |
| 学情分析 | `miniprogram/api/analysis.js` | ✅ `/api/v1/analytics/*` |
| 用户管理 | `miniprogram/api/user.js`     | ✅ `/api/v1/users/*`     |
| 文件上传 | `miniprogram/api/file.js`     | ✅ `/api/v1/files/*`     |

---

## 🎯 三、快速验证脚本（自动化方案）

### 脚本 1: 提取后端 API 端点清单

```bash
#!/bin/bash
# scripts/analyze-backend-endpoints.sh

echo "=== 提取后端所有API端点 ==="

# 搜索所有@router装饰器
grep -r "@router\." src/api/v1/endpoints/*.py \
  | grep -E "(get|post|put|patch|delete)" \
  | sed -E 's/.*@router\.(get|post|put|patch|delete)\("([^"]+)".*/\1 \2/' \
  | sort -u \
  > docs/operations/backend-endpoints.txt

echo "✅ 已导出到 docs/operations/backend-endpoints.txt"
```

### 脚本 2: 提取小程序 API 调用清单

```bash
#!/bin/bash
# scripts/analyze-miniprogram-calls.sh

echo "=== 提取小程序所有API调用 ==="

# 搜索所有request调用
grep -rh "request\.\(get\|post\|put\|delete\|patch\)" miniprogram/api/*.js \
  | grep -oE "'api/v1/[^']+'" \
  | sed "s/'//g" \
  | sort -u \
  > docs/operations/miniprogram-api-calls.txt

echo "✅ 已导出到 docs/operations/miniprogram-api-calls.txt"
```

### 脚本 3: 差异对比分析

```python
#!/usr/bin/env python3
# scripts/compare-api-usage.py

"""
API使用情况对比分析脚本
对比后端端点与小程序调用，输出未使用端点清单
"""

import re
from pathlib import Path
from typing import Set, Dict, List

def extract_backend_endpoints() -> Dict[str, Set[str]]:
    """提取后端所有API端点"""
    endpoints = {
        'GET': set(),
        'POST': set(),
        'PUT': set(),
        'PATCH': set(),
        'DELETE': set()
    }

    endpoint_files = Path('src/api/v1/endpoints').glob('*.py')

    for file in endpoint_files:
        content = file.read_text()

        # 匹配 @router.get("/path", ...)
        for method in ['get', 'post', 'put', 'patch', 'delete']:
            pattern = rf'@router\.{method}\(["\']([^"\']+)["\']'
            matches = re.findall(pattern, content, re.IGNORECASE)

            for path in matches:
                # 标准化路径（移除路径参数）
                normalized = re.sub(r'\{[^}]+\}', '*', path)
                endpoints[method.upper()].add(f"/api/v1{path}" if not path.startswith('/') else path)

    return endpoints

def extract_miniprogram_calls() -> Set[str]:
    """提取小程序所有API调用"""
    api_calls = set()

    # 搜索 miniprogram/api/*.js
    api_files = Path('miniprogram/api').glob('*.js')

    for file in api_files:
        content = file.read_text()

        # 匹配 request.get('api/v1/...')
        pattern = r"request\.\w+\(['\"]([^'\"]+)['\"]"
        matches = re.findall(pattern, content)

        for path in matches:
            if path.startswith('api/v1'):
                # 标准化路径（移除动态参数）
                normalized = re.sub(r'\$\{[^}]+\}', '*', path)
                api_calls.add(f"/{normalized}")

    return api_calls

def compare_usage(backend: Dict[str, Set[str]], frontend: Set[str]) -> Dict:
    """对比使用情况"""
    all_backend = set()
    for endpoints in backend.values():
        all_backend.update(endpoints)

    unused = all_backend - frontend
    used = all_backend & frontend
    frontend_only = frontend - all_backend

    return {
        'backend_total': len(all_backend),
        'frontend_total': len(frontend),
        'used': sorted(used),
        'unused_backend': sorted(unused),
        'undefined_frontend': sorted(frontend_only)
    }

def generate_report(result: Dict) -> str:
    """生成markdown报告"""
    report = f"""# API使用情况分析报告

## 📊 统计摘要

- 后端定义端点: {result['backend_total']} 个
- 小程序调用端点: {result['frontend_total']} 个
- 已使用端点: {len(result['used'])} 个
- **未使用后端端点: {len(result['unused_backend'])} 个**
- 前端调用但后端未定义: {len(result['undefined_frontend'])} 个

---

## ❌ 未使用的后端端点 (需人工确认)

"""

    for endpoint in result['unused_backend']:
        report += f"- `{endpoint}`\n"

    report += "\n---\n\n## ⚠️ 前端调用但后端未找到的端点\n\n"

    for endpoint in result['undefined_frontend']:
        report += f"- `{endpoint}`\n"

    report += "\n---\n\n## ✅ 已确认使用的端点\n\n"

    for endpoint in result['used'][:20]:  # 只显示前20个
        report += f"- `{endpoint}`\n"

    if len(result['used']) > 20:
        report += f"\n... 还有 {len(result['used']) - 20} 个端点\n"

    return report

if __name__ == '__main__':
    print("🔍 开始分析API使用情况...")

    backend = extract_backend_endpoints()
    frontend = extract_miniprogram_calls()
    result = compare_usage(backend, frontend)

    report = generate_report(result)

    output_file = Path('docs/operations/api-usage-report.md')
    output_file.write_text(report)

    print(f"✅ 报告已生成: {output_file}")
    print(f"\n📈 快速摘要:")
    print(f"   - 未使用后端端点: {len(result['unused_backend'])} 个")
    print(f"   - 使用中端点: {len(result['used'])} 个")
```

---

## 📋 四、人工复核检查清单

### 阶段 1: 初步筛查（30 分钟）

**执行步骤**:

1. ✅ 运行上述 3 个脚本
2. ✅ 查看生成的 `api-usage-report.md`
3. ✅ 标记明确未使用的端点（如测试端点、已废弃功能）
4. ✅ 标记需要深入调查的端点

**输出**: 《初步分类表》

| 端点               | 状态   | 分类     | 备注                   |
| ------------------ | ------ | -------- | ---------------------- |
| `/api/v1/goals/*`  | 未使用 | 待确认   | 目标管理功能是否上线？ |
| `/api/v1/wechat/*` | 未使用 | 可能废弃 | 微信服务是否还需要？   |

---

### 阶段 2: 深度验证（1-2 小时）

**针对"待确认"端点**:

1. **检查代码依赖**

   ```bash
   # 搜索该端点是否被内部调用
   grep -r "wechat_service" src/
   ```

2. **检查数据库表使用情况**

   ```python
   # 查看相关表是否有数据
   SELECT COUNT(*) FROM wechat_sessions;
   ```

3. **检查配置文件**

   ```bash
   grep -i "wechat" .env config/
   ```

4. **咨询产品/业务团队**
   - 该功能是否计划上线？
   - 是否属于遗留代码？

**输出**: 《确认分类表》

| 端点               | 最终状态 | 处理建议       | 负责人          |
| ------------------ | -------- | -------------- | --------------- |
| `/api/v1/goals/*`  | 未来会用 | 保留+标记 TODO | PM 确认 Q1 上线 |
| `/api/v1/wechat/*` | 废弃代码 | 可删除         | 技术负责人确认  |

---

### 阶段 3: 内部服务验证（1 小时）

**针对无直接 API 端点的 Service**:

| Service                           | 验证方法         | 使用情况                         |
| --------------------------------- | ---------------- | -------------------------------- |
| `answer_quality_service.py`       | 搜索谁调用了它   | 被 `learning_service.py` 调用 ✅ |
| `knowledge/extraction_service.py` | 搜索 import 语句 | 被 `homework_service.py` 调用 ✅ |
| `bailian_service.py`              | 基础设施         | 多处调用 ✅                      |

**命令**:

```bash
# 查找某个service的使用情况
grep -r "from.*answer_quality_service import" src/
grep -r "answer_quality_service\." src/
```

---

## 🗂️ 五、分类标准与处理建议

### 分类 1: ✅ 确认使用中

**标准**:

- 小程序有对应 API 调用
- 或被其他使用中的 Service 内部调用
- 或为基础设施（如 auth、file_upload）

**处理**: 保留，无需修改

---

### 分类 2: 🔄 计划使用（暂时保留）

**标准**:

- 产品规划中的功能
- 已开发但未上线
- 下个迭代会使用

**处理**:

- 添加 `# TODO: 计划Q1上线` 注释
- 在 `docs/architecture/roadmap.md` 标记
- 定期复查（每季度）

**示例**:

```python
# goals.py
# TODO: 目标管理功能计划2025 Q1上线
# 产品需求: PRD-2024-12-001
# 负责人: 张三

@router.post("/goals")
async def create_goal(...):
    pass
```

---

### 分类 3: ❓ 不确定（需要调查）

**标准**:

- 无明确使用证据
- 无产品规划
- 代码逻辑复杂，不确定影响范围

**处理**:

- 先不删除
- 添加 `@deprecated` 注释
- 记录到 `docs/operations/deprecated-features.md`
- 1 个月后复查

**示例**:

```python
# wechat_service.py
# @deprecated 2025-10-26
# 原因: 小程序端未调用，疑似遗留代码
# 负责人: 李四
# 复查日期: 2025-11-26

class WechatService:
    pass
```

---

### 分类 4: ❌ 确认废弃（可删除）

**标准**:

- 明确不再使用
- 功能已下线
- 技术负责人确认可删

**处理**:

1. **创建备份分支**

   ```bash
   git checkout -b backup/remove-wechat-service
   ```

2. **删除代码**

   ```bash
   git rm src/services/wechat_service.py
   git rm src/api/v1/endpoints/wechat.py
   ```

3. **更新文档**

   - 在 `CHANGELOG.md` 记录删除
   - 在 `docs/operations/removed-features.md` 归档

4. **测试验证**
   ```bash
   make test  # 确保所有测试通过
   make lint  # 确保无import错误
   ```

---

## 🔄 六、执行计划（3 天完成）

### Day 1: 自动化分析（2 小时）

- [ ] 创建 `scripts/analyze-backend-endpoints.sh`
- [ ] 创建 `scripts/analyze-miniprogram-calls.sh`
- [ ] 创建 `scripts/compare-api-usage.py`
- [ ] 运行脚本，生成报告
- [ ] 输出: `docs/operations/api-usage-report.md`

---

### Day 2: 人工分类（4 小时）

- [ ] 阅读自动化报告
- [ ] 逐个端点分类（按上述 4 种分类）
- [ ] 填写《确认分类表》
- [ ] 咨询产品/业务确认不确定项
- [ ] 输出: `docs/operations/api-classification-result.md`

---

### Day 3: 处理执行（2 小时）

- [ ] 为"计划使用"代码添加 TODO 注释
- [ ] 为"不确定"代码添加@deprecated 注释
- [ ] 创建备份分支
- [ ] 删除"确认废弃"代码（谨慎操作）
- [ ] 运行测试套件验证
- [ ] 提交代码+更新文档
- [ ] 输出: Git 提交记录 + `CHANGELOG.md`

---

## 📝 七、最终交付物清单

1. ✅ `docs/operations/api-usage-report.md` - 自动化分析报告
2. ✅ `docs/operations/api-classification-result.md` - 人工分类结果
3. ✅ `docs/operations/deprecated-features.md` - 废弃功能归档
4. ✅ `docs/operations/roadmap-features.md` - 计划功能清单
5. ✅ `CHANGELOG.md` - 更新日志
6. ✅ Git 分支 `backup/cleanup-unused-code` - 代码备份

---

## ⚠️ 风险提示与注意事项

### 风险 1: 误删生产使用的代码

**防范措施**:

- ✅ 在测试环境先验证
- ✅ 创建备份分支
- ✅ 分阶段删除（先标记@deprecated，观察 1 周）
- ✅ 保留详细删除日志

### 风险 2: 动态调用遗漏

**示例**:

```javascript
// 可能被遗漏的动态调用
const endpoint = `/api/v1/${moduleName}/list`
api.get(endpoint)
```

**防范措施**:

- 搜索 `api/v1/\${` 模式
- 搜索字符串拼接场景
- 人工复核关键业务模块

### 风险 3: 定时任务/后台任务调用

**防范措施**:

```bash
# 检查celery任务
grep -r "@celery.task" src/
grep -r "schedule" src/
```

---

## 🎯 八、快速决策树

```
发现未使用端点
    ├── 小程序有调用? ────→ YES ────→ ✅ 保留
    ├── NO ↓
    ├── 内部Service调用? ──→ YES ────→ ✅ 保留
    ├── NO ↓
    ├── 产品计划使用? ────→ YES ────→ 🔄 标记TODO
    ├── NO ↓
    ├── 有数据库数据? ────→ YES ────→ ❓ 调查
    ├── NO ↓
    └── 技术负责人确认废弃? → YES ───→ ❌ 删除
```

---

## 📞 联系与支持

- **文档维护**: 技术负责人
- **产品确认**: 产品经理
- **业务咨询**: 业务负责人
- **紧急回滚**: 执行 `git revert` 或从备份分支恢复

---

**最后更新**: 2025-10-26  
**文档版本**: v1.0  
**下次复查**: 2026-01-26 (3 个月后)
