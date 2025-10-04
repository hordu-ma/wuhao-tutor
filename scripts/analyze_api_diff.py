#!/usr/bin/env python3
"""
前后端API对齐分析工具
直接分析代码，不需要运行服务器
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple


class APIAnalyzer:
    """API分析器"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.backend_routes: Dict[str, Dict] = {}
        self.frontend_calls: Dict[str, Dict] = {}
        self.issues: List[Dict] = []

    def analyze_backend_routes(self):
        """分析后端路由定义"""
        print("📊 分析后端API路由...")

        # 首先分析 api.py 获取各模块的prefix
        api_file = self.project_root / "src" / "api" / "v1" / "api.py"
        module_prefixes = self._parse_api_router_file(api_file)

        # 分析所有endpoint文件
        endpoints_dir = self.project_root / "src" / "api" / "v1" / "endpoints"
        if not endpoints_dir.exists():
            print(f"❌ 后端endpoints目录不存在: {endpoints_dir}")
            return

        for py_file in endpoints_dir.glob("*.py"):
            if py_file.name.startswith("_"):
                continue
            module_name = py_file.stem
            module_prefix = module_prefixes.get(module_name, "")
            self._parse_backend_file(py_file, module_prefix)

        print(f"✅ 找到 {len(self.backend_routes)} 个后端路由")

    def _parse_api_router_file(self, file_path: Path) -> Dict[str, str]:
        """解析 api.py 文件获取各模块的 prefix"""
        content = file_path.read_text()
        module_prefixes = {}

        # 匹配 include_router 调用，提取模块名和 prefix
        # 例如: api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
        pattern = r'api_router\.include_router\(\s*(\w+)\.router\s*,\s*prefix=["\'](/[^"\']*)["\']'

        for match in re.finditer(pattern, content):
            module_name = match.group(1)
            prefix = match.group(2)
            module_prefixes[module_name] = prefix

        # 对于没有 prefix 的模块，设置为空字符串
        no_prefix_pattern = r"api_router\.include_router\(\s*(\w+)\.router\s*,\s*tags="
        for match in re.finditer(no_prefix_pattern, content):
            module_name = match.group(1)
            if module_name not in module_prefixes:
                module_prefixes[module_name] = ""

        return module_prefixes

    def _parse_backend_file(self, file_path: Path, module_prefix: str = ""):
        """解析后端Python文件中的路由"""
        content = file_path.read_text()

        # 提取router定义中的prefix（如果有）
        router_prefix = ""
        prefix_match = re.search(
            r'router\s*=\s*APIRouter\([^)]*prefix=["\'](/[^"\']*)["\']', content
        )
        if prefix_match:
            router_prefix = prefix_match.group(1)

        # 提取所有@router装饰的路由
        route_pattern = (
            r'@router\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']*)["\']'
        )
        for match in re.finditer(route_pattern, content, re.MULTILINE):
            method = match.group(1).upper()
            path = match.group(2)

            # 组合完整路径: /api/v1 + module_prefix + router_prefix + path
            full_path = (
                "/api/v1" + module_prefix + router_prefix + (path if path else "")
            )

            route_key = f"{method} {full_path}"
            self.backend_routes[route_key] = {
                "method": method,
                "path": full_path,
                "file": file_path.name,
            }

    def analyze_frontend_calls(self):
        """分析前端API调用"""
        print("\n📊 分析前端API调用...")

        # 分析frontend/src/api目录
        frontend_api_dir = self.project_root / "frontend" / "src" / "api"
        if not frontend_api_dir.exists():
            print(f"❌ 前端API目录不存在: {frontend_api_dir}")
            return

        for ts_file in frontend_api_dir.glob("*.ts"):
            if ts_file.name in ["index.ts", "types.ts"]:
                continue
            self._parse_frontend_file(ts_file)

        print(f"✅ 找到 {len(self.frontend_calls)} 个前端API调用")

    def _parse_frontend_file(self, file_path: Path):
        """解析前端TypeScript文件中的API调用"""
        content = file_path.read_text()

        # 提取baseURL定义
        base_url = "/api/v1"
        base_match = re.search(r'baseURL\s*=\s*["\']([^"\']*)["\']', content)
        if base_match:
            base_url = base_match.group(1)

        # 提取API_PREFIX常量定义
        api_prefix = ""
        prefix_match = re.search(
            r'const\s+API_PREFIX\s*=\s*["\']([^"\']*)["\']', content
        )
        if prefix_match:
            api_prefix = prefix_match.group(1)

        # 提取所有http.get/post/put/delete调用
        # 匹配模板字符串: http.get<T>(`${API_PREFIX}/path`)
        # 匹配普通字符串: http.get<T>('/path')
        http_pattern = r'http\.(get|post|put|delete|patch)<[^>]*>\s*\(\s*`\$\{API_PREFIX\}([^`]*)`|http\.(get|post|put|delete|patch)<[^>]*>\s*\(\s*`\$\{[^}]+\}([^`]*)`|http\.(get|post|put|delete|patch)<[^>]*>\s*\(\s*["\']([^"\']*)["\']'

        for match in re.finditer(http_pattern, content):
            # 提取method和path
            if match.group(1):  # ${API_PREFIX}模式
                method = match.group(1).upper()
                path = api_prefix + match.group(2)
            elif match.group(3):  # ${其他变量}模式
                method = match.group(3).upper()
                path = match.group(4)
                # 如果路径不是绝对路径，使用base_url
                if not path.startswith("/api"):
                    path = base_url + path
            else:  # 普通字符串模式
                method = match.group(5).upper()
                path = match.group(6)
                if not path.startswith("/api"):
                    path = base_url + path

            # 处理路径中的变量（如 ${sessionId} -> {id}）
            path = re.sub(r"\$\{[^}]+\}", "{id}", path)

            # 组合完整路径
            full_path = path if path.startswith("/api") else base_url + path

            call_key = f"{method} {full_path}"
            self.frontend_calls[call_key] = {
                "method": method,
                "path": full_path,
                "file": file_path.name,
            }

    def compare_apis(self):
        """比较前后端API差异"""
        print("\n🔍 比较前后端API差异...\n")

        backend_keys = set(self.backend_routes.keys())
        frontend_keys = set(self.frontend_calls.keys())

        # 1. 前端调用但后端不存在
        missing_backend = frontend_keys - backend_keys
        if missing_backend:
            print("❌ 前端调用但后端不存在的API:")
            for key in sorted(missing_backend):
                call_info = self.frontend_calls[key]
                print(f"   - {key}")
                print(f"     文件: {call_info['file']}")
                self.issues.append(
                    {
                        "type": "missing_backend",
                        "api": key,
                        "frontend_file": call_info["file"],
                    }
                )
            print()

        # 2. 后端存在但前端未调用
        missing_frontend = backend_keys - frontend_keys
        if missing_frontend:
            print("⚠️  后端存在但前端未调用的API:")
            for key in sorted(missing_frontend):
                route_info = self.backend_routes[key]
                print(f"   - {key}")
                print(f"     文件: {route_info['file']}")
            print()

        # 3. 路径参数不匹配检查
        self._check_path_params()

        # 4. 输出匹配的API
        matching = backend_keys & frontend_keys
        if matching:
            print(f"✅ 前后端匹配的API: {len(matching)} 个")
            for key in sorted(matching):
                print(f"   - {key}")

    def _check_path_params(self):
        """检查路径参数是否匹配"""
        print("🔍 检查路径参数匹配...\n")

        for frontend_key in self.frontend_calls.keys():
            # 查找可能匹配的后端路由（方法相同，路径相似）
            method = self.frontend_calls[frontend_key]["method"]
            fe_path = self.frontend_calls[frontend_key]["path"]

            for backend_key in self.backend_routes.keys():
                if not backend_key.startswith(method):
                    continue

                be_path = self.backend_routes[backend_key]["path"]

                # 检查路径参数格式差异
                # 前端: /api/v1/homework/{id}
                # 后端: /homework/{homework_id}
                if self._paths_similar(fe_path, be_path):
                    if fe_path != be_path:
                        print(f"⚠️  路径参数格式可能不匹配:")
                        print(f"   前端: {frontend_key}")
                        print(f"   后端: {backend_key}")
                        self.issues.append(
                            {
                                "type": "path_mismatch",
                                "frontend": frontend_key,
                                "backend": backend_key,
                            }
                        )
                        print()

    def _paths_similar(self, path1: str, path2: str) -> bool:
        """判断两个路径是否相似（忽略参数名差异）"""
        # 替换所有参数为通配符
        p1 = re.sub(r"\{[^}]+\}", "*", path1)
        p2 = re.sub(r"\{[^}]+\}", "*", path2)
        return p1.endswith(p2) or p2.endswith(p1)

    def generate_report(self):
        """生成分析报告"""
        print("\n" + "=" * 60)
        print("📝 API对齐分析报告")
        print("=" * 60)

        print(f"\n📊 统计:")
        print(f"   - 后端路由数量: {len(self.backend_routes)}")
        print(f"   - 前端调用数量: {len(self.frontend_calls)}")
        print(f"   - 发现问题数量: {len(self.issues)}")

        if self.issues:
            print("\n🔧 需要修复的问题:")
            issue_types = {}
            for issue in self.issues:
                issue_type = issue["type"]
                issue_types[issue_type] = issue_types.get(issue_type, 0) + 1

            for issue_type, count in issue_types.items():
                print(f"   - {issue_type}: {count} 个")

        # 保存详细报告
        report_path = self.project_root / "reports" / "api_alignment_report.json"
        report_path.parent.mkdir(exist_ok=True)

        report = {
            "timestamp": "2025-10-04T00:00:00Z",
            "backend_routes": list(self.backend_routes.keys()),
            "frontend_calls": list(self.frontend_calls.keys()),
            "issues": self.issues,
            "stats": {
                "backend_count": len(self.backend_routes),
                "frontend_count": len(self.frontend_calls),
                "issue_count": len(self.issues),
            },
        }

        report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False))
        print(f"\n💾 详细报告已保存: {report_path}")


def main():
    """主函数"""
    project_root = Path(__file__).parent.parent

    print("🚀 开始分析前后端API对齐情况...\n")

    analyzer = APIAnalyzer(project_root)

    # 分析后端
    analyzer.analyze_backend_routes()

    # 分析前端
    analyzer.analyze_frontend_calls()

    # 比较差异
    analyzer.compare_apis()

    # 生成报告
    analyzer.generate_report()

    print("\n✅ 分析完成！")


if __name__ == "__main__":
    main()
