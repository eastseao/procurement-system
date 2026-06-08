#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
采购管理系统 - 主入口
功能：物料下单、物料查询、供应商管理、催款记录、采购垫付、差旅报销、备忘录、设置
V1.7 更新：版本介绍接入 GitHub、完善作者信息、检查更新按钮、物料下单新增供应商/项目号筛选
"""

import sys
import os
import traceback
import threading
import webbrowser
import tkinter as tk
from tkinter import messagebox
import ctypes

from version import __version__, __version_date__, check_for_updates_async

DEFAULT_DATA_DIR = os.path.join(os.path.expanduser("~"), "采购管理系统数据")

# ── 全局异常日志（先定义占位，加载设置后更新）──
LOG_FILE = ""


def _log_exception(exc_type, exc_value, exc_tb):
    if not LOG_FILE:
        return
    tb_lines = traceback.format_exception(exc_type, exc_value, exc_tb)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write("=" * 60 + "\n")
        f.writelines(tb_lines)
        f.write("\n")

sys.excepthook = _log_exception

try:
    import customtkinter as ctk
except ImportError:
    messagebox.showerror("依赖缺失", "请先安装 customtkinter：pip install customtkinter")
    sys.exit(1)

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

from database import Database
from pages.packaging_page import PackagingPage
from pages.query_page import QueryPage
from pages.supplier_page import SupplierPage
from pages.collection_page import CollectionPage
from pages.purchase_page import PurchasePage
from pages.travel_page import TravelPage
from pages.memo_page import MemoPage
from pages.quotation_page import QuotationPage
from pages.dashboard_page import DashboardPage
from pages.settings_page import SettingsPage, load_settings
from pages.tangxun_page import TangxunPage

# ── pystray 系统托盘 ──
try:
    import pystray
    from PIL import Image as PILImage
    PYSTRAY_AVAILABLE = True
except ImportError:
    PYSTRAY_AVAILABLE = False

settings = load_settings()
# 解析数据存放目录
_data_dir = settings.get("data_dir", "")
if not _data_dir:
    _data_dir = DEFAULT_DATA_DIR
os.makedirs(_data_dir, exist_ok=True)
LOG_FILE = os.path.join(_data_dir, "error.log")

ctk.set_appearance_mode(settings.get("appearance_mode", "light"))
ctk.set_default_color_theme("blue")

# ── 莫兰迪暖色调色板（适配 Win10 / Win11）──────────────
COLORS = {
    "primary":         "#C1816D",   # 莫兰迪陶土色
    "primary_hover":   "#A86B58",
    "primary_light":   "#FDF2EE",
    "success":         "#8FA882",   # 莫兰迪鼠尾草绿
    "warning":         "#C9A96E",   # 莫兰迪麦色
    "danger":          "#B56A6A",   # 莫兰迪暗玫瑰
    "bg":              "#F5F0EB",   # 暖米白背景
    "card":            "#FFFAF5",   # 暖白卡片
    "sidebar":         "#F0EBE3",   # 暖灰侧边栏
    "sidebar_text":    "#5D4E37",   # 暖棕色文字
    "sidebar_active":  "#E8D5C4",   # 选中项暖陶土背景
    "sidebar_active_text": "#8B5E3C",
    "sidebar_hover":   "#E8DDD0",
    "text":            "#4A3728",   # 深暖棕
    "text_secondary":  "#8B7355",   # 柔和暖棕
    "border":          "#D4C5B2",
    "divider":         "#E8DDD0",
}


def _get_resource_path(rel_path):
    """兼容PyInstaller打包后的资源路径"""
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, rel_path)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), rel_path)


ICO_PATH  = _get_resource_path("assets/同仁堂企业LOGO2.ico")
COLLAPSE_ICON_PATH = _get_resource_path("assets/icon_collapse.png")
EXPAND_ICON_PATH   = _get_resource_path("assets/icon_expand.png")
LOGO_PATH          = _get_resource_path("assets/logo_40x40.png")

# ── 导航栏图标路径 ──
NAV_ICON_PATHS = {
    "dashboard":  _get_resource_path("assets/nav_dashboard.png"),
    "packaging":  _get_resource_path("assets/nav_packaging.png"),
    "quotation":  _get_resource_path("assets/nav_quotation.png"),
    "query":      _get_resource_path("assets/nav_query.png"),
    "supplier":   _get_resource_path("assets/nav_supplier.png"),
    "collection": _get_resource_path("assets/nav_collection.png"),
    "purchase":   _get_resource_path("assets/nav_purchase.png"),
    "travel":     _get_resource_path("assets/nav_travel.png"),
    "memo":       _get_resource_path("assets/nav_memo.png"),
    "settings":   _get_resource_path("assets/nav_settings.png"),
}


def _add_tooltip(widget, text):
    """为控件添加鼠标悬浮提示（黄色小标签）"""
    tip = None

    def _enter(event):
        nonlocal tip
        if tip:
            return
        x = widget.winfo_rootx() + widget.winfo_width() // 2
        y = widget.winfo_rooty() + widget.winfo_height() + 2
        tip = tk.Toplevel(widget)
        tip.wm_overrideredirect(True)
        tip.wm_geometry("+%d+%d" % (x, y))
        label = tk.Label(
            tip, text=text,
            background="#FFFFCC", foreground="#333333",
            font=("Microsoft YaHei", 10),
            relief="solid", borderwidth=1, padx=6, pady=2,
        )
        label.pack()

    def _leave(event):
        nonlocal tip
        if tip:
            tip.destroy()
            tip = None

    widget.bind("<Enter>", _enter, add="+")
    widget.bind("<Leave>", _leave, add="+")


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(f"采购助手 V{__version__}")
        self.geometry("1280x800")
        self.minsize(1100, 700)
        self.configure(fg_color=COLORS["bg"])

        # 设置程序图标
        if os.path.exists(ICO_PATH):
            try:
                self.iconbitmap(ICO_PATH)
            except Exception:
                pass

        # 居中显示
        self.update_idletasks()
        w = self.winfo_screenwidth()
        h = self.winfo_screenheight()
        self.geometry(f"1280x800+{(w-1280)//2}+{(h-800)//2}")

        self.db = Database(_data_dir)
        self.current_page = None
        self._nav_compact = False    # 汉堡包折叠：仅图标模式
        self._pinned = False          # 窗口置顶状态

        # ── 系统托盘状态 ──
        self._tray_enabled = settings.get("tray_enabled", "0") == "1"
        self._tray_icon = None
        self._tray_thread = None

        self._build_ui()
        self._switch_page("dashboard")

        # ── 拦截关闭事件 ──
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

        # ── 设置标题栏配色（延迟执行，确保窗口已映射）──
        self.after(200, self._set_titlebar_color)

        # ── 版本更新检查（后台线程，不阻塞 UI）──
        self.after(800, self._check_version_updates)

    def _check_version_updates(self):
        """后台检查 GitHub 是否有新版本，有则弹出通知"""
        def on_checked(result):
            if not result["has_update"]:
                return
            # 在主线程中弹出更新通知
            self.after(0, lambda: self._show_update_dialog(result))
        
        check_for_updates_async(on_checked)

    def _show_update_dialog(self, result):
        """显示新版本通知对话框（莫兰迪风格）"""
        import tkinter as tk
        from tkinter import ttk
        
        current = result["current_version"]
        latest = result["latest_version"]
        notes = result.get("release_notes", "")
        url = result.get("download_url", "")
        
        # 截取更新日志前500字
        notes_short = notes[:500] + "..." if len(notes) > 500 else notes
        
        dialog = tk.Toplevel(self)
        dialog.title("发现新版本")
        dialog.geometry("520x420")
        dialog.resizable(False, False)
        dialog.configure(bg="#FFFAF5")
        dialog.transient(self)
        dialog.grab_set()
        
        # 居中
        dialog.update_idletasks()
        dw, dh = 520, 420
        sw = dialog.winfo_screenwidth()
        sh = dialog.winfo_screenheight()
        dialog.geometry(f"{dw}x{dh}+{(sw-dw)//2}+{(sh-dh)//2}")
        
        # 标题栏
        header = tk.Frame(dialog, bg="#C1816D", height=80)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        tk.Label(
            header, text="🎉  发现新版本！",
            font=("Microsoft YaHei", 18, "bold"),
            fg="white", bg="#C1816D",
        ).pack(pady=(14, 0))
        
        tk.Label(
            header, text=f"采购助手 V{latest} 已发布",
            font=("Microsoft YaHei", 11),
            fg="#FFFAF5", bg="#C1816D",
        ).pack()
        
        # 内容区
        content = tk.Frame(dialog, bg="#FFFAF5", padx=24, pady=16)
        content.pack(fill="both", expand=True)
        
        # 版本对比
        ver_frame = tk.Frame(content, bg="#FFFAF5")
        ver_frame.pack(fill="x", pady=(0, 12))
        
        tk.Label(
            ver_frame, text=f"当前版本：V{current}",
            font=("Microsoft YaHei", 12),
            fg="#8B7355", bg="#FFFAF5",
        ).pack(side="left")
        
        tk.Label(
            ver_frame, text="→",
            font=("Microsoft YaHei", 12, "bold"),
            fg="#C1816D", bg="#FFFAF5",
        ).pack(side="left", padx=12)
        
        tk.Label(
            ver_frame, text=f"最新版本：V{latest}",
            font=("Microsoft YaHei", 12, "bold"),
            fg="#4A3728", bg="#FFFAF5",
        ).pack(side="left")
        
        # 更新日志
        if notes_short.strip():
            tk.Label(
                content, text="更新内容：",
                font=("Microsoft YaHei", 11, "bold"),
                fg="#4A3728", bg="#FFFAF5",
                anchor="w",
            ).pack(fill="x", pady=(8, 4))
            
            notes_text = tk.Text(
                content, 
                height=7, 
                width=54,
                font=("Microsoft YaHei", 10),
                fg="#4A3728", bg="#FDF2EE",
                relief="flat", borderwidth=0,
                padx=10, pady=8,
                wrap="word",
            )
            notes_text.insert("1.0", notes_short)
            notes_text.configure(state="disabled")
            notes_text.pack(fill="x")
        
        # 按钮区
        btn_frame = tk.Frame(dialog, bg="#FFFAF5", padx=24, pady=16)
        btn_frame.pack(fill="x")
        
        def go_download():
            if url:
                webbrowser.open(url)
            dialog.destroy()
        
        def remind_later():
            dialog.destroy()
        
        # 前往下载按钮
        download_btn = tk.Button(
            btn_frame, text="前往下载",
            font=("Microsoft YaHei", 12, "bold"),
            bg="#C1816D", fg="white",
            activebackground="#A86B58", activeforeground="white",
            relief="flat", padx=32, pady=10,
            cursor="hand2",
            command=go_download,
        )
        download_btn.pack(side="right", padx=(10, 0))
        
        # 暂不更新按钮
        later_btn = tk.Button(
            btn_frame, text="暂不更新",
            font=("Microsoft YaHei", 12),
            bg="#F0EBE3", fg="#5D4E37",
            activebackground="#E8DDD0", activeforeground="#5D4E37",
            relief="flat", padx=24, pady=10,
            cursor="hand2",
            command=remind_later,
        )
        later_btn.pack(side="right")

    def _build_ui(self):
        # ── 侧边栏 ──────────────────────────────────────
        self.sidebar = ctk.CTkFrame(
            self, width=155, fg_color=COLORS["sidebar"],
            corner_radius=0, border_width=0
        )
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # 右侧边线
        self.divider = tk.Frame(self, bg=COLORS["border"], width=1)
        self.divider.pack(side="left", fill="y")

        # 加载折叠/展开图标
        self._collapse_icon = None
        self._expand_icon = None
        if PIL_AVAILABLE:
            try:
                if os.path.exists(COLLAPSE_ICON_PATH):
                    self._collapse_icon = ctk.CTkImage(
                        light_image=Image.open(COLLAPSE_ICON_PATH), size=(24, 24))
                if os.path.exists(EXPAND_ICON_PATH):
                    self._expand_icon = ctk.CTkImage(
                        light_image=Image.open(EXPAND_ICON_PATH), size=(24, 24))
            except Exception:
                pass

        # 加载导航栏图标
        self._nav_icon_images = {}
        if PIL_AVAILABLE:
            for key, path in NAV_ICON_PATHS.items():
                if os.path.exists(path):
                    try:
                        self._nav_icon_images[key] = ctk.CTkImage(
                            light_image=Image.open(path), size=(28, 28))
                    except Exception:
                        self._nav_icon_images[key] = None
                else:
                    self._nav_icon_images[key] = None

        # ── 置顶按钮（侧边栏顶部居中）─────────────────────
        pin_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent", height=68)
        pin_frame.pack(side="top", fill="x", padx=0, pady=(6, 2))
        pin_frame.pack_propagate(False)

        self.pin_btn = ctk.CTkButton(
            pin_frame,
            text="📌",
            width=60, height=60,
            font=ctk.CTkFont(size=22),
            fg_color="transparent",
            text_color=COLORS["sidebar_text"],
            hover_color=COLORS["sidebar_hover"],
            corner_radius=10,
            command=self._toggle_pin,
        )
        self.pin_btn.pack(padx=8, pady=4, expand=True)
        _add_tooltip(self.pin_btn, "固定窗口到最前")

        # ── Logo（置顶按钮下方居中，点击跳转堂训页）─────────────────────
        logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent", height=48)
        logo_frame.pack(side="top", fill="x", padx=0, pady=(0, 4))
        logo_frame.pack_propagate(False)
        if PIL_AVAILABLE and os.path.exists(LOGO_PATH):
            try:
                self._logo_image = ctk.CTkImage(
                    light_image=Image.open(LOGO_PATH), size=(40, 40))
                self.logo_btn = ctk.CTkLabel(
                    logo_frame, image=self._logo_image, text="",
                    fg_color="transparent", cursor="hand2",
                )
                self.logo_btn.pack(expand=True)
                self.logo_btn.bind("<Button-1>", lambda e: self._switch_page("tangxun"))
                _add_tooltip(self.logo_btn, "同仁堂堂训")
            except Exception:
                pass

        # ── 导航按钮区域（均匀分布）─────────────────────
        self.nav_area = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.nav_area.pack(side="top", fill="both", expand=True)

        nav_items = [
            ("dashboard",  "仪表盘"),
            ("packaging",  "物料下单"),
            ("quotation",  "报价单"),
            ("query",      "物料查询"),
            ("supplier",   "供应商"),
            ("collection", "催款记录"),
            ("purchase",   "采购垫付"),
            ("travel",     "差旅报销"),
            ("memo",       "备忘录"),
        ]
        self.nav_buttons = {}
        for key, label in nav_items:
            icon = self._nav_icon_images.get(key)
            btn = ctk.CTkButton(
                self.nav_area,
                text=label,
                image=icon,
                compound="top",
                font=ctk.CTkFont(family="Microsoft YaHei", size=12),
                fg_color="transparent",
                text_color=COLORS["sidebar_text"],
                hover_color=COLORS["sidebar_hover"],
                anchor="center",
                height=58,
                corner_radius=6,
                command=lambda k=key: self._switch_page(k),
            )
            btn.pack(fill="x", padx=8, pady=1, expand=True)
            self.nav_buttons[key] = btn

        settings_icon = self._nav_icon_images.get("settings")
        self.settings_btn = ctk.CTkButton(
            self.nav_area,
            text="设置",
            image=settings_icon,
            compound="top",
            font=ctk.CTkFont(family="Microsoft YaHei", size=12),
            fg_color="transparent",
            text_color=COLORS["sidebar_text"],
            hover_color=COLORS["sidebar_hover"],
            anchor="center",
            height=58,
            corner_radius=6,
            command=self._open_settings,
        )
        self.settings_btn.pack(fill="x", padx=8, pady=1, expand=True)

        # ── 折叠按钮（侧边栏最底部）────────────────────
        self.hamburger_btn = ctk.CTkButton(
            self.sidebar,
            text="",
            image=self._collapse_icon if self._collapse_icon else None,
            font=ctk.CTkFont(family="Microsoft YaHei", size=20),
            fg_color="transparent",
            text_color=COLORS["sidebar_text"],
            hover_color=COLORS["sidebar_hover"],
            height=48,
            corner_radius=8,
            command=self._toggle_compact,
        )
        self.hamburger_btn.pack(side="bottom", fill="x", padx=8, pady=(2, 10))
        _add_tooltip(self.hamburger_btn, "折叠导航")

        # ── 主内容区域 ──
        self.main_area = ctk.CTkFrame(self, fg_color=COLORS["bg"], corner_radius=0)
        self.main_area.pack(side="left", fill="both", expand=True)

    def _switch_page(self, key):
        for k, btn in self.nav_buttons.items():
            if k == key:
                btn.configure(
                    fg_color=COLORS["sidebar_active"],
                    text_color=COLORS["sidebar_active_text"],
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=COLORS["sidebar_text"],
                )
        # 重置设置按钮高亮
        self.settings_btn.configure(fg_color="transparent", text_color=COLORS["sidebar_text"])

        for widget in self.main_area.winfo_children():
            widget.destroy()

        if key == "dashboard":
            self.current_page = DashboardPage(self.main_area, self.db, COLORS)
        elif key == "packaging":
            self.current_page = PackagingPage(self.main_area, self.db, COLORS)
        elif key == "quotation":
            self.current_page = QuotationPage(self.main_area, self.db, COLORS)
        elif key == "query":
            self.current_page = QueryPage(self.main_area, self.db, COLORS)
        elif key == "supplier":
            self.current_page = SupplierPage(self.main_area, self.db, COLORS)
        elif key == "collection":
            self.current_page = CollectionPage(self.main_area, self.db, COLORS)
        elif key == "purchase":
            self.current_page = PurchasePage(self.main_area, self.db, COLORS)
        elif key == "travel":
            self.current_page = TravelPage(self.main_area, self.db, COLORS)
        elif key == "memo":
            self.current_page = MemoPage(self.main_area, self.db, COLORS)
        elif key == "tangxun":
            self.current_page = TangxunPage(self.main_area, self.db, COLORS)
        elif key == "settings":
            self.current_page = SettingsPage(self.main_area, self.db, COLORS)

        if self.current_page:
            self.current_page.pack(fill="both", expand=True)

    def _open_settings(self):
        """打开设置页面"""
        self._switch_page("settings")
        # 取消所有导航按钮高亮
        for k, btn in self.nav_buttons.items():
            btn.configure(fg_color="transparent", text_color=COLORS["sidebar_text"])
        # 高亮设置按钮
        self.settings_btn.configure(
            fg_color=COLORS["sidebar_active"],
            text_color=COLORS["sidebar_active_text"],
        )



    # ── 汉堡包折叠导航 ─────────────────────────────────
    _full_labels = {
        "dashboard":  "仪表盘",        "packaging":  "物料下单",
        "quotation":  "报价单",
        "query":      "物料查询",
        "supplier":   "供应商",
        "collection": "催款记录",
        "purchase":   "采购垫付",
        "travel":     "差旅报销",
        "memo":       "备忘录",
    }

    def _toggle_compact(self):
        """切换导航栏：图标+文字(compound=top) ↔ 仅图标模式"""
        self._nav_compact = not self._nav_compact
        if self._nav_compact:
            # 折叠：仅图标 + 适配图标宽度
            self.sidebar.configure(width=46)
            for key, btn in self.nav_buttons.items():
                icon = self._nav_icon_images.get(key)
                btn.configure(text="", image=icon, compound="center",
                              width=26, height=36, anchor="center")
                btn.pack_configure(padx=8, pady=1, expand=True)
                _add_tooltip(btn, self._full_labels.get(key, key))
            settings_icon = self._nav_icon_images.get("settings")
            self.settings_btn.configure(text="", image=settings_icon, compound="center",
                                        width=26, height=36, anchor="center")
            self.settings_btn.pack_configure(padx=8, pady=1, expand=True)
            _add_tooltip(self.settings_btn, "设置")
            # 底部按钮 -> 展开图标
            self.hamburger_btn.configure(image=self._expand_icon if self._expand_icon else None)
            self.hamburger_btn.pack_configure(padx=8, pady=(2, 10))
            _add_tooltip(self.hamburger_btn, "展开导航")
            # 缩小置顶按钮
            self.pin_btn.configure(text="📌", width=42, height=42, font=ctk.CTkFont(size=16))
        else:
            # 展开：图标在上，文字在下
            self.sidebar.configure(width=155)
            for key, btn in self.nav_buttons.items():
                label = self._full_labels.get(key, key)
                icon = self._nav_icon_images.get(key)
                btn.configure(text=label, image=icon, compound="top",
                              height=58, anchor="center", width=None,
                              font=ctk.CTkFont(family="Microsoft YaHei", size=12))
                btn.pack_configure(padx=8, pady=1, expand=True)
            settings_icon = self._nav_icon_images.get("settings")
            self.settings_btn.configure(text="设置", image=settings_icon, compound="top",
                                        height=58, anchor="center", width=None,
                                        font=ctk.CTkFont(family="Microsoft YaHei", size=12))
            self.settings_btn.pack_configure(padx=8, pady=1, expand=True)
            # 底部按钮 -> 折叠图标
            self.hamburger_btn.configure(image=self._collapse_icon if self._collapse_icon else None)
            self.hamburger_btn.pack_configure(padx=8, pady=(2, 10))
            _add_tooltip(self.hamburger_btn, "折叠导航")
            # 恢复置顶按钮大小
            self.pin_btn.configure(text="📌", width=60, height=60, font=ctk.CTkFont(size=22))

    # ── 窗口置顶 ─────────────────────────────────
    def _toggle_pin(self):
        """切换窗口是否固定在最前面"""
        self._pinned = not self._pinned
        self.attributes("-topmost", self._pinned)
        if self._pinned:
            self.pin_btn.configure(fg_color=COLORS["primary"], text_color="white", text="📍")
            _add_tooltip(self.pin_btn, "已固定 - 点击取消")
        else:
            self.pin_btn.configure(fg_color="transparent", text_color=COLORS["sidebar_text"], text="📌")
            _add_tooltip(self.pin_btn, "固定窗口到最前")

    # ── 标题栏配色（Win11 DWM API）───────────────────
    def _set_titlebar_color(self):
        """设置窗口标题栏配色为莫兰迪暖色，与页面保持一致"""
        try:
            hwnd = int(self.winfo_id())
            # Win11 DWMWA_CAPTION_COLOR / DWMWA_TEXT_COLOR
            DWMWA_CAPTION_COLOR = 35
            DWMWA_TEXT_COLOR = 36
            # 颜色格式: 0xAABBGGRR
            caption_color = 0xFFEBF0F5  # #F5F0EB (暖米白)
            text_color = 0xFF28374A     # #4A3728 (深暖棕)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, DWMWA_CAPTION_COLOR,
                ctypes.byref(ctypes.c_int(caption_color)), ctypes.sizeof(ctypes.c_int))
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, DWMWA_TEXT_COLOR,
                ctypes.byref(ctypes.c_int(text_color)), ctypes.sizeof(ctypes.c_int))
        except Exception:
            pass  # Win10 或不支持时静默跳过

    # ── 关闭窗口：按设置直接执行 ─────────────────
    def _on_closing(self):
        """拦截窗口关闭事件：按设置直接执行，不再弹窗询问"""
        if self._tray_enabled and PYSTRAY_AVAILABLE:
            self._minimize_to_tray()
        else:
            self._quit_app()

    # ── 系统托盘功能 ──────────────────────────────────

    def _minimize_to_tray(self):
        """收纳进系统托盘"""
        if not PYSTRAY_AVAILABLE:
            self._quit_app()
            return
        if self._tray_icon is not None:
            return  # 已经在托盘中

        self.withdraw()  # 隐藏窗口

        # 在新线程中启动托盘图标
        self._tray_thread = threading.Thread(target=self._run_tray, daemon=True)
        self._tray_thread.start()

    def _run_tray(self):
        """在新线程中运行托盘图标（pystray 的事件循环）"""
        try:
            # 加载托盘图标图片
            if os.path.exists(ICO_PATH):
                img = PILImage.open(ICO_PATH)
                # 缩小到适合托盘的尺寸（pystray 推荐 64x64）
                img = img.resize((64, 64), PILImage.LANCZOS)
            else:
                # 备用：创建纯色图标（莫兰迪陶土色）
                img = PILImage.new("RGBA", (64, 64), (193, 129, 109, 255))

            menu = pystray.Menu(
                pystray.MenuItem(
                    "显示窗口",
                    self._on_tray_restore,
                    default=True,
                ),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem(
                    "退出应用",
                    self._on_tray_quit,
                ),
            )

            self._tray_icon = pystray.Icon(
                "采购助手",
                img,
                f"采购助手 V{__version__}",
                menu,
            )
            self._tray_icon.run()
        except Exception:
            # 托盘启动失败，恢复窗口
            self.after(0, self._do_restore)

    def _on_tray_restore(self, icon=None, item=None):
        """托盘菜单：显示窗口"""
        if self._tray_icon:
            self._tray_icon.stop()
            self._tray_icon = None
        self.after(0, self._do_restore)

    def _on_tray_quit(self, icon=None, item=None):
        """托盘菜单：退出应用"""
        if self._tray_icon:
            self._tray_icon.stop()
            self._tray_icon = None
        self.after(0, self._quit_app)

    def _do_restore(self):
        """在主线程中恢复窗口"""
        self._tray_icon = None
        self.deiconify()
        self.lift()
        self.focus_force()
        self.attributes("-topmost", True)
        self.after(100, lambda: self.attributes("-topmost", False))

    def _quit_app(self):
        """完全退出应用"""
        if self._tray_icon:
            try:
                self._tray_icon.stop()
            except Exception:
                pass
            self._tray_icon = None

        try:
            self.db.close()
        except Exception:
            pass

        self.destroy()
        try:
            import sys
            sys.exit(0)
        except SystemExit:
            pass


if __name__ == "__main__":
    # ── 单进程互斥锁（Windows Mutex）──
    # 确保同一时间只能运行一个程序实例
    MUTEX_NAME = "Global\\采购助手Mutex_EastSeaO_2026"
    mutex = ctypes.windll.kernel32.CreateMutexW(None, False, MUTEX_NAME)
    last_error = ctypes.windll.kernel32.GetLastError()
    if last_error == 183:  # ERROR_ALREADY_EXISTS
        ctypes.windll.user32.MessageBoxW(
            None,
            "采购助手已经在运行中，不能同时启动多个实例。",
            "提示",
            0x40 | 0x0  # MB_OK | MB_ICONINFORMATION
        )
        sys.exit(0)

    app = App()
    app.mainloop()

    # 程序退出时释放互斥锁
    ctypes.windll.kernel32.ReleaseMutex(mutex)
    ctypes.windll.kernel32.CloseHandle(mutex)
