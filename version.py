#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
采购管理系统 - 版本管理模块
功能：版本常量定义、GitHub Releases 自动更新检查
"""

import json
import urllib.request
import urllib.error
import threading
import ssl
from datetime import datetime

__version__ = "2.0.2"
__version_date__ = "2026-06-10"

# ═══════════════════════════════════════════════════════
# GitHub 仓库信息（上传后请修改为你的实际仓库地址）
# ═══════════════════════════════════════════════════════
GITHUB_USER = "eastseao"           # ← GitHub 用户名（全小写）
GITHUB_REPO = "procurement-system"  # ← 替换为你的仓库名

GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/releases/latest"
GITHUB_RELEASES_URL = f"https://github.com/{GITHUB_USER}/{GITHUB_REPO}/releases"

# 检查超时时间（秒）
REQUEST_TIMEOUT = 8

# 缓存：避免同一次运行重复检查
_last_check_result = None
_check_lock = threading.Lock()


def get_latest_release():
    """
    通过 GitHub API 获取最新 release 信息。
    返回: (tag_name, html_url, body) 或 (None, None, None)
    """
    try:
        # 创建忽略 SSL 验证的上下文（兼容某些企业网络环境）
        ctx = ssl.create_default_context()
        
        req = urllib.request.Request(
            GITHUB_API_URL,
            headers={
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": f"ProcurementSystem/{__version__}",
            },
        )
        
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT, context=ctx) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            tag_name = data.get("tag_name", "").lstrip("v")
            html_url = data.get("html_url", "")
            body = data.get("body", "")
            return tag_name, html_url, body
            
    except urllib.error.HTTPError as e:
        if e.code == 404:
            # 仓库还没有 release，不算错误
            pass
        return None, None, None
    except Exception:
        return None, None, None


def _parse_version(version_str):
    """将版本字符串解析为可比较的元组，如 '1.5.0' -> (1, 5, 0)"""
    try:
        parts = version_str.strip().split(".")
        return tuple(int(p) for p in parts if p.isdigit())
    except Exception:
        return (0, 0, 0)


def check_for_updates(force=False):
    """
    检查 GitHub 是否有新版本可用。
    
    参数:
        force: 是否强制重新检查（忽略缓存）
    
    返回: dict {
        "has_update": bool,
        "current_version": str,
        "latest_version": str,
        "download_url": str,
        "release_notes": str,
    }
    """
    global _last_check_result
    
    with _check_lock:
        if _last_check_result is not None and not force:
            return _last_check_result
        
        latest, url, notes = get_latest_release()
        
        result = {
            "has_update": False,
            "current_version": __version__,
            "latest_version": latest or __version__,
            "download_url": url or GITHUB_RELEASES_URL,
            "release_notes": notes or "",
        }
        
        if latest is not None:
            current_tuple = _parse_version(__version__)
            latest_tuple = _parse_version(latest)
            result["has_update"] = latest_tuple > current_tuple
        
        _last_check_result = result
        return result


def check_for_updates_async(callback, force=False):
    """
    在后台线程中检查更新，完成后调用 callback(result_dict)。
    不会阻塞 UI 线程。
    
    使用示例:
        def on_check_done(result):
            if result["has_update"]:
                show_update_dialog(result)
        
        check_for_updates_async(on_check_done)
    """
    def _worker():
        result = check_for_updates(force=force)
        callback(result)
    
    t = threading.Thread(target=_worker, daemon=True)
    t.start()
    return t
