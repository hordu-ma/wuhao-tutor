#!/usr/bin/env python3
"""
后端对接完整性检查工具
检查数据库、AI服务、内部各层之间的对接情况
"""

import ast
import json
import os
import re
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set, Tuple


class BackendAlignmentAnalyzer:
    """后端对接分析器"""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.src_path = self.project_root / "src"

        # 存储分析结果
        self.models: Dict[str, Dict] = {}
        self.repositories: Dict[str, Dict] = {}
        self.services: Dict[str, Dict] = {}
        self.api_endpoints: Dict[str, Dict] = {}
        self.migrations: List[str] = []

        # 对接问题
        self.issues: Dict[str, List[str]] = defaultdict(list)

    def analyze(self):
        """执行完整分析"""
        print("🔍 开始后端对接完整性检查...\n")

        # 1. 分析数据模型
        self.analyze_models()

        # 2. 分析Repository层
        self.analyze_repositories()

        # 3. 分析Service层
        self.analyze_services()

        # 4. 分析API层
        self.analyze_api_endpoints()

        # 5. 分析数据库迁移
        self.analyze_migrations()

        # 6. 检查AI服务对接
        self.analyze_ai_service()

        # 7. 检查配置完整性
        self.analyze_configuration()

        # 8. 生成报告
        self.generate_report()

    def analyze_models(self):
        """分析数据模型"""
        print("📊 分析数据模型...")
        models_path = self.src_path / "models"

        for py_file in models_path.glob("*.py"):
            if py_file.name.startswith("_"):
                continue

            content = py_file.read_text(encoding="utf-8")

            # 查找模型类定义
            class_pattern = r"class\s+(\w+)\(BaseModel\):"
            matches = re.finditer(class_pattern, content)

            for match in matches:
                model_name = match.group(1)
                self.models[model_name] = {
                    "file": py_file.name,
                    "table_name": self._extract_table_name(content, model_name),
                    "relationships": self._extract_relationships(content, model_name),
                }

        print(f"   找到 {len(self.models)} 个模型\n")

    def analyze_repositories(self):
        """分析Repository层"""
        print("🗄️  分析Repository层...")
        repo_path = self.src_path / "repositories"

        for py_file in repo_path.glob("*.py"):
            if py_file.name.startswith("_") or py_file.name == "base_repository.py":
                continue

            content = py_file.read_text(encoding="utf-8")

            # 查找Repository类
            class_pattern = r"class\s+(\w+Repository)"
            matches = re.finditer(class_pattern, content)

            for match in matches:
                repo_name = match.group(1)
                self.repositories[repo_name] = {
                    "file": py_file.name,
                    "model": self._extract_repo_model(content, repo_name),
                    "methods": self._extract_repo_methods(content, repo_name),
                }

        print(f"   找到 {len(self.repositories)} 个Repository\n")

    def analyze_services(self):
        """分析Service层"""
        print("⚙️  分析Service层...")
        service_path = self.src_path / "services"

        for py_file in service_path.glob("*.py"):
            if py_file.name.startswith("_"):
                continue

            content = py_file.read_text(encoding="utf-8")

            # 查找Service类
            class_pattern = r"class\s+(\w+Service)"
            matches = re.finditer(class_pattern, content)

            for match in matches:
                service_name = match.group(1)
                self.services[service_name] = {
                    "file": py_file.name,
                    "repositories": self._extract_service_repos(content),
                    "methods": self._extract_service_methods(content, service_name),
                }

        print(f"   找到 {len(self.services)} 个Service\n")

    def analyze_api_endpoints(self):
        """分析API端点"""
        print("🌐 分析API端点...")
        api_path = self.src_path / "api" / "v1"

        if not api_path.exists():
            print("   ⚠️  未找到API目录\n")
            return

        for py_file in api_path.glob("*.py"):
            if py_file.name.startswith("_"):
                continue

            content = py_file.read_text(encoding="utf-8")

            # 查找路由定义
            route_pattern = r'@router\.(get|post|put|delete|patch)\(["\']([^"\']+)'
            matches = re.finditer(route_pattern, content)

            for match in matches:
                method, path = match.group(1), match.group(2)
                endpoint_key = f"{method.upper()} {path}"
                self.api_endpoints[endpoint_key] = {
                    "file": py_file.name,
                    "method": method.upper(),
                    "path": path,
                }

        print(f"   找到 {len(self.api_endpoints)} 个API端点\n")

    def analyze_migrations(self):
        """分析数据库迁移"""
        print("🔄 分析数据库迁移...")
        migrations_path = self.project_root / "alembic" / "versions"

        if not migrations_path.exists():
            self.issues["migrations"].append("未找到迁移目录")
            return

        for py_file in migrations_path.glob("*.py"):
            self.migrations.append(py_file.name)

        print(f"   找到 {len(self.migrations)} 个迁移文件\n")

    def analyze_ai_service(self):
        """分析AI服务对接"""
        print("🤖 分析阿里云百炼AI对接...")

        bailian_file = self.src_path / "services" / "bailian_service.py"
        if not bailian_file.exists():
            self.issues["ai_service"].append("未找到BailianService实现")
            return

        content = bailian_file.read_text(encoding="utf-8")

        # 检查必要的配置项
        required_configs = [
            "DASHSCOPE_API_KEY",
            "BAILIAN_APP_ID",
            "HOMEWORK_CORRECTION_APP_ID",
            "LEARNING_ASSISTANT_APP_ID",
            "KNOWLEDGE_QA_APP_ID",
        ]

        for config in required_configs:
            if config not in content:
                self.issues["ai_service"].append(f"缺少配置项: {config}")

        # 检查API调用方法
        api_methods = re.findall(r"async def (\w+)\(", content)
        print(f"   找到 {len(api_methods)} 个AI服务方法")

        # 检查错误处理
        if "try:" not in content or "except" not in content:
            self.issues["ai_service"].append("缺少错误处理机制")

        # 检查超时设置
        if "timeout" not in content:
            self.issues["ai_service"].append("未设置API调用超时")

        print()

    def analyze_configuration(self):
        """分析配置完整性"""
        print("⚙️  分析配置完整性...")

        config_file = self.src_path / "core" / "config.py"
        if not config_file.exists():
            self.issues["configuration"].append("未找到配置文件")
            return

        content = config_file.read_text(encoding="utf-8")

        # 检查必要的配置组
        required_sections = [
            "DATABASE_URL",
            "REDIS_URL",
            "DASHSCOPE_API_KEY",
            "SECRET_KEY",
            "UPLOAD_DIR",
        ]

        for section in required_sections:
            if section not in content:
                self.issues["configuration"].append(f"缺少配置项: {section}")

        print(f"   配置检查完成\n")

    def check_model_repository_alignment(self):
        """检查Model与Repository对齐"""
        print("🔗 检查Model↔Repository对齐...")

        # 检查每个Model是否有对应的Repository
        models_without_repo = []
        for model_name in self.models.keys():
            expected_repo = f"{model_name}Repository"
            if expected_repo not in self.repositories:
                models_without_repo.append(model_name)

        if models_without_repo:
            self.issues["model_repository"].append(
                f"以下模型缺少Repository: {', '.join(models_without_repo)}"
            )

        # 检查Repository是否引用了正确的Model
        for repo_name, repo_info in self.repositories.items():
            if repo_info["model"]:
                expected_model = repo_name.replace("Repository", "")
                if repo_info["model"] != expected_model:
                    self.issues["model_repository"].append(
                        f"{repo_name} 引用的模型({repo_info['model']})不匹配"
                    )

        print(f"   发现 {len(self.issues['model_repository'])} 个对齐问题\n")

    def check_service_repository_alignment(self):
        """检查Service与Repository对齐"""
        print("🔗 检查Service↔Repository对齐...")

        for service_name, service_info in self.services.items():
            if not service_info["repositories"]:
                self.issues["service_repository"].append(
                    f"{service_name} 未使用任何Repository"
                )

        print(f"   发现 {len(self.issues['service_repository'])} 个对齐问题\n")

    def generate_report(self):
        """生成综合报告"""
        print("\n" + "=" * 60)
        print("📋 后端对接完整性分析报告")
        print("=" * 60 + "\n")

        # 1. 基础统计
        print("📊 基础统计:")
        print(f"   - 数据模型: {len(self.models)} 个")
        print(f"   - Repository: {len(self.repositories)} 个")
        print(f"   - Service: {len(self.services)} 个")
        print(f"   - API端点: {len(self.api_endpoints)} 个")
        print(f"   - 数据库迁移: {len(self.migrations)} 个")
        print()

        # 2. 执行对齐检查
        self.check_model_repository_alignment()
        self.check_service_repository_alignment()

        # 3. 问题汇总
        total_issues = sum(len(issues) for issues in self.issues.values())

        if total_issues == 0:
            print("✅ 未发现对接问题！后端各层对齐状态良好。\n")
        else:
            print(f"⚠️  发现 {total_issues} 个对接问题:\n")

            for category, issues in self.issues.items():
                if issues:
                    print(f"   【{category}】")
                    for issue in issues:
                        print(f"      ❌ {issue}")
                    print()

        # 4. 详细信息
        print("\n" + "-" * 60)
        print("📄 详细信息")
        print("-" * 60 + "\n")

        print(f"数据模型列表 ({len(self.models)}):")
        for model_name, model_info in sorted(self.models.items()):
            print(
                f"   - {model_name} (表: {model_info['table_name']}, 文件: {model_info['file']})"
            )

        print(f"\nRepository列表 ({len(self.repositories)}):")
        for repo_name, repo_info in sorted(self.repositories.items()):
            print(
                f"   - {repo_name} (模型: {repo_info['model']}, 文件: {repo_info['file']})"
            )

        print(f"\nService列表 ({len(self.services)}):")
        for service_name, service_info in sorted(self.services.items()):
            repos = (
                ", ".join(service_info["repositories"])
                if service_info["repositories"]
                else "无"
            )
            print(
                f"   - {service_name} (使用仓储: {repos}, 文件: {service_info['file']})"
            )

        # 5. 生成JSON报告
        report_data = {
            "summary": {
                "models_count": len(self.models),
                "repositories_count": len(self.repositories),
                "services_count": len(self.services),
                "api_endpoints_count": len(self.api_endpoints),
                "migrations_count": len(self.migrations),
                "total_issues": total_issues,
            },
            "models": self.models,
            "repositories": self.repositories,
            "services": self.services,
            "api_endpoints": self.api_endpoints,
            "issues": dict(self.issues),
        }

        report_path = self.project_root / "reports" / "backend_alignment_report.json"
        report_path.parent.mkdir(exist_ok=True)

        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)

        print(f"\n💾 详细报告已保存: {report_path}")

        # 6. 生成Markdown报告
        self.generate_markdown_report()

    def generate_markdown_report(self):
        """生成Markdown格式报告"""
        report_path = self.project_root / "BACKEND_ALIGNMENT_REPORT.md"

        total_issues = sum(len(issues) for issues in self.issues.values())
        status_emoji = "✅" if total_issues == 0 else "⚠️"

        content = f"""# 后端对接完整性分析报告

**生成时间**: {self._get_timestamp()}  
**对齐状态**: {status_emoji} {'完全对齐' if total_issues == 0 else f'发现 {total_issues} 个问题'}

---

## 📊 基础统计

| 类别 | 数量 |
|------|------|
| 数据模型 (Models) | {len(self.models)} |
| 数据仓储 (Repositories) | {len(self.repositories)} |
| 业务服务 (Services) | {len(self.services)} |
| API端点 (Endpoints) | {len(self.api_endpoints)} |
| 数据库迁移 (Migrations) | {len(self.migrations)} |

---

## 🔍 对接检查结果

### 1. 数据库对接 (Models ↔ Database)

"""

        # Models列表
        content += f"**数据模型** ({len(self.models)} 个):\n\n"
        for model_name, model_info in sorted(self.models.items()):
            content += f"- `{model_name}` → 表 `{model_info['table_name']}` (定义于 `{model_info['file']}`)\n"

        content += "\n"

        # Repository列表
        content += f"### 2. Repository层对接 (Models ↔ Repositories)\n\n"
        content += f"**数据仓储** ({len(self.repositories)} 个):\n\n"
        for repo_name, repo_info in sorted(self.repositories.items()):
            content += f"- `{repo_name}` → 模型 `{repo_info['model']}` (定义于 `{repo_info['file']}`)\n"

        content += "\n"

        # Service列表
        content += f"### 3. Service层对接 (Repositories ↔ Services)\n\n"
        content += f"**业务服务** ({len(self.services)} 个):\n\n"
        for service_name, service_info in sorted(self.services.items()):
            repos = (
                ", ".join([f"`{r}`" for r in service_info["repositories"]])
                if service_info["repositories"]
                else "无"
            )
            content += f"- `{service_name}` → 使用仓储: {repos} (定义于 `{service_info['file']}`)\n"

        content += "\n"

        # 问题汇总
        if total_issues > 0:
            content += f"## ⚠️ 发现的问题 ({total_issues} 个)\n\n"

            for category, issues in self.issues.items():
                if issues:
                    content += f"### {category.replace('_', ' ').title()}\n\n"
                    for issue in issues:
                        content += f"- ❌ {issue}\n"
                    content += "\n"
        else:
            content += "## ✅ 未发现问题\n\n所有对接检查通过！\n\n"

        # 建议
        content += """---

## 💡 改进建议

### 立即修复 (P0)
"""

        if self.issues.get("model_repository"):
            content += (
                "1. **补充缺失的Repository**: 为每个Model创建对应的Repository类\n"
            )

        if self.issues.get("ai_service"):
            content += "2. **完善AI服务配置**: 添加缺失的配置项和错误处理\n"

        if self.issues.get("configuration"):
            content += "3. **补充环境配置**: 添加缺失的必要配置项\n"

        content += """
### 优化建议 (P1)
1. 为所有Repository添加单元测试
2. 完善Service层的业务逻辑验证
3. 添加API端点的集成测试
4. 优化数据库查询性能

### 长期改进 (P2)
1. 实现完整的Repository模式 (为所有Model)
2. 添加Service层的依赖注入
3. 实现统一的异常处理机制
4. 添加性能监控和日志记录

---

## 📚 相关文档

- [数据访问层文档](docs/architecture/data-access-layer.md)
- [API设计文档](docs/api/README.md)
- [开发指南](docs/guide/backend-development.md)
"""

        with open(report_path, "w", encoding="utf-8") as f:
            f.write(content)

        print(f"📄 Markdown报告已保存: {report_path}\n")

    # ===== 辅助方法 =====

    def _extract_table_name(self, content: str, model_name: str) -> str:
        """提取表名"""
        pattern = (
            rf'class {model_name}\(BaseModel\):.*?__tablename__\s*=\s*["\'](\w+)["\']'
        )
        match = re.search(pattern, content, re.DOTALL)
        return match.group(1) if match else "未知"

    def _extract_relationships(self, content: str, model_name: str) -> List[str]:
        """提取关系字段"""
        pattern = r'relationship\(["\'](\w+)["\']\)'
        return re.findall(pattern, content)

    def _extract_repo_model(self, content: str, repo_name: str) -> str:
        """提取Repository关联的Model"""
        pattern = rf"class {repo_name}.*?BaseRepository\[(\w+)\]"
        match = re.search(pattern, content)
        return match.group(1) if match else "未知"

    def _extract_repo_methods(self, content: str, repo_name: str) -> List[str]:
        """提取Repository的方法"""
        pattern = rf"class {repo_name}.*?(?=class|\Z)"
        class_content = re.search(pattern, content, re.DOTALL)
        if not class_content:
            return []

        method_pattern = r"async def (\w+)\("
        return re.findall(method_pattern, class_content.group(0))

    def _extract_service_repos(self, content: str) -> List[str]:
        """提取Service使用的Repository"""
        pattern = r"self\.(\w+_repository)\s*="
        repos = re.findall(pattern, content)
        return list(set(repos))

    def _extract_service_methods(self, content: str, service_name: str) -> List[str]:
        """提取Service的方法"""
        pattern = rf"class {service_name}.*?(?=class|\Z)"
        class_content = re.search(pattern, content, re.DOTALL)
        if not class_content:
            return []

        method_pattern = r"async def (\w+)\("
        return re.findall(method_pattern, class_content.group(0))

    def _get_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime

        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def main():
    """主函数"""
    import sys

    # 获取项目根目录
    if len(sys.argv) > 1:
        project_root = sys.argv[1]
    else:
        project_root = os.getcwd()

    # 创建分析器并执行分析
    analyzer = BackendAlignmentAnalyzer(project_root)
    analyzer.analyze()


if __name__ == "__main__":
    main()
