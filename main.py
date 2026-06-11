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
    def __init__(self):
        super().__init__()
        self.title("")  # 空标题（不显示文字）
        self.geometry("1280x800")
        self.minsize(1100, 700)
        self.configure(fg_color=COLORS["bg"])

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
        # ── 侧边栏（窄版图标栏，图标+文字纵向排列）─────────
        self._sidebar_width = 72

        # 加载导航栏图标（线性版 + 选中实心版）
        self._nav_icon_images = {}         # 线性（未选中）
        self._nav_icon_active_images = {}  # 实心（选中）
        if PIL_AVAILABLE:
            for k, path in NAV_ICON_PATHS.items():
                sz = (22, 22)
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

        # ── 底层容器 ──
        self._bottom_container = ctk.CTkFrame(self, fg_color=COLORS["bg"], corner_radius=0)
        self._bottom_container.pack(side="top", fill="both", expand=True)

        # ── 侧边栏 ──
        self.sidebar = ctk.CTkFrame(
            self._bottom_container, width=self._sidebar_width,
            fg_color=COLORS["sidebar"], corner_radius=0, border_width=0
        )
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # 右侧边线
        self.divider = tk.Frame(self._bottom_container, bg=COLORS["border"], width=1)
        self.divider.pack(side="left", fill="y")

        # ── 导航区域（普通Frame，无滚动条）─────────────
        self.nav_canvas = ctk.CTkFrame(
            self.sidebar, fg_color="transparent", corner_radius=0
        )
        self.nav_canvas.pack(side="top", fill="both", expand=True)

        # 导航项列表（purchase/travel/memo 只显示图标，无文字；settings 移到底部）
        # 格式: (page_key, 显示文字, icon_key)  文字为空则只显示图标
        self.NAV_ITEMS = [
            ("dashboard",   "看板",  "dashboard"),
            ("packaging",   "下单",  "packaging"),
            ("quotation",   "报价",  "quotation"),
            ("compare",     "比价",  "compare"),
            ("contract",    "合同",  "contract"),
            ("supplier",    "厂家",  "supplier"),
            ("query",       "台账",  "query"),
            ("product_bom", "BOM",   "product_bom"),
            ("collection",  "应付",  "collection"),
            ("purchase",    "",      "purchase"),    # 只图标
            ("travel",      "",      "travel"),      # 只图标
            ("memo",        "",      "memo"),        # 只图标
        ]

        self.nav_buttons = {}

        for item_key, item_label, icon_key in self.NAV_ITEMS:
            self._add_nav_item(item_key, item_label, icon_key)

        # ── 底部分隔线 ──
        bottom_sep = ctk.CTkFrame(self.sidebar, fg_color=COLORS["divider"], height=1)
        bottom_sep.pack(side="bottom", fill="x", padx=8, pady=(4, 8))

        # ── 底部导航区（设置按钮）──
        self.nav_bottom = ctk.CTkFrame(self.sidebar, fg_color="transparent", corner_radius=0)
        self.nav_bottom.pack(side="bottom", fill="x", padx=4, pady=(0, 8))
        self._add_nav_item("settings", "", "settings", parent=self.nav_bottom)

        # ── 右侧主内容区（圆角矩形白色背景）──────────────
        self.main_area = ctk.CTkFrame(
            self._bottom_container,
            fg_color="#FFFFFF",
            corner_radius=16,
        )
        self.main_area.pack(side="left", fill="both", expand=True, padx=(12, 12), pady=(12, 12))

        # 页面内容容器
        self._page_content = ctk.CTkFrame(self.main_area, fg_color="transparent", corner_radius=16)
        self._page_content.pack(fill="both", expand=True, padx=4, pady=4)

    def _add_nav_item(self, item_key, item_label, icon_key, parent=None):
        """添加导航按钮；parent=None时用nav_canvas，否则用指定parent"""
        _parent = parent or self.nav_canvas
        has_text = bool(item_label)

        if has_text:
            # ── 有文字项：CTkButton 图标+文字 ──
            icon = self._nav_icon_images.get(icon_key)
            btn = ctk.CTkButton(
                _parent,
                text=item_label,
                image=icon,
                compound="top",
                font=ctk.CTkFont(family="Microsoft YaHei", size=11),
                fg_color="transparent",
                text_color=COLORS["sidebar_text"],
                hover_color=COLORS["sidebar_hover"],
                anchor="center",
                width=56,
                height=48,
                corner_radius=8,
                command=lambda k=item_key: self._switch_page(k),
            )
            btn.pack(pady=2)
            self.nav_buttons[item_key] = btn
        else:
            # ── 纯图标项：CTkFrame + CTkLabel（绕过CTkButton空文本渲染bug）──
            icon_path = NAV_ICON_PATHS.get(icon_key, "")
            img = None
            if PIL_AVAILABLE and os.path.exists(icon_path):
                try:
                    img = ctk.CTkImage(light_image=Image.open(icon_path), size=(26, 26))
                except Exception:
                    pass

            # 可点击容器
            container = ctk.CTkFrame(
                _parent, fg_color="transparent", corner_radius=8,
                width=56, height=44,
            )
            container.pack(pady=2)
            container.pack_propagate(False)

            # 图标标签（关键：cursor也要设为hand2，并绑定点击事件到标签本身）
            if img:
                icon_label = ctk.CTkLabel(container, image=img, text="", width=26, height=26, cursor="hand2")
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

    def _switch_page(self, key):
        """切换页面并更新导航栏选中状态（线性图标→实心图标）"""
        # 判断是否为纯图标项
        icon_only_items = {"purchase", "travel", "memo", "settings"}

        for k, widget in self.nav_buttons.items():
            is_io = getattr(widget, '_is_icon_only', False)
            if is_io:
                # ── 纯图标项（Frame+Label）──
                widget.configure(fg_color="transparent")
                # 切换回线性图标
                ik = getattr(widget, '_icon_key', k)
                if PIL_AVAILABLE:
                    try:
                        p = NAV_ICON_PATHS.get(ik, "")
                        if os.path.exists(p):
                            linear_img = ctk.CTkImage(light_image=Image.open(p), size=(26, 26))
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
                            linear_img = ctk.CTkImage(light_image=Image.open(p), size=(22, 22))
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
                if PIL_AVAILABLE:
                    try:
                        ap = NAV_ICON_ACTIVE_PATHS.get(key, "")
                        if os.path.exists(ap):
                            active_img = ctk.CTkImage(light_image=Image.open(ap), size=(26, 26))
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
                            active_img = ctk.CTkImage(light_image=Image.open(ap), size=(22, 22))
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
