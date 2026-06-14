#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
采购管理系统 - 主入口 V2.3.3
功能：物料下单、物料查询、供应商管理、催款记录、采购垫付、差旅报销、备忘录、设置、计划
V2.3.3 更新：看板三列动态（下单/报价/其他）+核心指标一行四个、计划页优化
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
from pages.contract_page import ContractPage
from pages.product_bom_page import ProductBomPage
from pages.third_party_page import ThirdPartyPage
from pages.plan_page import PlanPage

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

# ── 经典蓝色调色板（Blue）────────────────────────────
_COLORS_BLUE_LIGHT = {
    "primary":         "#4A90E2",
    "primary_hover":   "#3A7BC8",
    "primary_light":   "#E8F2FC",
    "success":         "#5B9279",
    "warning":         "#E4A36A",
    "danger":          "#B56A6A",
    "bg":              "#F5F7FA",
    "card":            "#FFFFFF",
    "sidebar":         "#EEF2F7",
    "sidebar_text":    "#2C3E50",
    "sidebar_active":  "#D6E4F2",
    "sidebar_active_text": "#1A5490",
    "sidebar_hover":   "#DCE5F0",
    "text":            "#1F2937",
    "text_secondary":  "#6B7280",
    "border":          "#D1D5DB",
    "divider":         "#E5E7EB",
    "nav_group_bg":   "#D6E4F2",
    "nav_indicator":   "#4A90E2",
    "radius_card":     12,
    "radius_btn_primary": 8,
    "radius_btn_secondary": 4,
    "radius_input":    6,
    "radius_modal":    16,
    "radius_nav_item": 4,
    "font_micro":     10,
    "font_body":      12,
    "font_subtitle":  14,
    "font_title":     20,
    "spacing_xs":     4,
    "spacing_sm":     8,
    "spacing_md":     12,
    "spacing_lg":     16,
    "spacing_xl":     24,
    "spacing_xxl":    32,
}

_COLORS_BLUE_DARK = {
    "primary":         "#4A90E2",
    "primary_hover":   "#5BA0F2",
    "primary_light":   "#1E2D3D",
    "success":         "#5B9279",
    "warning":         "#E4A36A",
    "danger":          "#B56A6A",
    "bg":              "#0F1419",
    "card":            "#1A2027",
    "sidebar":         "#161C23",
    "sidebar_text":    "#E5E7EB",
    "sidebar_active":  "#1E2D3D",
    "sidebar_active_text": "#5BA0F2",
    "sidebar_hover":   "#1F2832",
    "text":            "#E5E7EB",
    "text_secondary":  "#9CA3AF",
    "border":          "#2D3748",
    "divider":         "#1F2832",
    "nav_group_bg":   "#1E2D3D",
    "nav_indicator":   "#4A90E2",
    "radius_card":     12,
    "radius_btn_primary": 8,
    "radius_btn_secondary": 4,
    "radius_input":    6,
    "radius_modal":    16,
    "radius_nav_item": 4,
    "font_micro":     10,
    "font_body":      12,
    "font_subtitle":  14,
    "font_title":     20,
    "spacing_xs":     4,
    "spacing_sm":     8,
    "spacing_md":     12,
    "spacing_lg":     16,
    "spacing_xl":     24,
    "spacing_xxl":    32,
}

# ── Windows 11 原生调色板（Win11 Mica/Acrylic 风格）──────────────
# 参考：Microsoft Fluent Design System + WinUI 3
# 强调色：Accent #0078D4（Win11 蓝）；中性色采用 Mica 表面 #FAFAFA / #202020
_COLORS_WIN11_LIGHT = {
    "primary":         "#0078D4",
    "primary_hover":   "#106EBE",
    "primary_light":   "#EAF6FD",
    "success":         "#107C10",
    "warning":         "#FFA500",
    "danger":          "#D13438",
    "bg":              "#FAFAFA",
    "card":            "#FFFFFF",
    "sidebar":         "#F3F3F3",
    "sidebar_text":    "#1F1F1F",
    "sidebar_active":  "#E5E5E5",
    "sidebar_active_text": "#0078D4",
    "sidebar_hover":   "#EDEDED",
    "text":            "#1F1F1F",
    "text_secondary":  "#605E5C",
    "border":          "#E5E5E5",
    "divider":         "#EDEBE9",
    "nav_group_bg":   "#E5E5E5",
    "nav_indicator":   "#0078D4",
    "radius_card":     8,
    "radius_btn_primary": 4,
    "radius_btn_secondary": 4,
    "radius_input":    4,
    "radius_modal":    8,
    "radius_nav_item": 4,
    "font_micro":     10,
    "font_body":      12,
    "font_subtitle":  14,
    "font_title":     20,
    "spacing_xs":     4,
    "spacing_sm":     8,
    "spacing_md":     12,
    "spacing_lg":     16,
    "spacing_xl":     24,
    "spacing_xxl":    32,
}

_COLORS_WIN11_DARK = {
    "primary":         "#4CC2FF",
    "primary_hover":   "#5CCBFF",
    "primary_light":   "#1E2A30",
    "success":         "#6CCB5F",
    "warning":         "#FFB900",
    "danger":          "#F1707A",
    "bg":              "#202020",
    "card":            "#2C2C2C",
    "sidebar":         "#1C1C1C",
    "sidebar_text":    "#FFFFFF",
    "sidebar_active":  "#383838",
    "sidebar_active_text": "#4CC2FF",
    "sidebar_hover":   "#2A2A2A",
    "text":            "#FFFFFF",
    "text_secondary":  "#A19F9D",
    "border":          "#3F3F3F",
    "divider":         "#2A2A2A",
    "nav_group_bg":   "#383838",
    "nav_indicator":   "#4CC2FF",
    "radius_card":     8,
    "radius_btn_primary": 4,
    "radius_btn_secondary": 4,
    "radius_input":    4,
    "radius_modal":    8,
    "radius_nav_item": 4,
    "font_micro":     10,
    "font_body":      12,
    "font_subtitle":  14,
    "font_title":     20,
    "spacing_xs":     4,
    "spacing_sm":     8,
    "spacing_md":     12,
    "spacing_lg":     16,
    "spacing_xl":     24,
    "spacing_xxl":    32,
}


def get_colors(color_theme="classic_blue", mode="light"):
    """
    返回指定颜色方案 + 明暗模式下的颜色字典。

    参数:
        color_theme: "classic_blue" / "win11"
        mode:        "light" / "dark"
    """
    if color_theme == "win11":
        return dict(_COLORS_WIN11_DARK if mode == "dark" else _COLORS_WIN11_LIGHT)
    # 默认：经典蓝色
    return dict(_COLORS_BLUE_DARK if mode == "dark" else _COLORS_BLUE_LIGHT)


