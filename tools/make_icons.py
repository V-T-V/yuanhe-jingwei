# -*- coding: utf-8 -*-
"""元和经纬 · PWA 图标生成（石青底 + 朱砂印风格，PIL 绘制）
运行：python tools/make_icons.py → icons/icon-192.png / icon-512.png / icon-maskable-512.png
"""
import os

from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ICONS = os.path.join(ROOT, "icons")
os.makedirs(ICONS, exist_ok=True)

AZUR = (47, 93, 112)
CREAM = (246, 239, 220)
CINNABAR = (176, 58, 37)


def draw_icon(size, maskable=False):
    img = Image.new("RGB", (size, size), AZUR)
    d = ImageDraw.Draw(img)
    pad = int(size * (0.18 if maskable else 0.10))
    inner = size - 2 * pad
    # 双圈印框
    d.rectangle([pad, pad, pad + inner, pad + inner], outline=CREAM, width=max(2, size // 64))
    d.rectangle([pad + size // 26, pad + size // 26, pad + inner - size // 26, pad + inner - size // 26],
                outline=CREAM, width=max(1, size // 96))
    # 朱砂方点阵（「元和」四方印意）
    dot = max(3, size // 16)
    cx = size // 2
    gap = max(4, size // 7)
    for ddx in (-1, 1):
        for ddy in (-1, 1):
            x0 = cx + ddx * gap - dot // 2
            y0 = cx + ddy * gap - dot // 2
            d.rectangle([x0, y0, x0 + dot, y0 + dot], fill=CINNABAR)
    d.ellipse([cx - dot, cx - dot, cx + dot, cx + dot], outline=CREAM, width=max(1, size // 128))
    return img


for name, size, mk in [("icon-192.png", 192, False),
                       ("icon-512.png", 512, False),
                       ("icon-maskable-512.png", 512, True)]:
    draw_icon(size, mk).save(os.path.join(ICONS, name))
    print("生成", name)
