#!/usr/bin/env python3
"""
前后端API对齐分析工具 - 修复版本
解决VS Code终端输出缓冲问题
"""

import json
import re
import sys
from pathlib import Path
from typing import Dict, List


# 关键修复: 强制所有输出立即刷新
def print_flush(msg: str = ""):
    """打印并立即刷新输出"""
    print(msg, flush=True)


class APIAnalyzer:
    """API分析器"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.backend_routes: Dict[str, Dict] = {}
        self.frontend_calls: Dict[str, Dict] = {}
        self.issues: List[Dict] = []

    def analyze_backend_routes(self):
        """分析后端路由"""
        print_flush("🔍 分析后端API路由...")

        api_dir = self.project_root / "src" / "api" / "v1" / "endpoints"
        if not api_dir.exists():
            print_flush(f"❌ 后端API目录不存在: {api_dir}")
            return

        python_files = list(api_dir.glob("*.py"))
        print_flush(f"   找到 {len(python_files)} 个后端文件")

        for file_path in python_files:
            if file_path.name.startswith("_"):
                continue

            print_flush(f"   - 处理: {file_path.name}")
            try:
                content = file_path.read_text(encoding="utf-8")
                self._extract_routes(content, file_path.stem)
            except Exception as e:
                print_flush(f"     ⚠️  读取失败: {e}")

        print_flush(f"✓ 后端API数量: {len(self.backend_routes)}")

    def _extract_routes(self, content: str, module: str):
        """提取路由定义"""
        # 匹配 @router.get/post/put/delete/patch
        pattern = r'@router\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']\)'

        for match in re.finditer(pattern, content):
            method = match.group(1).upper()
            path = match.group(2)

            # 规范化路径
            if not path.startswith("/"):
                path = "/" + path

            full_path = f"/api/v1/{module}{path}"
            key = f"{method} {full_path}"

            self.backend_routes[key] = {
                "method": method,
                "path": full_path,
                "module": module,
            }

    def analyze_frontend_calls(self):
        """分析前端API调用"""
        print_flush("\n🔍 分析前端API调用...")

        frontend_dir = self.project_root / "frontend" / "src"
        miniprogram_dir = self.project_root / "miniprogram"

        # 分析Vue前端
        if frontend_dir.exists():
            print_flush("   处理Web前端...")
            self._scan_directory(frontend_dir, "web")

        # 分析小程序
        if miniprogram_dir.exists():
            print_flush("   处理小程序...")
            self._scan_directory(miniprogram_dir, "miniprogram")

        print_flush(f"✓ 前端API调用数量: {len(self.frontend_calls)}")

    def _scan_directory(self, directory: Path, source: str):
        """扫描目录中的API调用"""
        extensions = {".ts", ".js", ".vue"}
        files = [f for f in directory.rglob("*") if f.suffix in extensions]

        print_flush(f"     找到 {len(files)} 个源文件")

        for file_path in files[:100]:  # 限制文件数量避免太慢
            try:
                content = file_path.read_text(encoding="utf-8")
                self._extract_api_calls(content, source, file_path)
            except Exception as e:
                # 忽略读取错误
                pass

    def _extract_api_calls(self, content: str, source: str, file_path: Path):
        """提取API调用"""
        # 匹配各种API调用模式
        patterns = [
            r'(get|post|put|delete|patch)\(["\']([^"\']+)["\']\)',  # axios, fetch
            r'request\(["\']([^"\']+)["\'],\s*["\']?(GET|POST|PUT|DELETE|PATCH)["\']?',
            r'url:\s*["\']([^"\']+)["\'],\s*method:\s*["\']?(GET|POST|PUT|DELETE|PATCH)["\']?',
        ]

        for pattern in patterns:
            for match in re.finditer(pattern, content, re.IGNORECASE):
                try:
                    if len(match.groups()) == 2:
                        method_or_path = match.group(1)
                        path_or_method = match.group(2)

                        # 判断哪个是method,哪个是path
                        if method_or_path.upper() in [
                            "GET",
                            "POST",
                            "PUT",
                            "DELETE",
                            "PATCH",
                        ]:
                            method = method_or_path.upper()
                            path = path_or_method
                        else:
                            method = path_or_method.upper()
                            path = method_or_path

                        # 规范化路径
                        if path.startswith("/api/v1/"):
                            key = f"{method} {path}"
                            self.frontend_calls[key] = {
                                "method": method,
                                "path": path,
                                "source": source,
                                "file": str(file_path.relative_to(self.project_root)),
                            }
                except:
                    continue

    def compare_apis(self):
        """对比前后端API"""
        print_flush("\n🔍 对比前后端API...")

        # 检查前端调用的API是否存在于后端
        for key, call in self.frontend_calls.items():
            if key not in self.backend_routes:
                # 检查是否是路径参数不匹配
                if self._check_path_mismatch(call):
                    continue

                self.issues.append(
                    {
                        "type": "missing_backend",
                        "severity": "error",
                        "frontend": call,
                        "message": f"前端调用的API在后端不存在: {key}",
                    }
                )

        # 检查路径参数名称不一致
        self._check_parameter_mismatches()

        print_flush(f"✓ 发现问题数量: {len(self.issues)}")

    def _check_path_mismatch(self, call: Dict) -> bool:
        """检查路径参数不匹配"""
        method = call["method"]
        path = call["path"]

        # 查找可能匹配的后端路由(忽略参数名称)
        pattern = re.sub(r"\{[^}]+\}", r"\\{[^}]+\\}", path)

        for backend_key in self.backend_routes:
            if backend_key.startswith(f"{method} "):
                backend_path = backend_key.split(" ", 1)[1]
                backend_pattern = re.sub(r"\{[^}]+\}", r"\\{[^}]+\\}", backend_path)

                if re.match(f"^{backend_pattern}$", path) or re.match(
                    f"^{pattern}$", backend_path
                ):
                    return True

        return False

    def _check_parameter_mismatches(self):
        """检查路径参数名称不一致"""
        for frontend_key, frontend_call in self.frontend_calls.items():
            method = frontend_call["method"]
            frontend_path = frontend_call["path"]

            # 提取前端路径参数
            frontend_params = re.findall(r"\{([^}]+)\}", frontend_path)

            for backend_key, backend_route in self.backend_routes.items():
                if not backend_key.startswith(f"{method} "):
                    continue

                backend_path = backend_route["path"]

                # 检查路径结构是否相似
                frontend_pattern = re.sub(r"\{[^}]+\}", "{}", frontend_path)
                backend_pattern = re.sub(r"\{[^}]+\}", "{}", backend_path)

                if frontend_pattern == backend_pattern:
                    # 提取后端路径参数
                    backend_params = re.findall(r"\{([^}]+)\}", backend_path)

                    if frontend_params != backend_params:
                        self.issues.append(
                            {
                                "type": "path_mismatch",
                                "severity": "warning",
                                "frontend": frontend_call,
                                "backend": backend_route,
                                "frontend_params": frontend_params,
                                "backend_params": backend_params,
                                "message": f"路径参数名称不一致: {frontend_key} vs {backend_key}",
                            }
                        )

    def generate_report(self) -> Dict:
        """生成分析报告"""
        print_flush("\n📊 生成报告...")

        # 按类型统计问题
        issues_by_type = {}
        for issue in self.issues:
            issue_type = issue["type"]
            if issue_type not in issues_by_type:
                issues_by_type[issue_type] = []
            issues_by_type[issue_type].append(issue)

        report = {
            "summary": {
                "total_backend_routes": len(self.backend_routes),
                "total_frontend_calls": len(self.frontend_calls),
                "total_issues": len(self.issues),
                "issues_by_type": {k: len(v) for k, v in issues_by_type.items()},
            },
            "backend_routes": list(self.backend_routes.keys()),
            "frontend_calls": list(self.frontend_calls.keys()),
            "issues": self.issues,
            "issues_by_type": issues_by_type,
        }

        return report

    def print_summary(self, report: Dict):
        """打印摘要"""
        print_flush("\n" + "=" * 60)
        print_flush("📊 API 对齐分析报告")
        print_flush("=" * 60)

        summary = report["summary"]
        print_flush(f"\n📈 统计信息:")
        print_flush(f"  - 后端API数量: {summary['total_backend_routes']}")
        print_flush(f"  - 前端调用数量: {summary['total_frontend_calls']}")
        print_flush(f"  - 发现问题数量: {summary['total_issues']}")

        if summary["total_issues"] > 0:
            print_flush(f"\n🔧 需要修复的问题:")
            for issue_type, count in summary["issues_by_type"].items():
                print_flush(f"  - {issue_type}: {count} 个")

        print_flush("\n💾 详细报告已保存: reports/api_alignment_report.json")
        print_flush("\n✅ 分析完成!")


def main():
    """主函数"""
    print_flush("=" * 60)
    print_flush("🚀 前后端API对齐分析工具")
    print_flush("=" * 60)

    # 获取项目根目录
    project_root = Path(__file__).parent.parent
    print_flush(f"\n📁 项目目录: {project_root}")

    # 创建分析器
    analyzer = APIAnalyzer(project_root)

    # 执行分析
    analyzer.analyze_backend_routes()
    analyzer.analyze_frontend_calls()
    analyzer.compare_apis()

    # 生成报告
    report = analyzer.generate_report()

    # 保存报告
    reports_dir = project_root / "reports"
    reports_dir.mkdir(exist_ok=True)
    report_path = reports_dir / "api_alignment_report.json"

    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # 打印摘要
    analyzer.print_summary(report)

    # 强制刷新输出
    sys.stdout.flush()
    sys.stderr.flush()


if __name__ == "__main__":
    main()
