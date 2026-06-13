#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""看板页面 V1.9.3 - 优化版（KPI趋势卡 + 点击跳转 + 待办聚合 + 动态活动流）"""

import customtkinter as ctk
import tkinter as tk
from datetime import datetime, date, timedelta
import calendar
import configparser
import os

# 各模块莫兰迪色
MODULE_COLORS = {
    "packaging":  "#C1816D",   # 陶土色 - 物料下单
    "collection": "#8FA882",   # 鼠尾草绿 - 催款记录
    "purchase":   "#C9A96E",   # 麦色 - 采购垫付
    "travel":     "#B56A6A",   # 暗玫瑰 - 差旅报销
    "memo":       "#7BA5B5",   # 灰蓝 - 备忘录
    "quotation":  "#9B8AAE",   # 淡紫 - 报价单
    "compare":    "#C4A35A",   # 琥珀 - 三方比价
    "contract":   "#6B9080",   # 青绿 - 合同
    "arrival":    "#D4A76A",   # 金麦色 - 到货提醒
}

# 趋势箭头配色
TREND_UP_COLOR   = "#8FA882"   # 绿色 - 上升
TREND_DOWN_COLOR = "#B56A6A"   # 红色 - 下降
TREND_NEUTRAL    = "#B0A8A0"   # 灰色 - 持平

# 可配置的 KPI 卡片预设列表
AVAILABLE_KPI_CARDS = {
    "packaging": {
        "title": "物料下单",
        "keys": [("处理中", "packaging_active"), ("已完成", "packaging_done")],
        "color": "#C1816D", "page_key": "packaging"
    },
    "collection": {
        "title": "催款记录",
        "keys": [(None, "collection_total")],
        "color": "#8FA882", "page_key": "collection"
    },
    "purchase": {
        "title": "采购垫付",
        "keys": [("总笔数", "purchase_total"), ("待报销", "purchase_pending")],
        "color": "#C9A96E", "page_key": "purchase"
    },
    "travel": {
        "title": "差旅报销",
        "keys": [("行程数", "travel_total"), ("待报销", "travel_pending")],
        "color": "#B56A6A", "page_key": "travel"
    },
    "contract_pending": {
        "title": "待签合同",
        "keys": [(None, "contract_pending")],
        "color": "#6B9080", "page_key": "packaging"
    },
    "compare_month": {
        "title": "本月比价",
        "keys": [(None, "compare_month")],
        "color": "#C4A35A", "page_key": "compare"
    },
}


from ui_utils import WheelScrollFrame


