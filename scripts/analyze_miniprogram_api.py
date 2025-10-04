#!/usr/bin/env python3
"""
分析微信小程序API调用与后端API的对齐情况
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple


def extract_backend_routes() -> Set[str]:
    """从API对齐报告中提取后端路由"""
    report_path = Path(__file__).parent.parent / "reports" / "api_alignment_report.json"

    with open(report_path) as f:
        report = json.load(f)

    return set(report["backend_routes"])


def extract_miniprogram_api_calls() -> Dict[str, List[Tuple[str, str]]]:
    """从小程序API文件中提取API调用

    Returns:
        Dict[文件名, List[Tuple[端点路径, HTTP方法]]]
    """
    miniprogram_api_dir = Path(__file__).parent.parent / "miniprogram" / "api"
    api_calls = {}

    # 匹配 request.get/post/put/delete/patch 调用
    request_pattern = re.compile(
        r"request\.(get|post|put|delete|patch)\(['\"]([^'\"]+)['\"]"
    )

    for api_file in miniprogram_api_dir.glob("*.js"):
        if api_file.name == "index.js":
            continue

        with open(api_file, encoding="utf-8") as f:
            content = f.read()

        matches = request_pattern.findall(content)
        calls = []

        for method, path in matches:
            # 标准化路径
            normalized_path = path
            if not normalized_path.startswith("/"):
                normalized_path = f"/api/v1/{normalized_path}"
            elif not normalized_path.startswith("/api/v1/"):
                normalized_path = f"/api/v1/{normalized_path.lstrip('/')}"

            calls.append((normalized_path, method.upper()))

        if calls:
            api_calls[api_file.name] = calls

    return api_calls


def normalize_route(route: str) -> str:
    """标准化路由，将路径参数替换为占位符"""
    # 替换 UUID 格式的参数
    route = re.sub(r"/[0-9a-f-]{36}", "/{id}", route)
    # 替换其他路径参数
    route = re.sub(r"/\{[^}]+\}", "/{id}", route)
    return route


def check_api_alignment(
    backend_routes: Set[str], miniprogram_calls: Dict[str, List[Tuple[str, str]]]
) -> Dict:
    """检查API对齐情况"""

    # 将后端路由转换为标准格式
    backend_endpoints = {}
    for route in backend_routes:
        parts = route.split(" ", 1)
        if len(parts) == 2:
            method, path = parts
            normalized = normalize_route(path)
            key = f"{method} {normalized}"
            backend_endpoints[key] = path

    # 分析小程序调用
    issues = []
    warnings = []
    all_miniprogram_calls = set()

    for filename, calls in miniprogram_calls.items():
        for path, method in calls:
            normalized = normalize_route(path)
            key = f"{method} {normalized}"
            all_miniprogram_calls.add(key)

            if key not in backend_endpoints:
                issues.append(
                    {
                        "file": filename,
                        "method": method,
                        "path": path,
                        "normalized": normalized,
                        "issue": "后端不存在对应的API端点",
                    }
                )

    # 检查未使用的后端API
    unused_backend_apis = []
    for key, path in backend_endpoints.items():
        if key not in all_miniprogram_calls:
            # 排除一些明确只用于web前端的API
            method = key.split(" ")[0]
            if not any(skip in path for skip in ["/health", "/auth/", "/files/"]):
                warnings.append(
                    {"endpoint": f"{method} {path}", "warning": "小程序未调用此后端API"}
                )

    # 统计
    total_backend = len(backend_endpoints)
    total_miniprogram = len(all_miniprogram_calls)
    matched = total_miniprogram - len(issues)

    return {
        "timestamp": "2025-10-04",
        "backend_endpoints_count": total_backend,
        "miniprogram_calls_count": total_miniprogram,
        "matched_count": matched,
        "issues": issues,
        "warnings": warnings,
        "miniprogram_api_calls": {
            filename: [f"{method} {path}" for path, method in calls]
            for filename, calls in miniprogram_calls.items()
        },
        "summary": {
            "alignment_rate": (
                f"{(matched / total_miniprogram * 100):.1f}%"
                if total_miniprogram > 0
                else "N/A"
            ),
            "issue_count": len(issues),
            "warning_count": len(warnings),
            "status": "✅ 完全对齐" if len(issues) == 0 else "⚠️ 存在问题",
        },
    }


def main():
    """主函数"""
    print("=" * 80)
    print("微信小程序 API 对齐检查")
    print("=" * 80)

    # 提取后端路由
    print("\n📋 提取后端API路由...")
    backend_routes = extract_backend_routes()
    print(f"   发现 {len(backend_routes)} 个后端API端点")

    # 提取小程序API调用
    print("\n📱 分析小程序API调用...")
    miniprogram_calls = extract_miniprogram_api_calls()
    total_calls = sum(len(calls) for calls in miniprogram_calls.values())
    print(f"   发现 {total_calls} 个API调用，分布在 {len(miniprogram_calls)} 个文件中")

    # 检查对齐情况
    print("\n🔍 检查API对齐情况...")
    result = check_api_alignment(backend_routes, miniprogram_calls)

    # 输出结果
    print("\n" + "=" * 80)
    print("📊 检查结果")
    print("=" * 80)
    print(f"\n状态: {result['summary']['status']}")
    print(f"对齐率: {result['summary']['alignment_rate']}")
    print(f"问题数: {result['summary']['issue_count']}")
    print(f"警告数: {result['summary']['warning_count']}")

    if result["issues"]:
        print("\n❌ 发现的问题:")
        for i, issue in enumerate(result["issues"], 1):
            print(f"\n  {i}. {issue['file']}")
            print(f"     {issue['method']} {issue['path']}")
            print(f"     问题: {issue['issue']}")

    if result["warnings"]:
        print(f"\n⚠️  发现 {len(result['warnings'])} 个未被小程序使用的后端API")
        print("   (可能由Web前端使用，仅供参考)")

    # 保存报告
    output_path = (
        Path(__file__).parent.parent
        / "reports"
        / "miniprogram_api_alignment_report.json"
    )
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"\n✅ 详细报告已保存至: {output_path}")
    print("\n" + "=" * 80)

    return 0 if len(result["issues"]) == 0 else 1


if __name__ == "__main__":
    exit(main())
