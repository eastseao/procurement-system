#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""设置页面 - v1.5 - 左右分栏布局"""

import os
import sys
import tkinter as tk
from tkinter import messagebox, filedialog
import customtkinter as ctk

# ── 注册表开机自启 ─────────────────────────────
_REG_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
_REG_NAME = "采购助手"


def _get_exe_path():
    """获取当前程序路径（兼容打包和源码运行）"""
    if hasattr(sys, "_MEIPASS"):
        return sys.executable
    main_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "main.py")
    return main_path


def _open_reg_key(open_mode):
    """打开注册表 Run 键，返回 (hkey, key) 或 (None, None)"""
    try:
        import winreg
        hkey = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            _REG_KEY,
            0,
            winreg.KEY_READ | open_mode,
        )
        return hkey, winreg
    except ImportError:
        return None, None
    except FileNotFoundError:
        return None, None


def is_auto_start_enabled():
    """判断是否已开启开机自启（注册表方式）"""
    hkey, wr = _open_reg_key(0)
    if hkey is None:
        return False
    try:
        wr.QueryValueEx(hkey, _REG_NAME)
        wr.CloseKey(hkey)
        return True
    except FileNotFoundError:
        wr.CloseKey(hkey)
        return False
    except Exception:
        try:
            wr.CloseKey(hkey)
        except Exception:
            pass
        return False


def set_auto_start(enable):
    """设置开机自启：写入/删除注册表 Run 项"""
    import winreg
    exe_path = _get_exe_path()
    try:
        if enable:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                _REG_KEY,
                0,
                winreg.KEY_SET_VALUE,
            )
            # 打包exe直接写路径；开发模式用 python exe + 脚本路径
            if exe_path.lower().endswith(".py"):
                python_exe = sys.executable
                value = f'"{python_exe}" "{exe_path}"'
            else:
                value = f'"{exe_path}"'
            winreg.SetValueEx(key, _REG_NAME, 0, winreg.REG_SZ, value)
            winreg.CloseKey(key)
            return True
        else:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                _REG_KEY,
                0,
                winreg.KEY_SET_VALUE,
            )
            try:
                winreg.DeleteValue(key, _REG_NAME)
            except FileNotFoundError:
                pass
            winreg.CloseKey(key)
            return True
    except Exception as e:
        return False


def get_settings_path():
    """获取设置文件路径"""
    data_dir = os.path.join(os.path.expanduser("~"), "采购管理系统数据")
    os.makedirs(data_dir, exist_ok=True)
    return os.path.join(data_dir, "settings.txt")


def load_settings():
    """从文件加载设置"""
    defaults = {
        "appearance_mode": "light",
        "color_theme": "morandi_warm",
        "auto_start": "0",
        "tray_enabled": "0",
        "data_dir": "",
    }
    path = get_settings_path()
    if not os.path.exists(path):
        return defaults
    
    settings = dict(defaults)
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    k, v = line.split("=", 1)
                    settings[k.strip()] = v.strip()
    except Exception:
        pass
    return settings


def save_settings(settings):
    """保存设置到文件"""
    path = get_settings_path()
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write("# 采购助手设置文件\n")
            for k, v in settings.items():
                f.write(f"{k}={v}\n")
        return True
    except Exception:
        return False


# ── 设置分类定义 ─────────────────────────────
SETTING_CATEGORIES = [
    ("外观设置", "🎨"),
    ("数据管理", "💾"),
    ("启动设置", "🚀"),
    ("系统设置", "⚙️"),
    ("版本介绍", "ℹ️"),
    ("关于作者", "✍️"),
]


