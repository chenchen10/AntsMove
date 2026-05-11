#!/usr/bin/env python3
"""
美术资源生成脚本 — 生成 PRD v1.0 中 G-美术专家 负责的全部素材

素材清单：
1. guide_overlay.png  — 新手引导遮罩层（1200×700，半透明黑色，中央镂空）
2. guide_circle.png   — 高亮圆圈（180×180，金色描边+柔光）
3. item_speed.png     — 加速药水图标（128×128）
4. item_double.png    — 双倍收益券图标（128×128）
5. item_stun.png      — 干扰粉尘图标（128×128）
6. star_full.png      — 满星图标（128×128）
7. star_empty.png     — 空星图标（128×128）
"""

import os
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import math

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
IMAGES_DIR = os.path.join(PROJECT_DIR, 'images')

# 项目配色（来自 config.py）
ACCENT_GOLD = (218, 165, 32)
ACCENT_BLUE = (70, 130, 220)
ACCENT_RED = (220, 80, 70)
DARK_BROWN = (74, 56, 43)
OUTLINE_COLOR = (43, 27, 16)  # #2B1B10 深色描边
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 700


def draw_star(draw, cx, cy, outer_r, inner_r, fill_color, outline_color=None, outline_width=2):
    """绘制五角星"""
    points = []
    for i in range(10):
        angle = math.radians(i * 36 - 90)
        r = outer_r if i % 2 == 0 else inner_r
        x = cx + r * math.cos(angle)
        y = cy + r * math.sin(angle)
        points.append((x, y))
    if fill_color:
        draw.polygon(points, fill=fill_color)
    if outline_color:
        draw.polygon(points, outline=outline_color, width=outline_width)


