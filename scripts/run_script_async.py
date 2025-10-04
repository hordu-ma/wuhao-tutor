#!/usr/bin/env python3
"""
异步运行脚本的包装器 - 解决 VS Code 终端缓冲问题
用法: python scripts/run_script_async.py <script_path> [args...]
"""
import subprocess
import sys
import tempfile
import time
from pathlib import Path


def main():
    if len(sys.argv) < 2:
        print(
            "用法: python scripts/run_script_async.py <script_path> [args...]",
            flush=True,
        )
        sys.exit(1)

    script_path = sys.argv[1]
    script_args = sys.argv[2:] if len(sys.argv) > 2 else []

    # 创建临时输出文件
    output_file = Path(tempfile.gettempdir()) / f"script_output_{int(time.time())}.txt"

    print(f"🚀 启动脚本: {script_path}", flush=True)
    print(f"📝 输出文件: {output_file}", flush=True)
    print("-" * 60, flush=True)

    # 构建命令
    cmd = ["uv", "run", "python", script_path] + script_args

    # 后台运行脚本，输出重定向到文件
    with open(output_file, "w") as f:
        process = subprocess.Popen(cmd, stdout=f, stderr=subprocess.STDOUT, text=True)

    print(f"✅ 脚本已在后台启动 (PID: {process.pid})", flush=True)
    print(f"⏳ 等待脚本完成...", flush=True)

    # 等待进程完成，同时监控输出文件
    last_size = 0
    while process.poll() is None:
        time.sleep(0.5)
        if output_file.exists():
            current_size = output_file.stat().st_size
            if current_size > last_size:
                # 读取新内容
                with open(output_file, "r") as f:
                    f.seek(last_size)
                    new_content = f.read()
                    print(new_content, end="", flush=True)
                    last_size = current_size

    # 进程完成后读取剩余输出
    if output_file.exists():
        with open(output_file, "r") as f:
            f.seek(last_size)
            remaining = f.read()
            if remaining:
                print(remaining, end="", flush=True)

    # 获取返回码
    return_code = process.returncode

    print("-" * 60, flush=True)
    if return_code == 0:
        print(f"✅ 脚本执行成功", flush=True)
    else:
        print(f"❌ 脚本执行失败 (返回码: {return_code})", flush=True)

    # 清理临时文件
    try:
        output_file.unlink()
    except:
        pass

    sys.exit(return_code)


if __name__ == "__main__":
    main()
