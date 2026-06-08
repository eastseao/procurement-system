#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成导航栏图标 PNG — 20×20 几何图标，莫兰迪暖棕色"""

from PIL import Image, ImageDraw
import os

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
S = 20          # 图标尺寸
C = (93, 78, 55)  # #5D4E37 sidebar_text
W = 2            # 默认线宽

def new_icon():
    return Image.new("RGBA", (S, S), (0, 0, 0, 0))

def save(img, name):
    path = os.path.join(OUT_DIR, f"nav_{name}.png")
    img.save(path)
    print(f"  ✅ nav_{name}.png")

# ── 1. 仪表盘 — 三个竖条（柱状图） ──
img = new_icon()
d = ImageDraw.Draw(img)
d.rectangle([2, 12, 6, 18], fill=C)       # 左低
d.rectangle([8, 6, 12, 18], fill=C)       # 中中
d.rectangle([14, 2, 18, 18], fill=C)      # 右高
save(img, "dashboard")

# ── 2. 物料下单 — 箱子 ──
img = new_icon()
d = ImageDraw.Draw(img)
d.rectangle([3, 6, 17, 17], outline=C, width=1)  # 箱体
d.rectangle([3, 6, 17, 9], fill=C)                # 箱盖
d.line([7, 9, 7, 17], fill=C)                      # 中间竖线
d.line([8, 11, 14, 11], fill=C)                    # 横线装饰(×)
d.line([8, 12, 14, 12], fill=C)
save(img, "packaging")

# ── 3. 报价单 — 文档 ──
img = new_icon()
d = ImageDraw.Draw(img)
d.rectangle([3, 2, 16, 18], outline=C, width=1)   # 文档外框
d.polygon([12, 2, 12, 7, 16, 7], fill=C)           # 折角
d.line([6, 10, 14, 10], fill=C)                     # 文字行1
d.line([6, 13, 10, 13], fill=C)                     # 文字行2
save(img, "quotation")

# ── 4. 物料查询 — 放大镜 ──
img = new_icon()
d = ImageDraw.Draw(img)
d.ellipse([2, 2, 13, 13], outline=C, width=2)      # 镜片
d.line([12, 12, 18, 18], fill=C, width=2)           # 手柄
save(img, "query")

# ── 5. 供应商 — 建筑 ──
img = new_icon()
d = ImageDraw.Draw(img)
d.rectangle([3, 8, 17, 18], fill=C)                 # 楼体
d.polygon([2, 8, 10, 1, 18, 8], fill=C)             # 屋顶
d.rectangle([7, 13, 10, 18], fill=(0,0,0,0), outline=(245, 240, 235), width=1)  # 门
d.rectangle([4, 10, 6, 12], fill=(0,0,0,0), outline=(245,240,235), width=1)     # 左窗
d.rectangle([14, 10, 16, 12], fill=(0,0,0,0), outline=(245,240,235), width=1)   # 右窗
save(img, "supplier")

# ── 6. 催款记录 — 货币符号 ──
img = new_icon()
d = ImageDraw.Draw(img)
d.ellipse([1, 2, 19, 18], outline=C, width=1)       # 圆形边框
d.line([10, 4, 10, 16], fill=C, width=2)             # $ 竖线
d.line([6, 7, 10, 7], fill=C, width=2)               # 上横
d.line([7, 10, 10, 10], fill=C, width=2)             # 中横
d.line([7, 13, 10, 13], fill=C, width=2)             # 下横
save(img, "collection")

# ── 7. 采购垫付 — 卡片 ──
img = new_icon()
d = ImageDraw.Draw(img)
d.rounded_rectangle([1, 3, 19, 17], radius=2, outline=C, width=1)  # 卡片
d.rectangle([3, 5, 10, 9], fill=C)                                  # 芯片
d.line([14, 13, 17, 13], fill=C, width=1)                            # 磁条
d.line([14, 15, 16, 15], fill=C, width=1)
save(img, "purchase")

# ── 8. 差旅报销 — 飞机 ──
img = new_icon()
d = ImageDraw.Draw(img)
d.polygon([2, 16, 10, 7, 18, 16], outline=C, width=1)   # 机身
d.line([10, 7, 10, 2], fill=C, width=2)                   # 尾翼
d.line([6, 2, 10, 2], fill=C, width=2)                    # 尾翼横
save(img, "travel")

# ── 9. 备忘录 — 铅笔/笔记 ──
img = new_icon()
d = ImageDraw.Draw(img)
d.rectangle([3, 3, 14, 17], outline=C, width=1)          # 笔记本
d.line([6, 7, 12, 7], fill=C, width=1)                    # 横线1
d.line([6, 10, 12, 10], fill=C, width=1)                  # 横线2
d.line([6, 13, 10, 13], fill=C, width=1)                  # 横线3
d.polygon([15, 4, 17, 1, 19, 2, 16, 5], fill=C)          # 铅笔尖
save(img, "memo")

# ── 10. 设置 — 齿轮 ──
img = new_icon()
d = ImageDraw.Draw(img)
cx, cy, r = 10, 10, 5
d.ellipse([cx-r, cy-r, cx+r, cy+r], outline=C, width=1)   # 中心圆
# 四周小齿
for deg in range(0, 360, 45):
    import math
    rad = math.radians(deg)
    x1 = cx + (r+1) * math.cos(rad) - 1
    y1 = cy + (r+1) * math.sin(rad) - 1
    x2 = cx + (r+3) * math.cos(rad) - 1
    y2 = cy + (r+3) * math.sin(rad) - 1
    d.rectangle([x1, y1, x2+2, y2+2], fill=C)
save(img, "settings")

print(f"\n🎉 全部 10 个图标已生成到: {OUT_DIR}")
