#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成 10 秒卡通宣传动画 GIF：双吉祥物弹跳 + 星星泡泡 + 标题特效。"""
import math, os, random
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1280, 720
FPS = 10
SECONDS = 10
FRAMES = FPS * SECONDS
BASE = os.path.dirname(os.path.abspath(__file__))
WHALE = os.path.join(BASE, "..", "doubao-collab-ui", "deepseek-whale.png")
BEAN = os.path.join(BASE, "..", "doubao-collab-ui", "doubao-bean.png")
OUT = os.path.join(BASE, "promo-10s.gif")

def load(path, size):
    im = Image.open(path).convert("RGBA")
    im.thumbnail((size, size), Image.LANCZOS)
    return im

whale = load(WHALE, 220)
bean = load(BEAN, 200)

def font(sz):
    for p in ["C:/Windows/Fonts/msyhbd.ttc", "C:/Windows/Fonts/msyh.ttc", "C:/Windows/Fonts/simhei.ttf"]:
        if os.path.exists(p):
            try: return ImageFont.truetype(p, sz)
            except Exception: pass
    return ImageFont.load_default()

F_TITLE = font(86)
F_SUB = font(42)
F_TAG = font(30)

# 调色板
SKY_TOP = (255, 236, 240)
SKY_BOT = (224, 240, 255)
INK = (59, 43, 79)

rng = random.Random(42)
stars = [(rng.randint(0, W), rng.randint(0, H // 2), rng.uniform(0.3, 1.0), rng.uniform(0, 6.28)) for _ in range(26)]
bubbles = [(rng.randint(0, W), rng.randint(H // 3, H), rng.randint(6, 22), rng.uniform(0.5, 1.6), rng.uniform(0, 6.28)) for _ in range(14)]

def draw_bg(t):
    bg = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(bg)
    for y in range(H):
        k = y / H
        c = tuple(int(SKY_TOP[i] + (SKY_BOT[i] - SKY_TOP[i]) * k) for i in range(3))
        d.line([(0, y), (W, y)], fill=c + (255,))
    # 星星
    for sx, sy, s, ph in stars:
        a = int(120 + 110 * math.sin(t * 2.2 + ph))
        d.ellipse([sx - 3, sy - 3, sx + 3, sy + 3], fill=(255, 255, 200, a))
    # 泡泡
    for bx, by, r, sp, ph in bubbles:
        yy = by - (t * 30 * sp) % H
        a = int(90 + 80 * math.sin(t * 3 + ph))
        d.ellipse([bx - r, yy - r, bx + r, yy + r], outline=(255, 255, 255, a), width=3)
    # 底部云朵
    d.rounded_rectangle([-80, 560, 420, 680], 40, fill=(255, 255, 255, 210))
    d.rounded_rectangle([W - 420, 590, W + 80, 700], 40, fill=(255, 255, 255, 210))
    return bg

def paste_mascot(frame, img, cx, cy, scale, rot):
    w, h = img.size
    im = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
    if rot:
        im = im.rotate(rot, expand=True, resample=Image.BICUBIC)
    frame.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))

def draw_text(frame, t):
    d = ImageDraw.Draw(frame)
    # 标题：进场 + 呼吸
    p = min(1.0, t / 0.6)
    ease = 1 - (1 - p) ** 3
    title = "双AI工作室"
    tw = d.textlength(title, font=F_TITLE)
    ts = 0.8 + 0.2 * ease
    th = F_TITLE.size
    # 用临时图缩放实现弹跳
    tmp = Image.new("RGBA", (W, H * 2), (0, 0, 0, 0))
    td = ImageDraw.Draw(tmp)
    td.text((W / 2 - tw / 2, 120), title, font=F_TITLE, fill=INK + (255,), stroke_width=6, stroke_fill=(255, 255, 255))
    tmp = tmp.crop((0, 100, W, 100 + th + 40))
    bounce = abs(math.sin(t * 2.6)) * 10
    tmp = tmp.resize((int(tmp.width * ts), int(tmp.height * ts)), Image.LANCZOS)
    frame.alpha_composite(tmp, (int(W / 2 - tmp.width / 2), int(150 - bounce)))
    # 副标题
    if t > 0.8:
        sub = "DeepSeek × 豆包 · 卡通联名"
        sw = d.textlength(sub, font=F_SUB)
        sa = min(255, int(255 * (t - 0.8) / 0.5))
        d.text((W / 2 - sw / 2, 268), sub, font=F_SUB, fill=(90, 110, 180, sa))
    # 底部标签
    if t > 4.5:
        tag = "由 DeepSeek 写码 · 豆包 Seedream 作画"
        tw2 = d.textlength(tag, font=F_TAG)
        ta = min(255, int(255 * (t - 4.5) / 0.6))
        d.rounded_rectangle([W / 2 - tw2 / 2 - 18, 628, W / 2 + tw2 / 2 + 18, 672], 18, fill=(255, 255, 255, 200))
        d.text((W / 2 - tw2 / 2, 635), tag, font=F_TAG, fill=INK + (ta,))

def render_frame(t):
    frame = draw_bg(t)
    # 吉祥物：从两侧滑入，然后弹跳
    enter = min(1.0, t / 0.8)
    ease = 1 - (1 - enter) ** 3
    wcx = W * 0.33 - (1 - ease) * 420
    bcx = W * 0.67 + (1 - ease) * 420
    wy = 470 + abs(math.sin(t * 2.4)) * 16
    by = 480 + abs(math.sin(t * 2.4 + 0.8)) * 18
    ws = 1 + 0.03 * math.sin(t * 2.4)
    bs = 1 + 0.03 * math.sin(t * 2.4 + 0.8)
    paste_mascot(frame, whale, wcx, wy, ws, math.sin(t * 1.2) * 4)
    paste_mascot(frame, bean, bcx, by, bs, -math.sin(t * 1.2 + 0.5) * 5)
    draw_text(frame, t)
    return frame

frames = []
for i in range(FRAMES):
    t = i / FPS
    frames.append(render_frame(t))
    if i % 25 == 0:
        print(f"frame {i}/{FRAMES}")

frames[0].save(OUT, save_all=True, append_images=frames[1:], duration=100, loop=0, optimize=True)
print("saved:", OUT, os.path.getsize(OUT), "bytes")