class DashboardPage(ctk.CTkFrame):
    """看板主页面 - V1.9.7 P2 优化（KPI卡片迷你趋势图）"""

    def __init__(self, parent, db, C, switch_page=None):
        super().__init__(parent, fg_color=C["bg"], corner_radius=0)
        self.db = db
        self.C = C
        self.switch_page = switch_page  # 页面切换回调
        self._value_labels = {}   # key -> label widget
        self._trend_labels = {}   # key -> trend label widget
        self._sparkline_labels = {}  # key -> sparkline image label
        self._progress_bars = {}   # key -> progress bar widget
        self._card_refs = {}      # key -> card frame (for hover effect)
        self._build_ui()
        self.update_idletasks()  # 确保 UI 完全渲染后再加载数据
        self._load_data()
        # 每5分钟自动刷新
        self._auto_refresh()

    # ──────────────────────────────────────────────
    # UI 构建
    # ──────────────────────────────────────────────
    def _build_ui(self):
        # 主容器（无滚动条，固定布局）
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True)

        # ── 顶部：看板总览标题栏 ──
        header_bar = ctk.CTkFrame(main_frame, fg_color="transparent")
        header_bar.pack(fill="x", padx=24, pady=(16, 0))

        ctk.CTkLabel(
            header_bar, text="看板总览",
            font=ctk.CTkFont(family="Microsoft YaHei", size=20, weight="bold"),
            text_color=self.C["text"],
        ).pack(side="left")

        self.time_label = ctk.CTkLabel(
            header_bar, text="",
            font=ctk.CTkFont(family="Microsoft YaHei", size=12),
            text_color=self.C["text_secondary"],
        )
        self.time_label.pack(side="right", padx=(0, 8))

        # ── 下方两列布局：左侧最新动态 + 右侧核心指标（顶部对齐）──
        bottom_row = ctk.CTkFrame(main_frame, fg_color="transparent")
        bottom_row.pack(fill="both", expand=True, padx=24, pady=(16, 16))

        # 右侧列：核心指标（2×2网格，每个圆角矩形）
        right_col = ctk.CTkFrame(bottom_row, fg_color="transparent")
        right_col.pack(side="right", fill="both", expand=True, padx=(16, 0))

        ctk.CTkLabel(
            right_col, text="核心指标",
            font=ctk.CTkFont(family="Microsoft YaHei", size=17, weight="bold"),
            text_color=self.C["text"],
        ).pack(anchor="w", padx=0, pady=(0, 8))

        # ── 2×2 网格容器 ──
        kpi_grid = ctk.CTkFrame(right_col, fg_color="transparent")
        kpi_grid.pack(fill="both", expand=True)

        # ── 从 settings 读取用户选择的 KPI 卡片 ──
        _settings_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "settings.txt")
        # 尝试从标准数据目录读取
        _data_dir = os.path.join(os.path.expanduser("~"), "采购管理系统数据")
        _std_settings_path = os.path.join(_data_dir, "settings.txt")
        _config = configparser.ConfigParser()
        # 先读标准目录的设置（兼容 key=value 格式和 INI 格式）
        if os.path.exists(_std_settings_path):
            try:
                _config.read(_std_settings_path, encoding="utf-8")
            except (configparser.MissingSectionHeaderError, Exception):
                pass  # 文件是 key=value 格式，非 INI 格式，忽略
        elif os.path.exists(_settings_path):
            try:
                _config.read(_settings_path, encoding="utf-8")
            except (configparser.MissingSectionHeaderError, Exception):
                pass
        _default_kpis = "packaging,collection,purchase,travel"
        try:
            _selected_kpis = _config.get("General", "kpi_cards") if "General" in _config else _default_kpis
        except Exception:
            _selected_kpis = _default_kpis
        # 也尝试从 key=value 格式读取
        if _selected_kpis == _default_kpis:
            for _try_path in [_std_settings_path, _settings_path]:
                if not os.path.exists(_try_path):
                    continue
                try:
                    with open(_try_path, "r", encoding="utf-8") as _f:
                        for _line in _f:
                            _line = _line.strip()
                            if _line.startswith("kpi_cards="):
                                _selected_kpis = _line.split("=", 1)[1].strip()
                                break
                except Exception:
                    pass
                if _selected_kpis != _default_kpis:
                    break
        self._selected_kpi_keys = [k.strip() for k in _selected_kpis.split(",") if k.strip()]

        # ── 动态构建选中的 KPI 卡片（2列网格）──
        self._kpi_grid = kpi_grid  # 保存引用，供刷新时重建
        row = None
        for i, kpi_key in enumerate(self._selected_kpi_keys):
            if kpi_key not in AVAILABLE_KPI_CARDS:
                continue
            if i % 2 == 0:
                row = ctk.CTkFrame(kpi_grid, fg_color="transparent")
                row.pack(fill="x", pady=(0, 6))
            kpi_cfg = AVAILABLE_KPI_CARDS[kpi_key]
            self._make_kpi_card(row, title=kpi_cfg["title"],
                keys=kpi_cfg["keys"], color=kpi_cfg["color"], page_key=kpi_cfg["page_key"])

        # 左侧列：最新动态（不固定高度，与右侧核心指标顶部对齐）
        left_col = ctk.CTkFrame(bottom_row, fg_color=self.C["card"],
            corner_radius=self.C["radius_card"],
            border_width=1, border_color=self.C["border"])
        left_col.pack(side="left", fill="both", expand=True)

        # 标题行：最新动态 + 刷新按钮
        title_row = ctk.CTkFrame(left_col, fg_color="transparent")
        title_row.pack(fill="x", padx=16, pady=(12, 6))

        ctk.CTkLabel(
            title_row, text="最新动态",
            font=ctk.CTkFont(size=17, weight="bold"),
            text_color=self.C["text"],
        ).pack(side="left")

        # ── 刷新胶囊按钮 ──
        refresh_btn = ctk.CTkButton(
            title_row, text="🔄 刷新", width=60, height=26,
            font=ctk.CTkFont(size=11),
            fg_color="transparent",
            text_color=self.C["text_secondary"],
            hover_color="#E8D5C4",
            corner_radius=20, border_width=1,
            border_color="#E8D5C4",
            command=self._manual_refresh,
        )
        refresh_btn.pack(side="right", padx=(4, 0))

        # ── 类型筛选胶囊按钮（无滚动条）──
        filter_frame = ctk.CTkFrame(left_col, fg_color="transparent", height=36)
        filter_frame.pack(fill="x", padx=8, pady=(0, 4))
        filter_frame.pack_propagate(False)
        self._filter_frame = filter_frame

        self._activity_type_filter = "all"  # 当前筛选类型（默认值，显示全部）
        filter_types = [
            ("全部", "all"),
            ("报价单", "quotation"),
            ("三方比价", "compare"),
            ("物料下单", "packaging"),
            ("合同", "contract"),
            ("催款", "collection"),
            ("垫付", "purchase"),
            ("出差", "travel"),
            ("备忘录", "memo"),
            ("到货提醒", "arrival"),
        ]
        self._filter_buttons = {}
        for label, key in filter_types:
            btn = ctk.CTkButton(
                filter_frame, text=label, width=64, height=26,
                font=ctk.CTkFont(size=11),
                fg_color="#E8D5C4" if key == "all" else "transparent",
                text_color="#8B5E3C" if key == "all" else self.C["text_secondary"],
                hover_color="#E8D5C4",
                corner_radius=20, border_width=1,
                border_color="#E8D5C4",
                command=lambda k=key, l=label: self._on_filter_click(k, l),
            )
            btn.pack(side="left", padx=(0, 4))
            self._filter_buttons[key] = btn

        # ── 最新动态列表（使用 WheelScrollFrame 隐藏滚动条）──
        self.activity_frame = WheelScrollFrame(
            left_col, fg_color=self.C["card"],
        )
        self.activity_frame.pack(fill="both", expand=True, padx=8, pady=(0, 8))

    # ── KPI 卡片（支持网格布局：同一行内并排）────
    def _make_kpi_card(self, parent, title, keys, color, page_key):
        """构建 KPI 卡片（圆角矩形，支持同行并排）"""
        card = ctk.CTkFrame(
            parent, fg_color=color, corner_radius=14, height=100,
        )
        card.pack(side="left", expand=True, fill="both", padx=(0, 6))
        card.pack_propagate(False)

        card._orig_fg = color
        card.bind("<Enter>", lambda e, c=card: self._on_card_hover_enter(c))
        card.bind("<Leave>", lambda e, c=card: self._on_card_hover_leave(c))

        # 整卡可点击
        btn = ctk.CTkButton(
            card, text="", fg_color="transparent",
            hover=False, corner_radius=20,
            command=lambda k=page_key: self._on_card_click(k),
        )
        btn.place(x=0, y=0, relwidth=1, relheight=1)
        btn.bind("<Enter>", lambda e, c=card: self._on_card_hover_enter(c))
        btn.bind("<Leave>", lambda e, c=card: self._on_card_hover_leave(c))

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=14, pady=(12, 8))

        # 标题行
        title_row = ctk.CTkFrame(inner, fg_color="transparent")
        title_row.pack(fill="x")

        ctk.CTkLabel(
            title_row, text=title,
            font=ctk.CTkFont(family="Microsoft YaHei", size=13, weight="bold"),
            text_color="#FFFFFF",
        ).pack(side="left")

        # 迷你趋势图（右上角）
        sparkline_key = f"{page_key}_sparkline"
        sparkline_label = ctk.CTkLabel(title_row, text="", width=60, height=24)
        sparkline_label.pack(side="right", padx=(2, 0))
        self._sparkline_labels[sparkline_key] = sparkline_label

        # 趋势标签
        trend_label = ctk.CTkLabel(
            title_row, text="",
            font=ctk.CTkFont(family="Microsoft YaHei", size=12, weight="bold"),
            text_color="#E8E8E8",
        )
        trend_label.pack(side="right", padx=(2, 0))
        self._trend_labels[title] = trend_label

        # 值区域
        if len(keys) == 1:
            _, key = keys[0]
            val_label = ctk.CTkLabel(
                inner, text="—",
                font=ctk.CTkFont(family="Microsoft YaHei", size=29, weight="bold"),
                text_color="#FFFFFF",
            )
            val_label.pack(anchor="w", pady=(4, 0))
            unit_label = ctk.CTkLabel(
                inner, text="",
                font=ctk.CTkFont(family="Microsoft YaHei", size=12),
                text_color="#F0E8E0",
            )
            unit_label.pack(anchor="w", pady=(2, 0))
            self._value_labels[key] = val_label
            self._value_labels[f"{key}_unit"] = unit_label
        else:
            vals_row = ctk.CTkFrame(inner, fg_color="transparent")
            vals_row.pack(fill="x", pady=(6, 0))
            for sub, key in keys:
                col_frame = ctk.CTkFrame(vals_row, fg_color="transparent")
                col_frame.pack(side="left", fill="x", expand=True)
                val_label = ctk.CTkLabel(
                    col_frame, text="—",
                    font=ctk.CTkFont(family="Microsoft YaHei", size=24, weight="bold"),
                    text_color="#FFFFFF",
                )
                val_label.pack(anchor="w")
                ctk.CTkLabel(
                    col_frame, text=sub,
                    font=ctk.CTkFont(family="Microsoft YaHei", size=12),
                    text_color="#F0E8E0",
                ).pack(anchor="w", pady=(1, 0))
                self._value_labels[key] = val_label

        # 底部进度条
        progress_key = f"{page_key}_progress"
        progress_frame = ctk.CTkFrame(inner, fg_color="transparent")
        progress_frame.pack(fill="x", pady=(4, 0))
        progress_bar = ctk.CTkProgressBar(
            progress_frame, height=3,
            fg_color=color, progress_color="#FFFFFF", corner_radius=2,
        )
        progress_bar.pack(fill="x")
        progress_bar.set(0)
        self._progress_bars[progress_key] = progress_bar
        self._card_refs[page_key] = card

    def _on_card_hover_enter(self, card):
        """卡片悬停进入：增加边框高亮效果"""
        try:
            card.configure(
                border_width=2,
                border_color="#FFFFFF",   # 纯白边框，不使用 rgba
                fg_color=self._lighten_color(card._orig_fg, 0.08),
            )
        except Exception:
            pass

    def _on_card_hover_leave(self, card):
        """卡片悬停离开：恢复原状"""
        try:
            card.configure(
                border_width=0,
                border_color="",
                fg_color=card._orig_fg,
            )
        except Exception:
            pass

    def _lighten_color(self, hex_color, factor=0.08):
        """将颜色变亮（factor: 0-1）"""
        try:
            h = hex_color.lstrip('#')
            r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
            r = min(255, int(r + (255 - r) * factor))
            g = min(255, int(g + (255 - g) * factor))
            b = min(255, int(b + (255 - b) * factor))
            return f"#{r:02X}{g:02X}{b:02X}"
        except Exception:
            return hex_color

    # ── 迷你趋势图生成 ──────────────────────────────────
    def _generate_sparkline(self, values, width=60, height=24):
        """用 PIL 绘制迷你趋势图(Sparkline)，返回 CTkImage"""
        try:
            from PIL import Image, ImageDraw
            from customtkinter import CTkImage

            img = Image.new("RGBA", (width, height), (255, 255, 255, 0))
            draw = ImageDraw.Draw(img)

            if not values or len(values) < 2:
                draw.line([(0, height//2), (width, height//2)], fill="#CCCCCC", width=1)
            else:
                min_v = min(values) if any(v > 0 for v in values) else 0
                max_v = max(values) if values else 1
                if max_v == min_v or max_v == 0:
                    y = height // 2
                    draw.line([(0, y), (width, y)], fill="#8FA882", width=1)
                else:
                    pts = []
                    for i, v in enumerate(values):
                        x = int(i * width / (len(values) - 1))
                        y = int(height - (v - min_v) / (max_v - min_v) * (height - 4) - 2)
                        pts.append((x, y))
                    draw.line(pts, fill="#8FA882", width=1)

            ctk_img = CTkImage(light_image=img, size=(width, height))
            return ctk_img
        except Exception as e:
            print(f"Sparkline 生成失败: {e}")
            return None

    def _update_sparkline(self, key, values):
        """更新指定卡片的迷你趋势图"""
        sparkline_key = f"{key}_sparkline"
        label = self._sparkline_labels.get(sparkline_key)
        if label is None:
            return

        ctk_img = self._generate_sparkline(values)
        if ctk_img:
            label.configure(image=ctk_img, text="")
            label._ctk_image = ctk_img

    def _update_progress_bar(self, key, rate):
        """更新指定卡片的底部进度条（rate: 0.0-1.0）"""
        progress_key = f"{key}_progress"
        bar = self._progress_bars.get(progress_key)
        if bar is not None:
            bar.set(max(0.0, min(1.0, rate)))

    # ──────────────────────────────────────────────
    # 数据加载
    # ──────────────────────────────────────────────
    def _load_data(self):
        """加载所有 KPI 数据（含6个月趋势 + 完成率）"""
        try:
            now = datetime.now().strftime("%Y-%m-%d %H:%M")
            # 更新时间标签（如果存在）
            if hasattr(self, 'time_label'):
                self.time_label.configure(text=f"更新时间：{now}")

            # 物料下单
            packaging_active = self.db.get_packagings(archived=0)
            packaging_done = self.db.get_packagings(archived=1)
            active_cnt = len(packaging_active)
            done_cnt = len(packaging_done)
            total_cnt = active_cnt + done_cnt
            self._set_value("packaging_active", str(active_cnt))
            self._set_value("packaging_done", str(done_cnt))
            self._update_trend("物料下单", active_cnt, "packaging_orders", "created_at")
            pkg_trend = self._fetch_6month_counts("packaging_orders", "created_at")
            self._update_sparkline("packaging", pkg_trend)
            completion_rate = done_cnt / total_cnt if total_cnt > 0 else 0
            self._update_progress_bar("packaging", completion_rate)

            # 催款记录
            collections = self.db.get_collections()
            total_cnt = len(collections)
            unpaid_cnt = len([c for c in collections if c.get("status") not in ("已结清", "已完成")])
            self._set_value("collection_total", str(total_cnt))
            self._set_value("collection_total_unit", "条记录")
            self._update_trend("催款记录", total_cnt, "collection_reminders", "created_at")
            coll_trend = self._fetch_6month_counts("collection_reminders", "created_at")
            self._update_sparkline("collection", coll_trend)
            clear_rate = (total_cnt - unpaid_cnt) / total_cnt if total_cnt > 0 else 0
            self._update_progress_bar("collection", clear_rate)

            # 采购垫付
            purchases = self.db.get_purchases(archived=0)
            total_cnt = len(purchases)
            reimbursed_cnt = sum(1 for p in purchases if p.get("reimbursement_status") == "已报销")
            purchase_pending_amt = sum(
                p.get("total", 0) for p in purchases
                if p.get("reimbursement_status") != "已报销"
            )
            self._set_value("purchase_total", str(total_cnt))
            self._set_value("purchase_pending", f"¥{purchase_pending_amt:.0f}")
            self._update_trend("采购垫付", total_cnt, "purchase", "created_at")
            pur_trend = self._fetch_6month_counts("purchase", "created_at")
            self._update_sparkline("purchase", pur_trend)
            reimburse_rate = reimbursed_cnt / total_cnt if total_cnt > 0 else 0
            self._update_progress_bar("purchase", reimburse_rate)

            # 差旅报销
            travels = self.db.get_travels(archived=0)
            total_cnt = len(travels)
            reimbursed_cnt = sum(1 for t in travels if t.get("reimbursement_status") == "已报销")
            travel_pending_amt = sum(
                t.get("total", 0) for t in travels
                if t.get("reimbursement_status") != "已报销"
            )
            self._set_value("travel_total", str(total_cnt))
            self._set_value("travel_pending", f"¥{travel_pending_amt:.0f}")
            self._update_trend("差旅报销", total_cnt, "travel", "created_at")
            trav_trend = self._fetch_6month_counts("travel", "created_at")
            self._update_sparkline("travel", trav_trend)
            reimburse_rate = reimbursed_cnt / total_cnt if total_cnt > 0 else 0
            self._update_progress_bar("travel", reimburse_rate)

            # 待签合同数（新增）
            try:
                cur = self.db.conn.cursor()
                cur.execute("SELECT COUNT(*) FROM packaging_orders WHERE contract_status NOT IN ('已签', '已完成', '') OR contract_status IS NULL")
                pending_contract_cnt = cur.fetchone()[0]
                self._set_value("contract_pending", str(pending_contract_cnt))
                self._set_value("contract_pending_unit", "个合同")
            except Exception:
                self._set_value("contract_pending", "—")

            # 本月比价次数（新增）
            try:
                today = date.today()
                month_start = today.replace(day=1).strftime("%Y-%m-%d")
                month_end = f"{today.strftime('%Y-%m-%d')} 23:59:59"
                cur = self.db.conn.cursor()
                cur.execute("SELECT COUNT(*) FROM third_party_records WHERE created_at >= ? AND created_at <= ?", (month_start, month_end))
                compare_cnt = cur.fetchone()[0]
                self._set_value("compare_month", str(compare_cnt))
                self._set_value("compare_month_unit", "次比价")
            except Exception:
                self._set_value("compare_month", "—")

            # 最新动态
            self._update_activity_feed()

        except Exception as e:
            print(f"加载看板数据失败: {e}")
            import traceback
            traceback.print_exc()

    def _update_trend(self, card_title, current_val, table_name, date_field):
        """计算环比趋势并更新趋势标签"""
        try:
            # 查询上月同期数据量
            import sqlite3
            conn = self.db.conn
            cur = conn.cursor()

            # 获取本月和上月的范围
            today = date.today()
            this_month_start = today.replace(day=1).strftime("%Y-%m-01")
            # 上月最后一天
            if today.month == 1:
                last_month_end = today.replace(year=today.year-1, month=12, day=31)
            else:
                last_month_end = today.replace(month=today.month-1, day=1)
                # 上月最后一天
                import calendar
                last_day = calendar.monthrange(last_month_end.year, last_month_end.month)[1]
                last_month_end = last_month_end.replace(day=last_day)
            last_month_start = last_month_end.replace(day=1).strftime("%Y-%m-01")

            # 表名映射
            table_map = {
                "packaging_orders": "packaging_orders",
                "collection_reminders": "collection_reminders",
                "purchase": "purchase",
                "travel": "travel",
                "memos": "memos",
            }
            tbl = table_map.get(table_name, table_name)

            # 查上月数据量
            try:
                cur.execute(
                    f"SELECT COUNT(*) FROM {tbl} WHERE created_at >= ? AND created_at <= ?",
                    (last_month_start, last_month_end.strftime("%Y-%m-%d") + " 23:59:59")
                )
                last_month_count = cur.fetchone()[0]
            except Exception:
                last_month_count = 0

            # 计算趋势
            trend_lbl = self._trend_labels.get(card_title)
            if trend_lbl is None:
                return

            if last_month_count == 0:
                if current_val > 0:
                    trend_lbl.configure(text="● 新增", text_color=TREND_UP_COLOR)
                else:
                    trend_lbl.configure(text="● —", text_color=TREND_NEUTRAL)
            else:
                pct = (current_val - last_month_count) / last_month_count * 100
                if pct > 0:
                    trend_lbl.configure(
                        text=f"↑ {pct:.0f}%",
                        text_color=TREND_UP_COLOR,
                    )
                elif pct < 0:
                    trend_lbl.configure(
                        text=f"↓ {abs(pct):.0f}%",
                        text_color=TREND_DOWN_COLOR,
                    )
                else:
                    trend_lbl.configure(text="→ 持平", text_color=TREND_NEUTRAL)

        except Exception as e:
            print(f"趋势计算失败({card_title}): {e}")

    # ── 6个月趋势数据获取 ──────────────────────────────
    def _fetch_6month_counts(self, table_name, date_field):
        """获取近6个月的数据量列表（用于迷你趋势图）"""
        try:
            import calendar
            from datetime import date as date_cls
            today = date_cls.today()
            counts = []
            for i in range(5, -1, -1):
                y = today.year
                m = today.month - i
                while m <= 0:
                    y -= 1
                    m += 12
                month_start = f"{y}-{m:02d}-01"
                last_day = calendar.monthrange(y, m)[1]
                month_end = f"{y}-{m:02d}-{last_day:02d}"
                cur = self.db.conn.cursor()
                cur.execute(
                    f"SELECT COUNT(*) FROM {table_name} WHERE {date_field} >= ? AND {date_field} <= ?",
                    (month_start, month_end + " 23:59:59")
                )
                count = cur.fetchone()[0]
                counts.append(count)
            return counts
        except Exception as e:
            print(f"6个月趋势数据获取失败({table_name}): {e}")
            return []

    def _on_filter_click(self, key, label):
        """点击类型筛选胶囊按钮"""
        self._activity_type_filter = key
        # 更新按钮样式
        for k, btn in self._filter_buttons.items():
            is_active = (k == key)
            btn.configure(
                fg_color="#E8D5C4" if is_active else "transparent",
                text_color="#8B5E3C" if is_active else self.C["text_secondary"],
            )
        # 重新加载动态
        self._update_activity_feed()

    def _update_activity_feed(self):
        """更新最近活动动态流（30条，含报价/比价/下单/合同/催款/垫付/出差）"""
        # 清空旧内容（只销毁 _inner 内的部件，保留 canvas/scrollbar）
        for widget in self.activity_frame._inner.winfo_children():
            widget.destroy()

        try:
            activities = []

            # 从各表获取最近记录（按 created_at 倒序，合并后取前30条）
            import sqlite3

            # 1️⃣ 报价单生成
            try:
                cur = self.db.conn.cursor()
                cur.execute(
                    "SELECT product_names, supplier_name, created_at FROM quotation_records "
                    "WHERE created_at IS NOT NULL ORDER BY created_at DESC LIMIT 30"
                )
                for row in cur.fetchall():
                    names, supplier, ts = row
                    name_str = names[:30] + "..." if names and len(names) > 30 else (names or '未命名')
                    sup_str = f"→{supplier}" if supplier else ""
                    activities.append((ts, f"📋 生成报价单：{name_str} {sup_str}", "quotation"))
            except Exception:
                pass

            # 2️⃣ 三方比价
            try:
                cur = self.db.conn.cursor()
                cur.execute(
                    "SELECT product_name, final_supplier, created_at FROM third_party_records "
                    "WHERE created_at IS NOT NULL ORDER BY created_at DESC LIMIT 30"
                )
                for row in cur.fetchall():
                    prod, supplier, ts = row
                    prod_str = prod[:25] + "..." if prod and len(prod) > 25 else (prod or '未命名')
                    sup_str = f"→{supplier}" if supplier else ""
                    activities.append((ts, f"⚖️ 三方比价：{prod_str} {sup_str}", "compare"))
            except Exception:
                pass

            # 3️⃣ 物料下单
            try:
                cur = self.db.conn.cursor()
                cur.execute(
                    "SELECT material_name, contract_status, created_at FROM packaging_orders "
                    "WHERE created_at IS NOT NULL ORDER BY created_at DESC LIMIT 30"
                )
                for row in cur.fetchall():
                    name, status, ts = row
                    name_str = name[:20] + "..." if name and len(name) > 20 else (name or '未命名')
                    activities.append((ts, f"📦 新增物料下单：{name_str}", "packaging"))
                    # 如果有合同状态变更也记录
                    if status and status not in ("", None):
                        activities.append((ts, f"📝 合同状态变更为：{status}", "contract"))
            except Exception:
                pass

            # 4️⃣ 催款记录
            try:
                cur = self.db.conn.cursor()
                cur.execute(
                    "SELECT supplier_name, amount_due, status, created_at FROM collection_reminders "
                    "WHERE created_at IS NOT NULL ORDER BY created_at DESC LIMIT 30"
                )
                for row in cur.fetchall():
                    name, amount, status, ts = row
                    name_str = name[:18] + "..." if name and len(name) > 18 else (name or '未知供应商')
                    amt_str = f" ¥{amount:.0f}" if amount else ""
                    activities.append((ts, f"💰 新增催款记录：{name_str}{amt_str}", "collection"))
            except Exception:
                pass

            # 5️⃣ 采购垫付
            try:
                cur = self.db.conn.cursor()
                cur.execute(
                    "SELECT project, handler, created_at FROM purchase "
                    "WHERE created_at IS NOT NULL ORDER BY created_at DESC LIMIT 30"
                )
                for row in cur.fetchall():
                    project, handler, ts = row
                    proj_str = project or '默认项目'
                    handler_str = f"({handler})" if handler else ""
                    activities.append((ts, f"💳 采购垫付：{proj_str} {handler_str}", "purchase"))
            except Exception:
                pass

            # 6️⃣ 出差新增记录
            try:
                cur = self.db.conn.cursor()
                cur.execute(
                    "SELECT reason, destination, created_at FROM travel "
                    "WHERE created_at IS NOT NULL ORDER BY created_at DESC LIMIT 30"
                )
                for row in cur.fetchall():
                    reason, dest, ts = row
                    reason_str = reason[:15] + "..." if reason and len(reason) > 15 else (reason or '出差')
                    dest_str = dest or ''
                    activities.append((ts, f"✈️ 出差记录：{reason_str} →{dest_str}", "travel"))
            except Exception:
                pass

            # 7️⃣ 备忘录
            try:
                cur = self.db.conn.cursor()
                cur.execute(
                    "SELECT content, created_at FROM memos "
                    "WHERE created_at IS NOT NULL ORDER BY created_at DESC LIMIT 30"
                )
                for row in cur.fetchall():
                    content, ts = row
                    content_str = content[:25] + "..." if content and len(content) > 25 else (content or '无标题')
                    activities.append((ts, f"📝 新增备忘录：{content_str}", "memo"))
            except Exception:
                pass

            # 8️⃣ 到货提醒（预计到达日为今天或明天）
            try:
                cur = self.db.conn.cursor()
                today_str = date.today().strftime("%Y-%m-%d")
                tomorrow = date.today() + timedelta(days=1)
                tomorrow_str = tomorrow.strftime("%Y-%m-%d")
                cur.execute(
                    "SELECT id, material_name, expected_arrival, order_factory "
                    "FROM packaging_orders "
                    "WHERE expected_arrival IN (?, ?) "
                    "AND archived = 0 "
                    "ORDER BY expected_arrival ASC "
                    "LIMIT 30",
                    (today_str, tomorrow_str)
                )
                for row in cur.fetchall():
                    oid, name, arr_date, factory = row
                    name_str = name[:20] + "..." if name and len(name) > 20 else (name or '未命名')
                    factory_str = f"（{factory}）" if factory else ""
                    is_today = (arr_date == today_str)
                    prefix = "🔔 今天到货" if is_today else "⏰ 明天到货"
                    activities.append((arr_date, f"{prefix}：{name_str} {factory_str}", "arrival"))
            except Exception:
                pass

            # ── 按筛选条件过滤 ──
            if self._activity_type_filter and self._activity_type_filter != "all":
                activities = [
                    (ts, desc, mod_key) for ts, desc, mod_key in activities
                    if mod_key == self._activity_type_filter
                ]

            # 按时间倒序排列，取前30条
            activities.sort(key=lambda x: x[0], reverse=True)
            recent = activities[:30]

            if not recent:
                ctk.CTkLabel(
                    self.activity_frame._inner, text="暂无最新动态",
                    font=ctk.CTkFont(size=13),
                    text_color=self.C["text_secondary"],
                ).pack(anchor="w", pady=8)
                return

            for ts, desc, mod_key in recent:
                item = ctk.CTkFrame(self.activity_frame._inner, fg_color="transparent")
                item.pack(fill="x", pady=2)

                # 时间
                try:
                    dt = datetime.strptime(ts[:16], "%Y-%m-%d %H:%M")
                    time_str = dt.strftime("%m-%d %H:%M")
                except Exception:
                    time_str = str(ts)[:16] if ts else "未知时间"

                # 模块颜色圆点
                dot_color = MODULE_COLORS.get(mod_key, "#B0A8A0")
                ctk.CTkLabel(
                    item, text="●", width=12,
                    font=ctk.CTkFont(size=10),
                    text_color=dot_color,
                    anchor="center",
                ).pack(side="left", padx=(0, 2))

                ctk.CTkLabel(
                    item, text=time_str, width=65,
                    font=ctk.CTkFont(size=11, weight="bold"),
                    text_color=self.C["text_secondary"],
                    anchor="w",
                ).pack(side="left", padx=(0, 6))

                ctk.CTkLabel(
                    item, text=desc,
                    font=ctk.CTkFont(size=11),
                    text_color=self.C["text"],
                    anchor="w",
                ).pack(side="left", fill="x", expand=True)

        except Exception as e:
            print(f"活动流加载失败: {e}")

    # ──────────────────────────────────────────────
    # 交互
    # ──────────────────────────────────────────────
    def _on_card_click(self, page_key):
        """卡片点击 → 切换页面"""
        if self.switch_page:
            self.switch_page(page_key)

    # ──────────────────────────────────────────────
    # 工具方法
    # ──────────────────────────────────────────────
    def _set_value(self, key, value):
        if key in self._value_labels:
            self._value_labels[key].configure(text=value)

    def _manual_refresh(self):
        """手动刷新按钮回调"""
        self._load_data()

    def _auto_refresh(self):
        """每5分钟自动刷新"""
        self._load_data()
        self.after(300000, self._auto_refresh)

    def _rebuild_kpi_cards(self):
        """根据 settings.txt 中的 kpi_cards 配置重建 KPI 卡片网格"""
        import os
        import configparser

        # 重新读取设置
        _settings_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "settings.txt")
        _data_dir = os.path.join(os.path.expanduser("~"), "采购管理系统数据")
        _std_settings_path = os.path.join(_data_dir, "settings.txt")
        _config = configparser.ConfigParser()
        if os.path.exists(_std_settings_path):
            try:
                _config.read(_std_settings_path, encoding="utf-8")
            except Exception:
                pass
        elif os.path.exists(_settings_path):
            try:
                _config.read(_settings_path, encoding="utf-8")
            except Exception:
                pass

        _default_kpis = "packaging,collection,purchase,travel"
        try:
            _selected_kpis = _config.get("General", "kpi_cards") if "General" in _config else _default_kpis
        except Exception:
            _selected_kpis = _default_kpis

        if _selected_kpis == _default_kpis:
            for _try_path in [_std_settings_path, _settings_path]:
                if not os.path.exists(_try_path):
                    continue
                try:
                    with open(_try_path, "r", encoding="utf-8") as _f:
                        for _line in _f:
                            _line = _line.strip()
                            if _line.startswith("kpi_cards="):
                                _selected_kpis = _line.split("=", 1)[1].strip()
                                break
                except Exception:
                    pass
                if _selected_kpis != _default_kpis:
                    break

        new_keys = [k.strip() for k in _selected_kpis.split(",") if k.strip()]

        # 对比是否发生变化
        if new_keys == self._selected_kpi_keys:
            return

        # 更新并重建
        self._selected_kpi_keys = new_keys

        # 清空旧引用
        self._value_labels = {}
        self._trend_labels = {}
        self._sparkline_labels = {}
        self._progress_bars = {}
        self._card_refs = {}

        # 销毁旧网格中的所有卡片
        if hasattr(self, '_kpi_grid') and self._kpi_grid.winfo_exists():
            for child in self._kpi_grid.winfo_children():
                child.destroy()

        # 重建卡片
        row = None
        for i, kpi_key in enumerate(self._selected_kpi_keys):
            if kpi_key not in AVAILABLE_KPI_CARDS:
                continue
            if i % 2 == 0:
                row = ctk.CTkFrame(self._kpi_grid, fg_color="transparent")
                row.pack(fill="x", pady=(0, 6))
            kpi_cfg = AVAILABLE_KPI_CARDS[kpi_key]
            self._make_kpi_card(row, title=kpi_cfg["title"],
                keys=kpi_cfg["keys"], color=kpi_cfg["color"], page_key=kpi_cfg["page_key"])

    def refresh(self):
        self._rebuild_kpi_cards()
        self._load_data()
