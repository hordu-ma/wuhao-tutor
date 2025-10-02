#!/usr/bin/env python3
"""
后端启动脚本
用于避免文件描述符问题，稳定启动FastAPI应用
"""

import subprocess
import sys
import time
import signal
import os
from pathlib import Path

# 设置项目根目录
PROJECT_ROOT = Path(__file__).parent
os.chdir(PROJECT_ROOT)

def start_backend():
    """启动后端服务"""
    try:
        # 构建启动命令
        cmd = [
            "uv", "run", "uvicorn",
            "src.main:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--reload"
        ]

        print("🚀 正在启动后端服务...")
        print(f"命令: {' '.join(cmd)}")

        # 启动进程，不重定向输出
        process = subprocess.Popen(
            cmd,
            cwd=PROJECT_ROOT,
            stdout=None,  # 继承父进程的stdout
            stderr=None,  # 继承父进程的stderr
            preexec_fn=os.setsid if hasattr(os, 'setsid') else None
        )

        # 保存进程ID
        with open(PROJECT_ROOT / ".dev-pids" / "backend.pid", "w") as f:
            f.write(str(process.pid))

        print(f"✅ 后端服务已启动，PID: {process.pid}")
        print("🔗 API地址: http://localhost:8000")
        print("📊 健康检查: http://localhost:8000/health")
        print("📖 API文档: http://localhost:8000/docs")
        print("\n按 Ctrl+C 停止服务")

        # 等待进程
        try:
            process.wait()
        except KeyboardInterrupt:
            print("\n🛑 正在停止后端服务...")

            # 优雅关闭
            try:
                if hasattr(os, 'killpg'):
                    os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                else:
                    process.terminate()

                # 等待进程结束
                process.wait(timeout=10)
                print("✅ 后端服务已停止")
            except subprocess.TimeoutExpired:
                print("⚠️  强制停止后端服务...")
                if hasattr(os, 'killpg'):
                    os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                else:
                    process.kill()
            except ProcessLookupError:
                print("✅ 后端服务已停止")

        return process.returncode

    except FileNotFoundError:
        print("❌ 错误: 找不到 uv 命令，请确保已安装 uv")
        return 1
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        return 1
    finally:
        # 清理PID文件
        pid_file = PROJECT_ROOT / ".dev-pids" / "backend.pid"
        if pid_file.exists():
            pid_file.unlink()

def stop_backend():
    """停止后端服务"""
    pid_file = PROJECT_ROOT / ".dev-pids" / "backend.pid"

    if not pid_file.exists():
        print("❌ 没有找到运行中的后端服务")
        return 1

    try:
        with open(pid_file) as f:
            pid = int(f.read().strip())

        print(f"🛑 正在停止后端服务 (PID: {pid})...")

        # 尝试优雅关闭
        os.kill(pid, signal.SIGTERM)

        # 等待进程结束
        for _ in range(50):  # 等待5秒
            try:
                os.kill(pid, 0)  # 检查进程是否还存在
                time.sleep(0.1)
            except ProcessLookupError:
                break
        else:
            # 强制杀死
            print("⚠️  强制停止服务...")
            os.kill(pid, signal.SIGKILL)

        pid_file.unlink()
        print("✅ 后端服务已停止")
        return 0

    except (FileNotFoundError, ProcessLookupError):
        print("✅ 后端服务已停止")
        pid_file.unlink()
        return 0
    except Exception as e:
        print(f"❌ 停止失败: {e}")
        return 1

def main():
    """主函数"""
    # 确保.dev-pids目录存在
    (PROJECT_ROOT / ".dev-pids").mkdir(exist_ok=True)

    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "stop":
            return stop_backend()
        elif command == "restart":
            stop_backend()
            time.sleep(2)
            return start_backend()
        else:
            print(f"❌ 未知命令: {command}")
            print("用法: python start_backend.py [stop|restart]")
            return 1
    else:
        return start_backend()

if __name__ == "__main__":
    exit(main())
