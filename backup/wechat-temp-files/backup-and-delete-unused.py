#!/usr/bin/env python3
"""
备份并删除微信小程序无依赖文件
"""
import json
import os
import shutil
from datetime import datetime
from pathlib import Path

# 项目根目录
ROOT_DIR = Path(__file__).parent.parent.parent
BACKUP_DIR = (
    Path(__file__).parent
    / f'unused-files-backup-{datetime.now().strftime("%Y%m%d-%H%M%S")}'
)
ANALYSE_FILE = ROOT_DIR / "analyse-data.json"


def main():
    print("=" * 80)
    print("微信小程序无依赖文件备份和删除工具")
    print("=" * 80)

    # 读取分析文件
    print(f"\n📖 读取分析文件: {ANALYSE_FILE}")
    with open(ANALYSE_FILE, "r") as f:
        data = json.load(f)

    unused_files = data.get("unusedCodeFiles", [])
    print(f"✅ 找到 {len(unused_files)} 个无依赖文件")

    # 创建备份目录
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    print(f"\n📁 创建备份目录: {BACKUP_DIR}")

    # 统计信息
    total_size = 0
    backed_up = 0
    deleted = 0
    not_found = 0
    errors = []

    print("\n开始处理文件...")
    print("-" * 80)

    for i, file_info in enumerate(unused_files, 1):
        file_path = file_info.get("path", "")
        file_size = file_info.get("size", 0)

        source_path = ROOT_DIR / "miniprogram" / file_path

        # 显示进度
        print(f"[{i}/{len(unused_files)}] {file_path}", end="")

        if not source_path.exists():
            print(" ❌ 文件不存在")
            not_found += 1
            continue

        try:
            # 备份文件
            backup_path = BACKUP_DIR / file_path
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_path, backup_path)
            backed_up += 1
            total_size += file_size

            # 删除原文件
            source_path.unlink()
            deleted += 1

            print(" ✅ 已备份并删除")

        except Exception as e:
            print(f" ⚠️  错误: {str(e)}")
            errors.append({"file": file_path, "error": str(e)})

    # 显示统计信息
    print("\n" + "=" * 80)
    print("处理完成！")
    print("=" * 80)
    print(f"✅ 备份成功: {backed_up} 个文件")
    print(f"✅ 删除成功: {deleted} 个文件")
    print(f"❌ 文件不存在: {not_found} 个")
    print(f"⚠️  处理错误: {len(errors)} 个")
    print(f"📦 总大小: {total_size:,} bytes ({total_size/1024/1024:.2f} MB)")
    print(f"📁 备份位置: {BACKUP_DIR}")

    if errors:
        print("\n错误详情:")
        for err in errors:
            print(f"  - {err['file']}: {err['error']}")

    # 保存日志
    log_file = BACKUP_DIR / "backup-log.txt"
    with open(log_file, "w") as f:
        f.write(f"备份时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"备份文件数: {backed_up}\n")
        f.write(f"删除文件数: {deleted}\n")
        f.write(f"总大小: {total_size:,} bytes\n")
        f.write(f"\n备份文件列表:\n")
        for file_info in unused_files:
            f.write(f"  - {file_info.get('path', 'unknown')}\n")

    print(f"\n📝 日志已保存: {log_file}")

    # 清理空目录
    print("\n🧹 清理空目录...")
    cleaned_dirs = 0
    for root, dirs, files in os.walk(ROOT_DIR / "miniprogram", topdown=False):
        for dir_name in dirs:
            dir_path = Path(root) / dir_name
            try:
                if not any(dir_path.iterdir()):
                    dir_path.rmdir()
                    cleaned_dirs += 1
                    print(f"  ✅ 删除空目录: {dir_path.relative_to(ROOT_DIR)}")
            except:
                pass

    print(f"\n✅ 清理了 {cleaned_dirs} 个空目录")
    print("\n🎉 所有操作完成!")


if __name__ == "__main__":
    main()
