#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""看板页面 V1.9.3 - 优化版（KPI趋势卡 + 点击跳转 + 待办聚合 + 动态活动流）"""

import customtkinter as ctk
import tkinter as tk
from datetime import datetime, date
import calendar

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
}

# 趋势箭头配色
TREND_UP_COLOR   = "#8FA882"   # 绿色 - 上升
TREND_DOWN_COLOR = "#B56A6A"   # 红色 - 下降
TREND_NEUTRAL    = "#B0A8A0"   # 灰色 - 持平


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
        self._load_data()
        # 每5分钟自动刷新
        self._auto_refresh()

    # ──────────────────────────────────────────────
    # UI 构建
    # ──────────────────────────────────────────────
    def _build_ui(self):
        # 主滚动容器
        scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True)
        self._scroll_frame = scroll_frame

        # ── 待办聚合条 ─────────────────────────────────
        self._build_todo_bar(scroll_frame)

        # ── 下方两列布局：左侧最新活动 + 右侧核心指标 ──
        bottom_row = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        bottom_row.pack(fill="both", expand=True, padx=24, pady=(0, 16))

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

        # 第一行
        row1 = ctk.CTkFrame(kpi_grid, fg_color="transparent")
        row1.pack(fill="x", pady=(0, 6))
        self._make_kpi_card(row1, title="物料下单",
            keys=[("处理中", "packaging_active"), ("已完成", "packaging_done")],
            color=MODULE_COLORS["packaging"], page_key="packaging")
        self._make_kpi_card(row1, title="催款记录",
            keys=[(None, "collection_total")],
            color=MODULE_COLORS["collection"], page_key="collection")

        # 第二行
        row2 = ctk.CTkFrame(kpi_grid, fg_color="transparent")
        row2.pack(fill="x", pady=(0, 6))
        self._make_kpi_card(row2, title="采购垫付",
            keys=[("总笔数", "purchase_total"), ("待报销", "purchase_pending")],
            color=MODULE_COLORS["purchase"], page_key="purchase")
        self._make_kpi_card(row2, title="差旅报销",
            keys=[("行程数", "travel_total"), ("待报销", "travel_pending")],
            color=MODULE_COLORS["travel"], page_key="travel")

        # 左侧列：最新活动（高度扩大，显示30条）
        left_col = ctk.CTkFrame(bottom_row, fg_color=self.C["card"],
            corner_radius=self.C["radius_card"],
            border_width=1, border_color=self.C["border"],
            width=560)
        left_col.pack(side="left", fill="both")
        left_col.pack_propagate(False)

        ctk.CTkLabel(
            left_col, text="最新活动",
            font=ctk.CTkFont(size=17, weight="bold"),
            text_color=self.C["text"],
        ).pack(anchor="w", padx=16, pady=(12, 6))

        self.activity_frame = ctk.CTkScrollableFrame(
            left_col, fg_color="transparent",
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
            hover=False, corner_radius=18,
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

    # ── 待办聚合条 ──────────────────────────────────
    def _build_todo_bar(self, parent):
        """构建待办聚合条（P1 优化：可折叠 + 胶囊按钮）"""
        # 主容器
        self.todo_bar = ctk.CTkFrame(
            parent,
            fg_color="#FFF8F0",
            corner_radius=self.C["radius_card"],
            border_width=1,
            border_color="#C9A96E",
        )
        self.todo_bar.pack(fill="x", padx=24, pady=(0, 12))

        # 可点击的横幅（显示待办数量）
        self.todo_banner = ctk.CTkFrame(
            self.todo_bar,
            fg_color="transparent",
            cursor="hand2",
        )
        self.todo_banner.pack(fill="x", padx=16, pady=(10, 10))
        self.todo_banner.bind("<Button-1>", lambda e: self._toggle_todo_detail())

        # 左侧图标 + 文本
        banner_inner = ctk.CTkFrame(self.todo_banner, fg_color="transparent")
        banner_inner.pack(side="left", fill="x", expand=True)

        self.todo_icon_label = ctk.CTkLabel(
            banner_inner, text="📋", font=ctk.CTkFont(size=17),
        )
        self.todo_icon_label.pack(side="left", padx=(0, 8))

        self.todo_banner_label = ctk.CTkLabel(
            banner_inner,
            text="正在加载待办事项...",
            font=ctk.CTkFont(family="Microsoft YaHei", size=13, weight="bold"),
            text_color=self.C["text"],
        )
        self.todo_banner_label.pack(side="left")

        # 右侧展开/折叠指示器
        self.todo_arrow_label = ctk.CTkLabel(
            self.todo_banner, text="▼", font=ctk.CTkFont(size=13),
            text_color=self.C["text_secondary"],
        )
        self.todo_arrow_label.pack(side="right")

        # 可折叠的详情区域（默认隐藏）
        self.todo_detail_frame = ctk.CTkFrame(
            self.todo_bar,
            fg_color="transparent",
        )
        # 不打包，默认隐藏

        # 待办列表容器
        self.todo_list_frame = ctk.CTkFrame(
            self.todo_detail_frame,
            fg_color="transparent",
        )
        self.todo_list_frame.pack(fill="x", padx=16, pady=(0, 10))

        # "前往处理"胶囊按钮
        self.todo_action_btn = ctk.CTkButton(
            self.todo_detail_frame,
            text="前往处理 ▶",
            width=120, height=32,
            fg_color=MODULE_COLORS["packaging"],
            hover_color="#A06050",
            font=ctk.CTkFont(family="Microsoft YaHei", size=13, weight="bold"),
            corner_radius=16,  # 胶囊形状
            command=self._on_todo_click,
        )
        self.todo_action_btn.pack(side="right", padx=16, pady=(0, 10))

        # 折叠状态
        self._todo_collapsed = True

    # ── 卡片悬停效果 ──────────────────────────────────
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

            # 待办聚合条（仅查询数据库，不生成KPI卡片）
            memos = self.db.get_memos(status="待处理")
            self._update_todo_bar(packaging_active, collections, memos)
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

    def _toggle_todo_detail(self):
        """切换待办详情的展开/折叠状态"""
        if self._todo_collapsed:
            # 展开
            self.todo_detail_frame.pack(fill="x", padx=0, pady=(0, 0), after=self.todo_banner)
            self.todo_arrow_label.configure(text="▲")
            self._todo_collapsed = False
        else:
            # 折叠
            self.todo_detail_frame.pack_forget()
            self.todo_arrow_label.configure(text="▼")
            self._todo_collapsed = True

    def _update_todo_bar(self, packaging_active, collections, memos):
        """更新待办聚合条（P1 优化：可折叠 + 紧急程度色块）"""
        todo_details = []

        # 物料下单：待签批
        pending_contracts = [r for r in packaging_active
                             if r.get("contract_status") in ("待签批", "", None)]
        if pending_contracts:
            todo_details.append({
                "icon": "📦",
                "text": f"{len(pending_contracts)} 份合同待签批",
                "priority": "red",  # 紧急
                "page": "packaging",
            })

        # 催款记录：未结清
        unpaid = [c for c in collections if c.get("status") not in ("已结清", "已完成")]
        if unpaid:
            todo_details.append({
                "icon": "💰",
                "text": f"{len(unpaid)} 笔催款待跟进",
                "priority": "orange",  # 中等
                "page": "collection",
            })

        # 备忘录：待处理
        if len(memos) > 0:
            todo_details.append({
                "icon": "📝",
                "text": f"{len(memos)} 条备忘录待处理",
                "priority": "blue",  # 一般
                "page": "memo",
            })

        # 更新横幅文本
        if todo_details:
            todo_count = len(todo_details)
            self.todo_banner_label.configure(text=f"📋 你有 {todo_count} 项待办")
            self.todo_bar.configure(fg_color="#FFF4E6", border_color="#E4A36A")
        else:
            self.todo_banner_label.configure(text="✅ 所有事项已处理完毕")
            self.todo_bar.configure(fg_color="#F0F8F0", border_color="#C9A96E")

        # 更新详情列表
        self._update_todo_list(todo_details)

    def _update_activity_feed(self):
        """更新最近活动动态流（30条，含报价/比价/下单/合同/催款/垫付/出差）"""
        # 清空旧内容
        for widget in self.activity_frame.winfo_children():
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

            # 按时间倒序排列，取前30条
            activities.sort(key=lambda x: x[0], reverse=True)
            recent = activities[:30]

            if not recent:
                ctk.CTkLabel(
                    self.activity_frame, text="暂无最近活动",
                    font=ctk.CTkFont(size=13),
                    text_color=self.C["text_secondary"],
                ).pack(anchor="w", pady=8)
                return

            for ts, desc, mod_key in recent:
                item = ctk.CTkFrame(self.activity_frame, fg_color="transparent")
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

    def _update_todo_list(self, todo_details):
        """更新待办详情列表（带紧急程度色块）"""
        # 清空现有列表
        for widget in self.todo_list_frame.winfo_children():
            widget.destroy()

        # 优先级颜色映射
        priority_colors = {
            "red": "#D4917A",      # 紧急 - 红色
            "orange": "#E4A36A",   # 中等 - 橙色
            "blue": "#7BA5B5",     # 一般 - 蓝色
        }

        for todo in todo_details:
            # 待办项容器
            item_frame = ctk.CTkFrame(
                self.todo_list_frame,
                fg_color="transparent",
                corner_radius=4,
            )
            item_frame.pack(fill="x", pady=(2, 2))

            # 紧急程度色块（左侧竖条）
            priority_color = priority_colors.get(todo["priority"], "#7BA5B5")
            priority_bar = ctk.CTkFrame(
                item_frame,
                width=4, height=20,
                fg_color=priority_color,
                corner_radius=2,
            )
            priority_bar.pack(side="left", padx=(0, 8))

            # 待办文本
            text_label = ctk.CTkLabel(
                item_frame,
                text=f"{todo['icon']} {todo['text']}",
                font=ctk.CTkFont(family="Microsoft YaHei", size=13),
                text_color=self.C["text"],
                anchor="w",
            )
            text_label.pack(side="left", fill="x", expand=True)

            # 点击跳转到对应页面
            if self.switch_page:
                item_frame.bind("<Button-1>", lambda e, p=todo["page"]: self.switch_page(p))
                text_label.bind("<Button-1>", lambda e, p=todo["page"]: self.switch_page(p))
                item_frame.configure(cursor="hand2")
                text_label.configure(cursor="hand2")

    def _on_todo_click(self):
        """待办条点击 → 切换到第一个有待办的页面"""
        try:
            packaging_active = self.db.get_packagings(archived=0)
            pending = [r for r in packaging_active
                       if r.get("contract_status") in ("待签批", "", None)]
            if pending and self.switch_page:
                self.switch_page("packaging")
                return

            collections = self.db.get_collections()
            unpaid = [c for c in collections if c.get("status") not in ("已结清", "已完成")]
            if unpaid and self.switch_page:
                self.switch_page("collection")
                return

            memos = self.db.get_memos(status="待处理")
            if memos and self.switch_page:
                self.switch_page("memo")
        except Exception as e:
            print(f"待办跳转失败: {e}")

    # ──────────────────────────────────────────────
    # 工具方法
    # ──────────────────────────────────────────────
    def _set_value(self, key, value):
        if key in self._value_labels:
            self._value_labels[key].configure(text=value)

    def _auto_refresh(self):
        """每5分钟自动刷新"""
        self._load_data()
        self.after(300000, self._auto_refresh)

    def refresh(self):
        self._load_data()
