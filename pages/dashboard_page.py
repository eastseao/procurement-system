#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""看板页面 V1.9.3 - 优化版（KPI趋势卡 + 点击跳转 + 待办聚合 + 动态活动流）"""

import customtkinter as ctk
import tkinter as tk
from datetime import datetime, date
import json
import urllib.request
import threading

# 各模块莫兰迪色
MODULE_COLORS = {
    "packaging":  "#C1816D",   # 陶土色 - 物料下单
    "collection": "#8FA882",   # 鼠尾草绿 - 催款记录
    "purchase":   "#C9A96E",   # 麦色 - 采购垫付
    "travel":     "#B56A6A",   # 暗玫瑰 - 差旅报销
    "memo":       "#7BA5B5",   # 灰蓝 - 备忘录
}

# 趋势箭头配色
TREND_UP_COLOR   = "#8FA882"   # 绿色 - 上升
TREND_DOWN_COLOR = "#B56A6A"   # 红色 - 下降
TREND_NEUTRAL    = "#B0A8A0"   # 灰色 - 持平


class DashboardPage(ctk.CTkFrame):
    """看板主页面 - V1.9.3 优化版"""

    def __init__(self, parent, db, C, switch_page=None):
        super().__init__(parent, fg_color=C["bg"], corner_radius=0)
        self.db = db
        self.C = C
        self.switch_page = switch_page  # 页面切换回调
        self._value_labels = {}   # key -> label widget
        self._trend_labels = {}   # key -> trend label widget
        self._build_ui()
        self._load_data()
        self._fetch_weather()
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

        # ── 顶部横幅 ──────────────────────────────────
        banner = ctk.CTkFrame(
            scroll_frame, fg_color=self.C["primary"], corner_radius=16,
        )
        banner.pack(fill="x", padx=24, pady=(16, 12))

        banner_inner = ctk.CTkFrame(banner, fg_color="transparent")
        banner_inner.pack(fill="x", padx=28, pady=(22, 22))

        # 左侧：标题 + 副标题
        left_col = ctk.CTkFrame(banner_inner, fg_color="transparent")
        left_col.pack(side="left", fill="y")

        ctk.CTkLabel(
            left_col,
            text="看板",
            font=ctk.CTkFont(family="Microsoft YaHei", size=26, weight="bold"),
            text_color="white",
        ).pack(anchor="w")

        ctk.CTkLabel(
            left_col,
            text="采购管理数据总览",
            font=ctk.CTkFont(family="Microsoft YaHei", size=13),
            text_color="#F5F0EB",
        ).pack(anchor="w", pady=(4, 0))

        # 右侧：天气 + 更新时间
        right_col = ctk.CTkFrame(banner_inner, fg_color="transparent")
        right_col.pack(side="right", fill="y")

        wt_frame = ctk.CTkFrame(right_col, fg_color="transparent")
        wt_frame.pack(side="right", pady=(10, 0))

        self.weather_label = ctk.CTkLabel(
            wt_frame,
            text="🌤 天气获取中...",
            font=ctk.CTkFont(family="Microsoft YaHei", size=12),
            text_color="#F5F0EB",
        )
        self.weather_label.pack(side="left", padx=(0, 12))

        self.time_label = ctk.CTkLabel(
            wt_frame,
            text="",
            font=ctk.CTkFont(family="Microsoft YaHei", size=12),
            text_color="#F5F0EB",
        )
        self.time_label.pack(side="left")

        # ── 待办聚合条 ─────────────────────────────────
        self._build_todo_bar(scroll_frame)

        # ── KPI 卡片区 ───────────────────────────────
        cards_label = ctk.CTkLabel(
            scroll_frame,
            text="核心指标",
            font=ctk.CTkFont(family="Microsoft YaHei", size=15, weight="bold"),
            text_color=self.C["text"],
        )
        cards_label.pack(anchor="w", padx=28, pady=(8, 8))

        card_grid = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        card_grid.pack(fill="x", padx=24, pady=(0, 12))
        card_grid.grid_columnconfigure((0, 1, 2), weight=1)

        # 第1行：3张卡片
        self._make_kpi_card(
            card_grid, 0, 0,
            title="物料下单",
            keys=[("处理中", "packaging_active"), ("已完成", "packaging_done")],
            color=MODULE_COLORS["packaging"],
            page_key="packaging",
            col_pad=(0, 6),
        )
        self._make_kpi_card(
            card_grid, 0, 1,
            title="催款记录",
            keys=[(None, "collection_total")],  # 单值卡
            color=MODULE_COLORS["collection"],
            page_key="collection",
            col_pad=6,
        )
        self._make_kpi_card(
            card_grid, 0, 2,
            title="采购垫付",
            keys=[("总笔数", "purchase_total"), ("待报销", "purchase_pending")],
            color=MODULE_COLORS["purchase"],
            page_key="purchase",
            col_pad=(6, 0),
        )

        # 第2行：2张卡片
        card_grid2 = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        card_grid2.pack(fill="x", padx=24, pady=(0, 12))
        card_grid2.grid_columnconfigure((0, 1), weight=1)

        self._make_kpi_card(
            card_grid2, 0, 0,
            title="差旅报销",
            keys=[("行程数", "travel_total"), ("待报销", "travel_pending")],
            color=MODULE_COLORS["travel"],
            page_key="travel",
            col_pad=(0, 6),
        )
        self._make_kpi_card(
            card_grid2, 0, 1,
            title="备忘录",
            keys=[(None, "memo_pending")],
            color=MODULE_COLORS["memo"],
            page_key="memo",
            col_pad=(6, 0),
        )

        # ── 采购趋势图 + 最近活动 ─────────────────────
        bottom_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        bottom_frame.pack(fill="x", padx=24, pady=(0, 16))
        bottom_frame.grid_columnconfigure(0, weight=2)
        bottom_frame.grid_columnconfigure(1, weight=1)

        # 左侧：采购金额趋势图
        self._build_trend_chart(bottom_frame)

        # 右侧：最近活动动态流
        self._build_activity_feed(bottom_frame)

    # ── 待办聚合条 ──────────────────────────────────
    def _build_todo_bar(self, parent):
        """构建待办聚合条"""
        self.todo_bar = ctk.CTkFrame(
            parent,
            fg_color="#FFF8F0",
            corner_radius=10,
            border_width=1,
            border_color="#C9A96E",
        )
        self.todo_bar.pack(fill="x", padx=24, pady=(0, 12))

        inner = ctk.CTkFrame(self.todo_bar, fg_color="transparent")
        inner.pack(fill="x", padx=16, pady=(10, 10))

        # 左侧图标
        ctk.CTkLabel(
            inner, text="⚠️", font=ctk.CTkFont(size=16),
        ).pack(side="left", padx=(0, 8))

        # 待办文字（动态更新）
        self.todo_text_label = ctk.CTkLabel(
            inner,
            text="正在加载待办事项...",
            font=ctk.CTkFont(family="Microsoft YaHei", size=12),
            text_color=self.C["text"],
        )
        self.todo_text_label.pack(side="left", fill="x", expand=True)

        # 右侧"前往处理"按钮
        self.todo_action_btn = ctk.CTkButton(
            inner, text="前往处理 ▶", width=100, height=28,
            fg_color=MODULE_COLORS["packaging"],
            hover_color="#A06050",
            font=ctk.CTkFont(family="Microsoft YaHei", size=12, weight="bold"),
            corner_radius=8, command=self._on_todo_click,
        )
        self.todo_action_btn.pack(side="right")

    # ── KPI 卡片（可点击 + 趋势）────────────────────
    def _make_kpi_card(self, parent, row, col, title, keys, color, page_key, col_pad):
        """构建可点击的 KPI 趋势卡片"""
        card = ctk.CTkFrame(
            parent, fg_color=color, corner_radius=18,
        )
        padx_val = col_pad if isinstance(col_pad, tuple) else (col_pad, col_pad)
        card.grid(row=row, column=col, sticky="nsew", padx=padx_val, pady=(0, 6))

        # 整卡可点击的透明覆盖按钮
        btn = ctk.CTkButton(
            card, text="", fg_color="transparent",
            hover=False,
            corner_radius=18,
            command=lambda k=page_key: self._on_card_click(k),
        )
        btn.place(x=0, y=0, relwidth=1, relheight=1)

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=22, pady=(20, 22))

        # 标题行（标题 + 趋势箭头）
        title_row = ctk.CTkFrame(inner, fg_color="transparent")
        title_row.pack(fill="x")

        ctk.CTkLabel(
            title_row, text=title,
            font=ctk.CTkFont(family="Microsoft YaHei", size=14, weight="bold"),
            text_color="#FFFFFF",
        ).pack(side="left")

        # 趋势标签（箭头 + 百分比）
        trend_label = ctk.CTkLabel(
            title_row, text="",
            font=ctk.CTkFont(family="Microsoft YaHei", size=11, weight="bold"),
            text_color="#E8E8E8",
        )
        trend_label.pack(side="right")
        self._trend_labels[title] = trend_label

        # 值区域
        if len(keys) == 1:
            # 单值卡
            _, key = keys[0]
            val_label = ctk.CTkLabel(
                inner, text="—",
                font=ctk.CTkFont(family="Microsoft YaHei", size=40, weight="bold"),
                text_color="#FFFFFF",
            )
            val_label.pack(anchor="w", pady=(10, 0))
            unit_label = ctk.CTkLabel(
                inner, text="",
                font=ctk.CTkFont(family="Microsoft YaHei", size=12),
                text_color="#F0E8E0",
            )
            unit_label.pack(anchor="w", pady=(4, 0))
            self._value_labels[key] = val_label
            self._value_labels[f"{key}_unit"] = unit_label
        else:
            # 双值卡
            vals_row = ctk.CTkFrame(inner, fg_color="transparent")
            vals_row.pack(fill="x", pady=(14, 0))

            for sub, key in keys:
                col_frame = ctk.CTkFrame(vals_row, fg_color="transparent")
                col_frame.pack(side="left", fill="x", expand=True)

                val_label = ctk.CTkLabel(
                    col_frame, text="—",
                    font=ctk.CTkFont(family="Microsoft YaHei", size=30, weight="bold"),
                    text_color="#FFFFFF",
                )
                val_label.pack(anchor="w")

                ctk.CTkLabel(
                    col_frame, text=sub,
                    font=ctk.CTkFont(family="Microsoft YaHei", size=11),
                    text_color="#F0E8E0",
                ).pack(anchor="w", pady=(2, 0))

                self._value_labels[key] = val_label

    # ── 采购趋势图 ──────────────────────────────────
    def _build_trend_chart(self, parent):
        """构建采购金额趋势图（本月 vs 上月）"""
        chart_frame = ctk.CTkFrame(
            parent, fg_color=self.C["card"], corner_radius=14,
        )
        chart_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=(0, 6))

        ctk.CTkLabel(
            chart_frame, text="📈  采购金额趋势（近6个月）",
            font=ctk.CTkFont(family="Microsoft YaHei", size=13, weight="bold"),
            text_color=self.C["text"],
        ).pack(anchor="w", padx=16, pady=(14, 8))

        # 图表占位（用 CTkFrame 模拟简易柱状图）
        self.chart_container = ctk.CTkFrame(chart_frame, fg_color="transparent")
        self.chart_container.pack(fill="both", expand=True, padx=16, pady=(0, 14))

    # ── 最近活动动态流 ──────────────────────────────
    def _build_activity_feed(self, parent):
        """构建最近活动动态流"""
        feed_frame = ctk.CTkFrame(
            parent, fg_color=self.C["card"], corner_radius=14,
        )
        feed_frame.grid(row=0, column=1, sticky="nsew", padx=(8, 0), pady=(0, 6))

        ctk.CTkLabel(
            feed_frame, text="🕐  最近活动",
            font=ctk.CTkFont(family="Microsoft YaHei", size=13, weight="bold"),
            text_color=self.C["text"],
        ).pack(anchor="w", padx=16, pady=(14, 8))

        self.activity_frame = ctk.CTkFrame(feed_frame, fg_color="transparent")
        self.activity_frame.pack(fill="both", expand=True, padx=16, pady=(0, 14))

    # ──────────────────────────────────────────────
    # 数据加载
    # ──────────────────────────────────────────────
    def _load_data(self):
        """加载所有 KPI 数据"""
        try:
            now = datetime.now().strftime("%Y-%m-%d %H:%M")
            self.time_label.configure(text=f"更新时间：{now}")

            # 物料下单
            packaging_active = self.db.get_packagings(archived=0)
            packaging_done  = self.db.get_packagings(archived=1)
            self._set_value("packaging_active", str(len(packaging_active)))
            self._set_value("packaging_done", str(len(packaging_done)))
            self._update_trend("物料下单", len(packaging_active), "packaging_orders", "created_at")

            # 催款记录
            collections = self.db.get_collections()
            self._set_value("collection_total", str(len(collections)))
            self._set_value("collection_total_unit", "条记录")
            self._update_trend("催款记录", len(collections), "collections", "created_at")

            # 采购垫付
            purchases = self.db.get_purchases(archived=0)
            purchase_pending_amt = sum(
                p.get("total", 0) for p in purchases
                if p.get("reimbursement_status") != "已报销"
            )
            self._set_value("purchase_total", str(len(purchases)))
            self._set_value("purchase_pending", f"¥{purchase_pending_amt:.0f}")
            self._update_trend("采购垫付", len(purchases), "purchases", "created_at")

            # 差旅报销
            travels = self.db.get_travels(archived=0)
            travel_pending_amt = sum(
                t.get("total", 0) for t in travels
                if t.get("reimbursement_status") != "已报销"
            )
            self._set_value("travel_total", str(len(travels)))
            self._set_value("travel_pending", f"¥{travel_pending_amt:.0f}")
            self._update_trend("差旅报销", len(travels), "travels", "created_at")

            # 备忘录
            memos = self.db.get_memos(status="待处理")
            self._set_value("memo_pending", str(len(memos)))
            self._set_value("memo_pending_unit", "条待处理")
            self._update_trend("备忘录", len(memos), "memos", "created_at")

            # 待办聚合条
            self._update_todo_bar(packaging_active, collections, memos)

            # 趋势图
            self._update_trend_chart()

            # 最近活动
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
                "collections": "collections",
                "purchases": "purchases",
                "travels": "travels",
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

    def _update_todo_bar(self, packaging_active, collections, memos):
        """更新待办聚合条"""
        todos = []

        # 物料下单：待签批
        pending_contracts = [r for r in packaging_active
                             if r.get("contract_status") in ("待签批", "", None)]
        if pending_contracts:
            todos.append(f"📦 {len(pending_contracts)} 份合同待签批")

        # 催款记录：未结清
        unpaid = [c for c in collections if c.get("status") not in ("已结清", "已完成")]
        if unpaid:
            todos.append(f"💰 {len(unpaid)} 笔催款待跟进")

        # 备忘录：待处理
        if len(memos) > 0:
            todos.append(f"📝 {len(memos)} 条备忘录待处理")

        if todos:
            text = "  |  ".join(todos) + "  |  点击前往处理 ▶"
            self.todo_text_label.configure(text=text)
            self.todo_bar.configure(fg_color="#FFF4E6")
        else:
            self.todo_text_label.configure(text="✅ 所有事项已处理完毕，暂无待办")
            self.todo_bar.configure(fg_color="#F0F8F0")

    def _update_trend_chart(self):
        """更新采购金额趋势图（简易柱状图）"""
        # 清空旧图表
        for widget in self.chart_container.winfo_children():
            widget.destroy()

        try:
            import calendar
            today = date.today()
            months = []
            amounts = []

            for i in range(5, -1, -1):
                # 计算月份
                y = today.year
                m = today.month - i
                while m <= 0:
                    y -= 1
                    m += 12
                months.append(f"{m}月")
                # 查询该月采购垫付总额
                month_start = f"{y}-{m:02d}-01"
                last_day = calendar.monthrange(y, m)[1]
                month_end = f"{y}-{m:02d}-{last_day:02d}"

                try:
                    cur = self.db.conn.cursor()
                    cur.execute(
                        "SELECT SUM(total) FROM purchases WHERE created_at >= ? AND created_at <= ?",
                        (month_start, month_end + " 23:59:59")
                    )
                    row = cur.fetchone()
                    amt = row[0] or 0
                    amounts.append(amt)
                except Exception:
                    amounts.append(0)

            # 绘制简易柱状图（用 CTkProgressBar 模拟）
            bars_frame = ctk.CTkFrame(self.chart_container, fg_color="transparent")
            bars_frame.pack(fill="both", expand=True)

            max_amt = max(amounts) if amounts else 1
            if max_amt == 0:
                max_amt = 1

            for i, (month, amt) in enumerate(zip(months, amounts)):
                row_f = ctk.CTkFrame(bars_frame, fg_color="transparent")
                row_f.pack(fill="x", pady=3)

                ctk.CTkLabel(
                    row_f, text=month, width=40,
                    font=ctk.CTkFont(size=11),
                    text_color=self.C["text_secondary"],
                ).pack(side="left")

                bar = ctk.CTkProgressBar(
                    row_f, width=180, height=14,
                    fg_color="#F0E8E0",
                    progress_color=MODULE_COLORS["purchase"],
                    corner_radius=4,
                )
                bar.pack(side="left", padx=(8, 8))
                bar.set(amt / max_amt if max_amt > 0 else 0)

                ctk.CTkLabel(
                    row_f, text=f"¥{amt:.0f}",
                    font=ctk.CTkFont(size=11),
                    text_color=self.C["text"],
                ).pack(side="left")

        except Exception as e:
            print(f"趋势图绘制失败: {e}")

    def _update_activity_feed(self):
        """更新最近活动动态流"""
        # 清空旧内容
        for widget in self.activity_frame.winfo_children():
            widget.destroy()

        try:
            activities = []

            # 从各表获取最近5条记录（按 created_at 倒序）
            import sqlite3

            # 物料下单
            try:
                cur = self.db.conn.cursor()
                cur.execute(
                    "SELECT material_name, created_at FROM packaging_orders "
                    "WHERE created_at IS NOT NULL ORDER BY created_at DESC LIMIT 3"
                )
                for row in cur.fetchall():
                    name, ts = row
                    activities.append((ts, f"📦 新增物料下单：{name or '未命名'}"))
            except Exception:
                pass

            # 催款记录
            try:
                cur = self.db.conn.cursor()
                cur.execute(
                    "SELECT supplier_name, created_at FROM collections "
                    "WHERE created_at IS NOT NULL ORDER BY created_at DESC LIMIT 3"
                )
                for row in cur.fetchall():
                    name, ts = row
                    activities.append((ts, f"💰 新增催款记录：{name or '未知供应商'}"))
            except Exception:
                pass

            # 备忘录
            try:
                cur = self.db.conn.cursor()
                cur.execute(
                    "SELECT title, created_at FROM memos "
                    "WHERE created_at IS NOT NULL ORDER BY created_at DESC LIMIT 3"
                )
                for row in cur.fetchall():
                    title, ts = row
                    activities.append((ts, f"📝 新增备忘录：{title or '无标题'}"))
            except Exception:
                pass

            # 按时间倒序排列，取前5条
            activities.sort(reverse=True)
            recent = activities[:5]

            if not recent:
                ctk.CTkLabel(
                    self.activity_frame, text="暂无最近活动",
                    font=ctk.CTkFont(size=12),
                    text_color=self.C["text_secondary"],
                ).pack(anchor="w", pady=8)
                return

            for ts, desc in recent:
                item = ctk.CTkFrame(self.activity_frame, fg_color="transparent")
                item.pack(fill="x", pady=3)

                # 时间
                try:
                    dt = datetime.strptime(ts[:16], "%Y-%m-%d %H:%M")
                    time_str = dt.strftime("%m-%d %H:%M")
                except Exception:
                    time_str = str(ts)[:16] if ts else "未知时间"

                ctk.CTkLabel(
                    item, text=time_str, width=65,
                    font=ctk.CTkFont(size=11, weight="bold"),
                    text_color=MODULE_COLORS["travel"],
                    anchor="w",
                ).pack(side="left", padx=(0, 8))

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

    # ── 天气预报（保持不变）───────────────────────
    def _fetch_weather(self):
        def _worker():
            try:
                url = "https://wttr.in/?format=j1"
                req = urllib.request.Request(
                    url,
                    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
                )
                with urllib.request.urlopen(req, timeout=10) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    current = data["current_condition"][0]
                    area = data["nearest_area"][0]
                    city = area.get("areaName", [{"value": "未知"}])[0]["value"]
                    temp = current.get("temp_C", "N/A")
                    desc = current.get("weatherDesc", [{"value": ""}])[0]["value"]
                    code = current.get("weatherCode", "113")
                    emoji = self._weather_emoji(code)
                    weather_text = f"{emoji} {city} {temp}°C {desc}"
                    self.after(0, lambda t=weather_text: self.weather_label.configure(text=t))
            except Exception:
                self.after(0, lambda: self.weather_label.configure(text="🌤 天气获取失败"))

        t = threading.Thread(target=_worker, daemon=True)
        t.start()

    def _weather_emoji(self, code):
        try:
            code = int(code)
        except Exception:
            return "🌤️"
        if code in (113, 116):
            return "☀️"
        if code in (119, 122):
            return "☁️"
        if code in (176, 263, 266, 293, 296, 299, 302, 305, 308, 311, 314, 317, 320,
                    323, 326, 329, 332, 335, 338):
            return "🌧️"
        if code in (200, 386, 389, 392, 395):
            return "⛈️"
        return "🌤️"

    def refresh(self):
        self._load_data()