# ── 向后兼容：旧 get_colors(theme) 签名仍然可用 ──
def _get_colors_legacy(theme="light"):
    """旧版签名：仅传入 theme，返回经典蓝配色"""
    return get_colors("classic_blue", theme)

# 根据设置选择主题（启动时使用）
_color_theme = settings.get("color_theme", "classic_blue")
if _color_theme not in ("classic_blue", "win11"):
    _color_theme = "classic_blue"
_mode = settings.get("theme", "light")
if _mode not in ("light", "dark"):
    _mode = "light"
COLORS = get_colors(_color_theme, _mode)


def _get_resource_path(rel_path):
    """兼容PyInstaller打包后的资源路径"""
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, rel_path)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), rel_path)


# ── 图标路径（统一高清版）──
ICON_PATH_256    = _get_resource_path("assets/同仁堂logo/同仁堂企业LOGO_×256.ico")   # 所有层级统一用 256 高清 ICO
TRAY_ICON_PATH    = ICON_PATH_256     # 系统托盘
TASKBAR_ICON_PATH = ICON_PATH_256     # 任务栏
TITLEBAR_ICON_PATH = ICON_PATH_256    # 标题栏（小图标）
ICO_PATH          = ICON_PATH_256     # 向后兼容
LOGO_PATH         = ICON_PATH_256     # 向后兼容

# ── 导航栏图标路径（线性版）──
NAV_ICON_PATHS = {
    "dashboard":   _get_resource_path("assets/nav_dashboard.png"),
    "packaging":   _get_resource_path("assets/nav_packaging.png"),
    "quotation":   _get_resource_path("assets/nav_quotation.png"),
    "query":       _get_resource_path("assets/nav_query.png"),
    "supplier":    _get_resource_path("assets/nav_supplier.png"),
    "collection":  _get_resource_path("assets/nav_collection.png"),
    "purchase":    _get_resource_path("assets/nav_purchase.png"),
    "travel":      _get_resource_path("assets/nav_travel.png"),
    "memo":        _get_resource_path("assets/nav_memo.png"),
    "contract":    _get_resource_path("assets/nav_contract.png"),
    "settings":    _get_resource_path("assets/nav_settings.png"),
    "product_bom": _get_resource_path("assets/nav_product_bom.png"),
    "compare":     _get_resource_path("assets/nav_compare.png"),
    "plan":        _get_resource_path("assets/nav_plan.png"),
}
# ── 导航栏图标路径（选中实心版）──
NAV_ICON_ACTIVE_PATHS = {k: _get_resource_path(f"assets/nav_{k}_active.png") for k in NAV_ICON_PATHS}


from ui_utils import WheelScrollFrame


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


# ── 无滚动条的滚动容器（鼠标滚轮控制）──
class WheelScrollFrame(ctk.CTkFrame):
    """无可见滚动条的滚动容器，支持鼠标滚轮上下滚动"""
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)

        self._canvas = tk.Canvas(self, highlightthickness=0)
        self._scrollbar = ctk.CTkScrollbar(self, command=self._canvas.yview)
        # 完全隐藏滚动条
        self._scrollbar.configure(button_height=0, button_width=0, width=0)
        _inner_kwargs = {k: v for k, v in kwargs.items() if k in ('fg_color', 'corner_radius')}
        self._inner = ctk.CTkFrame(self._canvas, **_inner_kwargs)
        self._window_id = self._canvas.create_window((0, 0), window=self._inner, anchor='nw')

        self._scrollbar.pack(side='right', fill='y')
        self._canvas.pack(side='left', fill='both', expand=True)

        self._inner.bind('<Configure>', lambda e: self._canvas.configure(scrollregion=self._canvas.bbox('all')))
        self._canvas.configure(yscrollcommand=self._scrollbar.set)

        # 鼠标滚轮绑定
        def _on_wheel(event):
            self._canvas.yview_scroll(int(-1 * (event.delta / 120)), 'units')
        for w in (self, self._canvas, self._inner):
            w.bind('<MouseWheel>', _on_wheel)
            w.bind('<Button-4>', lambda e, s=self._canvas: s.yview_scroll(-1, 'units'))
            w.bind('<Button-5>', lambda e, s=self._canvas: s.yview_scroll(1, 'units'))


