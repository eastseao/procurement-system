#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
采购管理系统 - 主入口
功能：物料下单、物料查询、供应商管理、催款记录、采购垫付、差旅报销、备忘录、设置
V1.9.0 修复：系统托盘常驻、金额自动匹配、甲方电话修正
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

# ── 莫兰迪暖色调色板（V1.9.8 配色微调）──────────────
# 参考：UI优化.md 第七节
# 支持 light/dark 两套主题，通过 settings.txt 中 theme=light/dark 切换
_COLORS_LIGHT = {
    "primary":         "#D4917A",
    "primary_hover":   "#C1816D",
    "primary_light":    "#FDF2EE",
    "success":         "#5B9279",
    "warning":         "#E4A36A",
    "danger":          "#B56A6A",
    "bg":              "#FEF9F2",
    "card":            "#FFFFFF",
    "sidebar":         "#F3EDE6",
    "sidebar_text":    "#5D4E37",
    "sidebar_active":  "#E8D5C4",
    "sidebar_active_text": "#8B5E3C",
    "sidebar_hover":   "#E8DDD0",
    "text":            "#4A3728",
    "text_secondary":  "#8B7355",
    "border":          "#D4C5B5",
    "divider":         "#E8DDD0",
    "nav_group_bg":   "#E8D5C4",
    "nav_indicator":   "#D4917A",
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

_COLORS_DARK = {
    "primary":         "#D4917A",
    "primary_hover":   "#E0A080",
    "primary_light":   "#3A2E28",
    "success":         "#5B9279",
    "warning":         "#E4A36A",
    "danger":          "#B56A6A",
    "bg":              "#1E1B18",
    "card":            "#2C2824",
    "sidebar":         "#252220",
    "sidebar_text":    "#EAE5DD",
    "sidebar_active":  "#3A2E28",
    "sidebar_active_text": "#D4917A",
    "sidebar_hover":   "#302B26",
    "text":            "#EAE5DD",
    "text_secondary":  "#A89888",
    "border":          "#3A3530",
    "divider":         "#302B26",
    "nav_group_bg":   "#302B26",
    "nav_indicator":   "#D4917A",
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

def get_colors(theme="light"):
    """返回指定主题的颜色字典"""
    if theme == "dark":
        return dict(_COLORS_DARK)
    return dict(_COLORS_LIGHT)

# 根据设置选择主题（启动时使用）
_theme = settings.get("theme", "light")
if _theme not in ("light", "dark"):
    _theme = "light"
COLORS = get_colors(_theme)


def _get_resource_path(rel_path):
    """兼容PyInstaller打包后的资源路径"""
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, rel_path)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), rel_path)


