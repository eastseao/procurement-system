#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""设置页面 - v1.7 - 左右分栏布局"""

import os
import sys
import webbrowser
import tkinter as tk
from tkinter import messagebox, filedialog
import customtkinter as ctk

from version import __version__, GITHUB_RELEASES_URL
from ui_utils import WheelScrollFrame

# ── PIL 可用性检查 ──
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


def _get_resource_path(rel_path):
    """兼容PyInstaller打包后的资源路径"""
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, rel_path)
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), rel_path)

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
        "theme":           "light",
        "auto_start":      "0",
        "tray_enabled":   "0",
        "data_dir":       "",
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
    ("数据备份", "💾"),
    ("软件介绍", "ℹ️"),
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
        header = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0, height=52)
        header.pack(fill="x", padx=20, pady=(16, 8))
        header.pack_propagate(False)

        ctk.CTkLabel(
            header, text="软件设置",
            font=ctk.CTkFont(family="Microsoft YaHei", size=16, weight="bold"),
            text_color=self.C["text"],
        ).pack(side="left", pady=14)

        # ── 主内容区（左右分栏）─────────────────────
        content = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        content.pack(fill="both", expand=True)

        # 左侧分类导航（圆角卡片）
        left_nav = ctk.CTkFrame(content, width=180, fg_color=self.C["card"], corner_radius=12)
        left_nav.pack(side="left", fill="y", padx=(24, 0), pady=16)
        left_nav.pack_propagate(False)


        self._nav_buttons = {}
        for cat_name, cat_icon in SETTING_CATEGORIES:
            btn = ctk.CTkButton(
                left_nav,
                text=f"  {cat_icon}  {cat_name}",
                font=ctk.CTkFont(family="Microsoft YaHei", size=14),
                fg_color="transparent",
                text_color=self.C["text"],
                hover_color=self.C["sidebar_hover"],
                anchor="w",
                height=40,
                corner_radius=20,
                command=lambda c=cat_name: self._show_category(c),
            )
            btn.pack(fill="x", padx=8, pady=2)
            self._nav_buttons[cat_name] = btn

        # 分隔线
        separator = tk.Frame(content, width=1, bg="#E0D6CC")
        separator.pack(side="left", fill="y")


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
        elif category == "数据备份":
            self._build_data_backup()
        elif category == "软件介绍":
            self._build_version_info()
        elif category == "关于作者":
            self._build_about_author()

    def _build_appearance(self):
        """构建外观设置内容"""
        # 主题外观
        card = ctk.CTkFrame(self._right_content, fg_color=self.C["card"], corner_radius=self.C["radius_card"])
        card.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(card, text="主题外观",
                     font=ctk.CTkFont(family="Microsoft YaHei", size=16, weight="bold"),
                     text_color=self.C["text"]).pack(anchor="w", padx=20, pady=(16, 8))

        self.appear_var = tk.StringVar(value=self.settings["appearance_mode"])
        modes = [("亮色模式", "light"), ("暗色模式", "dark"), ("跟随系统", "system")]
        for label, value in modes:
            rb = ctk.CTkRadioButton(
                card, text=label, variable=self.appear_var, value=value,
                font=ctk.CTkFont(family="Microsoft YaHei", size=14),
                fg_color=self.C["primary"], hover_color=self.C["primary_hover"],
                command=self._on_appearance_changed,
            )
            rb.pack(anchor="w", padx=28, pady=3)

        ctk.CTkLabel(card,
                     text="选择亮色或暗色模式，\"跟随系统\"根据 Windows 设置自动切换",
                     font=ctk.CTkFont(family="Microsoft YaHei", size=13),
                     text_color=self.C["text_secondary"]).pack(anchor="w", padx=28, pady=(0, 16))

        # 主题配色（P2 暗色模式）
        ctk.CTkLabel(card, text="主题配色",
                     font=ctk.CTkFont(family="Microsoft YaHei", size=16, weight="bold"),
                     text_color=self.C["text"]).pack(anchor="w", padx=20, pady=(16, 8))

        self.theme_mode_var = tk.StringVar(value=self.settings.get("theme", "light"))
        theme_modes = [("亮色配色", "light"), ("暗色配色", "dark")]
        for label, value in theme_modes:
            rb = ctk.CTkRadioButton(
                card, text=label, variable=self.theme_mode_var, value=value,
                font=ctk.CTkFont(family="Microsoft YaHei", size=14),
                fg_color=self.C["primary"], hover_color=self.C["primary_hover"],
            )
            rb.pack(anchor="w", padx=28, pady=3)

        ctk.CTkLabel(card,
                     text="更改后需要重启软件生效",
                     font=ctk.CTkFont(family="Microsoft YaHei", size=12),
                     text_color=self.C["text_secondary"]).pack(anchor="w", padx=28, pady=(0, 16))

        # 颜色方案
        ctk.CTkLabel(card, text="颜色方案",
                     font=ctk.CTkFont(family="Microsoft YaHei", size=16, weight="bold"),
                     text_color=self.C["text"]).pack(anchor="w", padx=20, pady=(8, 8))

        self.theme_var = tk.StringVar(value=self.settings["color_theme"])
        themes = [("莫兰迪暖色（默认）", "morandi_warm"), ("经典蓝色", "classic_blue")]
        for label, value in themes:
            rb = ctk.CTkRadioButton(
                card, text=label, variable=self.theme_var, value=value,
                font=ctk.CTkFont(family="Microsoft YaHei", size=14),
                fg_color=self.C["primary"], hover_color=self.C["primary_hover"],
            )
            rb.pack(anchor="w", padx=28, pady=3)

        ctk.CTkLabel(card,
                     text="更改后需要重启软件生效",
                     font=ctk.CTkFont(family="Microsoft YaHei", size=13),
                     text_color=self.C["text_secondary"]).pack(anchor="w", padx=28, pady=(4, 16))

        # 保存按钮
        self._add_save_button()

    def _build_data_management(self):
        """构建数据管理内容"""
        card = ctk.CTkFrame(self._right_content, fg_color=self.C["card"], corner_radius=self.C["radius_card"])
        card.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(card, text="数据存放位置",
                     font=ctk.CTkFont(family="Microsoft YaHei", size=16, weight="bold"),
                     text_color=self.C["text"]).pack(anchor="w", padx=20, pady=(16, 8))

        current_dir = self.settings.get("data_dir", "")
        if not current_dir:
            current_dir = os.path.join(os.path.expanduser("~"), "采购管理系统数据")
        self.data_dir_var = tk.StringVar(value=current_dir)

        path_frame = ctk.CTkFrame(card, fg_color="transparent")
        path_frame.pack(fill="x", padx=20, pady=(0, 8))

        ctk.CTkEntry(
            path_frame, textvariable=self.data_dir_var,
            font=ctk.CTkFont(family="Microsoft YaHei", size=13),
            state="readonly",
        ).pack(side="left", fill="x", expand=True, padx=(0, 8))

        ctk.CTkButton(
            path_frame, text="浏览...", width=80, height=32,
            fg_color=self.C["primary"], hover_color=self.C["primary_hover"],
            font=ctk.CTkFont(size=14),
            command=self._browse_data_dir, corner_radius=20,
        ).pack(side="right")

        btn_row = ctk.CTkFrame(card, fg_color="transparent")
        btn_row.pack(fill="x", padx=20, pady=(0, 16))
        ctk.CTkButton(
            btn_row, text="打开目录",
            fg_color="transparent", text_color=self.C["primary"],
            font=ctk.CTkFont(size=13),
            command=self._open_data_dir, corner_radius=20,
        ).pack(side="left")
        ctk.CTkLabel(
            btn_row,
            text="修改后点击「保存设置」生效，数据库将自动迁移",
            font=ctk.CTkFont(size=12),
            text_color=self.C["text_secondary"],
        ).pack(side="left", padx=(12, 0))

        # 保存按钮
        self._add_save_button()

    def _build_startup(self):
        """构建启动设置内容"""
        card = ctk.CTkFrame(self._right_content, fg_color=self.C["card"], corner_radius=self.C["radius_card"])
        card.pack(fill="x", pady=(0, 12))

        auto_start_val = self.settings.get("auto_start", "0") == "1"
        self.auto_start_var = tk.IntVar(value=1 if auto_start_val else 0)

        ctk.CTkCheckBox(
            card, text="开机自动启动",
            variable=self.auto_start_var,
            font=ctk.CTkFont(family="Microsoft YaHei", size=16),
            checkbox_width=22, checkbox_height=22,
            fg_color=self.C["primary"], hover_color=self.C["primary_hover"],
            command=self._on_auto_start_toggled,
        ).pack(anchor="w", padx=20, pady=16)

        ctk.CTkLabel(card,
                     text="勾选后，采购助手将在 Windows 启动时自动运行",
                     font=ctk.CTkFont(family="Microsoft YaHei", size=12),
                     text_color=self.C["text_secondary"]).pack(anchor="w", padx=42, pady=(0, 16))

        # 保存按钮
        self._add_save_button()

    def _build_system(self):
        """构建系统设置内容"""
        card = ctk.CTkFrame(self._right_content, fg_color=self.C["card"], corner_radius=self.C["radius_card"])
        card.pack(fill="x", pady=(0, 12))

        tray_val = self.settings.get("tray_enabled", "0") == "1"
        self.tray_enabled_var = tk.IntVar(value=1 if tray_val else 0)

        ctk.CTkCheckBox(
            card, text="常驻任务栏",
            variable=self.tray_enabled_var,
            font=ctk.CTkFont(family="Microsoft YaHei", size=16),
            checkbox_width=22, checkbox_height=22,
            fg_color=self.C["primary"], hover_color=self.C["primary_hover"],
        ).pack(anchor="w", padx=20, pady=16)

        ctk.CTkLabel(card,
                     text="开启后，关闭窗口时将弹出选项，可选择「收纳进任务栏」而非直接退出",
                     font=ctk.CTkFont(family="Microsoft YaHei", size=12),
                     text_color=self.C["text_secondary"]).pack(anchor="w", padx=42, pady=(0, 16))

        # ── 核心指标选择 ──
        ctk.CTkLabel(card, text="看板核心指标",
                     font=ctk.CTkFont(family="Microsoft YaHei", size=16, weight="bold"),
                     text_color=self.C["text"]).pack(anchor="w", padx=20, pady=(16, 8))

        ctk.CTkLabel(card,
                     text="选择在看板页面显示的核心指标卡片（勾选后需刷新看板生效）",
                     font=ctk.CTkFont(family="Microsoft YaHei", size=12),
                     text_color=self.C["text_secondary"]).pack(anchor="w", padx=20, pady=(0, 8))

        # KPI 卡片选项
        self.kpi_check_vars = {}
        kpi_options = [
            ("packaging", "物料下单（处理中/已完成）"),
            ("collection", "催款记录（总条数）"),
            ("purchase", "采购垫付（总笔数/待报销）"),
            ("travel", "差旅报销（行程数/待报销）"),
            ("contract_pending", "待签合同数"),
            ("compare_month", "本月比价次数"),
        ]
        default_kpis = [k.strip() for k in self.settings.get("kpi_cards", "packaging,collection,purchase,travel").split(",")]
        for key, label in kpi_options:
            var = tk.IntVar(value=1 if key in default_kpis else 0)
            self.kpi_check_vars[key] = var
            cb = ctk.CTkCheckBox(
                card, text=label, variable=var,
                font=ctk.CTkFont(family="Microsoft YaHei", size=13),
                checkbox_width=18, checkbox_height=18,
                fg_color=self.C["primary"], hover_color=self.C["primary_hover"],
            )
            cb.pack(anchor="w", padx=28, pady=2)

        # ── 快捷键说明 ──
        ctk.CTkLabel(card, text="全局快捷键",
                     font=ctk.CTkFont(family="Microsoft YaHei", size=16, weight="bold"),
                     text_color=self.C["text"]).pack(anchor="w", padx=20, pady=(16, 8))

        hotkeys = [
            ("F11", "切换全屏模式 / Esc 退出全屏"),
            ("Ctrl + S", "保存当前页面数据"),
            ("Ctrl + F", "聚焦搜索框"),
            ("Ctrl + E", "导出当前列表数据"),
        ]
        for key, desc in hotkeys:
            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=28, pady=2)
            key_label = ctk.CTkLabel(
                row, text=key, width=80,
                font=ctk.CTkFont(family="Consolas", size=13, weight="bold"),
                text_color=self.C["primary"],
                anchor="center",
            )
            key_label.pack(side="left")
            ctk.CTkLabel(
                row, text=desc,
                font=ctk.CTkFont(family="Microsoft YaHei", size=12),
                text_color=self.C["text_secondary"],
            ).pack(side="left", padx=(8, 0))

        # 保存按钮
        self._add_save_button()

    def _build_data_backup(self):
        """构建数据备份与恢复内容"""
        card = ctk.CTkFrame(self._right_content, fg_color=self.C["card"], corner_radius=self.C["radius_card"])
        card.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(card, text="数据备份",
                     font=ctk.CTkFont(family="Microsoft YaHei", size=16, weight="bold"),
                     text_color=self.C["text"]).pack(anchor="w", padx=20, pady=(16, 8))

        ctk.CTkLabel(card,
                     text="将整个数据库打包为 ZIP 文件，可在需要时恢复",
                     font=ctk.CTkFont(family="Microsoft YaHei", size=12),
                     text_color=self.C["text_secondary"]).pack(anchor="w", padx=20, pady=(0, 12))

        # 备份按钮行
        btn_row = ctk.CTkFrame(card, fg_color="transparent")
        btn_row.pack(fill="x", padx=20, pady=(0, 8))

        ctk.CTkButton(
            btn_row, text="📦 备份数据", width=140, height=36,
            fg_color=self.C["success"], hover_color="#7A9A6E",
            font=ctk.CTkFont(size=14),
            command=self._backup_database, corner_radius=20,
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            btn_row, text="📂 恢复数据", width=140, height=36,
            fg_color="#B56A6A", hover_color="#A05858",
            font=ctk.CTkFont(size=14),
            command=self._restore_database, corner_radius=20,
        ).pack(side="left")

        # 备份状态标签
        self.backup_status_label = ctk.CTkLabel(
            card, text="",
            font=ctk.CTkFont(family="Microsoft YaHei", size=12),
            text_color=self.C["text_secondary"],
        )
        self.backup_status_label.pack(anchor="w", padx=20, pady=(8, 4))

        # ── 恢复默认设置 ──
        sep = tk.Frame(card, height=1, bg=self.C["divider"])
        sep.pack(fill="x", padx=20, pady=(16, 12))

        ctk.CTkLabel(card, text="重置为默认设置",
                     font=ctk.CTkFont(family="Microsoft YaHei", size=16, weight="bold"),
                     text_color=self.C["text"]).pack(anchor="w", padx=20, pady=(0, 8))

        ctk.CTkLabel(card,
                     text="将窗口大小、筛选条件、表列宽等恢复到初始状态",
                     font=ctk.CTkFont(family="Microsoft YaHei", size=12),
                     text_color=self.C["text_secondary"]).pack(anchor="w", padx=20, pady=(0, 12))

        ctk.CTkButton(
            card, text="🔄 恢复默认设置", width=160, height=34,
            fg_color="#C9A96E", hover_color="#B8985E",
            font=ctk.CTkFont(size=13),
            command=self._reset_to_defaults, corner_radius=20,
        ).pack(anchor="w", padx=28)

        # 保存按钮
        self._add_save_button()

    def _backup_database(self):
        """备份数据库到用户选择的目录"""
        import shutil
        from datetime import datetime as dt
        db_path = os.path.join(self.settings.get("data_dir", ""), "procurement.db")
        if not os.path.exists(db_path):
            default_dir = os.path.join(os.path.expanduser("~"), "采购管理系统数据")
            db_path = os.path.join(default_dir, "procurement.db")

        if not os.path.exists(db_path):
            messagebox.showerror("错误", "未找到数据库文件")
            return

        save_dir = filedialog.askdirectory(title="选择备份保存位置")
        if not save_dir:
            return

        timestamp = dt.now().strftime("%Y%m%d_%H%M%S")
        zip_name = f"采购助手备份_{timestamp}.zip"
        zip_path = os.path.join(save_dir, zip_name)

        try:
            import zipfile
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                zf.write(db_path, "procurement.db")
            size_mb = os.path.getsize(zip_path) / (1024 * 1024)
            self.backup_status_label.configure(text=f"✅ 备份成功：{zip_name} ({size_mb:.1f}MB)")
            messagebox.showinfo("备份成功", f"数据库已备份到:\n{zip_path}")
        except Exception as e:
            messagebox.showerror("备份失败", f"备份数据库失败：\n{e}")
            self.backup_status_label.configure(text=f"❌ 备份失败：{e}")

    def _restore_database(self):
        """从备份恢复数据库"""
        filetypes=[("ZIP 压缩包", "*.zip"), ("数据库文件", "*.db *.sqlite"), ("所有文件", "*.*")]
        restore_path = filedialog.askopenfilename(title="选择备份文件", filetypes=filetypes)
        if not restore_path:
            return

        if not messagebox.askyesno("确认恢复",
            "恢复数据将覆盖当前数据库！\n\n建议先手动备份当前数据库。\n\n是否继续？"):
            return

        db_path = os.path.join(self.settings.get("data_dir", ""), "procurement.db")
        if not os.path.exists(db_path):
            default_dir = os.path.join(os.path.expanduser("~"), "采购管理系统数据")
            db_path = os.path.join(default_dir, "procurement.db")

        try:
            import zipfile
            if restore_path.endswith(".zip"):
                # 从 ZIP 提取
                with zipfile.ZipFile(restore_path, 'r') as zf:
                    names = zf.namelist()
                    if "procurement.db" in names:
                        zf.extract("procurement.db", os.path.dirname(db_path))
                    else:
                        # 取第一个 .db 文件
                        db_files = [n for n in names if n.endswith(".db")]
                        if db_files:
                            zf.extract(db_files[0], os.path.dirname(db_path))
                            import shutil
                            extracted = os.path.join(os.path.dirname(db_path), db_files[0])
                            shutil.copy2(extracted, db_path)
            else:
                # 直接复制 DB 文件
                import shutil
                shutil.copy2(restore_path, db_path)

            messagebox.showinfo("恢复成功", "数据库恢复成功！\n\n请重启软件以加载新数据。")
            self.backup_status_label.configure(text="✅ 数据库恢复成功，请重启软件")
        except Exception as e:
            messagebox.showerror("恢复失败", f"恢复数据库失败：\n{e}")

    def _reset_to_defaults(self):
        """恢复默认设置"""
        if not messagebox.askyesno("确认重置",
            "将恢复以下设置为默认值：\n\n• 窗口大小和位置\n• 表格列宽\n• 筛选条件\n\n是否继续？"):
            return

        try:
            # 清除窗口位置/大小相关设置
            for key in ["window_width", "window_height", "window_x", "window_y"]:
                self.settings.pop(key, None)

            # 保存
            save_settings(self.settings)
            messagebox.showinfo("重置成功", "已恢复默认设置！\n\n请重启软件生效。")
        except Exception as e:
            messagebox.showerror("重置失败", f"重置失败：{e}")

    def _build_version_info(self):
        """构建软件介绍内容"""
        card = ctk.CTkFrame(self._right_content, fg_color=self.C["card"], corner_radius=self.C["radius_card"])
        card.pack(fill="x", pady=(0, 12))

        # ── 标题栏 ──────────────────────────────
        ctk.CTkLabel(
            card, text="采购助手 · 软件介绍",
            font=ctk.CTkFont(family="Microsoft YaHei", size=20, weight="bold"),
            text_color=self.C["text"],
        ).pack(anchor="w", padx=20, pady=(20, 10))

        # ── 当前版本 ──────────────
        ver_row = ctk.CTkFrame(card, fg_color="transparent")
        ver_row.pack(fill="x", padx=20, pady=(0, 4))

        ctk.CTkLabel(
            ver_row, text=f"当前版本  V{__version__}",
            font=ctk.CTkFont(family="Microsoft YaHei", size=17, weight="bold"),
            text_color=self.C["primary"],
        ).pack(side="left")

        # ── GitHub Releases 链接 ────────────────
        github_frame = ctk.CTkFrame(card, fg_color=self.C["primary_light"], corner_radius=8)
        github_frame.pack(fill="x", padx=20, pady=(8, 12))

        ctk.CTkLabel(
            github_frame, text="📦  已托管至 GitHub，支持在线版本迭代与自动更新",
            font=ctk.CTkFont(family="Microsoft YaHei", size=13),
            text_color=self.C["text"],
        ).pack(anchor="w", padx=14, pady=(10, 2))

        # 按钮行：前往下载 + 检查更新
        btn_row = ctk.CTkFrame(github_frame, fg_color="transparent")
        btn_row.pack(fill="x", padx=14, pady=(4, 10))

        release_btn = ctk.CTkButton(
            btn_row, text="🔗 前往 Releases 下载最新版本",
            width=240, height=34,
            fg_color=self.C["primary"], hover_color=self.C["primary_hover"],
            font=ctk.CTkFont(family="Microsoft YaHei", size=13, weight="bold"),
            corner_radius=20,
            command=lambda: webbrowser.open(GITHUB_RELEASES_URL),
        )
        release_btn.pack(side="left", padx=(0, 10))

        check_update_btn = ctk.CTkButton(
            btn_row, text="🔄 检查更新",
            width=110, height=34,
            fg_color="#6B8FA3", hover_color="#5A7A93",
            font=ctk.CTkFont(family="Microsoft YaHei", size=13, weight="bold"),
            corner_radius=20,
            command=self._on_check_update,
        )
        check_update_btn.pack(side="left")

        # ── 分隔线 ──────────────────────────────
        sep = tk.Frame(card, height=1, bg=self.C["divider"])
        sep.pack(fill="x", padx=20, pady=(4, 12))

        # ── 一句话简介 ──────────────────────────
        ctk.CTkLabel(
            card, text="一句话简介",
            font=ctk.CTkFont(family="Microsoft YaHei", size=16, weight="bold"),
            text_color=self.C["text"],
        ).pack(anchor="w", padx=20, pady=(0, 6))

        ctk.CTkLabel(
            card, text="专为食品行业包装采购打造的桌面工具，覆盖物料下单、三方比价、报价合同、供应商管理、\n成品BOM、应付垫付报销、待办备忘等全流程，一站式提升采购效率。",
            font=ctk.CTkFont(family="Microsoft YaHei", size=13),
            text_color=self.C["text_secondary"],
            justify="left", anchor="w",
        ).pack(fill="x", padx=24, pady=(0, 12))

        # ── 功能模块介绍 ──────────────────────
        ctk.CTkLabel(
            card, text="功能模块介绍",
            font=ctk.CTkFont(family="Microsoft YaHei", size=16, weight="bold"),
            text_color=self.C["text"],
        ).pack(anchor="w", padx=20, pady=(14, 6))

        modules = [
            ("📈 采购看板",     "核心指标概览、KPI 圆角卡片、最新活动动态实时推送"),
            ("📦 物料下单",     "创建和管理包装物料采购订单，支持合同上传自动解析"),
            ("📑 报价管理",     "生成产品包装报价单，内置 Excel 模板，支持一键导出"),
            ("🤝 三方比价",     "多家供应商报价对比，支持阶梯拆分、自动生成比价表"),
            ("📄 合同生成",     "自动生成采购合同，支持自定义模板和签字区域"),
            ("🏭 厂家管理",     "供应商信息档案维护，联系方式、资质文件统一管理"),
            ("🔎 物料查询",     "多条件筛选物料信息，支持 CSV 导入和 Excel 导出"),
            ("📋 成品 BOM",     "产品物料清单管理，支持 Excel 导入导出和批量编辑"),
            ("💰 应付管理",     "催款记录与应付账款跟踪，掌握回款与应付动态"),
            ("💳 垫付管理",     "采购垫付款项记录，关联报销流程闭环管理"),
            ("🧾 差旅报销",     "差旅费用明细录入与汇总统计，支持多维度筛选"),
            ("📝 待办事项",     "工作备忘录管理，支持分类检索、关键字搜索"),
            ("⚙️ 系统设置",     "外观主题切换、数据目录自定义、开机自启、托盘常驻"),
        ]
        
        for title, desc in modules:
            module_frame = ctk.CTkFrame(card, fg_color="transparent")
            module_frame.pack(fill="x", padx=24, pady=(0, 6))
            
            ctk.CTkLabel(
                module_frame, text=title,
                font=ctk.CTkFont(family="Microsoft YaHei", size=13, weight="bold"),
                text_color=self.C["primary"],
                width=120,
            ).pack(side="left", anchor="w")
            
            ctk.CTkLabel(
                module_frame, text=desc,
                font=ctk.CTkFont(family="Microsoft YaHei", size=12),
                text_color=self.C["text_secondary"],
                justify="left", anchor="w",
            ).pack(side="left", padx=(8, 0), fill="x", expand=True)

        # ── 技术栈 ──────────────────────────
        ctk.CTkLabel(
            card, text="技术栈",
            font=ctk.CTkFont(family="Microsoft YaHei", size=16, weight="bold"),
            text_color=self.C["text"],
        ).pack(anchor="w", padx=20, pady=(0, 6))

        tech_stack = [
            "Python 3.12 + CustomTkinter 5.2（桌面 GUI 框架）",
            "SQLite 数据库（轻量本地存储，零配置）",
            "Pillow（图标与图像处理）",
            "PyInstaller（单文件 EXE 打包分发）",
        ]
        for tech in tech_stack:
            ctk.CTkLabel(
                card, text=f"  • {tech}",
                font=ctk.CTkFont(family="Microsoft YaHei", size=13),
                text_color=self.C["text_secondary"],
                justify="left", anchor="w",
            ).pack(fill="x", padx=24, pady=(0, 2))

        # ── 分隔线 ──────────────────────────
        sep3 = tk.Frame(card, height=1, bg=self.C["divider"])
        sep3.pack(fill="x", padx=20, pady=(12, 4))

        # ── 设计亮点 ──────────────────────────
        ctk.CTkLabel(
            card, text="设计亮点",
            font=ctk.CTkFont(family="Microsoft YaHei", size=16, weight="bold"),
            text_color=self.C["text"],
        ).pack(anchor="w", padx=20, pady=(0, 6))

        design_highlights = [
            "侧边栏可折叠，极简功能导向",
            "窗口置顶 · 开机自启 · 系统托盘",
            "自定义数据存放位置 · 全模块 Excel 导入/导出",
            "启动自动检测 GitHub Releases · 在线更新提醒",
        ]
        for h in design_highlights:
            ctk.CTkLabel(
                card, text=f"  • {h}",
                font=ctk.CTkFont(family="Microsoft YaHei", size=13),
                text_color=self.C["text_secondary"],
                justify="left", anchor="w",
            ).pack(fill="x", padx=24, pady=(0, 2))

        # ── 版权 ──────────────────────────────
        sep4 = tk.Frame(card, height=1, bg=self.C["divider"])
        sep4.pack(fill="x", padx=20, pady=(14, 10))
        ctk.CTkLabel(
            card, text="© 2026 EastSeaO",
            font=ctk.CTkFont(family="Microsoft YaHei", size=12),
            text_color=self.C["text_secondary"],
        ).pack(anchor="w", padx=20, pady=(0, 14))
    def _on_check_update(self):
        """手动检查更新"""
        from version import check_for_updates_async
        
        def callback(result):
            if result["has_update"]:
                messagebox.showinfo(
                    "发现新版本",
                    f"检测到新版本 V{result['latest_version']}！\n"
                    f"当前版本：V{result['current_version']}\n\n"
                    f"请前往 GitHub Releases 下载。"
                )
                webbrowser.open(result["download_url"])
            else:
                messagebox.showinfo(
                    "已是最新版本",
                    f"当前版本 V{result['current_version']} 已是最新。\n"
                    f"GitHub 上暂无更新的 Release。"
                )
        
        check_for_updates_async(callback, force=True)

    def _build_about_author(self):
        """构建关于作者内容"""
        card = ctk.CTkFrame(self._right_content, fg_color=self.C["card"], corner_radius=self.C["radius_card"])
        card.pack(fill="x", pady=(0, 12))

        # ── 标题 ──────────────────────────
        ctk.CTkLabel(
            card, text="关于作者",
            font=ctk.CTkFont(family="Microsoft YaHei", size=20, weight="bold"),
            text_color=self.C["text"],
        ).pack(anchor="w", padx=20, pady=(20, 10))

        sep = tk.Frame(card, height=1, bg=self.C["divider"])
        sep.pack(fill="x", padx=20, pady=(0, 12))

        # ── 作者信息（左侧头像 + 右侧信息）──────────────────────
        info_container = ctk.CTkFrame(card, fg_color="transparent")
        info_container.pack(fill="x", padx=20, pady=(0, 12))

        # 左侧：作者头像
        avatar_frame = ctk.CTkFrame(info_container, fg_color="transparent")
        avatar_frame.pack(side="left", padx=(0, 20))

        avatar_path = _get_resource_path("assets/avatar.png")
        if os.path.exists(avatar_path) and PIL_AVAILABLE:
            try:
                avatar_img = ctk.CTkImage(
                    light_image=Image.open(avatar_path),
                    size=(200, 200))
                avatar_label = ctk.CTkLabel(
                    avatar_frame, image=avatar_img, text="")
                avatar_label.image = avatar_img  # 保持引用
                avatar_label.pack()
            except Exception:
                pass

        # 右侧：作者信息
        info_frame = ctk.CTkFrame(info_container, fg_color="transparent")
        info_frame.pack(side="left", fill="both", expand=True)

        spacer = ctk.CTkFrame(info_frame, fg_color="transparent", height=50)
        spacer.pack()

        author_lines = [
            ("👤", "作者", "王维（微信：EastSeaO）"),
            ("🏢", "就职", "北京同仁堂健康药业（青海）有限公司"),
            ("💼", "部门", "采购部 · 包装采购业务"),
        ]

        for icon, label, value in author_lines:
            row = ctk.CTkFrame(info_frame, fg_color="transparent")
            row.pack(fill="x", padx=4, pady=6)

            ctk.CTkLabel(
                row, text=f"{icon}  {label}：",
                font=ctk.CTkFont(family="Microsoft YaHei", size=14),
                text_color=self.C["text"],
                width=80,
            ).pack(side="left")

            ctk.CTkLabel(
                row, text=value,
                font=ctk.CTkFont(family="Microsoft YaHei", size=14, weight="bold"),
                text_color=self.C["primary"],
            ).pack(side="left")

        # ── 分隔线 ──────────────────────────
        sep2 = tk.Frame(card, height=1, bg=self.C["divider"])
        sep2.pack(fill="x", padx=20, pady=(16, 12))

        # ── 作者自述（来自 author2.0.md）────────────────────────
        ctk.CTkLabel(
            card, text="作者自述",
            font=ctk.CTkFont(family="Microsoft YaHei", size=16, weight="bold"),
            text_color=self.C["text"],
        ).pack(anchor="w", padx=20, pady=(0, 8))

        author_intro = (
            "作为一线采购从业者，作者在日常工作中发现传统手工台账、分散的 Excel 文件\n"
            "难以满足采购全流程的跟踪与管理需求。因此，利用业余时间独立自主开发了\n"
            '"采购助手"桌面端管理系统，覆盖物料下单、报价比价、合同生成、垫付报销、\n'
            "催款台账等核心业务环节。"
        )
        ctk.CTkLabel(
            card, text=author_intro,
            font=ctk.CTkFont(family="Microsoft YaHei", size=13),
            text_color=self.C["text_secondary"],
            justify="left", anchor="w",
        ).pack(fill="x", padx=24, pady=(0, 8))

        author_usage = (
            "本系统已在同仁堂健康药业（青海）采购部实际运行使用，并持续迭代优化。\n"
            "如果你对系统功能有任何建议，或者希望合作开发更多定制化功能，\n"
            '欢迎通过微信 EastSeaO 与作者交流。'
        )
        ctk.CTkLabel(
            card, text=author_usage,
            font=ctk.CTkFont(family="Microsoft YaHei", size=13),
            text_color=self.C["text_secondary"],
            justify="left", anchor="w",
        ).pack(fill="x", padx=24, pady=(0, 12))

        # ── 座右铭 ──────────────────────────
        quote_frame = ctk.CTkFrame(card, fg_color=self.C["primary_light"], corner_radius=8)
        quote_frame.pack(fill="x", padx=20, pady=(0, 12))

        ctk.CTkLabel(
            quote_frame, text='"用代码解决重复劳动，用数据提升采购效率。"',
            font=ctk.CTkFont(family="Microsoft YaHei", size=14, weight="bold", slant="italic"),
            text_color=self.C["primary"],
        ).pack(anchor="w", padx=16, pady=(12, 12))

        # ── 分隔线 ──────────────────────────
        sep3 = tk.Frame(card, height=1, bg=self.C["divider"])
        sep3.pack(fill="x", padx=20, pady=(12, 8))

        # ── 联系方式 ──────────────────────────
        ctk.CTkLabel(
            card, text="联系方式",
            font=ctk.CTkFont(family="Microsoft YaHei", size=16, weight="bold"),
            text_color=self.C["text"],
        ).pack(anchor="w", padx=20, pady=(0, 8))

        ctk.CTkLabel(
            card, text="如果你觉得这个程序对你有所帮助，",
            font=ctk.CTkFont(family="Microsoft YaHei", size=13),
            text_color=self.C["text_secondary"],
        ).pack(anchor="w", padx=24, pady=(0, 2))
        ctk.CTkLabel(
            card, text='欢迎加作者微信 "EastSeaO"，探讨加入更多功能。',
            font=ctk.CTkFont(family="Microsoft YaHei", size=13),
            text_color=self.C["text_secondary"],
        ).pack(anchor="w", padx=24, pady=(0, 10))

        # ── 微信二维码 ──────────────────────────
        wx_qr_path = _get_resource_path("assets/wx.png")
        if os.path.exists(wx_qr_path) and PIL_AVAILABLE:
            try:
                wx_img = ctk.CTkImage(
                    light_image=Image.open(wx_qr_path),
                    size=(150, 150))
                wx_frame = ctk.CTkFrame(card, fg_color="transparent")
                wx_frame.pack(anchor="w", padx=24, pady=(10, 16))

                wx_label = ctk.CTkLabel(
                    wx_frame, image=wx_img, text="")
                wx_label.image = wx_img  # 保持引用
                wx_label.pack(anchor="w")

                ctk.CTkLabel(
                    wx_frame, text="微信扫码添加作者",
                    font=ctk.CTkFont(family="Microsoft YaHei", size=12),
                    text_color=self.C["text_secondary"],
                ).pack(pady=(6, 0))
            except Exception:
                pass

        # ── GitHub 仓库 ──────────────────────
        github_frame = ctk.CTkFrame(card, fg_color=self.C["primary_light"], corner_radius=8)
        github_frame.pack(fill="x", padx=20, pady=(4, 6))

        ctk.CTkLabel(
            github_frame, text="🌐  GitHub 仓库",
            font=ctk.CTkFont(family="Microsoft YaHei", size=13, weight="bold"),
            text_color=self.C["text"],
        ).pack(anchor="w", padx=14, pady=(10, 2))

        repo_btn = ctk.CTkButton(
            github_frame, text="eastseao / procurement-system",
            width=280, height=34,
            fg_color=self.C["primary"], hover_color=self.C["primary_hover"],
            font=ctk.CTkFont(family="Microsoft YaHei", size=13, weight="bold"),
            corner_radius=20,
            command=lambda: webbrowser.open(GITHUB_RELEASES_URL.replace("/releases", "")),
        )
        repo_btn.pack(anchor="w", padx=14, pady=(4, 10))

        ctk.CTkLabel(card, text="").pack(pady=(6, 4))

    def _add_save_button(self):
        """在右侧内容区底部添加保存按钮"""
        btn_frame = ctk.CTkFrame(self._right_content, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(8, 24))

        ctk.CTkButton(
            btn_frame, text="✓ 保存设置", width=140, height=40,
            fg_color=self.C["success"], hover_color="#7A9472",
            font=ctk.CTkFont(family="Microsoft YaHei", size=16, weight="bold"),
            command=self._save_all, corner_radius=20,
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
        self.settings["theme"] = self.theme_mode_var.get()
        self.settings["auto_start"] = "1" if self.auto_start_var.get() == 1 else "0"
        self.settings["tray_enabled"] = "1" if self.tray_enabled_var.get() == 1 else "0"

        # 保存 KPI 指标选择
        selected_kpis = [k for k, v in self.kpi_check_vars.items() if v.get() == 1]
        self.settings["kpi_cards"] = ",".join(selected_kpis) if selected_kpis else "packaging,collection,purchase,travel"

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