class SettingsPage(ctk.CTkFrame):
    def __init__(self, parent, db, colors):
        super().__init__(parent, fg_color=colors["bg"], corner_radius=0)
        self.C = colors
        self.db = db
        self.settings = load_settings()

        # 用注册表真实状态覆盖 settings 中的值
        reg_enabled = is_auto_start_enabled()
        self.settings["auto_start"] = "1" if reg_enabled else "0"

        self._current_category = "外观设置"
        self._build()
        self._show_category("外观设置")  # 默认显示外观设置

    def _build(self):
        # ── 顶部标题栏 ─────────────────────────────
        header = ctk.CTkFrame(self, fg_color=self.C["card"], corner_radius=0, height=64)
        header.pack(fill="x")
        header.pack_propagate(False)

        ctk.CTkLabel(
            header, text="⚙  软件设置",
            font=ctk.CTkFont(family="Microsoft YaHei", size=20, weight="bold"),
            text_color=self.C["text"],
        ).pack(side="left", padx=24, pady=16)

        # ── 主内容区（左右分栏）─────────────────────
        content = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        content.pack(fill="both", expand=True)

        # 左侧分类导航
        left_nav = ctk.CTkFrame(content, width=180, fg_color=self.C["card"], corner_radius=0)
        left_nav.pack(side="left", fill="y", padx=(24, 0), pady=16)
        left_nav.pack_propagate(False)

        ctk.CTkLabel(
            left_nav, text="设置分类",
            font=ctk.CTkFont(family="Microsoft YaHei", size=14, weight="bold"),
            text_color=self.C["text"],
        ).pack(anchor="w", padx=16, pady=(16, 12))

        self._nav_buttons = {}
        for cat_name, cat_icon in SETTING_CATEGORIES:
            btn = ctk.CTkButton(
                left_nav,
                text=f"  {cat_icon}  {cat_name}",
                font=ctk.CTkFont(family="Microsoft YaHei", size=13),
                fg_color="transparent",
                text_color=self.C["text"],
                hover_color=self.C["sidebar_hover"],
                anchor="w",
                height=40,
                corner_radius=8,
                command=lambda c=cat_name: self._show_category(c),
            )
            btn.pack(fill="x", padx=8, pady=2)
            self._nav_buttons[cat_name] = btn

        # 右侧内容区
        self._right_content = ctk.CTkScrollableFrame(content, fg_color="transparent")
        self._right_content.pack(side="left", fill="both", expand=True, padx=(16, 24), pady=16)

    def _show_category(self, category):
        """切换显示的设置分类"""
        self._current_category = category

        # 更新导航按钮高亮
        for cat_name, btn in self._nav_buttons.items():
            if cat_name == category:
                btn.configure(fg_color=self.C["primary_light"], text_color=self.C["primary"])
            else:
                btn.configure(fg_color="transparent", text_color=self.C["text"])

        # 清空右侧内容区
        for widget in self._right_content.winfo_children():
            widget.destroy()

        # 根据分类显示对应内容
        if category == "外观设置":
            self._build_appearance()
        elif category == "数据管理":
            self._build_data_management()
        elif category == "启动设置":
            self._build_startup()
        elif category == "系统设置":
            self._build_system()
        elif category == "版本介绍":
            self._build_version_info()
        elif category == "关于作者":
            self._build_about_author()

    def _build_appearance(self):
        """构建外观设置内容"""
        # 主题外观
        card = ctk.CTkFrame(self._right_content, fg_color=self.C["card"], corner_radius=10)
        card.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(card, text="主题外观",
                     font=ctk.CTkFont(family="Microsoft YaHei", size=14, weight="bold"),
                     text_color=self.C["text"]).pack(anchor="w", padx=20, pady=(16, 8))

        self.appear_var = tk.StringVar(value=self.settings["appearance_mode"])
        modes = [("亮色模式", "light"), ("暗色模式", "dark"), ("跟随系统", "system")]
        for label, value in modes:
            rb = ctk.CTkRadioButton(
                card, text=label, variable=self.appear_var, value=value,
                font=ctk.CTkFont(family="Microsoft YaHei", size=13),
                fg_color=self.C["primary"], hover_color=self.C["primary_hover"],
                command=self._on_appearance_changed,
            )
            rb.pack(anchor="w", padx=28, pady=3)

        ctk.CTkLabel(card,
                     text="选择亮色或暗色模式，\"跟随系统\"根据 Windows 设置自动切换",
                     font=ctk.CTkFont(family="Microsoft YaHei", size=11),
                     text_color=self.C["text_secondary"]).pack(anchor="w", padx=28, pady=(0, 16))

        # 颜色方案
        ctk.CTkLabel(card, text="颜色方案",
                     font=ctk.CTkFont(family="Microsoft YaHei", size=14, weight="bold"),
                     text_color=self.C["text"]).pack(anchor="w", padx=20, pady=(8, 8))

        self.theme_var = tk.StringVar(value=self.settings["color_theme"])
        themes = [("莫兰迪暖色（默认）", "morandi_warm"), ("经典蓝色", "classic_blue")]
        for label, value in themes:
            rb = ctk.CTkRadioButton(
                card, text=label, variable=self.theme_var, value=value,
                font=ctk.CTkFont(family="Microsoft YaHei", size=13),
                fg_color=self.C["primary"], hover_color=self.C["primary_hover"],
            )
            rb.pack(anchor="w", padx=28, pady=3)

        ctk.CTkLabel(card,
                     text="更改后需要重启软件生效",
                     font=ctk.CTkFont(family="Microsoft YaHei", size=11),
                     text_color=self.C["text_secondary"]).pack(anchor="w", padx=28, pady=(4, 16))

        # 保存按钮
        self._add_save_button()

    def _build_data_management(self):
        """构建数据管理内容"""
        card = ctk.CTkFrame(self._right_content, fg_color=self.C["card"], corner_radius=10)
        card.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(card, text="数据存放位置",
                     font=ctk.CTkFont(family="Microsoft YaHei", size=14, weight="bold"),
                     text_color=self.C["text"]).pack(anchor="w", padx=20, pady=(16, 8))

        current_dir = self.settings.get("data_dir", "")
        if not current_dir:
            current_dir = os.path.join(os.path.expanduser("~"), "采购管理系统数据")
        self.data_dir_var = tk.StringVar(value=current_dir)

        path_frame = ctk.CTkFrame(card, fg_color="transparent")
        path_frame.pack(fill="x", padx=20, pady=(0, 8))

        ctk.CTkEntry(
            path_frame, textvariable=self.data_dir_var,
            font=ctk.CTkFont(family="Microsoft YaHei", size=12),
            state="readonly",
        ).pack(side="left", fill="x", expand=True, padx=(0, 8))

        ctk.CTkButton(
            path_frame, text="浏览...", width=80, height=32,
            fg_color=self.C["primary"], hover_color=self.C["primary_hover"],
            font=ctk.CTkFont(size=13),
            command=self._browse_data_dir,
        ).pack(side="right")

        btn_row = ctk.CTkFrame(card, fg_color="transparent")
        btn_row.pack(fill="x", padx=20, pady=(0, 16))
        ctk.CTkButton(
            btn_row, text="打开目录",
            fg_color="transparent", text_color=self.C["primary"],
            font=ctk.CTkFont(size=12),
            command=self._open_data_dir,
        ).pack(side="left")
        ctk.CTkLabel(
            btn_row,
            text="修改后点击「保存设置」生效，数据库将自动迁移",
            font=ctk.CTkFont(size=11),
            text_color=self.C["text_secondary"],
        ).pack(side="left", padx=(12, 0))

        # 保存按钮
        self._add_save_button()

    def _build_startup(self):
        """构建启动设置内容"""
        card = ctk.CTkFrame(self._right_content, fg_color=self.C["card"], corner_radius=10)
        card.pack(fill="x", pady=(0, 12))

        auto_start_val = self.settings.get("auto_start", "0") == "1"
        self.auto_start_var = tk.IntVar(value=1 if auto_start_val else 0)

        ctk.CTkCheckBox(
            card, text="开机自动启动",
            variable=self.auto_start_var,
            font=ctk.CTkFont(family="Microsoft YaHei", size=14),
            checkbox_width=22, checkbox_height=22,
            fg_color=self.C["primary"], hover_color=self.C["primary_hover"],
            command=self._on_auto_start_toggled,
        ).pack(anchor="w", padx=20, pady=16)

        ctk.CTkLabel(card,
                     text="勾选后，采购助手将在 Windows 启动时自动运行",
                     font=ctk.CTkFont(family="Microsoft YaHei", size=11),
                     text_color=self.C["text_secondary"]).pack(anchor="w", padx=42, pady=(0, 16))

        # 保存按钮
        self._add_save_button()

    def _build_system(self):
        """构建系统设置内容"""
        card = ctk.CTkFrame(self._right_content, fg_color=self.C["card"], corner_radius=10)
        card.pack(fill="x", pady=(0, 12))

        tray_val = self.settings.get("tray_enabled", "0") == "1"
        self.tray_enabled_var = tk.IntVar(value=1 if tray_val else 0)

        ctk.CTkCheckBox(
            card, text="常驻任务栏",
            variable=self.tray_enabled_var,
            font=ctk.CTkFont(family="Microsoft YaHei", size=14),
            checkbox_width=22, checkbox_height=22,
            fg_color=self.C["primary"], hover_color=self.C["primary_hover"],
        ).pack(anchor="w", padx=20, pady=16)

        ctk.CTkLabel(card,
                     text="开启后，关闭窗口时将弹出选项，可选择「收纳进任务栏」而非直接退出",
                     font=ctk.CTkFont(family="Microsoft YaHei", size=11),
                     text_color=self.C["text_secondary"]).pack(anchor="w", padx=42, pady=(0, 16))

        # 保存按钮
        self._add_save_button()

    def _build_version_info(self):
        """构建版本介绍内容"""
        card = ctk.CTkFrame(self._right_content, fg_color=self.C["card"], corner_radius=10)
        card.pack(fill="x", pady=(0, 12))

        # 标题
        ctk.CTkLabel(
            card, text="采购助手 · 版本介绍",
            font=ctk.CTkFont(family="Microsoft YaHei", size=18, weight="bold"),
            text_color=self.C["text"],
        ).pack(anchor="w", padx=20, pady=(20, 8))

        # 当前版本 + 作者
        info_frame = ctk.CTkFrame(card, fg_color="transparent")
        info_frame.pack(fill="x", padx=20, pady=(0, 4))
        ctk.CTkLabel(
            info_frame, text="当前版本 V1.5",
            font=ctk.CTkFont(family="Microsoft YaHei", size=13, weight="bold"),
            text_color=self.C["primary"],
        ).pack(side="left")
        ctk.CTkLabel(
            info_frame, text="   作者 EastSeaO",
            font=ctk.CTkFont(family="Microsoft YaHei", size=13),
            text_color=self.C["text_secondary"],
        ).pack(side="left")

        # 即将上传到github
        ctk.CTkLabel(
            card, text="即将上传到 GitHub 的库里进行在线的版本迭代",
            font=ctk.CTkFont(family="Microsoft YaHei", size=12),
            text_color=self.C["text_secondary"],
        ).pack(anchor="w", padx=20, pady=(0, 12))

        # 分隔线
        sep = tk.Frame(card, height=1, bg=self.C["divider"])
        sep.pack(fill="x", padx=20, pady=(0, 12))

        # 一句话简介
        ctk.CTkLabel(
            card, text="一句话简介",
            font=ctk.CTkFont(family="Microsoft YaHei", size=14, weight="bold"),
            text_color=self.C["text"],
        ).pack(anchor="w", padx=20, pady=(0, 6))

        ctk.CTkLabel(
            card, text="轻量、专注的采购桌面工具，覆盖物料下单、报价单、供应商管理、垫付报销等全流程。",
            font=ctk.CTkFont(family="Microsoft YaHei", size=12),
            text_color=self.C["text_secondary"],
            justify="left",
            anchor="w",
        ).pack(fill="x", padx=24, pady=(0, 12))

        # 核心功能
        ctk.CTkLabel(
            card, text="核心功能",
            font=ctk.CTkFont(family="Microsoft YaHei", size=14, weight="bold"),
            text_color=self.C["text"],
        ).pack(anchor="w", padx=20, pady=(0, 6))

        features = [
            "仪表盘 · 物料下单 · 报价单",
            "物料查询 · 供应商管理 · 催款记录",
            "采购垫付 · 差旅报销 · 备忘录",
        ]
        for f in features:
            ctk.CTkLabel(
                card, text=f"  • {f}",
                font=ctk.CTkFont(family="Microsoft YaHei", size=12),
                text_color=self.C["text_secondary"],
                justify="left",
                anchor="w",
            ).pack(fill="x", padx=24, pady=(0, 2))

        # 技术栈
        ctk.CTkLabel(
            card, text="技术栈",
            font=ctk.CTkFont(family="Microsoft YaHei", size=14, weight="bold"),
            text_color=self.C["text"],
        ).pack(anchor="w", padx=20, pady=(12, 6))

        ctk.CTkLabel(
            card, text="Python + CustomTkinter + SQLite",
            font=ctk.CTkFont(family="Microsoft YaHei", size=12),
            text_color=self.C["text_secondary"],
        ).pack(anchor="w", padx=24, pady=(0, 2))
        ctk.CTkLabel(
            card, text="莫兰迪暖色调 UI · Windows 10/11 原生适配",
            font=ctk.CTkFont(family="Microsoft YaHei", size=12),
            text_color=self.C["text_secondary"],
        ).pack(anchor="w", padx=24, pady=(0, 12))

        # 设计亮点
        ctk.CTkLabel(
            card, text="设计亮点",
            font=ctk.CTkFont(family="Microsoft YaHei", size=14, weight="bold"),
            text_color=self.C["text"],
        ).pack(anchor="w", padx=20, pady=(0, 6))

        highlights = [
            "侧边栏可折叠，极简功能导向",
            "窗口置顶 · 开机自启 · 系统托盘",
            "自定义数据存放位置 · 全模块 Excel 导入/导出",
        ]
        for h in highlights:
            ctk.CTkLabel(
                card, text=f"  • {h}",
                font=ctk.CTkFont(family="Microsoft YaHei", size=12),
                text_color=self.C["text_secondary"],
                justify="left",
                anchor="w",
            ).pack(fill="x", padx=24, pady=(0, 2))

        # 分隔线
        sep2 = tk.Frame(card, height=1, bg=self.C["divider"])
        sep2.pack(fill="x", padx=20, pady=(12, 12))

        # 作者寄语
        ctk.CTkLabel(
            card, text="作者寄语",
            font=ctk.CTkFont(family="Microsoft YaHei", size=14, weight="bold"),
            text_color=self.C["text"],
        ).pack(anchor="w", padx=20, pady=(0, 6))

        ctk.CTkLabel(
            card, text="如果你觉得这个程序对你有所帮助，欢迎加作者微信",
            font=ctk.CTkFont(family="Microsoft YaHei", size=12),
            text_color=self.C["text_secondary"],
        ).pack(anchor="w", padx=24, pady=(0, 2))
        ctk.CTkLabel(
            card, text="EastSeaO",
            font=ctk.CTkFont(family="Microsoft YaHei", size=13, weight="bold"),
            text_color=self.C["primary"],
        ).pack(anchor="w", padx=24, pady=(0, 2))
        ctk.CTkLabel(
            card, text="，探讨更多功能。",
            font=ctk.CTkFont(family="Microsoft YaHei", size=12),
            text_color=self.C["text_secondary"],
        ).pack(anchor="w", padx=24, pady=(0, 16))

        # 版权
        ctk.CTkLabel(
            card, text="© 2026 EastSeaO",
            font=ctk.CTkFont(family="Microsoft YaHei", size=11),
            text_color=self.C["text_secondary"],
        ).pack(anchor="w", padx=20, pady=(0, 16))

    def _build_about_author(self):
        """构建关于作者内容"""
        card = ctk.CTkFrame(self._right_content, fg_color=self.C["card"], corner_radius=10)
        card.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(
            card, text="作者信息",
            font=ctk.CTkFont(family="Microsoft YaHei", size=14, weight="bold"),
            text_color=self.C["text"],
        ).pack(anchor="w", padx=20, pady=(16, 8))

        sep = tk.Frame(card, height=1, bg=self.C["divider"])
        sep.pack(fill="x", padx=20, pady=(0, 8))

        author_lines = [
            "作者目前就职于北京同仁堂健康药业（青海）有限公司 采购部，",
            "负责包装采购业务。",
            "",
            "如果你觉得这个程序对你有所帮助，",
            '可以加作者微信 "EastSeaO"，探讨加入更多功能。',
        ]
        for line in author_lines:
            ctk.CTkLabel(
                card, text=line,
                font=ctk.CTkFont(family="Microsoft YaHei", size=12),
                text_color=self.C["text_secondary"],
                justify="left",
                anchor="w",
            ).pack(fill="x", padx=24, pady=(2 if line else 0, 2))

        ctk.CTkLabel(card, text="").pack(pady=(8, 0))

    def _add_save_button(self):
        """在右侧内容区底部添加保存按钮"""
        btn_frame = ctk.CTkFrame(self._right_content, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(8, 24))

        ctk.CTkButton(
            btn_frame, text="✓ 保存设置", width=140, height=40,
            fg_color=self.C["success"], hover_color="#7A9472",
            font=ctk.CTkFont(family="Microsoft YaHei", size=14, weight="bold"),
            command=self._save_all,
        ).pack(side="left", padx=4)

    def _browse_data_dir(self):
        """浏览并选择数据存放目录"""
        current = self.data_dir_var.get()
        if not os.path.exists(current):
            current = os.path.expanduser("~")
        new_dir = filedialog.askdirectory(initialdir=current, title="选择数据存放目录")
        if new_dir:
            self.data_dir_var.set(new_dir)

    def _open_data_dir(self):
        """在资源管理器中打开数据目录"""
        path = self.data_dir_var.get()
        if not path:
            path = os.path.join(os.path.expanduser("~"), "采购管理系统数据")
        if os.path.exists(path):
            os.startfile(path)
        else:
            messagebox.showwarning("提示", f"目录不存在：\n{path}")

    def _on_appearance_changed(self):
        mode = self.appear_var.get()
        ctk.set_appearance_mode(mode)

    def _on_auto_start_toggled(self):
        enabled = self.auto_start_var.get() == 1
        if enabled:
            ok = set_auto_start(True)
            if not ok:
                messagebox.showwarning("提示", "开机自启动设置失败，请检查系统权限")
                self.auto_start_var.set(0)
            else:
                messagebox.showinfo("成功", "已开启开机自动启动")
        else:
            set_auto_start(False)
            messagebox.showinfo("成功", "已关闭开机自动启动")

    def _save_all(self):
        """保存所有设置"""
        old_data_dir = self.settings.get("data_dir", "")
        new_data_dir = self.data_dir_var.get().strip()
        self.settings["data_dir"] = new_data_dir

        self.settings["appearance_mode"] = self.appear_var.get()
        self.settings["color_theme"] = self.theme_var.get()
        self.settings["auto_start"] = "1" if self.auto_start_var.get() == 1 else "0"
        self.settings["tray_enabled"] = "1" if self.tray_enabled_var.get() == 1 else "0"

        # 数据库迁移
        if old_data_dir != new_data_dir:
            default_dir = os.path.join(os.path.expanduser("~"), "采购管理系统数据")
            src_dir = old_data_dir if old_data_dir else default_dir
            dst_dir = new_data_dir if new_data_dir else default_dir
            src_db = os.path.join(src_dir, "procurement.db")
            dst_db = os.path.join(dst_dir, "procurement.db")
            if os.path.exists(src_db) and src_db != dst_db:
                try:
                    import shutil
                    os.makedirs(dst_dir, exist_ok=True)
                    if os.path.exists(dst_db):
                        if messagebox.askyesno("文件已存在", f"目标位置已有数据库文件：\n{dst_db}\n\n是否覆盖？"):
                            shutil.copy2(src_db, dst_db)
                    else:
                        shutil.copy2(src_db, dst_db)
                        messagebox.showinfo("迁移成功", f"数据库已从\n{src_db}\n复制到\n{dst_db}")
                except Exception as e:
                    messagebox.showerror("迁移失败", f"数据库迁移失败：\n{e}")

        if save_settings(self.settings):
            messagebox.showinfo("保存成功", "设置已保存，部分更改需要重启软件后生效")
        else:
            messagebox.showerror("保存失败", "设置保存失败，请重试")
