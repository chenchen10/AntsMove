#!/usr/bin/env python3
"""生成6种昆虫精灵图 - 高辨识度写实风格，8方向帧动画

改进点：
- 分辨率提升至64x64（部分昆虫更大），细节更丰富
- 每种昆虫有明确的标志性视觉特征
- 更自然的颜色过渡和光影效果
- 清晰的身体结构：头、胸、腹、腿、触角、翅膀
"""

from PIL import Image, ImageDraw, ImageFilter
import os
import math

BASE_DIR = os.path.join(os.path.dirname(__file__), "images", "insect")

# 昆虫定义：名称、尺寸、帧数
INSECTS = {
    "ladybug":     {"size": (64, 64), "frames": 3},
    "caterpillar": {"size": (80, 40), "frames": 4},
    "cricket":     {"size": (64, 64), "frames": 3},
    "beetle":      {"size": (64, 64), "frames": 3},
    "dragonfly":   {"size": (64, 72), "frames": 3},
    "bee":         {"size": (64, 64), "frames": 3},
}

DIRECTIONS = ["n", "ne", "e", "se", "s", "sw", "w", "nw"]

DIR_ANGLES = {
    "n": 0, "ne": 45, "e": 90, "se": 135,
    "s": 180, "sw": 225, "w": 270, "nw": 315,
}


def _draw_gradient_ellipse(draw, bbox, color_center, color_edge, steps=20):
    """绘制带渐变效果的椭圆"""
    x0, y0, x1, y1 = bbox
    cx = (x0 + x1) / 2
    cy = (y0 + y1) / 2
    rx = (x1 - x0) / 2
    ry = (y1 - y0) / 2
    for i in range(steps, 0, -1):
        t = i / steps
        r = int(color_center[0] * (1 - t) + color_edge[0] * t)
        g = int(color_center[1] * (1 - t) + color_edge[1] * t)
        b = int(color_center[2] * (1 - t) + color_edge[2] * t)
        a = 255
        if len(color_center) > 3:
            a = int(color_center[3] * (1 - t) + color_edge[3] * t)
        cur_rx = rx * t
        cur_ry = ry * t
        if cur_rx < 0.5 or cur_ry < 0.5:
            continue
        draw.ellipse(
            [cx - cur_rx, cy - cur_ry, cx + cur_rx, cy + cur_ry],
            fill=(r, g, b, a)
        )


def draw_ladybug(draw, w, h, frame, angle):
    """瓢虫 - 红色甲壳+黑色圆点，写实风格

    标志特征：鲜红色半球形甲壳，左右对称黑色圆点，
    甲壳中央有一条黑色分界线，头部黑色有白色斑纹
    """
    cx, cy = w // 2, h // 2

    # === 腿（6条，先画在身体下面） ===
    leg_color = (30, 30, 30)
    leg_positions = [
        # 前腿
        ((cx - 8, cy - 2), (cx - 18, cy - 10)),
        ((cx + 8, cy - 2), (cx + 18, cy - 10)),
        # 中腿
        ((cx - 12, cy + 4), (cx - 22, cy + 10)),
        ((cx + 12, cy + 4), (cx + 22, cy + 10)),
        # 后腿
        ((cx - 10, cy + 10), (cx - 20, cy + 18)),
        ((cx + 10, cy + 10), (cx + 20, cy + 18)),
    ]
    leg_wave = 2 if frame % 2 == 0 else -2
    for (x1, y1), (x2, y2) in leg_positions:
        my = y2 + leg_wave
        draw.line([(x1, y1), (x2, my)], fill=leg_color, width=2)
        # 腿关节
        draw.line([(x2, my), (x2 + 2, my + 3)], fill=leg_color, width=1)

    # === 身体（红色甲壳，椭圆形） ===
    body_rx, body_ry = 16, 14
    # 深色底色
    draw.ellipse(
        [cx - body_rx, cy - body_ry, cx + body_rx, cy + body_ry],
        fill=(160, 20, 20), outline=(120, 15, 15)
    )
    # 渐变高光层
    _draw_gradient_ellipse(
        draw,
        (cx - body_rx + 2, cy - body_ry + 2, cx + body_rx - 2, cy + body_ry - 2),
        color_center=(220, 60, 60),
        color_edge=(170, 25, 25),
        steps=15
    )

    # === 甲壳中线（黑色分界线） ===
    draw.line(
        [(cx, cy - body_ry + 3), (cx, cy + body_ry - 3)],
        fill=(40, 5, 5), width=2
    )

    # === 黑色圆点（左右对称分布） ===
    spots_left = [
        (cx - 8, cy - 8, 3),   # 左上
        (cx - 11, cy - 1, 3),  # 左中
        (cx - 7, cy + 6, 3),   # 左下
        (cx - 12, cy + 5, 2),  # 左外侧小点
    ]
    spots_right = [
        (cx + 8, cy - 8, 3),
        (cx + 11, cy - 1, 3),
        (cx + 7, cy + 6, 3),
        (cx + 12, cy + 5, 2),
    ]
    for sx, sy, r in spots_left + spots_right:
        draw.ellipse([sx - r, sy - r, sx + r, sy + r], fill=(15, 15, 15))

    # === 光泽高光（随帧动画偏移） ===
    hl_offset = frame * 2
    draw.ellipse(
        [cx - 10 + hl_offset, cy - 12, cx - 4 + hl_offset, cy - 8],
        fill=(240, 100, 100, 180)
    )

    # === 头部（黑色，略小） ===
    head_y = cy - body_ry - 4
    draw.ellipse(
        [cx - 6, head_y - 5, cx + 6, head_y + 5],
        fill=(25, 25, 25)
    )
    # 头部白色斑纹（瓢虫特征）
    draw.ellipse(
        [cx - 4, head_y - 3, cx - 1, head_y],
        fill=(200, 200, 200)
    )
    draw.ellipse(
        [cx + 1, head_y - 3, cx + 4, head_y],
        fill=(200, 200, 200)
    )
    # 眼睛
    draw.ellipse([cx - 5, head_y - 4, cx - 3, head_y - 1], fill=(10, 10, 10))
    draw.ellipse([cx + 3, head_y - 4, cx + 5, head_y - 1], fill=(10, 10, 10))

    # === 触角（短，锤状） ===
    draw.line([(cx - 3, head_y - 5), (cx - 6, head_y - 10)], fill=(30, 30, 30), width=1)
    draw.line([(cx + 3, head_y - 5), (cx + 6, head_y - 10)], fill=(30, 30, 30), width=1)
    # 触角末端加粗
    draw.ellipse([cx - 7, head_y - 12, cx - 5, head_y - 10], fill=(30, 30, 30))
    draw.ellipse([cx + 5, head_y - 12, cx + 7, head_y - 10], fill=(30, 30, 30))


