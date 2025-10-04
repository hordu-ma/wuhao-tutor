#!/usr/bin/env python3
"""
前后端API对齐分析工具 - 安全版本
添加了超时保护、详细日志和错误处理
"""

import json
import re
import signal
from contextlib import contextmanager
from pathlib import Path
from typing import Dict, List, Optional


class TimeoutError(Exception):
    """超时异常"""

    pass


@contextmanager
def timeout(seconds: int):
    """超时上下文管理器"""

    def handler(signum, frame):
        raise TimeoutError(f"操作超时({seconds}秒)")

    # 设置信号处理器
    signal.signal(signal.SIGALRM, handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)


class APIAnalyzer:
    """API分析器 - 增强错误处理版本"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.backend_routes: Dict[str, Dict] = {}
        self.frontend_calls: Dict[str, Dict] = {}
        self.issues: List[Dict] = []
        self.errors: List[str] = []

    def safe_read_file(
        self, file_path: Path, timeout_seconds: int = 5
    ) -> Optional[str]:
        """安全读取文件内容,带超时和错误处理"""
        try:
            print(f"   📖 读取: {file_path.name}...", end=" ", flush=True)

            # 检查文件大小
            file_size = file_path.stat().st_size
            if file_size > 1024 * 1024:  # 1MB
                print(f"⚠️  文件过大 ({file_size / 1024:.1f}KB), 跳过")
                self.errors.append(f"文件过大: {file_path}")
                return None

            with timeout(timeout_seconds):
                content = file_path.read_text(encoding="utf-8")
                print(f"✓ ({len(content)} 字符)")
                return content

        except TimeoutError as e:
            print(f"⏱️  超时")
            self.errors.append(f"读取超时: {file_path} - {e}")
            return None
        except UnicodeDecodeError:
            print(f"⚠️  编码错误")
            self.errors.append(f"编码错误: {file_path}")
            return None
        except Exception as e:
            print(f"❌ {type(e).__name__}: {e}")
            self.errors.append(f"读取失败: {file_path} - {e}")
            return None

    def analyze_backend_routes(self):
        """分析后端路由定义"""
        print("📊 分析后端API路由...")

        # 首先分析 api.py 获取各模块的prefix
        api_file = self.project_root / "src" / "api" / "v1" / "api.py"
        if not api_file.exists():
            print(f"❌ API路由文件不存在: {api_file}")
            return

        module_prefixes = self._parse_api_router_file(api_file)
        print(f"   找到 {len(module_prefixes)} 个模块前缀")

        # 分析所有endpoint文件
        endpoints_dir = self.project_root / "src" / "api" / "v1" / "endpoints"
        if not endpoints_dir.exists():
            print(f"❌ 后端endpoints目录不存在: {endpoints_dir}")
            return

        py_files = list(endpoints_dir.glob("*.py"))
        print(f"   准备分析 {len(py_files)} 个Python文件...")

        for i, py_file in enumerate(py_files, 1):
            if py_file.name.startswith("_"):
                print(f"   [{i}/{len(py_files)}] 跳过: {py_file.name}")
                continue

            print(f"   [{i}/{len(py_files)}] 处理: {py_file.name}")
            module_name = py_file.stem
            module_prefix = module_prefixes.get(module_name, "")
            self._parse_backend_file(py_file, module_prefix)

        print(f"✅ 找到 {len(self.backend_routes)} 个后端路由")

    def _parse_api_router_file(self, file_path: Path) -> Dict[str, str]:
        """解析 api.py 文件获取各模块的 prefix"""
        content = self.safe_read_file(file_path)
        if not content:
            return {}

        module_prefixes = {}

        # 匹配 include_router 调用，提取模块名和 prefix
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
        content = self.safe_read_file(file_path)
        if not content:
            return

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
        route_count = 0
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
            route_count += 1

        if route_count > 0:
            print(f"      → 找到 {route_count} 个路由")

    def analyze_frontend_calls(self):
        """分析前端API调用"""
        print("\n📊 分析前端API调用...")

        # 分析frontend/src/api目录
        frontend_api_dir = self.project_root / "frontend" / "src" / "api"
        if not frontend_api_dir.exists():
            print(f"❌ 前端API目录不存在: {frontend_api_dir}")
            return

        ts_files = [
            f
            for f in frontend_api_dir.glob("*.ts")
            if f.name not in ["index.ts", "types.ts"]
        ]
        print(f"   准备分析 {len(ts_files)} 个TypeScript文件...")

        for i, ts_file in enumerate(ts_files, 1):
            print(f"   [{i}/{len(ts_files)}] 处理: {ts_file.name}")
            self._parse_frontend_file(ts_file)

        print(f"✅ 找到 {len(self.frontend_calls)} 个前端API调用")

    def _parse_frontend_file(self, file_path: Path):
        """解析前端TypeScript文件中的API调用"""
        content = self.safe_read_file(file_path)
        if not content:
            return

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
        http_pattern = r'http\.(get|post|put|delete|patch)<[^>]*>\s*\(\s*`\$\{API_PREFIX\}([^`]*)`|http\.(get|post|put|delete|patch)<[^>]*>\s*\(\s*`\$\{[^}]+\}([^`]*)`|http\.(get|post|put|delete|patch)<[^>]*>\s*\(\s*["\']([^"\']*)["\']'

        call_count = 0
        for match in re.finditer(http_pattern, content):
            # 提取method和path
            if match.group(1):  # ${API_PREFIX}模式
                method = match.group(1).upper()
                path = api_prefix + match.group(2)
            elif match.group(3):  # ${其他变量}模式
                method = match.group(3).upper()
                path = match.group(4)
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
            call_count += 1

        if call_count > 0:
            print(f"      → 找到 {call_count} 个API调用")

    def compare_apis(self):
        """比较前后端API差异"""
        print("\n🔍 比较前后端API差异...\n")

        backend_keys = set(self.backend_routes.keys())
        frontend_keys = set(self.frontend_calls.keys())

        # 1. 前端调用但后端不存在
        missing_backend = frontend_keys - backend_keys
        if missing_backend:
            print(f"❌ 前端调用但后端不存在的API ({len(missing_backend)} 个):")
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
            print(f"⚠️  后端存在但前端未调用的API ({len(missing_frontend)} 个):")
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

    def _check_path_params(self):
        """检查路径参数是否匹配"""
        mismatch_count = 0
        for frontend_key in self.frontend_calls.keys():
            method = self.frontend_calls[frontend_key]["method"]
            fe_path = self.frontend_calls[frontend_key]["path"]

            for backend_key in self.backend_routes.keys():
                if not backend_key.startswith(method):
                    continue

                be_path = self.backend_routes[backend_key]["path"]

                if self._paths_similar(fe_path, be_path):
                    if fe_path != be_path:
                        if mismatch_count == 0:
                            print("⚠️  路径参数格式可能不匹配:")
                        print(f"   前端: {frontend_key}")
                        print(f"   后端: {backend_key}")
                        self.issues.append(
                            {
                                "type": "path_mismatch",
                                "frontend": frontend_key,
                                "backend": backend_key,
                            }
                        )
                        mismatch_count += 1

        if mismatch_count > 0:
            print()

    def _paths_similar(self, path1: str, path2: str) -> bool:
        """判断两个路径是否相似（忽略参数名差异）"""
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

        if self.errors:
            print(f"   - 处理错误数量: {len(self.errors)}")

        if self.issues:
            print("\n🔧 需要修复的问题:")
            issue_types = {}
            for issue in self.issues:
                issue_type = issue["type"]
                issue_types[issue_type] = issue_types.get(issue_type, 0) + 1

            for issue_type, count in issue_types.items():
                print(f"   - {issue_type}: {count} 个")

        if self.errors:
            print("\n⚠️  处理过程中的错误:")
            for error in self.errors[:10]:  # 只显示前10个
                print(f"   - {error}")
            if len(self.errors) > 10:
                print(f"   ... 还有 {len(self.errors) - 10} 个错误")

        # 保存详细报告
        report_path = self.project_root / "reports" / "api_alignment_report.json"
        report_path.parent.mkdir(exist_ok=True)

        from datetime import datetime

        report = {
            "timestamp": datetime.now().isoformat(),
            "backend_routes": list(self.backend_routes.keys()),
            "frontend_calls": list(self.frontend_calls.keys()),
            "issues": self.issues,
            "errors": self.errors,
            "stats": {
                "backend_count": len(self.backend_routes),
                "frontend_count": len(self.frontend_calls),
                "issue_count": len(self.issues),
                "error_count": len(self.errors),
            },
        }

        report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False))
        print(f"\n💾 详细报告已保存: {report_path}")


def main():
    """主函数"""
    project_root = Path(__file__).parent.parent

    print("🚀 开始分析前后端API对齐情况...\n")
    print(f"项目根目录: {project_root}\n")

    analyzer = APIAnalyzer(project_root)

    try:
        # 分析后端
        with timeout(60):  # 整体超时60秒
            analyzer.analyze_backend_routes()

        # 分析前端
        with timeout(60):
            analyzer.analyze_frontend_calls()

        # 比较差异
        analyzer.compare_apis()

        # 生成报告
        analyzer.generate_report()

        print("\n✅ 分析完成！")

        # 返回退出码
        return 0 if len(analyzer.issues) == 0 else 1

    except TimeoutError as e:
        print(f"\n❌ 分析超时: {e}")
        return 2
    except KeyboardInterrupt:
        print(f"\n⚠️  用户中断")
        return 130
    except Exception as e:
        print(f"\n❌ 分析失败: {type(e).__name__}: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
