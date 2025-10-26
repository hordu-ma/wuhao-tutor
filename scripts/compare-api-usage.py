#!/usr/bin/env python3
"""
API使用情况对比分析脚本
对比后端端点与小程序调用，输出未使用端点清单

创建日期: 2025-10-26
"""

import re
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set, Tuple


def extract_backend_endpoints() -> Dict[str, List[Tuple[str, str]]]:
    """
    提取后端所有API端点

    Returns:
        {
            'GET': [('/api/v1/homework/list', 'homework.py'), ...],
            'POST': [...],
            ...
        }
    """
    endpoints = defaultdict(list)

    endpoint_dir = Path("src/api/v1/endpoints")
    if not endpoint_dir.exists():
        print(f"❌ 目录不存在: {endpoint_dir}")
        return endpoints

    endpoint_files = list(endpoint_dir.glob("*.py"))
    print(f"📂 扫描 {len(endpoint_files)} 个后端文件...")

    for file in endpoint_files:
        if file.name.startswith("__"):
            continue

        content = file.read_text()

        # 匹配 @router.get("/path", ...)
        for method in ["get", "post", "put", "patch", "delete"]:
            pattern = rf'@router\.{method}\s*\(\s*["\']([^"\']+)["\']'
            matches = re.findall(pattern, content, re.IGNORECASE)

            for path in matches:
                # 标准化路径
                if not path.startswith("/"):
                    path = f"/{path}"

                # 统一格式（将路径参数标准化）
                normalized = re.sub(r"\{[^}]+\}", ":id", path)

                endpoints[method.upper()].append((normalized, file.name))

    return endpoints


def extract_miniprogram_calls() -> Set[str]:
    """
    提取小程序所有API调用

    Returns:
        {'/api/v1/homework/list', '/api/v1/learning/ask', ...}
    """
    api_calls = set()

    # 搜索 miniprogram/api/*.js
    api_dir = Path("miniprogram/api")
    if not api_dir.exists():
        print(f"❌ 目录不存在: {api_dir}")
        return api_calls

    api_files = list(api_dir.glob("*.js"))
    print(f"📱 扫描 {len(api_files)} 个小程序API文件...")

    for file in api_files:
        if file.name == "index.js":
            continue

        content = file.read_text()

        # 匹配 request.get('api/v1/...')
        pattern1 = r"request\.\w+\s*\(\s*['\"]([^'\"]+)['\"]"
        matches1 = re.findall(pattern1, content)

        # 匹配 request.get(`api/v1/...`)
        pattern2 = r"request\.\w+\s*\(\s*`([^`]+)`"
        matches2 = re.findall(pattern2, content)

        for path in matches1 + matches2:
            if "api/v1" in path:
                # 标准化路径
                if not path.startswith("/"):
                    path = f"/{path}"

                # 将动态参数统一为 :id
                normalized = re.sub(r"\$\{[^}]+\}", ":id", path)
                api_calls.add(normalized)

    # 也搜索页面文件中的直接调用
    pages_dir = Path("miniprogram/pages")
    if pages_dir.exists():
        for page_file in pages_dir.rglob("*.js"):
            content = page_file.read_text()

            # 匹配类似 api.homework.xxx 或直接的 /api/v1/ 调用
            pattern = r"['\"`](api/v1/[^'\">`]+)['\"`]"
            matches = re.findall(pattern, content)

            for path in matches:
                if not path.startswith("/"):
                    path = f"/{path}"
                normalized = re.sub(r"\$\{[^}]+\}", ":id", path)
                api_calls.add(normalized)

    return api_calls


def normalize_path(path: str) -> str:
    """标准化API路径用于对比"""
    # 移除末尾斜杠
    path = path.rstrip("/")

    # 统一路径参数格式
    path = re.sub(r"\{[^}]+\}", ":id", path)
    path = re.sub(r"/\d+", "/:id", path)
    path = re.sub(r"\$\{[^}]+\}", ":id", path)

    return path


def compare_usage(
    backend: Dict[str, List[Tuple[str, str]]], frontend: Set[str]
) -> Dict:
    """对比使用情况"""
    # 扁平化后端端点
    all_backend = {}  # {normalized_path: (method, file)}
    for method, endpoints in backend.items():
        for path, file in endpoints:
            normalized = normalize_path(path)
            all_backend[f"{method}:{normalized}"] = (method, path, file)

    # 标准化前端调用
    frontend_normalized = {normalize_path(p) for p in frontend}

    # 对比
    used = []
    unused = []

    for key, (method, path, file) in all_backend.items():
        normalized = normalize_path(path)

        # 检查是否被使用（不区分HTTP方法）
        if any(normalized in fp for fp in frontend_normalized):
            used.append((method, path, file))
        else:
            unused.append((method, path, file))

    # 前端调用但后端未定义
    backend_paths = {normalize_path(p) for _, p, _ in all_backend.values()}
    undefined = [
        fp for fp in frontend_normalized if not any(fp in bp for bp in backend_paths)
    ]

    return {
        "backend_total": len(all_backend),
        "frontend_total": len(frontend),
        "used": sorted(used),
        "unused": sorted(unused),
        "undefined_frontend": sorted(undefined),
    }


