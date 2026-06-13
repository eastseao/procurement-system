#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成线性+实心两套导航图标"""
from PIL import Image, ImageDraw
import os, math

OUT = os.path.join(os.path.dirname(__file__), 'assets')
S = 48
BG = (0, 0, 0, 0)
LINE  = (93, 78, 55, 255)
SOLID = (30, 20, 10, 255)
W = 3

def new_img():
    return Image.new("RGBA", (S, S), BG)

def save(img, name, active=False):
    suffix = "_active" if active else ""
    path = os.path.join(OUT, f"nav_{name}{suffix}.png")
    img.save(path)

def draw_icon(name, draw_fn):
    img = new_img(); d = ImageDraw.Draw(img)
    draw_fn(d, LINE, filled=False)
    save(img, name, active=False)
    img = new_img(); d = ImageDraw.Draw(img)
    draw_fn(d, SOLID, filled=True)
    save(img, name, active=True)
    print(f"  nav_{name}.png + nav_{name}_active.png")

def draw_dashboard(d, c, filled):
    if filled:
        d.rectangle([4,26,14,44], fill=c)
        d.rectangle([19,16,29,44], fill=c)
        d.rectangle([34,6,44,44], fill=c)
    else:
        d.rectangle([4,26,14,44], outline=c, width=W)
        d.rectangle([19,16,29,44], outline=c, width=W)
        d.rectangle([34,6,44,44], outline=c, width=W)

def draw_packaging(d, c, filled):
    if filled:
        d.rectangle([4,16,44,44], fill=c)
        d.rectangle([4,10,44,18], fill=c)
        d.line([24,18,24,44], fill=(200,180,160,255), width=W)
    else:
        d.rectangle([4,16,44,44], outline=c, width=W)
        d.rectangle([4,10,44,18], outline=c, width=W)
        d.line([24,18,24,44], fill=c, width=W)

def draw_quotation(d, c, filled):
    pts = [8,4, 32,4, 40,12, 40,44, 8,44]
    if filled:
        d.polygon(pts, fill=c)
        d.line([32,4,32,12,40,12], fill=(200,180,160,255), width=W)
        for y in [22,30,38]:
            d.line([14,y,34,y], fill=(240,235,228,255), width=W)
    else:
        d.polygon(pts, outline=c, fill=BG, width=W)
        d.line([32,4,32,12], fill=c, width=W)
        d.line([32,12,40,12], fill=c, width=W)
        for y in [22,30,38]:
            d.line([14,y,34,y], fill=c, width=W)

def draw_compare(d, c, filled):
    d.line([24,6,24,44], fill=c, width=W)
    d.line([8,44,40,44], fill=c, width=W)
    d.line([8,14,40,14], fill=c, width=W)
    if filled:
        d.ellipse([4,18,20,30], fill=c)
        d.ellipse([28,18,44,30], fill=c)
    else:
        d.ellipse([4,18,20,30], outline=c, width=W)
        d.ellipse([28,18,44,30], outline=c, width=W)

def draw_contract(d, c, filled):
    pts = [6,4, 38,4, 42,8, 42,44, 6,44]
    if filled:
        d.polygon(pts, fill=c)
        for y in [18,26,34]:
            d.line([12,y,36,y], fill=(240,235,228,255), width=W)
    else:
        d.polygon(pts, outline=c, fill=BG, width=W)
        for y in [18,26,34]:
            d.line([12,y,36,y], fill=c, width=W)

def draw_supplier(d, c, filled):
    if filled:
        d.polygon([4,44,24,6,44,44], fill=c)
        d.rectangle([14,30,22,44], fill=(200,180,160,255))
        d.rectangle([26,28,34,36], fill=(200,180,160,255))
    else:
        d.polygon([4,44,24,6,44,44], outline=c, fill=BG, width=W)
        d.rectangle([14,30,22,44], outline=c, width=W)
        d.rectangle([26,28,34,36], outline=c, width=W)

def draw_query(d, c, filled):
    if filled:
        d.ellipse([4,4,30,30], fill=c)
        d.ellipse([9,9,25,25], fill=(200,180,160,255))
    else:
        d.ellipse([4,4,30,30], outline=c, width=W)
    d.line([27,27,44,44], fill=c, width=5)

