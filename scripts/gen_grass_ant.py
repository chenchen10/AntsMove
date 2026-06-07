#!/usr/bin/env python3
"""生成高质量「普通路边小草蚁」精灵图（256x256 RGBA，俯视角）

视觉设计（V2 - 写实风格）：
- 基于日本黑褐蚁/草蚁的真实体色：深棕绿色调
- 三段式身体：头→胸→腹，清晰体节
- 6条分节长腿（3对），带关节和爪
- 膝状触角（elbowed antennae）
- 复眼（黑色大眼）+ 头部细节
- 大颚（mandibles）
- 甲壳自然光泽（柔和高光）+ 深色轮廓
- 透明背景
"""

from PIL import Image, ImageDraw, ImageFilter
import math
import os

OUT_PATH = os.path.join(os.path.dirname(__file__), '..', 'images', 'ant_processed', 'ant1.png')


def _lerp_color(c1, c2, t):
    return tuple(int(c1[i] + (c2[i] - c1[i]) * max(0, min(1, t))) for i in range(min(len(c1), len(c2))))


def _draw_gradient_ellipse(draw, bbox, color_center, color_edge, steps=28):
    x0, y0, x1, y1 = bbox
    cx_e = (x0 + x1) / 2
    cy_e = (y0 + y1) / 2
    rx = (x1 - x0) / 2
    ry = (y1 - y0) / 2
    for i in range(steps, 0, -1):
        t = i / steps
        color = _lerp_color(color_center, color_edge, t)
        cur_rx = rx * t
        cur_ry = ry * t
        if cur_rx < 0.5 or cur_ry < 0.5:
            continue
        draw.ellipse(
            [cx_e - cur_rx, cy_e - cur_ry, cx_e + cur_rx, cy_e + cur_ry],
            fill=color
        )


def _draw_soft_highlight(draw, cx, cy, rx, ry, base_color, strength=0.35):
    """用亮化版底色画高光，不用纯白"""
    hl = _lerp_color(base_color, (220, 220, 200), strength)
    draw.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=hl)


def _draw_shadow(draw, cx, cy, rx, ry, alpha=50):
    draw.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=(0, 0, 0, alpha))


def _draw_leg(draw, ax, ay, jx, jy, fx, fy, color_dark, color_light):
    """绘制一条完整的腿：大腿（粗）+ 小腿（细）+ 爪"""
    # 大腿
    draw.line([(ax, ay), (jx, jy)], fill=color_dark, width=4)
    # 关节球
    draw.ellipse([jx - 3, jy - 3, jx + 3, jy + 3], fill=color_dark)
    # 小腿
    draw.line([(jx, jy), (fx, fy)], fill=color_light, width=3)
    # 爪尖
    draw.ellipse([fx - 2, fy - 2, fx + 2, fy + 2], fill=color_dark)
    # 小腿上的细毛刺
    mx, my = (jx + fx) / 2, (jy + fy) / 2
    dx_n = fx - jx
    dy_n = fy - jy
    length = math.sqrt(dx_n * dx_n + dy_n * dy_n)
    if length > 1:
        # 垂直方向
        px, py = -dy_n / length, dx_n / length
        draw.line([(mx, my), (mx + px * 4, my + py * 4)], fill=color_light, width=1)
        draw.line([(mx, my), (mx - px * 4, my - py * 4)], fill=color_light, width=1)


