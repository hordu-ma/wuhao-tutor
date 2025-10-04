#!/usr/bin/env python3
"""诊断脚本挂起问题的工具"""

import os
import subprocess
import sys
import time
from pathlib import Path

# 强制禁用输出缓冲 - 这是关键！
# 使用 PYTHONUNBUFFERED 环境变量或在所有 print 中使用 flush=True


def print_section(title: str):
    """打印分隔符"""
    print(f"\n{'='*60}", flush=True)
    print(f"  {title}", flush=True)
    print(f"{'='*60}\n", flush=True)


def test_basic_python():
    """测试基本 Python 执行"""
    print_section("测试 1: 基本 Python 执行")
    start = time.time()
    result = subprocess.run(
        ["python3", "-c", "print('Python 工作正常')"],
        capture_output=True,
        text=True,
        timeout=5,
    )
    elapsed = time.time() - start
    print(f"✓ Python 执行成功 ({elapsed:.2f}s)", flush=True)
    print(f"  输出: {result.stdout.strip()}", flush=True)


def test_uv_version():
    """测试 uv 命令"""
    print_section("测试 2: uv 版本检查")
    start = time.time()
    result = subprocess.run(
        ["uv", "--version"], capture_output=True, text=True, timeout=5
    )
    elapsed = time.time() - start
    print(f"✓ uv 命令工作正常 ({elapsed:.2f}s)", flush=True)
    print(f"  版本: {result.stdout.strip()}", flush=True)


def test_uv_run_simple():
    """测试 uv run 简单命令"""
    print_section("测试 3: uv run 简单脚本")

    # 创建临时测试脚本
    test_script = Path(__file__).parent / "_test_simple.py"
    test_script.write_text("print('uv run 工作正常')")

    try:
        start = time.time()
        result = subprocess.run(
            ["uv", "run", "python", str(test_script)],
            capture_output=True,
            text=True,
            timeout=10,
        )
        elapsed = time.time() - start
        print(f"✓ uv run 执行成功 ({elapsed:.2f}s)", flush=True)
        print(f"  输出: {result.stdout.strip()}", flush=True)
    finally:
        test_script.unlink(missing_ok=True)


def test_file_io():
    """测试文件 I/O"""
    print_section("测试 4: 文件 I/O 性能")

    test_file = Path(__file__).parent / "_test_io.txt"

    # 写入测试
    start = time.time()
    test_file.write_text("测试数据\n" * 1000)
    write_time = time.time() - start

    # 读取测试
    start = time.time()
    content = test_file.read_text()
    read_time = time.time() - start

    test_file.unlink()

    print(f"✓ 文件 I/O 正常", flush=True)
    print(f"  写入 1000 行: {write_time:.3f}s", flush=True)
    print(f"  读取 1000 行: {read_time:.3f}s", flush=True)


def test_git_status():
    """测试 Git 命令"""
    print_section("测试 5: Git 命令")

    start = time.time()
    result = subprocess.run(
        ["git", "status", "--short"],
        capture_output=True,
        text=True,
        timeout=10,
        cwd=Path(__file__).parent.parent,
    )
    elapsed = time.time() - start

    if result.returncode == 0:
        print(f"✓ Git 命令工作正常 ({elapsed:.2f}s)", flush=True)
        lines = result.stdout.strip().split("\n") if result.stdout.strip() else []
        print(f"  修改的文件数: {len(lines)}", flush=True)
    else:
        print(f"✗ Git 命令失败", flush=True)
        print(f"  错误: {result.stderr}", flush=True)


def test_pathlib_walk():
    """测试目录遍历"""
    print_section("测试 6: 目录遍历性能")

    start = time.time()
    count = 0
    src_dir = Path(__file__).parent.parent / "src"

    if src_dir.exists():
        for path in src_dir.rglob("*.py"):
            count += 1
            if count > 100:  # 限制数量避免太慢
                break

    elapsed = time.time() - start
    print(f"✓ 目录遍历正常 ({elapsed:.3f}s)", flush=True)
    print(f"  找到 {count} 个 Python 文件", flush=True)


def test_subprocess_env():
    """测试子进程环境"""
    print_section("测试 7: 子进程环境变量")

    result = subprocess.run(["env"], capture_output=True, text=True, timeout=5)

    env_vars = result.stdout.strip().split("\n")
    print(f"✓ 环境变量数量: {len(env_vars)}", flush=True)

    # 检查关键环境变量
    important_vars = ["PATH", "VIRTUAL_ENV", "UV_PROJECT_ENVIRONMENT"]
    for var in important_vars:
        value = os.environ.get(var, "未设置")
        print(f"  {var}: {value[:80] if len(value) > 80 else value}", flush=True)


def main():
    """运行所有测试"""
    print("\n" + "=" * 60, flush=True)
    print("  诊断命令行脚本挂起问题", flush=True)
    print("  提示: 如果某个测试卡住,请按 Ctrl+C 中断", flush=True)
    print("=" * 60, flush=True)

    tests = [
        ("基本 Python", test_basic_python),
        ("uv 版本", test_uv_version),
        ("uv run", test_uv_run_simple),
        ("文件 I/O", test_file_io),
        ("Git 命令", test_git_status),
        ("目录遍历", test_pathlib_walk),
        ("环境变量", test_subprocess_env),
    ]

    failed = []

    for name, test_func in tests:
        try:
            test_func()
        except subprocess.TimeoutExpired:
            print(f"✗ 测试超时: {name}", flush=True)
            failed.append((name, "超时"))
        except Exception as e:
            print(f"✗ 测试失败: {name}", flush=True)
            print(f"  错误: {str(e)}", flush=True)
            failed.append((name, str(e)))

    # 总结
    print_section("诊断总结")
    if not failed:
        print("✓ 所有测试通过！", flush=True)
        print("\n可能的问题:", flush=True)
        print("  1. 特定脚本的逻辑问题 (无限循环、阻塞 I/O)", flush=True)
        print("  2. VS Code 终端缓冲区问题", flush=True)
        print("  3. 特定依赖包的问题", flush=True)
    else:
        print(f"✗ {len(failed)} 个测试失败:\n", flush=True)
        for name, error in failed:
            print(f"  - {name}: {error}", flush=True)
        print("\n建议:", flush=True)
        print("  1. 检查失败的测试对应的系统组件", flush=True)
        print("  2. 尝试在独立终端 (iTerm/Terminal.app) 运行", flush=True)
        print("  3. 检查系统资源使用情况 (活动监视器)", flush=True)

    # 强制刷新并退出
    sys.stdout.flush()
    sys.stderr.flush()


if __name__ == "__main__":
    main()
