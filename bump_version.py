#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
版本号自动更新 + 一键打包脚本

用法:
    python bump_version.py patch        # 2.3.0 -> 2.3.1
    python bump_version.py minor        # 2.3.0 -> 2.4.0
    python bump_version.py major        # 2.3.0 -> 3.0.0
    python bump_version.py build        # 仅更新构建日期，不动版本号
    python bump_version.py patch --no-build  # 只升版本号，不打包
    python bump_version.py patch --python "C:/Python312/python.exe"
"""

import re
import sys
import os
import io
import argparse
import subprocess
from datetime import datetime

# Windows GBK 终端兼容：把 stdout 强制成 UTF-8
if sys.platform == "win32":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")
    except Exception:
        pass

VERSION_FILE = "version.py"
SPEC_FILE = "采购助手V2.3.2.spec"
EXE_NAME = "采购助手"
DIST_DIR = "dist"

# 默认可执行 Python 路径（Python 3.12.10，含 matplotlib/全部依赖）
DEFAULT_PYTHON = r"C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe"


def read_version():
    """从 version.py 读取当前版本号和日期"""
    with open(VERSION_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    m_ver = re.search(r'__version__\s*=\s*"([^"]+)"', content)
    m_date = re.search(r'__version_date__\s*=\s*"([^"]+)"', content)
    if not m_ver:
        raise RuntimeError("version.py 中找不到 __version__")
    return m_ver.group(1), m_date.group(1) if m_date else None, content


def bump(parts, level):
    """根据级别提升版本号"""
    major, minor, patch = (parts + [0, 0, 0])[:3]
    if level == "major":
        return (major + 1, 0, 0)
    if level == "minor":
        return (major, minor + 1, 0)
    if level == "patch":
        return (major, minor, patch + 1)
    if level == "build":
        return (major, minor, patch)
    raise ValueError(f"未知级别: {level}")


def update_version_file(content, new_version, new_date):
    """更新 version.py 中的版本号和日期"""
    content = re.sub(
        r'__version__\s*=\s*"[^"]+"',
        f'__version__ = "{new_version}"',
        content,
    )
    if new_date:
        content = re.sub(
            r'__version_date__\s*=\s*"[^"]+"',
            f'__version_date__ = "{new_date}"',
            content,
        )
    with open(VERSION_FILE, "w", encoding="utf-8") as f:
        f.write(content)


def run_build(python_exe):
    """运行 PyInstaller 打包"""
    if not os.path.exists(SPEC_FILE):
        raise RuntimeError(f"找不到 spec 文件: {SPEC_FILE}")
    if not os.path.exists(python_exe):
        raise RuntimeError(f"找不到 Python: {python_exe}")

    print(f"\n[1/2] 清理旧产物 ...")
    for d in ("build", DIST_DIR):
        if os.path.exists(d):
            import shutil
            print(f"  - 删除 {d}/")
            shutil.rmtree(d, ignore_errors=True)

    print(f"\n[2/2] PyInstaller 打包 ({os.path.basename(python_exe)}) ...")
    cmd = [python_exe, "-m", "PyInstaller", "--clean", SPEC_FILE]
    print(f"  > {' '.join(cmd)}")
    result = subprocess.run(cmd, shell=False)
    if result.returncode != 0:
        raise RuntimeError(f"PyInstaller 打包失败 (exit {result.returncode})")

    exe_path = os.path.join(DIST_DIR, f"{EXE_NAME}.exe")
    if os.path.exists(exe_path):
        size_mb = os.path.getsize(exe_path) / (1024 * 1024)
        print(f"\n✅ 打包完成: {exe_path} ({size_mb:.1f} MB)")
    else:
        print(f"\n⚠️  未在 {exe_path} 找到 EXE，请检查 PyInstaller 输出")


def main():
    parser = argparse.ArgumentParser(
        description="自动更新版本号 + 一键打包",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "level",
        choices=["major", "minor", "patch", "build"],
        help="版本号更新级别 (build=仅更新日期)",
    )
    parser.add_argument(
        "--no-build",
        action="store_true",
        help="只更新版本号，不调用 PyInstaller",
    )
    parser.add_argument(
        "--python",
        default=DEFAULT_PYTHON,
        help=f"PyInstaller 使用的 Python 路径 (默认: {DEFAULT_PYTHON})",
    )
    args = parser.parse_args()

    cur_ver, cur_date, content = read_version()
    print(f"当前版本: {cur_ver}  (build {cur_date})")

    parts = [int(x) for x in cur_ver.split(".")]
    new_parts = bump(parts, args.level)
    new_ver = ".".join(str(x) for x in new_parts)
    new_date = datetime.now().strftime("%Y-%m-%d")

    if new_ver == cur_ver and args.level == "build":
        # 仅更新日期
        new_ver = cur_ver
    elif new_ver == cur_ver:
        print(f"⚠️  版本号未变化 ({cur_ver})，可能已经达到边界。已中止。")
        return 1

    print(f"新版本:   {new_ver}  (build {new_date})")
    update_version_file(content, new_ver, new_date)
    print(f"✅ version.py 已更新")

    if args.no_build:
        print("(已跳过打包 — --no-build)")
        return 0

    run_build(args.python)
    return 0


if __name__ == "__main__":
    sys.exit(main())