def analyze_module_usage(unused: List[Tuple[str, str, str]]) -> Dict[str, List]:
    """按模块分组统计未使用端点"""
    modules = defaultdict(list)

    for method, path, file in unused:
        module = file.replace(".py", "")
        modules[module].append(f"{method} {path}")

    return dict(modules)


def generate_report(result: Dict) -> str:
    """生成markdown报告"""

    report = f"""# API使用情况分析报告

> **生成时间**: 2025-10-26  
> **分析范围**: 后端 src/api/v1/endpoints vs 小程序 miniprogram/

---

## 📊 统计摘要

| 指标 | 数量 | 占比 |
|------|------|------|
| 后端定义端点总数 | {result['backend_total']} | 100% |
| 小程序调用端点总数 | {result['frontend_total']} | - |
| **✅ 已使用端点** | {len(result['used'])} | {len(result['used'])/result['backend_total']*100:.1f}% |
| **❌ 未使用端点** | {len(result['unused'])} | {len(result['unused'])/result['backend_total']*100:.1f}% |
| ⚠️ 前端调用但后端未定义 | {len(result['undefined_frontend'])} | - |

---

## ❌ 未使用的后端端点 ({len(result['unused'])}个)

**需要人工确认是否可以删除或标记为计划功能**

"""

    # 按模块分组
    modules = analyze_module_usage(result["unused"])

    for module, endpoints in sorted(modules.items()):
        report += f"\n### 📦 {module}.py ({len(endpoints)}个未使用)\n\n"
        for endpoint in sorted(endpoints):
            report += f"- `{endpoint}`\n"

    report += "\n---\n\n## ⚠️ 前端调用但后端未找到的端点\n\n"

    if result["undefined_frontend"]:
        report += "**可能原因**: 路径匹配问题、动态路由、或前端代码错误\n\n"
        for endpoint in result["undefined_frontend"][:20]:
            report += f"- `{endpoint}`\n"
        if len(result["undefined_frontend"]) > 20:
            report += f"\n... 还有 {len(result['undefined_frontend']) - 20} 个\n"
    else:
        report += "✅ 无此类问题\n"

    report += "\n---\n\n## ✅ 已确认使用的端点\n\n"

    # 按模块分组已使用端点
    used_modules = defaultdict(list)
    for method, path, file in result["used"]:
        module = file.replace(".py", "")
        used_modules[module].append(f"{method} {path}")

    for module, endpoints in sorted(used_modules.items()):
        report += f"\n### 📦 {module}.py ({len(endpoints)}个使用中)\n\n"
        for endpoint in sorted(endpoints)[:10]:  # 只显示前10个
            report += f"- `{endpoint}`\n"
        if len(endpoints) > 10:
            report += f"- ... 还有 {len(endpoints) - 10} 个端点\n"

    report += "\n---\n\n## 🔍 详细分析建议\n\n"

    # 重点模块分析
    homework_unused = len(modules.get("homework", []))
    homework_used = len(used_modules.get("homework", []))
    learning_unused = len(modules.get("learning", []))
    learning_used = len(used_modules.get("learning", []))

    report += f"""
### Homework 模块
- ✅ 使用中: {homework_used} 个端点
- ❌ 未使用: {homework_unused} 个端点
- 💡 **建议**: {'大量使用，核心模块' if homework_used > 5 else '使用较少，考虑合并'}

### Learning 模块  
- ✅ 使用中: {learning_used} 个端点
- ❌ 未使用: {learning_unused} 个端点
- 💡 **建议**: {'大量使用，核心模块' if learning_used > 5 else '使用较少'}

### 合并可行性分析
"""

    if homework_unused > homework_used / 2:
        report += "- ⚠️ Homework模块有较多未使用端点，可考虑清理后再合并\n"

    report += "\n---\n\n## 📋 下一步行动\n\n"
    report += """
1. **立即处理**: 检查"前端调用但后端未定义"的端点
2. **本周处理**: 与产品确认"未使用端点"的状态
3. **规划处理**: 
   - 为计划功能添加 TODO 注释
   - 为废弃功能添加 @deprecated 注释
   - 创建备份分支后删除确认废弃代码

---

**报告生成**: `scripts/compare-api-usage.py`  
**复查周期**: 每季度一次
"""

    return report


def main():
    print("🔍 开始分析API使用情况...\n")

    # 提取数据
    backend = extract_backend_endpoints()
    frontend = extract_miniprogram_calls()

    print(f"\n📈 统计:")
    total_backend = sum(len(eps) for eps in backend.values())
    print(f"   - 后端端点: {total_backend} 个")
    print(f"   - 小程序调用: {len(frontend)} 个")

    # 对比分析
    print("\n🔄 开始对比分析...")
    result = compare_usage(backend, frontend)

    # 生成报告
    report = generate_report(result)

    output_file = Path("docs/operations/api-usage-report.md")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(report, encoding="utf-8")

    print(f"\n✅ 报告已生成: {output_file}")
    print(f"\n📊 快速摘要:")
    print(f"   - ✅ 使用中端点: {len(result['used'])} 个")
    print(f"   - ❌ 未使用端点: {len(result['unused'])} 个")
    print(f"   - ⚠️  匹配问题: {len(result['undefined_frontend'])} 个")

    # 重点提示
    if result["unused"]:
        print(f"\n⚠️  发现 {len(result['unused'])} 个未使用端点，请查看报告进行确认")


if __name__ == "__main__":
    main()
