#!/usr/bin/env python3
"""
快速检查 API 对齐情况 - 直接返回结果，不使用终端
"""
import json
import subprocess
import sys
from pathlib import Path


def main():
    """运行 API 分析并立即返回结果"""
    print("🔍 开始检查 API 对齐情况...", flush=True)

    # 获取项目根目录
    project_root = Path(__file__).parent.parent
    script_path = project_root / "scripts" / "analyze_api_diff_safe.py"
    report_path = project_root / "reports" / "api_alignment_report.json"

    # 直接运行脚本（不通过 uv，避免缓冲问题）
    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=project_root,
        capture_output=True,
        text=True,
        timeout=30,
    )

    # 打印输出
    if result.stdout:
        print(result.stdout, flush=True)
    if result.stderr:
        print(result.stderr, file=sys.stderr, flush=True)

    # 读取并显示报告
    if report_path.exists():
        with open(report_path, "r", encoding="utf-8") as f:
            report = json.load(f)

        print("\n" + "=" * 60, flush=True)
        print("📊 API 对齐检查结果", flush=True)
        print("=" * 60, flush=True)

        issues = report.get("issues", [])
        print(f"\n发现问题数量: {len(issues)}", flush=True)

        if issues:
            # 按类型分组
            by_type = {}
            for issue in issues:
                issue_type = issue.get("type", "unknown")
                if issue_type not in by_type:
                    by_type[issue_type] = []
                by_type[issue_type].append(issue)

            print("\n🔧 需要修复的问题:", flush=True)
            for issue_type, type_issues in by_type.items():
                print(f"  - {issue_type}: {len(type_issues)} 个", flush=True)

            print("\n详细列表:", flush=True)
            for i, issue in enumerate(issues, 1):
                print(
                    f"\n{i}. [{issue.get('type')}] {issue.get('frontend_path')}",
                    flush=True,
                )
                if issue.get("details"):
                    print(f"   详情: {issue.get('details')}", flush=True)
        else:
            print("\n✅ 所有 API 都已对齐！", flush=True)

        print(f"\n详细报告: {report_path}", flush=True)
        print("=" * 60, flush=True)

    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