def _draw_antennae(draw, head_cx, head_top_y, color_seg1, color_seg2):
    """膝状触角"""
    # 左触角
    b_l = (head_cx - 5, head_top_y)
    e_l = (head_cx - 16, head_top_y - 20)
    t_l = (head_cx - 24, head_top_y - 36)
    draw.line([b_l, e_l], fill=color_seg1, width=3)
    draw.ellipse([e_l[0] - 3, e_l[1] - 3, e_l[0] + 3, e_l[1] + 3], fill=color_seg1)
    draw.line([e_l, t_l], fill=color_seg2, width=2)
    draw.ellipse([t_l[0] - 3, t_l[1] - 3, t_l[0] + 3, t_l[1] + 3], fill=color_seg2)

    # 右触角
    b_r = (head_cx + 5, head_top_y)
    e_r = (head_cx + 16, head_top_y - 20)
    t_r = (head_cx + 24, head_top_y - 36)
    draw.line([b_r, e_r], fill=color_seg1, width=3)
    draw.ellipse([e_r[0] - 3, e_r[1] - 3, e_r[0] + 3, e_r[1] + 3], fill=color_seg1)
    draw.line([e_r, t_r], fill=color_seg2, width=2)
    draw.ellipse([t_r[0] - 3, t_r[1] - 3, t_r[0] + 3, t_r[1] + 3], fill=color_seg2)