def generate_guide_overlay():
    """生成新手引导遮罩层 — 半透明黑色全屏蒙版"""
    print("生成 guide_overlay.png ...")
    img = Image.new('RGBA', (SCREEN_WIDTH, SCREEN_HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 全屏半透明黑色覆盖（alpha=160）
    overlay = Image.new('RGBA', (SCREEN_WIDTH, SCREEN_HEIGHT), (0, 0, 0, 160))
    img = Image.alpha_composite(img, overlay)

    img.save(os.path.join(IMAGES_DIR, 'guide', 'guide_overlay.png'))
    print("  ✓ guide_overlay.png")


def generate_guide_circle():
    """生成高亮圆圈 — 金色描边+柔光效果"""
    print("生成 guide_circle.png ...")
    size = 180
    # 创建比目标稍大的画布以容纳柔光
    canvas_size = size + 40
    img = Image.new('RGBA', (canvas_size, canvas_size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    cx, cy = canvas_size // 2, canvas_size // 2

    # 外层柔光（白色 glow，低透明度）
    for r_offset in range(15, 0, -1):
        glow_alpha = int(40 * (1 - r_offset / 15))
        glow_r = size // 2 + r_offset
        glow_color = (255, 255, 255, glow_alpha)
        draw.ellipse(
            [cx - glow_r, cy - glow_r, cx + glow_r, cy + glow_r],
            fill=glow_color
        )

    # 金色描边圆圈（3px宽）
    circle_r = size // 2
    for w in range(3):
        r = circle_r - w
        # 金色外层
        draw.ellipse(
            [cx - r, cy - r, cx + r, cy + r],
            outline=(ACCENT_GOLD[0], ACCENT_GOLD[1], ACCENT_GOLD[2], 200),
            width=1
        )

    # 内部虚化边缘
    for w in range(2):
        r = circle_r - 3 - w
        inner_alpha = 150 - w * 50
        draw.ellipse(
            [cx - r, cy - r, cx + r, cy + r],
            outline=(255, 255, 255, inner_alpha),
            width=1
        )

    img.save(os.path.join(IMAGES_DIR, 'guide', 'guide_circle.png'))
    print("  ✓ guide_circle.png")


def generate_item_speed():
    """生成加速药水图标 — 蓝色药水瓶"""
    print("生成 item_speed.png ...")
    size = 128
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    cx, cy = size // 2, size // 2

    # 瓶身（圆角矩形）
    body_color = ACCENT_BLUE
    body_dark = (50, 100, 180)
    draw.rounded_rectangle(
        [cx - 22, cy - 15, cx + 22, cy + 35],
        radius=10,
        fill=body_color,
        outline=OUTLINE_COLOR,
        width=3
    )

    # 瓶身内液体高光
    draw.rounded_rectangle(
        [cx - 18, cy - 10, cx - 5, cy + 10],
        radius=4,
        fill=(120, 170, 240, 100)
    )

    # 瓶颈
    draw.rectangle(
        [cx - 10, cy - 25, cx + 10, cy - 15],
        fill=body_dark,
        outline=OUTLINE_COLOR,
        width=2
    )

    # 瓶塞
    draw.rounded_rectangle(
        [cx - 12, cy - 32, cx + 12, cy - 24],
        radius=3,
        fill=(180, 140, 60),
        outline=OUTLINE_COLOR,
        width=2
    )

    # 速度闪电符号
    flash_color = (255, 255, 100)
    flash_points = [
        (cx + 2, cy - 8),
        (cx - 8, cy + 10),
        (cx + 1, cy + 6),
        (cx - 2, cy + 25),
        (cx + 8, cy + 5),
        (cx - 1, cy + 9),
    ]
    draw.polygon(flash_points, fill=flash_color, outline=OUTLINE_COLOR, width=1)

    # 底部圆弧
    draw.ellipse(
        [cx - 22, cy + 18, cx + 22, cy + 38],
        fill=body_color,
        outline=OUTLINE_COLOR,
        width=2
    )

    img.save(os.path.join(IMAGES_DIR, 'item', 'item_speed.png'))
    print("  ✓ item_speed.png")


def generate_item_double():
    """生成双倍收益券图标 — 金色票据"""
    print("生成 item_double.png ...")
    size = 128
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    cx, cy = size // 2, size // 2

    # 票据主体（圆角矩形）
    draw.rounded_rectangle(
        [cx - 35, cy - 25, cx + 35, cy + 25],
        radius=8,
        fill=(255, 230, 120),
        outline=OUTLINE_COLOR,
        width=3
    )

    # 票据内框
    draw.rounded_rectangle(
        [cx - 30, cy - 20, cx + 30, cy + 20],
        radius=5,
        fill=(255, 240, 160),
        outline=ACCENT_GOLD,
        width=1
    )

    # "×2" 文字效果（用形状模拟）
    # "×" 交叉线
    draw.line([(cx - 14, cy - 10), (cx - 2, cy + 2)], fill=ACCENT_GOLD, width=4)
    draw.line([(cx - 14, cy + 2), (cx - 2, cy - 10)], fill=ACCENT_GOLD, width=4)

    # "2" 数字
    # 用弧线和直线模拟2的形状
    draw.arc([cx + 0, cy - 14, cx + 22, cy + 4], 180, 360, fill=ACCENT_GOLD, width=4)
    draw.line([(cx + 22, cy - 5), (cx + 4, cy + 10)], fill=ACCENT_GOLD, width=4)
    draw.line([(cx + 4, cy + 10), (cx + 22, cy + 10)], fill=ACCENT_GOLD, width=4)

    # 左侧装饰虚线（撕票线）
    for y_pos in range(cy - 18, cy + 18, 8):
        draw.line([(cx - 38, y_pos), (cx - 36, y_pos + 4)], fill=OUTLINE_COLOR, width=1)

    # 金币装饰
    draw.ellipse([cx + 20, cy - 20, cx + 32, cy - 8], fill=ACCENT_GOLD, outline=OUTLINE_COLOR, width=1)
    draw.ellipse([cx + 22, cy - 18, cx + 30, cy - 10], fill=(255, 215, 60))

    img.save(os.path.join(IMAGES_DIR, 'item', 'item_double.png'))
    print("  ✓ item_double.png")


def generate_item_stun():
    """生成干扰粉尘图标 — 红色粉尘云"""
    print("生成 item_stun.png ...")
    size = 128
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    cx, cy = size // 2, size // 2

    # 粉尘云主体（多个重叠圆）
    dust_color = ACCENT_RED
    dust_light = (240, 130, 110)
    dust_dark = (180, 60, 50)

    # 主云团
    draw.ellipse([cx - 20, cy - 18, cx + 12, cy + 12], fill=dust_color, outline=OUTLINE_COLOR, width=2)
    draw.ellipse([cx - 8, cy - 22, cx + 24, cy + 8], fill=dust_light, outline=OUTLINE_COLOR, width=2)
    draw.ellipse([cx - 15, cy - 5, cx + 18, cy + 22], fill=dust_dark, outline=OUTLINE_COLOR, width=2)

    # 小粉尘粒子
    particles = [
        (cx - 28, cy - 12, 5), (cx + 22, cy - 18, 4),
        (cx + 28, cy + 5, 3), (cx - 25, cy + 15, 4),
        (cx + 15, cy + 18, 3), (cx - 10, cy - 25, 3),
    ]
    for px, py, pr in particles:
        draw.ellipse([px - pr, py - pr, px + pr, py + pr],
                     fill=dust_light, outline=OUTLINE_COLOR, width=1)

    # 星星/眩晕符号（×形）
    star_color = (255, 255, 100)
    sx, sy = cx + 5, cy - 5
    draw.line([(sx - 8, sy - 8), (sx + 8, sy + 8)], fill=star_color, width=3)
    draw.line([(sx - 8, sy + 8), (sx + 8, sy - 8)], fill=star_color, width=3)
    # 小星星
    draw.line([(sx - 4, sy - 12), (sx + 4, sy - 4)], fill=star_color, width=2)
    draw.line([(sx + 10, sy - 2), (sx + 16, sy + 4)], fill=star_color, width=2)

    img.save(os.path.join(IMAGES_DIR, 'item', 'item_stun.png'))
    print("  ✓ item_stun.png")


def generate_star_full():
    """生成满星图标 — 金色填充五角星"""
    print("生成 star_full.png ...")
    size = 128
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    cx, cy = size // 2, size // 2

    # 外发光效果
    for r_offset in range(6, 0, -1):
        glow_alpha = int(30 * (1 - r_offset / 6))
        outer_r = 48 + r_offset
        inner_r = 20 + r_offset // 2
        draw_star(draw, cx, cy, outer_r, inner_r,
                  fill_color=(255, 215, 60, glow_alpha))

    # 主星体
    draw_star(draw, cx, cy, 48, 20,
              fill_color=ACCENT_GOLD,
              outline_color=OUTLINE_COLOR,
              outline_width=3)

    # 内部高光（较小的亮星）
    draw_star(draw, cx - 5, cy - 5, 18, 8,
              fill_color=(255, 230, 100, 120),
              outline_color=None)

    img.save(os.path.join(IMAGES_DIR, 'star', 'star_full.png'))
    print("  ✓ star_full.png")


def generate_star_empty():
    """生成空星图标 — 灰色描边空心五角星"""
    print("生成 star_empty.png ...")
    size = 128
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    cx, cy = size // 2, size // 2

    # 半透明填充
    draw_star(draw, cx, cy, 48, 20,
              fill_color=(180, 180, 180, 60),
              outline_color=(180, 180, 180),
              outline_width=3)

    img.save(os.path.join(IMAGES_DIR, 'star', 'star_empty.png'))
    print("  ✓ star_empty.png")


def main():
    print("=" * 50)
    print("蚂蚁抢甜点 — 美术资源生成")
    print("=" * 50)
    print()

    # 确保目录存在
    for subdir in ['guide', 'item', 'star']:
        os.makedirs(os.path.join(IMAGES_DIR, subdir), exist_ok=True)

    # 生成所有素材
    generate_guide_overlay()
    generate_guide_circle()
    generate_item_speed()
    generate_item_double()
    generate_item_stun()
    generate_star_full()
    generate_star_empty()

    print()
    print("=" * 50)
    print("全部素材生成完成！")
    print()
    print("素材清单：")
    print("  images/guide/guide_overlay.png  — 引导遮罩层 (1200×700)")
    print("  images/guide/guide_circle.png   — 高亮圆圈 (220×220)")
    print("  images/item/item_speed.png      — 加速药水图标 (128×128)")
    print("  images/item/item_double.png     — 双倍收益券图标 (128×128)")
    print("  images/item/item_stun.png       — 干扰粉尘图标 (128×128)")
    print("  images/star/star_full.png       — 满星图标 (128×128)")
    print("  images/star/star_empty.png      — 空星图标 (128×128)")
    print("=" * 50)


if __name__ == '__main__':
    main()