ICO_PATH  = _get_resource_path("assets/同仁堂企业LOGO.ico")
LOGO_PATH          = _get_resource_path("assets/同仁堂企业LOGO.png")

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
    "contract":   _get_resource_path("assets/nav_contract.png"),
    "settings":   _get_resource_path("assets/nav_settings.png"),
    "product_bom": _get_resource_path("assets/nav_product_bom.png"),
    "compare":     _get_resource_path("assets/nav_compare.png"),
    "collapse":    _get_resource_path("assets/nav_collapse.png"),
    "expand":      _get_resource_path("assets/nav_expand.png"),
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
        self.title("采购助手")
        self.geometry("1280x800")
        self.minsize(1100, 700)
        self.configure(fg_color=COLORS["bg"])

        # ── 设置程序图标（标题栏 + 任务栏）──
        # 参照 V1.5 的极简方式：仅用 iconbitmap()，不用 iconphoto/AppUserModelID/WM_SETICON
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

        # ── 系统托盘状态 ──
        self._tray_enabled = settings.get("tray_enabled", "0") == "1"
        self._tray_icon = None
        self._tray_thread = None

        self._build_ui()
        self._switch_page("dashboard")

        # ── 系统托盘：始终显示 ──
        if PYSTRAY_AVAILABLE:
            self._start_tray()

        # ── 拦截关闭事件（隐藏窗口而非退出）──
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

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
        自动更新：下载新版本 EXE，创建更新脚本，重启应用。
        在后台线程下载，主线程显示进度。
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
        status_label = tk.Label(
            prog_dialog, textvariable=status_var,
            font=("Microsoft YaHei", 11),
            fg="#8B7355", bg="#FFFAF5",
        )
        status_label.pack(pady=(0, 12))

        # 进度条（ttk）
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
        exe_path = sys.executable  # 当前 EXE 完整路径
        exe_dir = os.path.dirname(exe_path)
        exe_name = os.path.basename(exe_path)
        new_exe_path = os.path.join(temp_dir, "procurement_update.exe")

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

                    with open(new_exe_path, "wb") as f:
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

                # 下载完成，创建更新脚本
                self.after(0, lambda: status_var.set("下载完成，正在准备更新..."))
                self.after(0, lambda: progress_bar.configure(value=100))

                # 写入更新批处理脚本
                bat_path = os.path.join(temp_dir, "procurement_update.bat")
                bat_content = f"""@echo off
timeout /t 2 /nobreak > nul
taskkill /f /im "{exe_name}" > nul 2>&1
timeout /t 1 /nobreak > nul
copy /Y "{new_exe_path}" "{exe_path}" > nul
start "" "{exe_path}"
del "{new_exe_path}" > nul 2>&1
"""
                with open(bat_path, "w", encoding="gbk") as f:
                    f.write(bat_content)

                self.after(0, lambda: prog_dialog.destroy())
                self.after(100, lambda: self._run_updater(bat_path))

            except Exception as e:
                self.after(0, lambda: prog_dialog.destroy())
                self.after(100, lambda: messagebox.showerror(
                    "更新失败", f"下载更新失败：\n{e}\n\n请尝试手动前往 Releases 下载。", parent=self
                ))

        threading.Thread(target=_download_worker, daemon=True).start()

    def _run_updater(self, bat_path):
        """启动更新脚本并退出当前应用"""
        try:
            import subprocess
            # 用 cmd /c start 启动批处理脚本（不阻塞）
            subprocess.Popen(
                f'cmd /c start "" "{bat_path}"',
                shell=True,
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0,
            )
        except Exception:
            pass
        # 退出当前应用
        self._quit_app()

    def _build_ui(self):
        # ── 侧边栏（分组折叠式）──────────────────────────
        self._sidebar_collapsed = False  # 整个侧边栏的折叠状态
        self._sidebar_expanded_width = 120
        self._sidebar_collapsed_width = 42

        self.sidebar = ctk.CTkFrame(
            self, width=self._sidebar_expanded_width, fg_color=COLORS["sidebar"],
            corner_radius=0, border_width=0
        )
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # 右侧边线
        self.divider = tk.Frame(self, bg=COLORS["border"], width=1)
        self.divider.pack(side="left", fill="y")

        # 加载导航栏图标
        self._nav_icon_images = {}
        if PIL_AVAILABLE:
            for k, path in NAV_ICON_PATHS.items():
                if os.path.exists(path):
                    try:
                        img = Image.open(path)
                        sz = (24, 24) if k not in ("collapse", "expand") else (18, 18)
                        self._nav_icon_images[k] = ctk.CTkImage(
                            light_image=img, size=sz)
                    except Exception:
                        self._nav_icon_images[k] = None
                else:
                    self._nav_icon_images[k] = None

        # ── 折叠/展开按钮 ──────────────────────────────
        self.toggle_frame = ctk.CTkFrame(
            self.sidebar, fg_color="transparent", height=44)
        self.toggle_frame.pack(fill="x", padx=4, pady=(6, 2))
        self.toggle_frame.pack_propagate(False)

        self.toggle_btn = ctk.CTkButton(
            self.toggle_frame,
            text="",
            image=self._nav_icon_images.get("collapse"),
            width=32, height=32,
            fg_color="transparent",
            hover_color=COLORS["sidebar_hover"],
            corner_radius=4,
            command=self._toggle_sidebar,
        )
        self.toggle_btn.pack(side="right", padx=(0, 4))

        # ── 导航滚动容器 ─────────────────────────────────
        self.nav_canvas = ctk.CTkScrollableFrame(
            self.sidebar, fg_color="transparent", corner_radius=0,
            scrollbar_button_color=COLORS["border"],
            scrollbar_button_hover_color=COLORS["sidebar_hover"],
        )
        self.nav_canvas.pack(side="top", fill="both", expand=True, padx=0, pady=(0, 0))

        # ── 导航分组结构 ─────────────────────────────────
        self.NAV_GROUPS = [
            {
                "label": "看板",
                "items": [("dashboard", "看板", "dashboard")],
            },
            {
                "label": "采购",
                "items": [
                    ("packaging",  "下单",   "packaging"),
                    ("quotation",  "报价",   "quotation"),
                    ("compare",    "比价",   "compare"),
                    ("contract",   "合同",   "contract"),
                    ("supplier",   "厂家",   "supplier"),
                ],
            },
            {
                "label": "数据",
                "items": [
                    ("query",      "查询",   "query"),
                    ("product_bom","BOM","product_bom"),
                ],
            },
            {
                "label": "财务",
                "items": [
                    ("collection", "应付",   "collection"),
                    ("purchase",   "垫付",   "purchase"),
                    ("travel",     "报销",   "travel"),
                ],
            },
            {
                "label": "工具",
                "items": [
                    ("memo",       "待办",   "memo"),
                    ("settings",   "设置",   "settings"),
                ],
            },
        ]

        # 加载折叠状态
        self._nav_collapsed = self._load_nav_state()

        self.nav_buttons = {}
        self._group_widgets = {}

        for group in self.NAV_GROUPS:
            self._add_group_header(group)
            for item_key, item_label, icon_key in group["items"]:
                self._add_nav_item(group, item_key, item_label, icon_key)

        # ── 主内容区域 ──
        self.main_area = ctk.CTkFrame(self, fg_color=COLORS["bg"], corner_radius=0)
        self.main_area.pack(side="left", fill="both", expand=True)

    # ── 导航栏分组折叠辅助方法 ──────────────────────────
    def _add_group_header(self, group):
        """添加分组标题（可点击折叠/展开）- P1 优化：三角图标 + 胶囊角标"""
        label = group["label"]
        key = label
        is_collapsed = key in self._nav_collapsed

        # 分组标题容器（可点击）
        header_frame = ctk.CTkFrame(
            self.nav_canvas,
            fg_color="transparent",
            corner_radius=COLORS["radius_nav_item"],
            cursor="hand2",  # 鼠标手型（如果支持）
        )
        header_frame.pack(fill="x", padx=4, pady=(8, 2))

        # 左侧：三角图标 + 标题
        arrow = "▶" if is_collapsed else "▼"
        title_label = ctk.CTkLabel(
            header_frame,
            text="{} {}".format(arrow, label),
            font=ctk.CTkFont(family="Microsoft YaHei", size=12, weight="bold"),
            text_color=COLORS["sidebar_text"],
            anchor="w",
        )
        title_label.pack(side="left", fill="x", expand=True, padx=(8, 4), pady=6)

        # 右侧：不再显示胶囊角标
        # （P1 优化：简化导航栏，去除数字角标）

        # 绑定点击事件到整个容器
        for widget in [header_frame, title_label]:
            widget.bind("<Button-1>", lambda e, g=group: self._toggle_group(g))
            widget.configure(cursor="hand2")

        # 悬停效果
        def _on_enter(e):
            header_frame.configure(fg_color=COLORS["sidebar_hover"])
        def _on_leave(e):
            header_frame.configure(fg_color="transparent")
        header_frame.bind("<Enter>", _on_enter)
        header_frame.bind("<Leave>", _on_leave)

        underline = ctk.CTkFrame(self.nav_canvas, height=1, fg_color=COLORS["divider"], corner_radius=0)
        underline.pack(fill="x", padx=8, pady=(0, 2))

        # 子项容器：所有子项放在这个 frame 里，折叠时隐藏整个容器
        content_frame = ctk.CTkFrame(self.nav_canvas, fg_color="transparent", corner_radius=0)
        if not is_collapsed:
            content_frame.pack(fill="x", padx=(12, 4), pady=(0, 4), after=underline)

        self._group_widgets[key] = {
            "header": header_frame,
            "title": title_label,
            "underline": underline,
            "content": content_frame,
        }

    def _add_nav_item(self, group, item_key, item_label, icon_key):
        """添加导航按钮到分组的 content_frame 中"""
        key = group["label"]
        content = self._group_widgets[key]["content"]

        icon = self._nav_icon_images.get(icon_key)
        btn = ctk.CTkButton(
            content,
            text=item_label,
            image=icon,
            compound="left",
            font=ctk.CTkFont(family="Microsoft YaHei", size=12),
            fg_color="transparent",
            text_color=COLORS["sidebar_text"],
            hover_color=COLORS["sidebar_hover"],
            anchor="w",
            height=40,
            corner_radius=COLORS["radius_nav_item"],
            command=lambda k=item_key: self._switch_page(k),
        )
        btn.pack(fill="x", padx=0, pady=1)

        self.nav_buttons[item_key] = btn

    def _toggle_group(self, group):
        """切换分组折叠/展开状态"""
        key = group["label"]
        widgets = self._group_widgets[key]
        content = widgets["content"]
        underline = widgets["underline"]
        title_label = widgets["title"]

        if key in self._nav_collapsed:
            # 展开：显示 content_frame，放在 underline 之后
            del self._nav_collapsed[key]
            content.pack(fill="x", padx=(12, 4), pady=(0, 4), after=underline)
        else:
            # 折叠：隐藏 content_frame
            self._nav_collapsed[key] = True
            content.pack_forget()

        # 更新三角图标
        is_collapsed = key in self._nav_collapsed
        arrow = "▶" if is_collapsed else "▼"
        title_label.configure(text="{} {}".format(arrow, key))

        self._save_nav_state()

    def _toggle_sidebar(self):
        """折叠/展开整个侧边栏"""
        if self._sidebar_collapsed:
            # 展开
            self._sidebar_collapsed = False
            self.sidebar.configure(width=self._sidebar_expanded_width)
            self.nav_canvas.pack(side="top", fill="both", expand=True, padx=0, pady=(0, 0))
            self.toggle_btn.pack(side="right", padx=(0, 4))
            self.toggle_btn.configure(image=self._nav_icon_images.get("collapse"))
            # 恢复所有导航按钮的文字
            for btn in self.nav_buttons.values():
                if hasattr(btn, "_orig_text"):
                    btn.configure(text=btn._orig_text)
        else:
            # 折叠
            self._sidebar_collapsed = True
            self.nav_canvas.pack_forget()
            self.sidebar.configure(width=self._sidebar_collapsed_width)
            self.toggle_btn.pack(side="top")
            self.toggle_btn.configure(image=self._nav_icon_images.get("expand"))
            # 保存当前文字并隐藏
            for btn in self.nav_buttons.values():
                if not hasattr(btn, "_orig_text"):
                    btn._orig_text = btn.cget("text")
                btn.configure(text="")
        self.sidebar.update_idletasks()

    def _save_nav_state(self):
        """保存导航折叠状态到 settings.txt"""
        try:
            settings = load_settings()
            collapsed_str = ",".join(self._nav_collapsed.keys())
            settings["nav_collapsed"] = collapsed_str
            settings_path = os.path.join(_data_dir, "settings.txt")
            with open(settings_path, "w", encoding="utf-8") as f:
                for k, v in settings.items():
                    f.write("{}={}\n".format(k, v))
        except Exception:
            pass

    def _load_nav_state(self):
        """从 settings.txt 加载导航折叠状态（兼容旧版本的分组名称）"""
        try:
            settings = load_settings()
            collapsed_str = settings.get("nav_collapsed", "")
            if collapsed_str:
                collapsed = {}
                for k in collapsed_str.split(","):
                    k = k.strip()
                    if not k:
                        continue
                    # 兼容旧版本名称
                    if k == "采购管理":
                        k = "采购"
                    elif k == "财务管理":
                        k = "财务"
                    collapsed[k] = True
                return collapsed
        except Exception:
            pass
        return {}

    def _switch_page(self, key):
        """切换页面并更新导航栏选中状态"""
        for k, btn in self.nav_buttons.items():
            btn.configure(
                fg_color="transparent",
                text_color=COLORS["sidebar_text"],
                border_width=0,
            )

        if key in self.nav_buttons:
            self.nav_buttons[key].configure(
                fg_color=COLORS["sidebar_active"],
                text_color=COLORS["sidebar_active_text"],
                border_width=0,
            )

        for widget in self.main_area.winfo_children():
            widget.destroy()

        if key == "dashboard":
            self.current_page = DashboardPage(self.main_area, self.db, COLORS, switch_page=self._switch_page)
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
        elif key == "contract":
            self.current_page = ContractPage(self.main_area, self.db, COLORS)
        elif key == "product_bom":
            self.current_page = ProductBomPage(self.main_area, self.db, COLORS)
        elif key == "compare":
            self.current_page = ThirdPartyPage(self.main_area, self.db, COLORS)
        elif key == "settings":
            self.current_page = SettingsPage(self.main_area, self.db, COLORS)

        if self.current_page:
            self.current_page.pack(fill="both", expand=True)
    def _open_settings(self):
        """打开设置页面"""
        self._switch_page("settings")
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
            # 加载托盘图标图片
            if os.path.exists(ICO_PATH):
                img = PILImage.open(ICO_PATH)
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
            # 加载托盘图标图片
            if os.path.exists(ICO_PATH):
                img = PILImage.open(ICO_PATH)
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