class App(ctk.CTk):
    # ── 窗口边缘阴影留白（像素）──
    # 暂时设为 0，禁用自绘阴影，确保不白屏
    _SHADOW_MARGIN = 0

    def __init__(self):
        super().__init__()
        self.title("采购助手")  # 窗口标题
        # ── 窗口尺寸 = 内容 + 阴影留白 ──
        self._content_w, self._content_h = 1280, 800
        self._content_minsize = (1100, 700)
        self.geometry(f"{self._content_w + 2 * self._SHADOW_MARGIN}x{self._content_h + 2 * self._SHADOW_MARGIN}")
        self.minsize(self._content_minsize[0] + 2 * self._SHADOW_MARGIN,
                     self._content_minsize[1] + 2 * self._SHADOW_MARGIN)
        # 窗口底色 = 透明，让阴影带的颜色直接显示
        # 注：CTk 不支持 8 位颜色，6 位同背景色即可
        self.configure(fg_color=COLORS["bg"])

        # ── 隐藏系统标题栏，使用自定义标题栏 ──
        self.overrideredirect(True)

        # ── 圆角窗口（延迟触发，等窗口完全初始化后再设置）──
        self._window_round_radius = 12
        self.after(200, self._set_rounded_corners)

        # ── 居中显示 ──
        self.update_idletasks()
        w = self.winfo_screenwidth()
        h = self.winfo_screenheight()
        self.geometry(
            f"{self._content_w + 2 * self._SHADOW_MARGIN}x"
            f"{self._content_h + 2 * self._SHADOW_MARGIN}"
            f"+{(w - self._content_w - 2 * self._SHADOW_MARGIN) // 2}"
            f"+{(h - self._content_h - 2 * self._SHADOW_MARGIN) // 2}"
        )

        # ── 确保窗口在任务栏可见（overrideredirect 后需要手动设置）──
        self.after(100, self._ensure_taskbar_visible)

        self.db = Database(_data_dir)
        self.current_page = None
        self._is_fullscreen = False  # 全屏状态标志
        self._is_maximized = False   # 最大化状态标志
        self._drag_data = {"x": 0, "y": 0}  # 窗口拖动数据
        self._sidebar_collapsed = False     # 侧边栏折叠状态

        # ── 系统托盘状态 ──
        self._tray_enabled = settings.get("tray_enabled", "0") == "1"
        self._tray_icon = None
        self._tray_thread = None

        self._build_ui()
        self._switch_page("dashboard")

        # ── 窗口尺寸变化时刷新（暂时禁用阴影，保留钩子）──
        # self.bind("<Configure>", self._refresh_shadow)

        # ── 恢复侧边栏折叠状态 ──
        _sidebar_collapsed = settings.get("sidebar_collapsed", "0") == "1"
        if _sidebar_collapsed:
            # 当前是展开状态（_build_ui 后），需要收起
            self._sidebar_collapsed = False  # 让 _toggle_sidebar 切换到收起
            self._toggle_sidebar()
            # _toggle_sidebar() 内部已经更新了标题栏折叠按钮文字

        # ── 标题栏/任务栏图标：全部使用同仁堂Logo 256 高清版（Win32 API） ──
        def _fix_icons():
            try:
                hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
                if not hwnd:
                    return

                # ── 标题栏小图标（ICON_SMALL）：系统自动从 256.ico 选最佳尺寸 ──
                if os.path.exists(ICON_PATH_256):
                    hIconSmall = ctypes.windll.user32.LoadImageW(
                        None, ICON_PATH_256, 1, 0, 0, 0x00000010  # IMAGE_ICON, LR_LOADFROMFILE, 尺寸=0自动选取
                    )
                    if hIconSmall:
                        ctypes.windll.user32.SendMessageW(hwnd, 0x0080, 0, hIconSmall)  # WM_SETICON, ICON_SMALL

                # ── 任务栏大图标（ICON_BIG）──
                if os.path.exists(ICON_PATH_256):
                    hIconBig = ctypes.windll.user32.LoadImageW(
                        None, ICON_PATH_256, 1, 0, 0, 0x00000010  # 自动选取最佳尺寸
                    )
                    if hIconBig:
                        ctypes.windll.user32.SendMessageW(hwnd, 0x0080, 1, hIconBig)   # WM_SETICON, ICON_BIG=1

                # ── tk 备用：wm_iconphoto（PIL 加载 256.ico 缩放）──
                try:
                    if os.path.exists(ICON_PATH_256):
                        img = PILImage.open(ICON_PATH_256).resize((64, 64), PILImage.LANCZOS)
                        photo = PILImageTk.PhotoImage(img)
                        self.wm_iconphoto(True, photo)
                        self._taskbar_icon_ref = photo
                except Exception:
                    pass

            except Exception:
                pass

        _fix_icons()
        self.after(200, _fix_icons)
        self.after(800, _fix_icons)
        self.after(2000, _fix_icons)

        # ── 标题栏颜色与导航栏一致 ──
        self._set_titlebar_color(COLORS["sidebar"])

        # ── 系统托盘：始终显示 ──
        if PYSTRAY_AVAILABLE:
            self._start_tray()

        # ── 拦截关闭事件（隐藏窗口而非退出）──
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

        # ── 版本更新检查（后台线程，不阻塞 UI）──
        self.after(800, self._check_version_updates)

        # ── 全局热键绑定 ──
        self._bind_global_hotkeys()

    def _ensure_taskbar_visible(self):
        """确保 overrideredirect 窗口在任务栏可见"""
        try:
            hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
            if hwnd:
                GWL_EXSTYLE = -20
                WS_EX_APPWINDOW = 0x00040000
                WS_EX_TOOLWINDOW = 0x00000080
                ex_style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
                ex_style = (ex_style | WS_EX_APPWINDOW) & ~WS_EX_TOOLWINDOW
                ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, ex_style)
        except Exception:
            pass

    def _set_rounded_corners(self):
        """设置窗口圆角（仅当窗口尺寸正常时生效，避免黑屏）"""
        try:
            hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
            if not hwnd:
                return
            w = self.winfo_width()
            h = self.winfo_height()
            if w < 200 or h < 200:
                return  # 窗口尚未完成初始化，跳过
            r = self._window_round_radius
            # 阴影区域的圆角要比内容稍大，避免阴影被内容圆角"切到"
            rgn = ctypes.windll.gdi32.CreateRoundRectRgn(0, 0, w + 1, h + 1, r * 2 + 16, r * 2 + 16)
            ctypes.windll.user32.SetWindowRgn(hwnd, rgn, True)
        except Exception:
            pass

    def _draw_window_shadow(self):
        """
        自绘窗口边缘阴影（4 条 CTkFrame 阴影带）。
        不依赖 DWM API，100% 兼容，不影响内容渲染。
        从内到外用 3 段实色梯度：深 → 中 → 浅，模拟 DWM 阴影。
        窗口尺寸变化时自动重绘。
        """
        try:
            m = self._SHADOW_MARGIN
            w = self.winfo_width()
            h = self.winfo_height()
            if w < 100 or h < 100:
                # 窗口尚未完成初始化，200ms 后重试
                self.after(200, self._draw_window_shadow)
                return

            # 销毁旧的阴影带
            if hasattr(self, "_shadow_frames") and self._shadow_frames:
                for f in self._shadow_frames:
                    try:
                        f.destroy()
                    except Exception:
                        pass
            self._shadow_frames = []

            # 根据当前主题选择阴影色（深 → 浅）
            is_dark = (settings.get("theme", "light") == "dark")
            if is_dark:
                # 暗色主题：阴影用纯黑色
                c_inner = "#000000"
                c_mid   = "#101010"
                c_outer = "#1A1A1A"
            else:
                # 亮色主题：阴影用偏蓝灰色（避免纯黑太硬）
                c_inner = "#5A6878"   # 内：最深的蓝灰
                c_mid   = "#8595A8"   # 中：中等蓝灰
                c_outer = "#C8D0DC"   # 外：最浅的灰

            # 把 m 像素分成 3 段：内(40%)、中(30%)、外(30%)
            inner_n = max(1, int(m * 0.4))
            mid_n   = max(1, int(m * 0.3))
            outer_n = m - inner_n - mid_n
            if outer_n < 1:
                outer_n = 1
                mid_n   = max(1, m - inner_n - outer_n)

            # 4 个方向的阴影带生成器（父组件是 _shadow_layer，位于内容之下）
            def add_band(direction, i):
                """direction: 't'/'b'/'l'/'r', i: 第几像素（0=最内）"""
                if i < inner_n:
                    color = c_inner
                elif i < inner_n + mid_n:
                    color = c_mid
                else:
                    color = c_outer

                content_w = max(1, w - 2 * m)
                content_h = max(1, h - 2 * m)

                if direction == 't':
                    band = ctk.CTkFrame(self._shadow_layer, fg_color=color, corner_radius=0,
                                         width=content_w, height=1)
                    band.place(x=m, y=i)
                elif direction == 'b':
                    band = ctk.CTkFrame(self._shadow_layer, fg_color=color, corner_radius=0,
                                         width=content_w, height=1)
                    band.place(x=m, y=h - i - 1)
                elif direction == 'l':
                    band = ctk.CTkFrame(self._shadow_layer, fg_color=color, corner_radius=0,
                                         width=1, height=content_h)
                    band.place(x=i, y=m)
                elif direction == 'r':
                    band = ctk.CTkFrame(self._shadow_layer, fg_color=color, corner_radius=0,
                                         width=1, height=content_h)
                    band.place(x=w - i - 1, y=m)
                self._shadow_frames.append(band)

            for i in range(m):
                add_band('t', i)
                add_band('b', i)
                add_band('l', i)
                add_band('r', i)

            # 把所有阴影带压到 _content_root 之下
            for f in self._shadow_frames:
                try:
                    f.lower(below=self._content_root)
                except Exception:
                    try:
                        f.lower()
                    except Exception:
                        pass
        except Exception:
            pass

    def _refresh_shadow(self, event=None):
        """窗口尺寸变化时重画阴影"""
        try:
            if hasattr(self, "_shadow_frames") and self._shadow_frames:
                self._draw_window_shadow()
        except Exception:
            pass

    # ── 窗口边缘缩放方法 ──
    def _get_resize_edge(self, x, y):
        """检测鼠标所在窗口边缘"""
        m = self._resize_margin
        w, h = self.winfo_width(), self.winfo_height()
        edge = ""
        if x <= m: edge += "w"
        elif x >= w - m: edge += "e"
        if y <= m: edge += "n"
        elif y >= h - m: edge += "s"
        return edge if edge else None

    def _on_resize_motion(self, event):
        if self._is_maximized:
            return
        edge = self._get_resize_edge(event.x, event.y)
        cursors = {
            "n": "sb_v_double_arrow", "s": "sb_v_double_arrow",
            "e": "sb_h_double_arrow", "w": "sb_h_double_arrow",
            "ne": "top_right_corner", "nw": "top_left_corner",
            "se": "bottom_right_corner", "sw": "bottom_left_corner",
        }
        self.config(cursor=cursors.get(edge, "arrow"))
        self._resize_edge = edge

    def _on_resize_press(self, event):
        if self._resize_edge:
            self._resize_start_x = event.x_root
            self._resize_start_y = event.y_root
            self._resize_start_w = self.winfo_width()
            self._resize_start_h = self.winfo_height()
            self._resize_start_winx = self.winfo_x()
            self._resize_start_winy = self.winfo_y()
            return "break"  # 阻止标题栏拖动

    def _on_resize_drag(self, event):
        if not self._resize_edge:
            return  # 不是缩放，让标题栏拖动处理
        dx = event.x_root - self._resize_start_x
        dy = event.y_root - self._resize_start_y
        edge = self._resize_edge
        new_w = self._resize_start_w
        new_h = self._resize_start_h
        new_x = self._resize_start_winx
        new_y = self._resize_start_winy

        if "e" in edge:
            new_w = max(1100, self._resize_start_w + dx)
        if "s" in edge:
            new_h = max(700, self._resize_start_h + dy)
        if "w" in edge:
            new_w = max(1100, self._resize_start_w - dx)
            new_x = self._resize_start_winx + (self._resize_start_w - new_w)
        if "n" in edge:
            new_h = max(700, self._resize_start_h - dy)
            new_y = self._resize_start_winy + (self._resize_start_h - new_h)

        self.geometry(f"{new_w}x{new_h}+{new_x}+{new_y}")

    def _on_resize_release(self, event):
        """缩放结束时更新圆角区域"""
        if self._resize_edge:
            self._resize_edge = None
            self.after(100, self._set_rounded_corners)

    # ── 窗口拖动方法 ──
    def _start_drag(self, event):
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y

    def _on_drag(self, event):
        if self._is_maximized:
            return
        dx = event.x - self._drag_data["x"]
        dy = event.y - self._drag_data["y"]
        x = self.winfo_x() + dx
        y = self.winfo_y() + dy
        self.geometry(f"+{x}+{y}")

    # ── 窗口控制方法 ──
    def _minimize_window(self):
        """最小化窗口（Win32 ShowWindow，overrideredirect 兼容）"""
        try:
            hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
            if hwnd:
                SW_MINIMIZE = 6
                ctypes.windll.user32.ShowWindow(hwnd, SW_MINIMIZE)
        except Exception:
            self.iconify()  # 兜底

    def _maximize_restore_window(self):
        """最大化/还原窗口"""
        if self._is_maximized:
            self.state("normal")
            self._is_maximized = False
        else:
            self.state("zoomed")
            self._is_maximized = True
        self.after(100, self._set_rounded_corners)  # 尺寸变化后更新圆角

    def _close_window(self):
        """关闭窗口（触发 _on_closing → 隐藏到托盘）"""
        self._on_closing()

    def _bind_global_hotkeys(self):
        """绑定全局热键：F11全屏、Ctrl+S保存、Ctrl+F搜索、Ctrl+E导出"""
        # F11: 全屏切换
        self.bind("<F11>", lambda e: self._toggle_fullscreen())
        # Esc: 退出全屏
        self.bind("<Escape>", lambda e: self._exit_fullscreen())
        # Ctrl+S: 保存（各页面自行处理）
        self.bind("<Control-s>", lambda e: self._on_ctrl_s())
        self.bind("<Control-S>", lambda e: self._on_ctrl_s())
        # Ctrl+F: 聚焦搜索
        self.bind("<Control-f>", lambda e: self._on_ctrl_f())
        self.bind("<Control-F>", lambda e: self._on_ctrl_f())
        # Ctrl+E: 导出
        self.bind("<Control-e>", lambda e: self._on_ctrl_e())
        self.bind("<Control-E>", lambda e: self._on_ctrl_e())

    def _toggle_fullscreen(self):
        """切换全屏模式（F11）"""
        self._is_fullscreen = not self._is_fullscreen
        self.attributes('-fullscreen', self._is_fullscreen)
        if not self._is_fullscreen:
            self.state('normal')  # 退出全屏后恢复正常窗口

    def _exit_fullscreen(self):
        """退出全屏（Esc）"""
        if self._is_fullscreen:
            self._is_fullscreen = False
            self.attributes('-fullscreen', False)
            self.state('normal')

    def _on_ctrl_s(self):
        """Ctrl+S: 触发当前页面的保存操作"""
        if self.current_page and hasattr(self.current_page, '_on_ctrl_s'):
            self.current_page._on_ctrl_s()

    def _on_ctrl_f(self):
        """Ctrl+F: 聚焦当前页面的搜索框"""
        if self.current_page and hasattr(self.current_page, '_on_ctrl_f'):
            self.current_page._on_ctrl_f()

    def _on_ctrl_e(self):
        """Ctrl+E: 触发当前页面的导出操作"""
        if self.current_page and hasattr(self.current_page, '_on_ctrl_e'):
            self.current_page._on_ctrl_e()

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

        def do_auto_update():
            asset_url = result.get("asset_download_url", "")
            if not asset_url:
                messagebox.showinfo("提示", "未找到自动更新包，请前往 Releases 手动下载。", parent=dialog)
                return
            dialog.destroy()
            self._auto_update(asset_url, latest)

        def remind_later():
            dialog.destroy()

        # 自动更新按钮
        auto_btn = tk.Button(
            btn_frame, text="自动更新",
            font=("Microsoft YaHei", 12, "bold"),
            bg="#5B9279", fg="white",
            activebackground="#4A7A63", activeforeground="white",
            relief="flat", padx=32, pady=10,
            cursor="hand2",
            command=do_auto_update,
        )
        auto_btn.pack(side="right", padx=(10, 0))

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

    def _auto_update(self, asset_url, latest_version):
        """
        自动更新：下载安装包，静默安装覆盖原文件。
        """
        import tempfile
        import urllib.request
        import urllib.error

        # 进度弹窗
        prog_dialog = tk.Toplevel(self)
        prog_dialog.title("正在更新")
        prog_dialog.geometry("400x180")
        prog_dialog.resizable(False, False)
        prog_dialog.configure(bg="#FFFAF5")
        prog_dialog.transient(self)
        prog_dialog.grab_set()
        prog_dialog.update_idletasks()
        sw = prog_dialog.winfo_screenwidth()
        sh = prog_dialog.winfo_screenheight()
        prog_dialog.geometry(f"400x180+{(sw-400)//2}+{(sh-180)//2}")

        tk.Label(
            prog_dialog, text=f"正在下载 采购助手 V{latest_version}...",
            font=("Microsoft YaHei", 13, "bold"),
            fg="#4A3728", bg="#FFFAF5",
        ).pack(pady=(24, 8))

        status_var = tk.StringVar(value="准备下载...")
        tk.Label(
            prog_dialog, textvariable=status_var,
            font=("Microsoft YaHei", 11),
            fg="#8B7355", bg="#FFFAF5",
        ).pack(pady=(0, 12))

        import tkinter.ttk as ttk
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Update.Horizontal.TProgressbar",
                       background="#C1816D", troughcolor="#F0EBE3",
                       borderwidth=0, thickness=18)
        progress_bar = ttk.Progressbar(
            prog_dialog, mode="indeterminate",
            style="Update.Horizontal.TProgressbar",
        )
        progress_bar.pack(fill="x", padx=40)
        progress_bar.start(10)

        temp_dir = tempfile.gettempdir()
        setup_path = os.path.join(temp_dir, "采购助手_Setup.exe")

        def _download_worker():
            try:
                status_var.set("正在连接下载服务器...")
                req = urllib.request.Request(
                    asset_url,
                    headers={"User-Agent": f"ProcurementSystem/{__version__}"},
                )
                with urllib.request.urlopen(req, timeout=30) as resp:
                    total = int(resp.headers.get("Content-Length", 0))
                    downloaded = 0
                    block_size = 8192

                    progress_bar.stop()
                    progress_bar.configure(mode="determinate", maximum=100)
                    self.after(0, lambda: progress_bar.configure(maximum=100))

                    with open(setup_path, "wb") as f:
                        while True:
                            block = resp.read(block_size)
                            if not block:
                                break
                            f.write(block)
                            downloaded += len(block)
                            if total > 0:
                                pct = int(downloaded * 100 / total)
                                self.after(0, lambda v=pct: progress_bar.configure(value=v))
                                self.after(0, lambda v=pct: status_var.set(f"已下载 {v}%"))

                # 下载完成，静默安装
                self.after(0, lambda: status_var.set("下载完成，正在安装更新..."))
                self.after(0, lambda: progress_bar.configure(value=100))

                # 获取当前安装目录
                exe_dir = os.path.dirname(sys.executable)

                # 启动安装程序（静默模式）
                self.after(0, lambda: prog_dialog.destroy())
                self.after(100, lambda: self._run_updater(setup_path, exe_dir))

            except Exception as e:
                self.after(0, lambda: prog_dialog.destroy())
                self.after(100, lambda: messagebox.showerror(
                    "更新失败", f"下载更新失败：\n{e}\n\n请尝试手动前往 Releases 下载。", parent=self
                ))

        threading.Thread(target=_download_worker, daemon=True).start()

    def _run_updater(self, setup_path, exe_dir):
        """启动安装程序（静默模式）并退出当前应用"""
        try:
            import subprocess
            # 静默安装到当前目录，覆盖所有文件，不显示界面
            cmd = f'"{setup_path}" /VERYSILENT /SUPPRESSMSGBOXES /NORESTART /DIR="{exe_dir}"'
            subprocess.Popen(
                cmd,
                shell=True,
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0,
            )
        except Exception:
            pass
        # 退出当前应用（安装程序会覆盖并重启）
        self._quit_app()

    def _set_titlebar_color(self, color_hex):
        """用 DWM API 设置 Windows 标题栏背景色（与导航栏一致）"""
        try:
            import ctypes
            from ctypes import wintypes

            # 解析十六进制颜色为 BGR DWORD
            r = int(color_hex[1:3], 16)
            g = int(color_hex[3:5], 16)
            b = int(color_hex[5:7], 16)
            # DWMWA_CAPTION_COLOR = 35, 值为 BGR 格式 DWORD
            color_value = (b << 16) | (g << 8) | r

            hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
            if not hwnd:
                # 备用：直接获取窗口句柄
                hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
            dwmapi = ctypes.windll.dwmapi
            # DWMWA_CAPTION_COLOR = 35 (Win10 1903+ / Win11)
            result = dwmapi.DwmSetWindowAttribute(
                hwnd,
                35,  # DWMWA_CAPTION_COLOR
                ctypes.byref(ctypes.c_ulong(color_value)),
                ctypes.sizeof(ctypes.c_ulong),
            )
        except Exception:
            pass  # 不影响主功能，静默失败

    def _build_ui(self):
        # ── 内容根容器（直接 pack 到 self）──────────────────────
        self._content_root = ctk.CTkFrame(
            self, fg_color=COLORS["bg"], corner_radius=0
        )
        self._content_root.pack(side="top", fill="both", expand=True)

        # ── 自定义标题栏（替换系统标题栏）──────────────────────
        _title_bar_height = 40
        self._title_bar = ctk.CTkFrame(
            self._content_root, height=_title_bar_height,
            fg_color=COLORS["sidebar"], corner_radius=0
        )
        self._title_bar.pack(side="top", fill="x")
        self._title_bar.pack_propagate(False)

        # ── 生成折叠按钮图标 ──
        _fold_icon_color = COLORS["sidebar_text"]
        _fold_icon_size = (20, 20)  # 恢复原来尺寸
        self._fold_icon_expanded = None   # 侧边栏展开时显示（竖线在左）
        self._fold_icon_collapsed = None  # 侧边栏折叠时显示（竖线在右）
        if PIL_AVAILABLE:
            try:
                # 展开状态图标：矩形 + 左侧竖线
                _img_exp = Image.new("RGBA", (24, 24), (0, 0, 0, 0))
                from PIL import ImageDraw
                _draw_exp = ImageDraw.Draw(_img_exp)
                _draw_exp.rounded_rectangle([2, 2, 22, 22], radius=3, outline=_fold_icon_color, width=2)
                _draw_exp.line([7, 5, 7, 19], fill=_fold_icon_color, width=2)
                self._fold_icon_expanded = ctk.CTkImage(light_image=_img_exp, size=_fold_icon_size)

                # 折叠状态图标：矩形 + 右侧竖线
                _img_col = Image.new("RGBA", (24, 24), (0, 0, 0, 0))
                _draw_col = ImageDraw.Draw(_img_col)
                _draw_col.rounded_rectangle([2, 2, 22, 22], radius=3, outline=_fold_icon_color, width=2)
                _draw_col.line([17, 5, 17, 19], fill=_fold_icon_color, width=2)
                self._fold_icon_collapsed = ctk.CTkImage(light_image=_img_col, size=_fold_icon_size)
            except Exception:
                pass

        # 折叠按钮（标题栏最左侧，恢复原来高度）
        self._title_collapse_btn = ctk.CTkButton(
            self._title_bar, text="",
            image=self._fold_icon_expanded,
            width=28, height=28,
            fg_color="transparent",
            hover_color=COLORS["sidebar_hover"],
            corner_radius=5,
            command=self._toggle_sidebar,
        )
        self._title_collapse_btn.pack(side="left", padx=(16, 2), pady=6)

        # 页面标题label（折叠按钮右侧）
        self._page_title_label = ctk.CTkLabel(
            self._title_bar, text="看板",
            font=ctk.CTkFont(family="Microsoft YaHei", size=15, weight="bold"),
            text_color=COLORS["sidebar_text"],
            anchor="w",
        )
        self._page_title_label.pack(side="left", padx=(8, 0), pady=7)

        self._title_bar.bind("<Button-1>", self._start_drag)
        self._title_bar.bind("<B1-Motion>", self._on_drag)

        # ── 窗口控制按钮（右侧，Win11 风格）──
        _ctrl_btn_w = 46
        _ctrl_btn_h = 32
        _ctrl_pady = 4  # (40 - 32) / 2

        # 关闭 — 悬停红色
        self._btn_close = ctk.CTkButton(
            self._title_bar, text="✕",
            width=_ctrl_btn_w, height=_ctrl_btn_h,
            font=ctk.CTkFont(size=14),
            fg_color="transparent",
            text_color=COLORS["sidebar_text"],
            hover_color="#E81123",
            corner_radius=6,
            command=self._close_window,
        )
        self._btn_close.pack(side="right", padx=(0, 6), pady=_ctrl_pady)

        # 最大化
        self._btn_maximize = ctk.CTkButton(
            self._title_bar, text="□",
            width=_ctrl_btn_w, height=_ctrl_btn_h,
            font=ctk.CTkFont(size=16),
            fg_color="transparent",
            text_color=COLORS["sidebar_text"],
            hover_color=COLORS["sidebar_hover"],
            corner_radius=6,
            command=self._maximize_restore_window,
        )
        self._btn_maximize.pack(side="right", pady=_ctrl_pady)

        # 最小化
        self._btn_minimize = ctk.CTkButton(
            self._title_bar, text="─",
            width=_ctrl_btn_w, height=_ctrl_btn_h,
            font=ctk.CTkFont(size=16),
            fg_color="transparent",
            text_color=COLORS["sidebar_text"],
            hover_color=COLORS["sidebar_hover"],
            corner_radius=6,
            command=self._minimize_window,
        )
        self._btn_minimize.pack(side="right", pady=_ctrl_pady)

        # ── 底层容器 ──
        self._bottom_container = ctk.CTkFrame(self._content_root, fg_color=COLORS["bg"], corner_radius=0)
        self._bottom_container.pack(side="top", fill="both", expand=True)

        # ── 窗口边缘缩放（所有边+角均可拖拽）──
        self._resize_margin = 6  # 边缘检测像素
        self._resize_edge = None  # 当前调整的边：n/s/e/w/ne/nw/se/sw
        self.bind("<Motion>", self._on_resize_motion)
        self.bind("<Button-1>", self._on_resize_press)
        self.bind("<B1-Motion>", self._on_resize_drag)
        self.bind("<ButtonRelease-1>", self._on_resize_release)

        # 加载导航栏图标（线性版 + 选中实心版）
        self._nav_icon_images = {}         # 线性（未选中）
        self._nav_icon_active_images = {}  # 实心（选中）
        if PIL_AVAILABLE:
            for k, path in NAV_ICON_PATHS.items():
                # 所有图标统一 16 × 16
                sz = (16, 16)
                # 线性版
                if os.path.exists(path):
                    try:
                        self._nav_icon_images[k] = ctk.CTkImage(
                            light_image=Image.open(path), size=sz)
                    except Exception:
                        self._nav_icon_images[k] = None
                else:
                    self._nav_icon_images[k] = None
                # 实心版
                apath = NAV_ICON_ACTIVE_PATHS.get(k, "")
                if os.path.exists(apath):
                    try:
                        self._nav_icon_active_images[k] = ctk.CTkImage(
                            light_image=Image.open(apath), size=sz)
                    except Exception:
                        self._nav_icon_active_images[k] = None
                else:
                    self._nav_icon_active_images[k] = None

        # ── 侧边栏（固定宽度 80px）──────────────────────
        self.sidebar = ctk.CTkFrame(
            self._bottom_container,
            width=80,
            fg_color=COLORS["sidebar"], corner_radius=0, border_width=0
        )
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)  # 固定宽度，不随内容变化

        # 右侧边线
        self.divider = tk.Frame(self._bottom_container, bg=COLORS["border"], width=1)
        self.divider.pack(side="left", fill="y")

        # ── 导航区域（普通Frame，无滚动条）─────────────
        self.nav_canvas = ctk.CTkFrame(
            self.sidebar, fg_color="transparent", corner_radius=0
        )
        self.nav_canvas.pack(side="top", fill="both", expand=True)

        # 导航项列表
        # 格式: (page_key, 显示文字, icon_key)
        # 文字为空则只显示图标（仅设置用）
        self.NAV_ITEMS = [
            ("dashboard",   "看板",  "dashboard"),
            ("packaging",   "下单",  "packaging"),
            ("plan",        "计划",  "plan"),
            ("quotation",   "报价",  "quotation"),
            ("compare",     "比价",  "compare"),
            ("contract",    "合同",  "contract"),
            ("supplier",    "厂家",  "supplier"),
            ("query",       "台账",  "query"),
            ("product_bom", "BOM",   "product_bom"),
            ("collection",  "应付",  "collection"),
            ("purchase",    "垫付",  "purchase"),
            ("travel",      "差旅",  "travel"),
            ("memo",       "备忘",  "memo"),
        ]

        self.nav_buttons = {}

        for item_key, item_label, icon_key in self.NAV_ITEMS:
            self._add_nav_item(item_key, item_label, icon_key)

        # ── 底部：分隔线 + 设置按钮 ──
        self._nav_bottom = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self._nav_bottom.pack(side="bottom", fill="x")

        bottom_sep = ctk.CTkFrame(self._nav_bottom, fg_color=COLORS["divider"], height=1)
        bottom_sep.pack(fill="x", padx=8, pady=(4, 4))

        # 设置按钮（纯图标，放在导航栏最下方）
        self._add_nav_item("settings", "", "settings", parent=self._nav_bottom)

        # ── 右侧主内容区（圆角矩形白色背景）──────────────
        self.main_area = ctk.CTkFrame(
            self._bottom_container,
            fg_color="#FFFFFF",
            corner_radius=16,
        )
        self.main_area.pack(side="left", fill="both", expand=True, padx=(12, 12), pady=(12, 12))

        # 页面内容容器（直接占满 main_area）
        self._page_content = ctk.CTkFrame(self.main_area, fg_color="transparent", corner_radius=16)
        self._page_content.pack(fill="both", expand=True, padx=4, pady=4)

    def _add_nav_item(self, item_key, item_label, icon_key, parent=None):
        """添加导航按钮；parent=None时用nav_canvas，否则用指定parent"""
        _parent = parent or self.nav_canvas
        has_text = bool(item_label)

        # 图标尺寸：统一 16 × 16
        _icon_sz = (16, 16)

        if has_text:
            # ── 有文字项：CTkButton 图标在左 + 文字在右 ──
            icon = self._nav_icon_images.get(icon_key)
            btn = ctk.CTkButton(
                _parent,
                text=item_label,
                image=icon,
                compound="left",
                font=ctk.CTkFont(family="Microsoft YaHei", size=11),
                fg_color="transparent",
                text_color=COLORS["sidebar_text"],
                hover_color=COLORS["sidebar_hover"],
                anchor="w",
                height=30,
                corner_radius=4,
                command=lambda k=item_key: self._switch_page(k),
            )
            btn.pack(pady=(4, 0), padx=4, fill="x")
            self.nav_buttons[item_key] = btn
        else:
            # ── 纯图标项（仅设置）：CTkFrame + CTkLabel ──
            icon_path = NAV_ICON_PATHS.get(icon_key, "")
            img = None
            if PIL_AVAILABLE and os.path.exists(icon_path):
                try:
                    img = ctk.CTkImage(light_image=Image.open(icon_path), size=_icon_sz)
                except Exception:
                    pass

            # 可点击容器（图标 16px + 内边距）
            container = ctk.CTkFrame(
                _parent, fg_color="transparent", corner_radius=4,
                width=28, height=28,
            )
            container.pack(pady=2)
            container.pack_propagate(False)

            # 图标标签（关键：cursor也要设为hand2，并绑定点击事件到标签本身）
            if img:
                icon_label = ctk.CTkLabel(container, image=img, text="", width=_icon_sz[0], height=_icon_sz[1], cursor="hand2")
                icon_label.pack(expand=True)
            else:
                icon_label = ctk.CTkLabel(container, text="?", cursor="hand2")
                icon_label.pack(expand=True)

            # 点击处理函数
            def _make_click_handler(k):
                def _handler(e=None):
                    self._switch_page(k)
                return _handler
            _click = _make_click_handler(item_key)

            # 悬停效果
            def _on_enter(e, c=container):
                c.configure(fg_color=COLORS["sidebar_hover"])
            def _on_leave(e, c=container):
                c.configure(fg_color="transparent")

            # 在容器上绑定事件
            container.configure(cursor="hand2")
            container.bind("<Enter>", _on_enter)
            container.bind("<Leave>", _on_leave)
            container.bind("<Button-1>", _click)

            # 在图标标签上也绑定（防止标签吞掉事件）
            icon_label.bind("<Button-1>", _click)
            icon_label.bind("<Enter>", _on_enter)
            icon_label.bind("<Leave>", _on_leave)

            # 存储引用（用于 switch_page 切换选中状态）
            self.nav_buttons[item_key] = container
            container._is_icon_only = True
            container._icon_key = icon_key
            container._base_img = img

    def _toggle_sidebar(self):
        """切换侧边栏折叠/展开状态"""
        self._sidebar_collapsed = not self._sidebar_collapsed

        if self._sidebar_collapsed:
            # 收起：隐藏侧边栏和分隔线
            self.sidebar.pack_forget()
            self.divider.pack_forget()
            if hasattr(self, '_title_collapse_btn') and self._fold_icon_collapsed:
                self._title_collapse_btn.configure(image=self._fold_icon_collapsed)
        else:
            # 展开：先忘记 main_area，再按正确顺序重新 pack
            self.main_area.pack_forget()
            self.sidebar.pack(side="left", fill="y")
            self.divider.pack(side="left", fill="y")
            self.main_area.pack(side="left", fill="both", expand=True,
                               padx=(12, 12), pady=(12, 12))
            if hasattr(self, '_title_collapse_btn') and self._fold_icon_expanded:
                self._title_collapse_btn.configure(image=self._fold_icon_expanded)

        # 保存状态到 settings.txt（兼容 key=value 格式）
        try:
            import os
            _data_dir = os.path.join(os.path.expanduser("~"), "采购管理系统数据")
            _sp = os.path.join(_data_dir, "settings.txt")
            _val = "1" if self._sidebar_collapsed else "0"

            _lines = []
            if os.path.exists(_sp):
                with open(_sp, "r", encoding="utf-8") as _f:
                    _lines = _f.readlines()

            _found = False
            for _i, _line in enumerate(_lines):
                if _line.strip().startswith("sidebar_collapsed="):
                    _lines[_i] = f"sidebar_collapsed={_val}\n"
                    _found = True
                    break

            if not _found:
                _lines.append(f"sidebar_collapsed={_val}\n")

            with open(_sp, "w", encoding="utf-8") as _f:
                _f.writelines(_lines)
        except Exception:
            pass

    def _switch_page(self, key):
        """切换页面并更新导航栏选中状态（线性图标→实心图标）"""
        # ── 标题栏显示当前页面标题 ──
        _page_titles = {
            "dashboard":   "看板",
            "packaging":   "下单",
            "plan":        "计划",
            "quotation":   "报价",
            "compare":     "比价",
            "contract":    "合同",
            "supplier":    "厂家",
            "query":       "台账",
            "product_bom": "BOM",
            "collection":  "催款",
            "purchase":    "垫付",
            "travel":      "差旅",
            "memo":        "备忘",
            "settings":    "设置",
        }
        if hasattr(self, '_page_title_label'):
            self._page_title_label.configure(text=_page_titles.get(key, "采购助手"))

        # 判断是否为纯图标项
        icon_only_items = {"purchase", "travel", "memo", "settings"}
        # 小尺寸图标键（垫付/差旅/待办/设置）
        _small_icon_keys = {"purchase", "travel", "memo", "settings"}

        for k, widget in self.nav_buttons.items():
            is_io = getattr(widget, '_is_icon_only', False)
            if is_io:
                # ── 纯图标项（Frame+Label）──
                widget.configure(fg_color="transparent")
                # 切换回线性图标
                ik = getattr(widget, '_icon_key', k)
                _isz = (16, 16)  # 所有图标统一 16px
                if PIL_AVAILABLE:
                    try:
                        p = NAV_ICON_PATHS.get(ik, "")
                        if os.path.exists(p):
                            linear_img = ctk.CTkImage(light_image=Image.open(p), size=_isz)
                            for child in widget.winfo_children():
                                if isinstance(child, ctk.CTkLabel):
                                    child.configure(image=linear_img)
                                    break
                    except Exception:
                        pass
            else:
                # ── 有文字项（CTkButton）──
                btn = widget
                linear_img = None
                if PIL_AVAILABLE:
                    try:
                        p = NAV_ICON_PATHS.get(k, "")
                        if os.path.exists(p):
                            linear_img = ctk.CTkImage(light_image=Image.open(p), size=(16, 16))
                    except Exception:
                        pass
                btn.configure(
                    fg_color="transparent",
                    text_color=COLORS["sidebar_text"],
                    border_width=0,
                    image=linear_img or self._nav_icon_images.get(k),
                )

        if key in self.nav_buttons:
            widget = self.nav_buttons[key]
            is_io = getattr(widget, '_is_icon_only', False)

            if is_io:
                # 纯图标项：高亮 + 实心图标
                widget.configure(fg_color=COLORS["sidebar_active"])
                ik = getattr(widget, '_icon_key', key)
                _isz = (16, 16)  # 所有图标统一 16px
                if PIL_AVAILABLE:
                    try:
                        ap = NAV_ICON_ACTIVE_PATHS.get(key, "")
                        if os.path.exists(ap):
                            active_img = ctk.CTkImage(light_image=Image.open(ap), size=_isz)
                            for child in widget.winfo_children():
                                if isinstance(child, ctk.CTkLabel):
                                    child.configure(image=active_img)
                                    break
                    except Exception:
                        pass
            else:
                # 有文字项：CTkButton 高亮 + 实心图标
                active_img = None
                if PIL_AVAILABLE:
                    try:
                        ap = NAV_ICON_ACTIVE_PATHS.get(key, "")
                        if os.path.exists(ap):
                            active_img = ctk.CTkImage(light_image=Image.open(ap), size=(16, 16))
                    except Exception:
                        pass
                widget.configure(
                    fg_color=COLORS["sidebar_active"],
                    text_color=COLORS["sidebar_active_text"],
                    border_width=0,
                    image=active_img or self._nav_icon_active_images.get(key) or self._nav_icon_images.get(key),
                )

        # 清空页面内容容器
        for widget in self._page_content.winfo_children():
            widget.destroy()

        # ── 构建页面专用配色：外层白色 + 内部卡片用导航栏色 ──
        _pg_colors = dict(COLORS)
        _pg_colors["bg"] = COLORS["sidebar"]   # 页面外层→导航栏色（与卡片协调）
        _pg_colors["card"] = COLORS["sidebar"]  # 卡片/区域→导航栏色

        if key == "dashboard":
            self.current_page = DashboardPage(self._page_content, self.db, _pg_colors, switch_page=self._switch_page)
        elif key == "packaging":
            self.current_page = PackagingPage(self._page_content, self.db, _pg_colors)
        elif key == "quotation":
            self.current_page = QuotationPage(self._page_content, self.db, _pg_colors)
        elif key == "query":
            self.current_page = QueryPage(self._page_content, self.db, _pg_colors)
        elif key == "supplier":
            self.current_page = SupplierPage(self._page_content, self.db, _pg_colors)
        elif key == "collection":
            self.current_page = CollectionPage(self._page_content, self.db, _pg_colors)
        elif key == "purchase":
            self.current_page = PurchasePage(self._page_content, self.db, _pg_colors)
        elif key == "travel":
            self.current_page = TravelPage(self._page_content, self.db, _pg_colors)
        elif key == "memo":
            self.current_page = MemoPage(self._page_content, self.db, _pg_colors)
        elif key == "contract":
            self.current_page = ContractPage(self._page_content, self.db, _pg_colors)
        elif key == "product_bom":
            self.current_page = ProductBomPage(self._page_content, self.db, _pg_colors)
        elif key == "compare":
            self.current_page = ThirdPartyPage(self._page_content, self.db, _pg_colors)
        elif key == "plan":
            self.current_page = PlanPage(self._page_content, self.db, _pg_colors)
        elif key == "settings":
            self.current_page = SettingsPage(self._page_content, self.db, _pg_colors)

        if self.current_page:
            self.current_page.pack(fill="both", expand=True)

    def _open_settings(self):
        """打开设置页面"""
        self._switch_page("settings")

    def _on_closing(self):
        """关闭窗口：隐藏到托盘（不退出，托盘始终显示）"""
        self.withdraw()  # 隐藏窗口，托盘图标保持

    def _start_tray(self):
        """启动时创建系统托盘图标"""
        if self._tray_icon is not None:
            return
        self._tray_thread = threading.Thread(target=self._run_tray, daemon=True)
        self._tray_thread.start()

    def _run_tray(self):
        """在新线程中运行托盘图标（pystray 的事件循环）"""
        try:
            # 加载托盘图标图片（×16.ico）
            if os.path.exists(TRAY_ICON_PATH):
                img = PILImage.open(TRAY_ICON_PATH)
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
        """托盘菜单：显示窗口（托盘图标始终保持）"""
        self.after(0, self._do_restore)

    def _on_tray_quit(self, icon=None, item=None):
        """托盘菜单：退出应用"""
        if self._tray_icon:
            self._tray_icon.stop()
            self._tray_icon = None
        self.after(0, self._quit_app)

    def _do_restore(self):
        """在主线程中恢复窗口（托盘图标保持不销毁）"""
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