def draw_product_bom(d, c, filled):
    if filled:
        d.rounded_rectangle([17,4,31,14], radius=2, fill=c)
        d.rounded_rectangle([4,34,18,44], radius=2, fill=c)
        d.rounded_rectangle([30,34,44,44], radius=2, fill=c)
    else:
        d.rounded_rectangle([17,4,31,14], radius=2, outline=c, width=W)
        d.rounded_rectangle([4,34,18,44], radius=2, outline=c, width=W)
        d.rounded_rectangle([30,34,44,44], radius=2, outline=c, width=W)
    d.line([24,14,24,24], fill=c, width=W)
    d.line([11,24,37,24], fill=c, width=W)
    d.line([11,24,11,34], fill=c, width=W)
    d.line([37,24,37,34], fill=c, width=W)

def draw_collection(d, c, filled):
    if filled:
        d.ellipse([6,16,42,44], fill=c)
        d.polygon([16,16,32,16,28,6,20,6], fill=c)
        d.line([24,22,24,40], fill=(200,180,160,255), width=W)
        d.line([16,28,32,28], fill=(200,180,160,255), width=W)
        d.line([16,36,32,36], fill=(200,180,160,255), width=W)
    else:
        d.ellipse([6,16,42,44], outline=c, width=W)
        d.polygon([16,16,32,16,28,6,20,6], outline=c, fill=BG, width=W)
        d.line([24,22,24,40], fill=c, width=W)
        d.line([16,28,32,28], fill=c, width=W)
        d.line([16,36,32,36], fill=c, width=W)

def draw_purchase(d, c, filled):
    if filled:
        d.rounded_rectangle([4,10,44,38], radius=4, fill=c)
        d.rectangle([4,18,44,26], fill=(200,180,160,255))
        d.rounded_rectangle([8,28,18,34], radius=2, fill=(200,180,160,255))
    else:
        d.rounded_rectangle([4,10,44,38], radius=4, outline=c, width=W)
        d.rectangle([4,18,44,26], fill=c)
        d.rounded_rectangle([8,28,18,34], radius=2, outline=c, width=W)

def draw_travel(d, c, filled):
    pts = [6,18,42,24,36,30,22,28,14,36,8,34,16,26,8,20]
    if filled:
        d.polygon(pts, fill=c)
    else:
        d.polygon(pts, outline=c, fill=BG, width=W)

def draw_memo(d, c, filled):
    if filled:
        d.rounded_rectangle([6,4,34,44], radius=3, fill=c)
        for y in [16,24,32]:
            d.line([12,y,28,y], fill=(200,180,160,255), width=W)
        d.polygon([36,10,44,18,38,44,30,36], fill=c)
    else:
        d.rounded_rectangle([6,4,34,44], radius=3, outline=c, width=W)
        for y in [16,24,32]:
            d.line([12,y,28,y], fill=c, width=W)
        d.polygon([36,10,44,18,38,44,30,36], outline=c, fill=BG, width=W)

def draw_settings(d, c, filled):
    cx, cy, r = 24, 24, 10
    if filled:
        d.ellipse([cx-r,cy-r,cx+r,cy+r], fill=c)
        d.ellipse([cx-5,cy-5,cx+5,cy+5], fill=(200,180,160,255))
    else:
        d.ellipse([cx-r,cy-r,cx+r,cy+r], outline=c, width=W)
        d.ellipse([cx-5,cy-5,cx+5,cy+5], outline=c, width=W)
    for deg in range(0, 360, 45):
        rad = math.radians(deg)
        x1 = cx + (r+1)*math.cos(rad)
        y1 = cy + (r+1)*math.sin(rad)
        x2 = cx + (r+7)*math.cos(rad)
        y2 = cy + (r+7)*math.sin(rad)
        d.line([(x1,y1),(x2,y2)], fill=c, width=5)

icons = [
    ("dashboard",   draw_dashboard),
    ("packaging",   draw_packaging),
    ("quotation",   draw_quotation),
    ("compare",     draw_compare),
    ("contract",    draw_contract),
    ("supplier",    draw_supplier),
    ("query",       draw_query),
    ("product_bom", draw_product_bom),
    ("collection",  draw_collection),
    ("purchase",    draw_purchase),
    ("travel",      draw_travel),
    ("memo",        draw_memo),
    ("settings",    draw_settings),
]

for name, fn in icons:
    draw_icon(name, fn)

print("Done.")