def draw_grass_ant(img, frame=0):
    """在给定 Image 上绘制一只高质量小草蚁（俯视角，朝上）"""
    draw = ImageDraw.Draw(img, 'RGBA')
    w, h = img.size
    cx, cy = w // 2, h // 2 + 15  # 整体偏下给触角留空间

    # === 色彩系统（深棕绿色，真实草蚁体色） ===
    ABD_C = (82, 95, 48)         # 腹部中心
    ABD_E = (48, 56, 28)         # 腹部边缘
    ABD_SEG = (42, 50, 24)       # 腹部节段线
    THOR_C = (90, 102, 52)       # 胸部中心
    THOR_E = (55, 64, 32)        # 胸部边缘
    HEAD_C = (78, 88, 42)        # 头部中心
    HEAD_E = (45, 52, 25)        # 头部边缘
    LEG_D = (58, 66, 32)         # 腿深色
    LEG_L = (95, 108, 52)        # 腿浅色
    ANT_C = (52, 60, 28)         # 触角深色
    ANT_T = (70, 80, 40)         # 触角浅色
    EYE_C = (18, 14, 10)         # 眼睛

    # === 腿部位置 ===
    leg_wave = frame % 3
    wave_offsets = [(0, 0), (3, -3), (-2, 2)]
    wdx, wdy = wave_offsets[leg_wave]

    # 前腿（连接胸部上方两侧）
    front = [
        (cx - 14, cy - 24,  cx - 36, cy - 42,  cx - 52, cy - 56),
        (cx + 14, cy - 24,  cx + 36, cy - 42,  cx + 52, cy - 56),
    ]
    # 中腿
    mid = [
        (cx - 18, cy - 6,   cx - 44, cy - 12,  cx - 58, cy - 4),
        (cx + 18, cy - 6,   cx + 44, cy - 12,  cx + 58, cy - 4),
    ]
    # 后腿
    back = [
        (cx - 16, cy + 12,  cx - 40, cy + 22,  cx - 54, cy + 36),
        (cx + 16, cy + 12,  cx + 40, cy + 22,  cx + 54, cy + 36),
    ]

    # === 先画腿（在身体下面） ===
    for legs in [front, mid, back]:
        for ax, ay, jx, jy, fx, fy in legs:
            _draw_leg(draw, ax, ay, jx + wdx, jy + wdy, fx + wdx, fy + wdy, LEG_D, LEG_L)

    # === 腹部 ===
    abd_rx, abd_ry = 42, 48
    abd_cx, abd_cy = cx, cy + 42

    _draw_shadow(draw, abd_cx + 5, abd_cy + 8, abd_rx + 3, abd_ry + 3, 45)
    _draw_gradient_ellipse(
        draw,
        (abd_cx - abd_rx, abd_cy - abd_ry, abd_cx + abd_rx, abd_cy + abd_ry),
        ABD_C, ABD_E, steps=32
    )
    draw.ellipse(
        [abd_cx - abd_rx, abd_cy - abd_ry, abd_cx + abd_rx, abd_cy + abd_ry],
        outline=ABD_E, width=2
    )

    # 腹部节段线
    for i in range(-3, 4):
        seg_y = abd_cy + i * 9
        seg_hw = int(abd_rx * 0.82 * math.cos(i * 0.28))
        if seg_hw > 4:
            draw.arc(
                [abd_cx - seg_hw, seg_y - 3, abd_cx + seg_hw, seg_y + 3],
                start=0, end=180, fill=ABD_SEG, width=1
            )

    # 腹部柔和高光（不用纯白）
    _draw_soft_highlight(draw, abd_cx - 14, abd_cy - 20, 16, 10, ABD_C, 0.30)
    _draw_soft_highlight(draw, abd_cx - 8, abd_cy - 26, 8, 5, ABD_C, 0.20)

    # 腹部末端尖
    tip_y = abd_cy + abd_ry - 4
    draw.polygon(
        [(abd_cx - 7, tip_y - 2), (abd_cx, tip_y + 10), (abd_cx + 7, tip_y - 2)],
        fill=ABD_E
    )

    # === 腹-胸连接（细腰） ===
    waist_y = abd_cy - abd_ry + 6
    draw.ellipse([cx - 8, waist_y - 4, cx + 8, waist_y + 4], fill=THOR_E)
    draw.line([(cx - 6, waist_y), (cx - 7, waist_y - 10)], fill=THOR_E, width=2)
    draw.line([(cx + 6, waist_y), (cx + 7, waist_y - 10)], fill=THOR_E, width=2)

    # === 胸部（三段） ===
    # 第一节（靠近腹部）
    t1_cx, t1_cy = cx, cy - 2
    t1_rx, t1_ry = 20, 16
    _draw_gradient_ellipse(draw, (t1_cx - t1_rx, t1_cy - t1_ry, t1_cx + t1_rx, t1_cy + t1_ry), THOR_C, THOR_E, 22)
    draw.ellipse([t1_cx - t1_rx, t1_cy - t1_ry, t1_cx + t1_rx, t1_cy + t1_ry], outline=THOR_E, width=1)
    _draw_soft_highlight(draw, t1_cx - 6, t1_cy - 6, 9, 5, THOR_C, 0.28)

    # 第二节（中胸）
    t2_cx, t2_cy = cx, cy - 24
    t2_rx, t2_ry = 18, 14
    _draw_gradient_ellipse(draw, (t2_cx - t2_rx, t2_cy - t2_ry, t2_cx + t2_rx, t2_cy + t2_ry), THOR_C, THOR_E, 20)
    draw.ellipse([t2_cx - t2_rx, t2_cy - t2_ry, t2_cx + t2_rx, t2_cy + t2_ry], outline=THOR_E, width=1)
    _draw_soft_highlight(draw, t2_cx - 5, t2_cy - 5, 8, 4, THOR_C, 0.25)

    # 第三节（后胸，靠近头部）
    t3_cx, t3_cy = cx, cy - 40
    t3_rx, t3_ry = 15, 11
    _draw_gradient_ellipse(draw, (t3_cx - t3_rx, t3_cy - t3_ry, t3_cx + t3_rx, t3_cy + t3_ry), THOR_C, THOR_E, 18)
    draw.ellipse([t3_cx - t3_rx, t3_cy - t3_ry, t3_cx + t3_rx, t3_cy + t3_ry], outline=THOR_E, width=1)
    _draw_soft_highlight(draw, t3_cx - 4, t3_cy - 4, 6, 3, THOR_C, 0.22)

    # 胸段之间连接
    draw.ellipse([cx - 10, t1_cy - t1_ry - 2, cx + 10, t1_cy - t1_ry + 4], fill=THOR_E)
    draw.ellipse([cx - 9, t2_cy - t2_ry - 2, cx + 9, t2_cy - t2_ry + 4], fill=THOR_E)

    # === 头-胸连接 ===
    draw.line([(cx - 5, t3_cy - t3_ry), (cx - 4, t3_cy - t3_ry - 8)], fill=HEAD_E, width=2)
    draw.line([(cx + 5, t3_cy - t3_ry), (cx + 4, t3_cy - t3_ry - 8)], fill=HEAD_E, width=2)

    # === 头部 ===
    head_cx, head_cy = cx, cy - 58
    head_r = 24

    _draw_shadow(draw, head_cx + 4, head_cy + 5, head_r + 2, head_r + 2, 40)
    _draw_gradient_ellipse(
        draw,
        (head_cx - head_r, head_cy - head_r, head_cx + head_r, head_cy + head_r),
        HEAD_C, HEAD_E, 26
    )
    draw.ellipse(
        [head_cx - head_r, head_cy - head_r, head_cx + head_r, head_cy + head_r],
        outline=HEAD_E, width=2
    )
    _draw_soft_highlight(draw, head_cx - 7, head_cy - 10, 12, 8, HEAD_C, 0.30)

    # === 复眼 ===
    for side, is_l in [('l', True), ('r', False)]:
        sign = -1 if is_l else 1
        ex = head_cx + sign * 15
        ey = head_cy - 2
        # 眼眶
        draw.ellipse([ex - 7, ey - 8, ex + 7, ey + 8], fill=EYE_C)
        # 复眼纹理（几个小点模拟小眼面）
        for ox, oy in [(-2, -3), (0, -4), (2, -3), (-3, 0), (0, -1), (3, 0), (-2, 2), (0, 3)]:
            draw.ellipse([ex + ox - 1, ey + oy - 1, ex + ox + 1, ey + oy + 1], fill=(30, 25, 18))
        # 高光
        draw.ellipse([ex + sign * 2 - 2, ey - 5, ex + sign * 2 + 1, ey - 2], fill=(120, 110, 95, 180))

    # === 单眼（头顶三个小点） ===
    for dx_off in [-4, 0, 4]:
        draw.ellipse(
            [head_cx + dx_off - 1, head_cy - head_r + 5,
             head_cx + dx_off + 1, head_cy - head_r + 7],
            fill=(35, 30, 20)
        )

    # === 大颚 ===
    mand_c = (52, 58, 28)
    # 左
    draw.polygon(
        [(head_cx - 5, head_cy + head_r - 5),
         (head_cx - 16, head_cy + head_r + 4),
         (head_cx - 12, head_cy + head_r + 9),
         (head_cx - 3, head_cy + head_r)],
        fill=mand_c, outline=LEG_D
    )
    # 右
    draw.polygon(
        [(head_cx + 5, head_cy + head_r - 5),
         (head_cx + 16, head_cy + head_r + 4),
         (head_cx + 12, head_cy + head_r + 9),
         (head_cx + 3, head_cy + head_r)],
        fill=mand_c, outline=LEG_D
    )

    # === 触角 ===
    _draw_antennae(draw, head_cx, head_cy - head_r + 3, ANT_C, ANT_T)


def generate():
    size = 256
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw_grass_ant(img, frame=0)

    # 轻微锐化
    img = img.filter(ImageFilter.SHARPEN)

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    img.save(OUT_PATH, 'PNG')
    print(f"✓ 已保存: {OUT_PATH}")
    print(f"  尺寸: {img.size}, 模式: {img.mode}")

    # 64x64 游戏内预览
    preview_path = os.path.join(os.path.dirname(OUT_PATH), '..', 'ant', 'ant1_preview.png')
    preview = img.resize((64, 64), Image.LANCZOS)
    preview.save(preview_path, 'PNG')
    print(f"✓ 预览: {preview_path} (64x64)")

    # 40x40 实际游戏尺寸预览
    game_path = os.path.join(os.path.dirname(OUT_PATH), '..', 'ant', 'ant1_game.png')
    game = img.resize((40, 40), Image.LANCZOS)
    game.save(game_path, 'PNG')
    print(f"✓ 游戏尺寸: {game_path} (40x40)")


if __name__ == '__main__':
    generate()