def draw_caterpillar(draw, w, h, frame, angle):
    """毛毛虫 - 深绿色分节身体，蠕动感

    标志特征：明显分节的圆柱形身体，每节有深浅交替的绿色，
    头部较大有触角和眼睛，身体有细微的绒毛感
    """
    cx, cy = w // 2, h // 2
    num_segments = 7
    seg_w = 9
    seg_h = 10
    start_x = cx - (num_segments * seg_w) // 2

    # === 身体分节（从尾到头，逐节绘制） ===
    for i in range(num_segments):
        sx = start_x + i * seg_w
        # 蠕动波浪效果
        wave = 3 * math.sin((i + frame * 0.5) * 0.8)
        base_y = cy + wave

        # 每节颜色深浅交替
        if i % 2 == 0:
            body_color = (50, 130, 40)
            dark_color = (35, 100, 28)
            highlight = (80, 170, 65)
        else:
            body_color = (60, 150, 48)
            dark_color = (40, 110, 32)
            highlight = (90, 185, 72)

        # 本节椭圆
        draw.ellipse(
            [sx, base_y - seg_h // 2, sx + seg_w - 1, base_y + seg_h // 2],
            fill=body_color, outline=dark_color
        )
        # 高光
        draw.ellipse(
            [sx + 2, base_y - seg_h // 2 + 1, sx + 5, base_y - seg_h // 2 + 4],
            fill=highlight
        )
        # 腹足（每节下方小突起）
        if i > 0 and i < num_segments - 1:
            foot_y = base_y + seg_h // 2 - 1
            draw.ellipse([sx + 2, foot_y, sx + 4, foot_y + 3], fill=(45, 120, 35))
            draw.ellipse([sx + seg_w - 5, foot_y, sx + seg_w - 3, foot_y + 3], fill=(45, 120, 35))

    # === 头部（较大，深绿色） ===
    head_x = start_x + num_segments * seg_w
    head_r = 7
    draw.ellipse(
        [head_x - 2, cy - head_r, head_x + head_r * 2, cy + head_r],
        fill=(40, 100, 30), outline=(30, 80, 22)
    )
    # 头部高光
    draw.ellipse(
        [head_x, cy - head_r + 1, head_x + 4, cy - head_r + 4],
        fill=(70, 150, 55)
    )
    # 眼睛（较大，有神）
    draw.ellipse([head_x + head_r - 2, cy - 5, head_x + head_r + 2, cy - 1], fill=(15, 15, 15))
    draw.ellipse([head_x + head_r - 1, cy - 4, head_x + head_r, cy - 2], fill=(255, 255, 255))
    # 触角（短小）
    draw.line([(head_x + head_r - 1, cy - head_r), (head_x + head_r + 3, cy - head_r - 5)],
              fill=(35, 90, 25), width=1)
    draw.line([(head_x + head_r + 1, cy - head_r), (head_x + head_r + 5, cy - head_r - 4)],
              fill=(35, 90, 25), width=1)

    # === 绒毛感（身体两侧细线） ===
    for i in range(num_segments):
        sx = start_x + i * seg_w + seg_w // 2
        wave = 3 * math.sin((i + frame * 0.5) * 0.8)
        base_y = cy + wave
        # 上方绒毛
        draw.line([(sx, base_y - seg_h // 2), (sx, base_y - seg_h // 2 - 3)],
                  fill=(70, 160, 55), width=1)
        # 下方绒毛
        draw.line([(sx, base_y + seg_h // 2), (sx, base_y + seg_h // 2 + 2)],
                  fill=(50, 130, 38), width=1)


def draw_cricket(draw, w, h, frame, angle):
    """蟋蟀 - 棕色身体+长触角+强壮后腿

    标志特征：扁平棕色身体，超长丝状触角，
    强壮的跳跃后腿（明显弯曲），翅膀有纹理
    """
    cx, cy = w // 2, h // 2

    # === 后腿（强壮，先画） ===
    leg_color = (100, 70, 35)
    leg_dark = (80, 55, 25)
    kick = 4 if frame % 2 == 0 else 0
    # 左后腿（分段绘制，更自然的关节）
    draw.line([(cx - 8, cy + 8), (cx - 16, cy + 14 + kick)], fill=leg_dark, width=3)
    draw.line([(cx - 16, cy + 14 + kick), (cx - 22, cy + 10 + kick)], fill=leg_color, width=2)
    draw.line([(cx - 22, cy + 10 + kick), (cx - 24, cy + 14 + kick)], fill=leg_color, width=1)
    # 右后腿
    draw.line([(cx + 8, cy + 8), (cx + 16, cy + 14 + kick)], fill=leg_dark, width=3)
    draw.line([(cx + 16, cy + 14 + kick), (cx + 22, cy + 10 + kick)], fill=leg_color, width=2)
    draw.line([(cx + 22, cy + 10 + kick), (cx + 24, cy + 14 + kick)], fill=leg_color, width=1)
    # 后腿关节标记
    draw.ellipse([cx - 17, cy + 12 + kick, cx - 15, cy + 15 + kick], fill=leg_dark)
    draw.ellipse([cx + 15, cy + 12 + kick, cx + 17, cy + 15 + kick], fill=leg_dark)

    # === 中腿和前腿（细，带关节） ===
    mid_leg_color = (90, 62, 30)
    # 中腿
    draw.line([(cx - 10, cy + 2), (cx - 15, cy + 6)], fill=mid_leg_color, width=1)
    draw.line([(cx - 15, cy + 6), (cx - 17, cy + 10)], fill=mid_leg_color, width=1)
    draw.line([(cx + 10, cy + 2), (cx + 15, cy + 6)], fill=mid_leg_color, width=1)
    draw.line([(cx + 15, cy + 6), (cx + 17, cy + 10)], fill=mid_leg_color, width=1)
    # 前腿
    draw.line([(cx - 8, cy - 4), (cx - 13, cy)], fill=mid_leg_color, width=1)
    draw.line([(cx - 13, cy), (cx - 15, cy + 4)], fill=mid_leg_color, width=1)
    draw.line([(cx + 8, cy - 4), (cx + 13, cy)], fill=mid_leg_color, width=1)
    draw.line([(cx + 13, cy), (cx + 15, cy + 4)], fill=mid_leg_color, width=1)

    # === 身体（扁平椭圆，棕色渐变，更精细） ===
    body_rx, body_ry = 13, 9
    # 底色
    _draw_gradient_ellipse(
        draw,
        (cx - body_rx, cy - body_ry, cx + body_rx, cy + body_ry),
        color_center=(160, 118, 58),
        color_edge=(105, 75, 38),
        steps=14
    )
    # 身体轮廓
    draw.ellipse(
        [cx - body_rx, cy - body_ry, cx + body_rx, cy + body_ry],
        outline=(90, 65, 30)
    )

    # === 翅膀纹理（覆盖在身体上，更精细） ===
    wing_color = (135, 98, 48)
    wing_dark = (115, 82, 38)
    # 左翅轮廓
    draw.arc(
        [cx - body_rx + 1, cy - body_ry, cx - 1, cy + 3],
        start=180, end=360, fill=wing_color, width=1
    )
    # 右翅轮廓
    draw.arc(
        [cx + 1, cy - body_ry, cx + body_rx - 1, cy + 3],
        start=180, end=360, fill=wing_color, width=1
    )
    # 翅脉线条（更自然的弧形）
    draw.line([(cx - 7, cy - 3), (cx - 3, cy - 6)], fill=(145, 108, 52), width=1)
    draw.line([(cx + 7, cy - 3), (cx + 3, cy - 6)], fill=(145, 108, 52), width=1)
    draw.line([(cx - 5, cy - 1), (cx - 1, cy - 5)], fill=(140, 102, 48), width=1)
    draw.line([(cx + 5, cy - 1), (cx + 1, cy - 5)], fill=(140, 102, 48), width=1)
    # 翅膀高光
    draw.ellipse([cx - 8, cy - 7, cx - 4, cy - 5], fill=(175, 130, 65, 180))
    draw.ellipse([cx + 4, cy - 7, cx + 8, cy - 5], fill=(175, 130, 65, 180))

    # === 头部（更圆润，细节更丰富） ===
    head_y = cy - body_ry - 4
    draw.ellipse(
        [cx - 6, head_y - 5, cx + 6, head_y + 5],
        fill=(115, 82, 40), outline=(88, 62, 30)
    )
    # 头部高光
    draw.ellipse([cx - 4, head_y - 3, cx + 1, head_y - 1], fill=(140, 100, 50))

    # 眼睛（大而突出，有神）
    draw.ellipse([cx - 6, head_y - 3, cx - 2, head_y + 2], fill=(20, 15, 10))
    draw.ellipse([cx + 2, head_y - 3, cx + 6, head_y + 2], fill=(20, 15, 10))
    # 眼睛高光（更明显）
    draw.ellipse([cx - 5, head_y - 2, cx - 3, head_y], fill=(70, 55, 35))
    draw.ellipse([cx + 3, head_y - 2, cx + 5, head_y], fill=(70, 55, 35))

    # === 触角（超长丝状，蟋蟀最大特征，更自然的弯曲） ===
    ant_color = (78, 55, 26)
    # 左触角：S形弯曲
    draw.line([(cx - 3, head_y - 5), (cx - 7, head_y - 12)], fill=ant_color, width=1)
    draw.line([(cx - 7, head_y - 12), (cx - 10, head_y - 18)], fill=ant_color, width=1)
    draw.line([(cx - 10, head_y - 18), (cx - 13, head_y - 24)], fill=ant_color, width=1)
    draw.line([(cx - 13, head_y - 24), (cx - 15, head_y - 28)], fill=ant_color, width=1)
    # 右触角
    draw.line([(cx + 3, head_y - 5), (cx + 7, head_y - 12)], fill=ant_color, width=1)
    draw.line([(cx + 7, head_y - 12), (cx + 10, head_y - 18)], fill=ant_color, width=1)
    draw.line([(cx + 10, head_y - 18), (cx + 13, head_y - 24)], fill=ant_color, width=1)
    draw.line([(cx + 13, head_y - 24), (cx + 15, head_y - 28)], fill=ant_color, width=1)

    # === 口器（更精细） ===
    draw.line([(cx - 2, head_y + 4), (cx - 3, head_y + 7)], fill=(82, 58, 30), width=1)
    draw.line([(cx + 2, head_y + 4), (cx + 3, head_y + 7)], fill=(82, 58, 30), width=1)
    draw.line([(cx, head_y + 4), (cx, head_y + 6)], fill=(75, 52, 25), width=1)


def draw_beetle(draw, w, h, frame, angle):
    """甲虫 - 深棕/深紫色+金属光泽甲壳

    标志特征：厚重的深色甲壳有金属光泽反射，
    大型头部有明显大颚，身体宽阔厚重
    """
    cx, cy = w // 2, h // 2

    # === 腿（6条，粗壮，带动画） ===
    leg_color = (35, 25, 20)
    leg_positions = [
        ((cx - 10, cy - 4), (cx - 20, cy - 12)),
        ((cx + 10, cy - 4), (cx + 20, cy - 12)),
        ((cx - 14, cy + 4), (cx - 24, cy + 10)),
        ((cx + 14, cy + 4), (cx + 24, cy + 10)),
        ((cx - 12, cy + 10), (cx - 22, cy + 18)),
        ((cx + 12, cy + 10), (cx + 22, cy + 18)),
    ]
    leg_wave = 2 if frame % 2 == 0 else -2
    for (x1, y1), (x2, y2) in leg_positions:
        my = y2 + leg_wave
        draw.line([(x1, y1), (x2, my)], fill=leg_color, width=2)
        # 爪子
        draw.line([(x2, my), (x2 + 2, my + 3)], fill=leg_color, width=1)

    # === 身体（厚重甲壳，深紫棕色） ===
    body_rx, body_ry = 17, 15
    # 底色
    draw.ellipse(
        [cx - body_rx, cy - body_ry, cx + body_rx, cy + body_ry],
        fill=(35, 25, 30), outline=(25, 18, 22)
    )
    # 金属光泽渐变
    _draw_gradient_ellipse(
        draw,
        (cx - body_rx + 2, cy - body_ry + 2, cx + body_rx - 2, cy + body_ry - 2),
        color_center=(75, 60, 80),
        color_edge=(40, 30, 38),
        steps=15
    )
    # 紫色金属反光
    _draw_gradient_ellipse(
        draw,
        (cx - 8, cy - 12, cx + 2, cy - 6),
        color_center=(100, 70, 120),
        color_edge=(60, 45, 70),
        steps=8
    )

    # === 甲壳中线 ===
    draw.line(
        [(cx, cy - body_ry + 2), (cx, cy + body_ry - 2)],
        fill=(20, 14, 18), width=2
    )

    # === 甲壳纹理（凹槽线） ===
    for i in range(-2, 3):
        if i == 0:
            continue
        offset = i * 4
        draw.arc(
            [cx + offset - 8, cy - 10, cx + offset + 8, cy + 10],
            start=250, end=290, fill=(50, 38, 55), width=1
        )

    # === 金属光泽高光（随帧偏移） ===
    hl_x = frame * 3
    draw.ellipse(
        [cx - 12 + hl_x, cy - 13, cx - 6 + hl_x, cy - 9],
        fill=(110, 85, 130, 160)
    )

    # === 头部（宽大，有大颚） ===
    head_y = cy - body_ry - 5
    draw.ellipse(
        [cx - 8, head_y - 6, cx + 8, head_y + 6],
        fill=(30, 22, 28), outline=(20, 15, 18)
    )
    # 头部金属光泽
    draw.ellipse(
        [cx - 5, head_y - 4, cx + 2, head_y - 1],
        fill=(65, 50, 72)
    )
    # 眼睛（两侧）
    draw.ellipse([cx - 8, head_y - 3, cx - 5, head_y + 1], fill=(10, 8, 10))
    draw.ellipse([cx + 5, head_y - 3, cx + 8, head_y + 1], fill=(10, 8, 10))

    # === 大颚（甲虫标志性特征） ===
    mandible_color = (45, 32, 25)
    # 左大颚
    draw.line([(cx - 5, head_y - 5), (cx - 10, head_y - 10)], fill=mandible_color, width=2)
    draw.line([(cx - 10, head_y - 10), (cx - 8, head_y - 12)], fill=mandible_color, width=2)
    # 右大颚
    draw.line([(cx + 5, head_y - 5), (cx + 10, head_y - 10)], fill=mandible_color, width=2)
    draw.line([(cx + 10, head_y - 10), (cx + 8, head_y - 12)], fill=mandible_color, width=2)

    # === 触角（短，锤状/锯齿状） ===
    draw.line([(cx - 4, head_y - 5), (cx - 7, head_y - 9)], fill=(40, 30, 35), width=1)
    draw.line([(cx - 7, head_y - 9), (cx - 5, head_y - 11)], fill=(40, 30, 35), width=1)
    draw.line([(cx + 4, head_y - 5), (cx + 7, head_y - 9)], fill=(40, 30, 35), width=1)
    draw.line([(cx + 7, head_y - 9), (cx + 5, head_y - 11)], fill=(40, 30, 35), width=1)


def draw_dragonfly(draw, w, h, frame, angle):
    """蜻蜓 - 蓝色身体+透明翅膀

    标志特征：细长的蓝色腹部，两对宽大透明翅膀，
    巨大的复眼占据头部大部分，翅膀有精细翅脉
    """
    cx, cy = w // 2, h // 2

    # === 翅膀（先画，在身体下面） ===
    wing_beat = frame * 3
    # 透明翅膀底色
    wing_base = (170, 210, 255, 140)
    wing_outline = (120, 170, 220, 180)
    wing_vein = (100, 150, 200, 160)

    # 上翅（大）
    draw.polygon(
        [(cx - 3, cy - 6), (cx - 22, cy - 14 - wing_beat),
         (cx - 20, cy - 4 - wing_beat), (cx - 2, cy - 2)],
        fill=wing_base, outline=wing_outline
    )
    draw.polygon(
        [(cx + 3, cy - 6), (cx + 22, cy - 14 - wing_beat),
         (cx + 20, cy - 4 - wing_beat), (cx + 2, cy - 2)],
        fill=wing_base, outline=wing_outline
    )
    # 下翅（略小）
    draw.polygon(
        [(cx - 3, cy - 2), (cx - 18, cy - 6 + wing_beat),
         (cx - 16, cy + 2 + wing_beat), (cx - 2, cy + 2)],
        fill=(160, 200, 250, 130), outline=wing_outline
    )
    draw.polygon(
        [(cx + 3, cy - 2), (cx + 18, cy - 6 + wing_beat),
         (cx + 16, cy + 2 + wing_beat), (cx + 2, cy + 2)],
        fill=(160, 200, 250, 130), outline=wing_outline
    )
    # 翅脉线条
    draw.line([(cx - 3, cy - 4), (cx - 16, cy - 10 - wing_beat)], fill=wing_vein, width=1)
    draw.line([(cx + 3, cy - 4), (cx + 16, cy - 10 - wing_beat)], fill=wing_vein, width=1)
    draw.line([(cx - 2, cy - 2), (cx - 12, cy - 4 + wing_beat)], fill=wing_vein, width=1)
    draw.line([(cx + 2, cy - 2), (cx + 12, cy - 4 + wing_beat)], fill=wing_vein, width=1)

    # === 身体（细长腹部，蓝色渐变） ===
    # 胸部
    draw.ellipse(
        [cx - 5, cy - 8, cx + 5, cy + 2],
        fill=(35, 90, 160), outline=(28, 70, 130)
    )
    # 腹部（细长，分节）
    abdomen_segments = 5
    for i in range(abdomen_segments):
        seg_y = cy + 3 + i * 5
        seg_w = 4 - i * 0.3  # 逐渐变细
        alpha = 255 - i * 10
        color = (40 + i * 5, 100 + i * 8, 180 + i * 5)
        draw.ellipse(
            [cx - seg_w, seg_y, cx + seg_w, seg_y + 5],
            fill=color, outline=(30, 80, 140)
        )
        # 节段分界线
        draw.line([(cx - seg_w + 1, seg_y), (cx + seg_w - 1, seg_y)],
                  fill=(30, 75, 130), width=1)

    # === 腹部末端（尾鳃） ===
    tail_y = cy + 3 + abdomen_segments * 5
    draw.line([(cx - 3, tail_y), (cx - 5, tail_y + 4)], fill=(45, 110, 190), width=1)
    draw.line([(cx + 3, tail_y), (cx + 5, tail_y + 4)], fill=(45, 110, 190), width=1)

    # === 头部（大复眼） ===
    head_y = cy - 14
    # 头部轮廓
    draw.ellipse(
        [cx - 7, head_y - 5, cx + 7, head_y + 5],
        fill=(30, 80, 145)
    )
    # 巨大复眼（蜻蜓最大特征）
    draw.ellipse(
        [cx - 7, head_y - 5, cx - 1, head_y + 2],
        fill=(20, 60, 120), outline=(15, 45, 95)
    )
    draw.ellipse(
        [cx + 1, head_y - 5, cx + 7, head_y + 2],
        fill=(20, 60, 120), outline=(15, 45, 95)
    )
    # 复眼高光
    draw.ellipse([cx - 5, head_y - 3, cx - 3, head_y - 1], fill=(60, 130, 200))
    draw.ellipse([cx + 3, head_y - 3, cx + 5, head_y - 1], fill=(60, 130, 200))

    # === 腿（6条，细长，收拢在胸部下方） ===
    leg_color = (25, 65, 115)
    for i, (dx, dy) in enumerate([
        (-4, -2), (4, -2), (-6, 2), (6, 2), (-5, 6), (5, 6)
    ]):
        draw.line(
            [(cx + dx, cy - 4 + dy), (cx + dx * 2.5, cy + dy + 6)],
            fill=leg_color, width=1
        )


def draw_bee(draw, w, h, frame, angle):
    """蜜蜂 - 黄黑条纹+绒毛质感

    标志特征：毛茸茸的黄黑条纹身体，透明膜质翅膀，
    胸部有密集绒毛，腹部末端有螫针
    """
    cx, cy = w // 2, h // 2

    # === 翅膀（先画，更自然的形状） ===
    wing_beat = frame * 3
    wing_color = (215, 235, 255, 155)
    wing_outline = (175, 200, 235, 185)
    # 左翅（更圆润的形状）
    draw.polygon(
        [(cx - 4, cy - 8), (cx - 14, cy - 16 + wing_beat),
         (cx - 18, cy - 10 + wing_beat), (cx - 16, cy - 2 + wing_beat),
         (cx - 3, cy - 4)],
        fill=wing_color, outline=wing_outline
    )
    # 右翅
    draw.polygon(
        [(cx + 4, cy - 8), (cx + 14, cy - 16 + wing_beat),
         (cx + 18, cy - 10 + wing_beat), (cx + 16, cy - 2 + wing_beat),
         (cx + 3, cy - 4)],
        fill=wing_color, outline=wing_outline
    )
    # 翅脉（更自然的弧线）
    draw.line([(cx - 4, cy - 6), (cx - 10, cy - 12 + wing_beat)], fill=(155, 185, 220, 145), width=1)
    draw.line([(cx - 8, cy - 4), (cx - 14, cy - 8 + wing_beat)], fill=(155, 185, 220, 145), width=1)
    draw.line([(cx + 4, cy - 6), (cx + 10, cy - 12 + wing_beat)], fill=(155, 185, 220, 145), width=1)
    draw.line([(cx + 8, cy - 4), (cx + 14, cy - 8 + wing_beat)], fill=(155, 185, 220, 145), width=1)

    # === 腿（6条，带关节动画） ===
    leg_color = (42, 36, 22)
    leg_wave = 1 if frame % 2 == 0 else -1
    leg_positions = [
        ((cx - 8, cy - 2), (cx - 15, cy - 8)),
        ((cx + 8, cy - 2), (cx + 15, cy - 8)),
        ((cx - 10, cy + 4), (cx - 17, cy + 8 + leg_wave)),
        ((cx + 10, cy + 4), (cx + 17, cy + 8 + leg_wave)),
        ((cx - 8, cy + 10), (cx - 15, cy + 16 + leg_wave)),
        ((cx + 8, cy + 10), (cx + 15, cy + 16 + leg_wave)),
    ]
    for (x1, y1), (x2, y2) in leg_positions:
        draw.line([(x1, y1), (x2, y2)], fill=leg_color, width=1)
        # 腿关节
        draw.ellipse([x2 - 1, y2 - 1, x2 + 1, y2 + 1], fill=leg_color)

    # === 腹部（黄黑条纹，蜜蜂核心特征，更饱满） ===
    body_rx, body_ry = 13, 14
    # 底色（黄色渐变，更鲜艳）
    _draw_gradient_ellipse(
        draw,
        (cx - body_rx, cy - body_ry + 4, cx + body_rx, cy + body_ry + 4),
        color_center=(240, 198, 42),
        color_edge=(195, 155, 28),
        steps=14
    )
    # 身体轮廓
    draw.ellipse(
        [cx - body_rx, cy - body_ry + 4, cx + body_rx, cy + body_ry + 4],
        outline=(180, 140, 22)
    )
    # 黑色条纹（5条横纹，更自然）
    stripe_color = (28, 24, 18)
    for i in range(5):
        stripe_y = cy - 3 + i * 3
        # 条纹宽度随位置变化（中间宽，两端窄）
        width_factor = 1.0 - abs(i - 2) * 0.15
        sw = int((body_rx - 3) * width_factor)
        draw.line(
            [(cx - sw, stripe_y), (cx + sw, stripe_y)],
            fill=stripe_color, width=2
        )
    # 条纹边缘柔化（模拟绒毛覆盖）
    for i in range(5):
        stripe_y = cy - 3 + i * 3
        draw.line(
            [(cx - body_rx + 2, stripe_y - 1), (cx + body_rx - 2, stripe_y - 1)],
            fill=(215, 175, 38), width=1
        )

    # === 胸部（绒毛感，深色，更蓬松） ===
    thorax_cy = cy - 11
    _draw_gradient_ellipse(
        draw,
        (cx - 11, thorax_cy - 7, cx + 11, thorax_cy + 7),
        color_center=(85, 68, 32),
        color_edge=(58, 45, 20),
        steps=12
    )
    # 胸部轮廓
    draw.ellipse(
        [cx - 11, thorax_cy - 7, cx + 11, thorax_cy + 7],
        outline=(50, 38, 16)
    )
    # 绒毛效果（更密集，更自然）
    import random
    random.seed(42)  # 固定种子保证一致性
    for _ in range(18):
        fx = cx + random.randint(-9, 9)
        fy = thorax_cy + random.randint(-6, 6)
        flen = random.randint(1, 3)
        draw.line([(fx, fy), (fx + 1, fy - flen)], fill=(105, 85, 38), width=1)

    # === 螫针（腹部末端，更明显） ===
    draw.line([(cx, cy + body_ry + 4), (cx - 1, cy + body_ry + 7)], fill=(32, 28, 16), width=1)
    draw.line([(cx, cy + body_ry + 4), (cx + 1, cy + body_ry + 7)], fill=(32, 28, 16), width=1)

    # === 头部（更圆润，细节更丰富） ===
    head_y = thorax_cy - 9
    draw.ellipse(
        [cx - 7, head_y - 6, cx + 7, head_y + 6],
        fill=(38, 32, 22), outline=(28, 22, 14)
    )
    # 头部高光
    draw.ellipse([cx - 4, head_y - 4, cx + 1, head_y - 2], fill=(55, 48, 32))

    # 眼睛（两侧，较大，有神）
    draw.ellipse([cx - 7, head_y - 3, cx - 3, head_y + 2], fill=(15, 12, 8))
    draw.ellipse([cx + 3, head_y - 3, cx + 7, head_y + 2], fill=(15, 12, 8))
    # 眼睛高光（更明显）
    draw.ellipse([cx - 6, head_y - 2, cx - 4, head_y], fill=(55, 48, 32))
    draw.ellipse([cx + 4, head_y - 2, cx + 6, head_y], fill=(55, 48, 32))

    # === 触角（短，膝状，更自然） ===
    ant_color = (38, 32, 20)
    draw.line([(cx - 2, head_y - 5), (cx - 5, head_y - 9)], fill=ant_color, width=1)
    draw.line([(cx - 5, head_y - 9), (cx - 4, head_y - 12)], fill=ant_color, width=1)
    draw.line([(cx + 2, head_y - 5), (cx + 5, head_y - 9)], fill=ant_color, width=1)
    draw.line([(cx + 5, head_y - 9), (cx + 4, head_y - 12)], fill=ant_color, width=1)
    # 触角末端加粗
    draw.ellipse([cx - 5, head_y - 13, cx - 3, head_y - 11], fill=ant_color)
    draw.ellipse([cx + 3, head_y - 13, cx + 5, head_y - 11], fill=ant_color)


DRAW_FUNCTIONS = {
    "ladybug": draw_ladybug,
    "caterpillar": draw_caterpillar,
    "cricket": draw_cricket,
    "beetle": draw_beetle,
    "dragonfly": draw_dragonfly,
    "bee": draw_bee,
}


def rotate_image(img, angle):
    """旋转图像，保持透明背景"""
    if angle == 0:
        return img
    return img.rotate(-angle, resample=Image.BICUBIC, expand=False)


def generate_insect_sprites(insect_name, config):
    """为一种昆虫生成所有方向和帧的精灵图"""
    w, h = config["size"]
    frames = config["frames"]
    draw_func = DRAW_FUNCTIONS[insect_name]

    out_dir = os.path.join(BASE_DIR, insect_name)
    os.makedirs(out_dir, exist_ok=True)

    count = 0
    for direction in DIRECTIONS:
        angle = DIR_ANGLES[direction]
        for frame_idx in range(frames):
            # 创建透明画布（增大尺寸以容纳旋转后的边角）
            canvas_size = max(w, h) * 2
            img = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)

            # 在画布中心绘制昆虫（朝上为基准）
            offset_x = (canvas_size - w) // 2
            offset_y = (canvas_size - h) // 2

            # 调整绘制坐标到画布中心
            draw_func(draw, w, h, frame_idx, angle)

            # 旋转到目标方向
            if angle != 0:
                img = rotate_image(img, angle)

            # 裁剪到内容边界
            bbox = img.getbbox()
            if bbox:
                img = img.crop(bbox)

            # 缩放到目标尺寸
            img = img.resize((w, h), Image.LANCZOS)

            # 保存
            filename = f"{insect_name}_{direction}_{frame_idx + 1}.png"
            img.save(os.path.join(out_dir, filename))
            count += 1

    return count


def main():
    total = 0
    for name, config in INSECTS.items():
        count = generate_insect_sprites(name, config)
        print(f"  {name}: {count} sprites ({config['size'][0]}x{config['size'][1]}, {config['frames']} frames)")
        total += count

    print(f"\n总计: {total} 个精灵图")
    print("目录结构:")
    for name in INSECTS:
        path = os.path.join(BASE_DIR, name)
        files = [f for f in os.listdir(path) if f.endswith(".png")]
        print(f"  {name}/ ({len(files)} files)")


if __name__ == "__main__":
    main()
