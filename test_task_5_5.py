#!/usr/bin/env python3
"""
任务5.5验证脚本 - 安全性和生产部署
验证所有安全配置、环境管理、Docker容器化等功能是否正常工作
"""

import os
import sys
import json
import time
import subprocess
import requests
from pathlib import Path
from typing import Dict, List, Any, Optional
import tempfile
import shutil


class Task55Validator:
    """任务5.5验证器"""

    def __init__(self):
        self.project_root = Path(__file__).parent
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0

    def log_test(self, test_name: str, passed: bool, details: str | None = None):
        """记录测试结果"""
        self.total_tests += 1
        if passed:
            self.passed_tests += 1
            status = "✅ PASS"
        else:
            status = "❌ FAIL"

        result = {
            "test": test_name,
            "status": status,
            "passed": passed,
            "details": details
        }
        self.test_results.append(result)
        print(f"{status}: {test_name}")
        if details:
            print(f"  详情: {details}")

    def test_security_headers_middleware(self) -> bool:
        """测试安全头中间件"""
        print("\n🔒 测试安全头中间件...")

        try:
            # 检查SecurityHeadersMiddleware类是否存在
            security_file = self.project_root / "src/core/security.py"
            if not security_file.exists():
                self.log_test("安全头中间件文件存在", False, "security.py文件不存在")
                return False

            # 检查关键安全头配置
            with open(security_file, 'r', encoding='utf-8') as f:
                content = f.read()

            security_headers = [
                "X-Content-Type-Options",
                "X-Frame-Options",
                "Content-Security-Policy",
                "Strict-Transport-Security",
                "Cross-Origin-Embedder-Policy",
                "Permissions-Policy"
            ]

            missing_headers = []
            for header in security_headers:
                if header not in content:
                    missing_headers.append(header)

            if missing_headers:
                self.log_test("安全头配置完整性", False, f"缺少安全头: {missing_headers}")
                return False
            else:
                self.log_test("安全头配置完整性", True, "所有关键安全头已配置")

            # 检查生产环境和开发环境差异化配置
            if "self.is_production" in content and "settings.DEBUG" in content:
                self.log_test("环境差异化配置", True, "支持生产和开发环境不同配置")
            else:
                self.log_test("环境差异化配置", False, "未实现环境差异化配置")

            return True

        except Exception as e:
            self.log_test("安全头中间件测试", False, f"异常: {e}")
            return False

    def test_environment_management(self) -> bool:
        """测试环境管理功能"""
        print("\n⚙️  测试环境管理功能...")

        try:
            env_manager = self.project_root / "scripts/env_manager.py"
            if not env_manager.exists():
                self.log_test("环境管理脚本存在", False, "env_manager.py不存在")
                return False

            self.log_test("环境管理脚本存在", True)

            # 检查配置模板目录
            config_dir = self.project_root / "config/templates"
            if config_dir.exists():
                template_files = list(config_dir.glob("*.template"))
                if len(template_files) >= 4:  # dev, test, staging, prod
                    self.log_test("环境配置模板", True, f"找到{len(template_files)}个模板文件")
                else:
                    self.log_test("环境配置模板", False, f"模板文件不完整，仅{len(template_files)}个")
            else:
                self.log_test("环境配置模板", False, "配置模板目录不存在")

            # 测试环境管理命令
            try:
                result = subprocess.run([
                    sys.executable, str(env_manager), "list"
                ], capture_output=True, text=True, cwd=self.project_root, timeout=30)

                if result.returncode == 0 and "可用环境" in result.stdout:
                    self.log_test("环境管理命令", True, "list命令执行成功")
                else:
                    self.log_test("环境管理命令", False, f"list命令失败: {result.stderr}")
            except Exception as e:
                self.log_test("环境管理命令", False, f"命令执行异常: {e}")

            return True

        except Exception as e:
            self.log_test("环境管理功能测试", False, f"异常: {e}")
            return False

    def test_docker_configuration(self) -> bool:
        """测试Docker容器化配置"""
        print("\n🐳 测试Docker容器化配置...")

        try:
            # 检查Dockerfile
            dockerfile = self.project_root / "Dockerfile"
            if dockerfile.exists():
                with open(dockerfile, 'r', encoding='utf-8') as f:
                    content = f.read()

                # 检查多阶段构建
                if "as builder" in content and "as runtime" in content:
                    self.log_test("Docker多阶段构建", True, "包含builder和runtime阶段")
                else:
                    self.log_test("Docker多阶段构建", False, "未使用多阶段构建")

                # 检查安全配置
                if "USER wuhao" in content or "useradd" in content:
                    self.log_test("Docker安全配置", True, "使用非root用户")
                else:
                    self.log_test("Docker安全配置", False, "未配置非root用户")

                # 检查健康检查
                if "HEALTHCHECK" in content:
                    self.log_test("Docker健康检查", True, "配置了健康检查")
                else:
                    self.log_test("Docker健康检查", False, "未配置健康检查")
            else:
                self.log_test("Dockerfile存在", False, "Dockerfile不存在")

            # 检查生产环境docker-compose.yml
            compose_file = self.project_root / "docker-compose.yml"
            if compose_file.exists():
                with open(compose_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # 检查关键服务
                required_services = ["app", "postgres", "redis", "nginx"]
                missing_services = []
                for service in required_services:
                    if f"{service}:" not in content:
                        missing_services.append(service)

                if missing_services:
                    self.log_test("Docker Compose服务", False, f"缺少服务: {missing_services}")
                else:
                    self.log_test("Docker Compose服务", True, "所有必需服务已配置")

                # 检查资源限制
                if "deploy:" in content and "resources:" in content:
                    self.log_test("Docker资源限制", True, "配置了资源限制")
                else:
                    self.log_test("Docker资源限制", False, "未配置资源限制")

                # 检查密钥管理
                if "secrets:" in content:
                    self.log_test("Docker密钥管理", True, "配置了密钥管理")
                else:
                    self.log_test("Docker密钥管理", False, "未配置密钥管理")
            else:
                self.log_test("生产环境Docker Compose", False, "docker-compose.yml不存在")

            return True

        except Exception as e:
            self.log_test("Docker配置测试", False, f"异常: {e}")
            return False

    def test_nginx_configuration(self) -> bool:
        """测试Nginx配置"""
        print("\n🌐 测试Nginx配置...")

        try:
            nginx_dir = self.project_root / "nginx"
            if not nginx_dir.exists():
                self.log_test("Nginx配置目录", False, "nginx目录不存在")
                return False

            # 检查主配置文件
            nginx_conf = nginx_dir / "nginx.conf"
            if nginx_conf.exists():
                with open(nginx_conf, 'r', encoding='utf-8') as f:
                    content = f.read()

                # 检查安全配置
                security_features = [
                    "gzip on",
                    "server_tokens off",
                    "limit_req_zone",
                    "ssl_protocols"
                ]

                missing_features = []
                for feature in security_features:
                    if feature not in content:
                        missing_features.append(feature)

                if missing_features:
                    self.log_test("Nginx安全配置", False, f"缺少配置: {missing_features}")
                else:
                    self.log_test("Nginx安全配置", True, "安全配置完整")
            else:
                self.log_test("Nginx主配置文件", False, "nginx.conf不存在")

            # 检查虚拟主机配置
            vhost_conf = nginx_dir / "conf.d/wuhao-tutor.conf"
            if vhost_conf.exists():
                with open(vhost_conf, 'r', encoding='utf-8') as f:
                    content = f.read()

                # 检查SSL和HTTPS重定向
                if "ssl_certificate" in content and "return 301 https" in content:
                    self.log_test("Nginx SSL配置", True, "配置了SSL和HTTPS重定向")
                else:
                    self.log_test("Nginx SSL配置", False, "SSL配置不完整")

                # 检查反向代理配置
                if "proxy_pass" in content:
                    # 检查nginx.conf中是否有upstream配置
                    nginx_conf = nginx_dir / "nginx.conf"
                    if nginx_conf.exists():
                        with open(nginx_conf, 'r', encoding='utf-8') as nginx_f:
                            nginx_content = nginx_f.read()
                        if "upstream" in nginx_content:
                            self.log_test("Nginx反向代理", True, "配置了反向代理和上游服务器")
                        else:
                            self.log_test("Nginx反向代理", False, "缺少upstream配置")
                    else:
                        self.log_test("Nginx反向代理", False, "nginx.conf不存在")
                else:
                    self.log_test("Nginx反向代理", False, "未配置proxy_pass")

                # 检查限流配置
                if "limit_req" in content and "limit_conn" in content:
                    self.log_test("Nginx限流配置", True, "配置了请求和连接限流")
                else:
                    self.log_test("Nginx限流配置", False, "限流配置不完整")
            else:
                self.log_test("Nginx虚拟主机配置", False, "虚拟主机配置不存在")

            return True

        except Exception as e:
            self.log_test("Nginx配置测试", False, f"异常: {e}")
            return False

    def test_secrets_management(self) -> bool:
        """测试密钥管理"""
        print("\n🔐 测试密钥管理...")

        try:
            secrets_manager = self.project_root / "scripts/secrets_manager.py"
            if not secrets_manager.exists():
                self.log_test("密钥管理脚本", False, "secrets_manager.py不存在")
                return False

            self.log_test("密钥管理脚本", True)

            # 检查secrets目录
            secrets_dir = self.project_root / "secrets"
            if secrets_dir.exists():
                secret_files = list(secrets_dir.glob("*.txt"))
                if len(secret_files) > 0:
                    self.log_test("密钥文件生成", True, f"找到{len(secret_files)}个密钥文件")

                    # 检查文件权限
                    for secret_file in secret_files:
                        permissions = oct(secret_file.stat().st_mode)[-3:]
                        if permissions != "600":
                            self.log_test("密钥文件权限", False, f"{secret_file.name}权限为{permissions}")
                            break
                    else:
                        self.log_test("密钥文件权限", True, "所有密钥文件权限正确(600)")
                else:
                    self.log_test("密钥文件生成", False, "未找到密钥文件")
            else:
                self.log_test("密钥目录", False, "secrets目录不存在")

            # 测试密钥管理命令
            try:
                result = subprocess.run([
                    sys.executable, str(secrets_manager), "list"
                ], capture_output=True, text=True, cwd=self.project_root, timeout=30)

                if result.returncode == 0 and "密钥状态" in result.stdout:
                    self.log_test("密钥管理命令", True, "list命令执行成功")
                else:
                    self.log_test("密钥管理命令", False, f"list命令失败")
            except Exception as e:
                self.log_test("密钥管理命令", False, f"命令执行异常: {e}")

            return True

        except Exception as e:
            self.log_test("密钥管理测试", False, f"异常: {e}")
            return False

    def test_deployment_scripts(self) -> bool:
        """测试部署脚本"""
        print("\n🚀 测试部署脚本...")

        try:
            deploy_script = self.project_root / "scripts/deploy.py"
            if not deploy_script.exists():
                self.log_test("部署管理脚本", False, "deploy.py不存在")
                return False

            self.log_test("部署管理脚本", True)

            # 测试部署脚本命令
            try:
                result = subprocess.run([
                    sys.executable, str(deploy_script), "--help"
                ], capture_output=True, text=True, cwd=self.project_root, timeout=30)

                if result.returncode == 0 and "可用命令" in result.stdout:
                    self.log_test("部署脚本帮助", True, "帮助命令执行成功")
                else:
                    self.log_test("部署脚本帮助", False, "帮助命令失败")

                # 检查关键命令
                commands = ["check", "build", "deploy", "status", "logs"]
                missing_commands = []
                for cmd in commands:
                    if cmd not in result.stdout:
                        missing_commands.append(cmd)

                if missing_commands:
                    self.log_test("部署脚本功能", False, f"缺少命令: {missing_commands}")
                else:
                    self.log_test("部署脚本功能", True, "所有关键命令都存在")

            except Exception as e:
                self.log_test("部署脚本测试", False, f"命令执行异常: {e}")

            return True

        except Exception as e:
            self.log_test("部署脚本测试", False, f"异常: {e}")
            return False

    def test_monitoring_configuration(self) -> bool:
        """测试监控配置"""
        print("\n📊 测试监控配置...")

        try:
            monitoring_dir = self.project_root / "monitoring"
            if not monitoring_dir.exists():
                self.log_test("监控配置目录", False, "monitoring目录不存在")
                return False

            # 检查Prometheus配置
            prometheus_conf = monitoring_dir / "prometheus.yml"
            if prometheus_conf.exists():
                with open(prometheus_conf, 'r', encoding='utf-8') as f:
                    content = f.read()

                # 检查关键监控目标
                targets = ["wuhao-tutor-app", "postgres", "redis", "nginx"]
                missing_targets = []
                for target in targets:
                    if target not in content:
                        missing_targets.append(target)

                if missing_targets:
                    self.log_test("Prometheus监控目标", False, f"缺少监控: {missing_targets}")
                else:
                    self.log_test("Prometheus监控目标", True, "所有关键服务都在监控中")

                # 检查告警配置
                if "alerting:" in content:
                    self.log_test("Prometheus告警配置", True, "配置了告警管理")
                else:
                    self.log_test("Prometheus告警配置", False, "未配置告警管理")
            else:
                self.log_test("Prometheus配置文件", False, "prometheus.yml不存在")

            return True

        except Exception as e:
            self.log_test("监控配置测试", False, f"异常: {e}")
            return False

    def test_cors_and_security_config(self) -> bool:
        """测试CORS和安全配置"""
        print("\n🔒 测试CORS和安全配置...")

        try:
            # 检查配置文件中的CORS设置
            config_file = self.project_root / "src/core/config.py"
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # 检查CORS配置
                if "BACKEND_CORS_ORIGINS" in content:
                    self.log_test("CORS配置", True, "配置了CORS源")
                else:
                    self.log_test("CORS配置", False, "未配置CORS")

                # 检查限流配置
                rate_limit_configs = [
                    "RATE_LIMIT_PER_IP",
                    "RATE_LIMIT_PER_USER",
                    "RATE_LIMIT_AI_SERVICE"
                ]

                missing_configs = []
                for config in rate_limit_configs:
                    if config not in content:
                        missing_configs.append(config)

                if missing_configs:
                    self.log_test("限流配置", False, f"缺少配置: {missing_configs}")
                else:
                    self.log_test("限流配置", True, "限流配置完整")

            # 检查main.py中的中间件配置
            main_file = self.project_root / "src/main.py"
            if main_file.exists():
                with open(main_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # 检查安全中间件
                security_middlewares = [
                    "SecurityHeadersMiddleware",
                    "RateLimitMiddleware",
                    "CORSMiddleware"
                ]

                missing_middlewares = []
                for middleware in security_middlewares:
                    if middleware not in content:
                        missing_middlewares.append(middleware)

                if missing_middlewares:
                    self.log_test("安全中间件", False, f"缺少中间件: {missing_middlewares}")
                else:
                    self.log_test("安全中间件", True, "所有安全中间件已配置")

            return True

        except Exception as e:
            self.log_test("CORS和安全配置测试", False, f"异常: {e}")
            return False

    def test_api_rate_limiting(self) -> bool:
        """测试API访问频率限制"""
        print("\n🚦 测试API访问频率限制...")

        try:
            # 检查限流相关代码
            security_file = self.project_root / "src/core/security.py"
            if security_file.exists():
                with open(security_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # 检查限流算法实现
                algorithms = ["TokenBucket", "SlidingWindowCounter", "RateLimiter"]
                missing_algorithms = []
                for algo in algorithms:
                    if f"class {algo}" not in content:
                        missing_algorithms.append(algo)

                if missing_algorithms:
                    self.log_test("限流算法实现", False, f"缺少算法: {missing_algorithms}")
                else:
                    self.log_test("限流算法实现", True, "限流算法实现完整")

                # 检查限流类型
                if "RateLimitType" in content:
                    self.log_test("限流类型定义", True, "定义了限流类型枚举")
                else:
                    self.log_test("限流类型定义", False, "未定义限流类型")

            return True

        except Exception as e:
            self.log_test("API限流测试", False, f"异常: {e}")
            return False

    def test_production_readiness(self) -> bool:
        """测试生产就绪状态"""
        print("\n🏭 测试生产就绪状态...")

        try:
            # 检查生产环境配置
            prod_env = self.project_root / ".env.prod"
            if prod_env.exists():
                with open(prod_env, 'r', encoding='utf-8') as f:
                    content = f.read()

                # 检查生产环境关键配置
                prod_configs = [
                    "ENVIRONMENT=production",
                    "DEBUG=false",
                    "SECRET_KEY=",
                    "POSTGRES_",
                    "REDIS_"
                ]

                missing_configs = []
                for config in prod_configs:
                    if config not in content:
                        missing_configs.append(config)

                if missing_configs:
                    self.log_test("生产环境配置", False, f"缺少配置: {missing_configs}")
                else:
                    self.log_test("生产环境配置", True, "生产环境配置完整")

                # 检查是否有默认密钥（实际文件应该不包含CHANGE_ME，只检查关键配置是否存在）
                critical_configs = ["SECRET_KEY=", "POSTGRES_PASSWORD=", "REDIS_PASSWORD="]
                missing_critical = []
                for config in critical_configs:
                    if config not in content or f"{config}CHANGE_ME" in content:
                        missing_critical.append(config.replace("=", ""))

                if missing_critical:
                    self.log_test("生产密钥安全", False, f"关键配置缺失或使用默认值: {missing_critical}")
                else:
                    self.log_test("生产密钥安全", True, "生产密钥已设置")
            else:
                self.log_test("生产环境配置文件", False, ".env.prod不存在")

            # 检查Docker生产配置
            docker_env = self.project_root / ".env.docker.production"
            if docker_env.exists():
                self.log_test("Docker生产环境配置", True, "Docker生产配置存在")
            else:
                self.log_test("Docker生产环境配置", False, "Docker生产配置不存在")

            return True

        except Exception as e:
            self.log_test("生产就绪测试", False, f"异常: {e}")
            return False

    def run_all_tests(self):
        """运行所有验证测试"""
        print("🧪 开始任务5.5验证测试...")
        print("=" * 60)

        # 执行所有测试
        test_methods = [
            self.test_security_headers_middleware,
            self.test_cors_and_security_config,
            self.test_api_rate_limiting,
            self.test_environment_management,
            self.test_docker_configuration,
            self.test_nginx_configuration,
            self.test_secrets_management,
            self.test_deployment_scripts,
            self.test_monitoring_configuration,
            self.test_production_readiness
        ]

        for test_method in test_methods:
            try:
                test_method()
            except Exception as e:
                self.log_test(f"{test_method.__name__}执行", False, f"异常: {e}")

        # 生成测试报告
        self.generate_report()

    def generate_report(self):
        """生成测试报告"""
        print("\n" + "=" * 60)
        print("📊 任务5.5验证测试报告")
        print("=" * 60)

        # 统计结果
        passed = self.passed_tests
        failed = self.total_tests - self.passed_tests
        success_rate = (passed / self.total_tests * 100) if self.total_tests > 0 else 0

        print(f"总测试数: {self.total_tests}")
        print(f"通过数量: {passed}")
        print(f"失败数量: {failed}")
        print(f"成功率: {success_rate:.1f}%")

        # 分类显示结果
        print(f"\n📋 详细测试结果:")
        for result in self.test_results:
            print(f"{result['status']}: {result['test']}")
            if result['details']:
                print(f"    {result['details']}")

        # 生成JSON报告
        report_data = {
            "task": "5.5 - 安全性和生产部署",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "summary": {
                "total_tests": self.total_tests,
                "passed_tests": passed,
                "failed_tests": failed,
                "success_rate": success_rate
            },
            "results": self.test_results
        }

        report_file = self.project_root / "task_5_5_validation_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)

        print(f"\n📄 详细报告已保存到: {report_file}")

        # 最终结果
        if success_rate >= 90:
            print(f"\n🎉 任务5.5验证测试 - 优秀 ({success_rate:.1f}%)")
            return 0
        elif success_rate >= 80:
            print(f"\n✅ 任务5.5验证测试 - 良好 ({success_rate:.1f}%)")
            return 0
        elif success_rate >= 70:
            print(f"\n⚠️  任务5.5验证测试 - 及格 ({success_rate:.1f}%)")
            return 1
        else:
            print(f"\n❌ 任务5.5验证测试 - 不及格 ({success_rate:.1f}%)")
            return 1


def main():
    """主函数"""
    validator = Task55Validator()
    return validator.run_all_tests()


if __name__ == "__main__":
    sys.exit(main())
