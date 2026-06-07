#!/usr/bin/env python3
"""生成「普通路边小草蚁」24帧行走循环动画 Sprite Sheet

动画规格：
- 24帧完整行走循环（对角步态）
- 单帧尺寸：256x256 RGBA，透明背景
- 输出：24张序列帧 + 1张 Sprite Sheet
- 蚂蚁面朝上方，朝向由游戏引擎旋转处理

步态分解（对角步态）：
- 帧 1-6:   左前腿+右后腿 前摆，右前腿+左后腿 支撑
- 帧 7-12:  左前腿+右后腿 落地，右前腿+左后腿 后摆
- 帧 13-18: 右前腿+左后腿 前摆，左前腿+右后腿 支撑
- 帧 19-24: 右前腿+左后腿 落地，左前腿+右后腿 后摆（回到起始位）
"""

from PIL import Image, ImageDraw, ImageFilter
import math
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(SCRIPT_DIR, '..', 'images', 'ant_processed', 'ant1_walk')
SHEET_PATH = os.path.join(SCRIPT_DIR, '..', 'images', 'ant_processed', 'ant1_walk_sheet.png')
FRAME_COUNT = 24
SIZE = 256


def _lerp(c1, c2, t):
    t = max(0.0, min(1.0, t))
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(min(len(c1), len(c2))))


def _draw_gradient_ellipse(draw, bbox, c_center, c_edge, steps=28):
    x0, y0, x1, y1 = bbox
    cx_e = (x0 + x1) / 2
    cy_e = (y0 + y1) / 2
    rx = (x1 - x0) / 2
    ry = (y1 - y0) / 2
    for i in range(steps, 0, -1):
        t = i / steps
        color = _lerp(c_center, c_edge, t)
        crx = rx * t
        cry = ry * t
        if crx < 0.5 or cry < 0.5:
            continue
        draw.ellipse([cx_e - crx, cy_e - cry, cx_e + crx, cy_e + cry], fill=color)


def _draw_highlight(draw, cx, cy, rx, ry, base_color, strength=0.35):
    hl = _lerp(base_color, (220, 220, 200), strength)
    draw.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=hl)


def _draw_shadow(draw, cx, cy, rx, ry, alpha=50):
    draw.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=(0, 0, 0, alpha))


def _draw_leg(draw, ax, ay, jx, jy, fx, fy, c_dark, c_light, lifted=False):
    """绘制一条腿。lifted=True 时颜色略浅表示抬起状态"""
    if lifted:
        c_dark = _lerp(c_dark, (130, 140, 80), 0.3)
        c_light = _lerp(c_light, (150, 160, 100), 0.3)
    # 大腿
    draw.line([(ax, ay), (jx, jy)], fill=c_dark, width=4)
    # 关节球
    draw.ellipse([jx - 3, jy - 3, jx + 3, jy + 3], fill=c_dark)
    # 小腿
    draw.line([(jx, jy), (fx, fy)], fill=c_light, width=3)
    # 爪尖
    draw.ellipse([fx - 2, fy - 2, fx + 2, fy + 2], fill=c_dark)
    # 小腿细毛
    mx, my = (jx + fx) / 2, (jy + fy) / 2
    dx_n = fx - jx
    dy_n = fy - jy
    length = math.sqrt(dx_n * dx_n + dy_n * dy_n)
    if length > 1:
        px, py = -dy_n / length, dx_n / length
        draw.line([(mx, my), (mx + px * 4, my + py * 4)], fill=c_light, width=1)
        draw.line([(mx, my), (mx - px * 4, my - py * 4)], fill=c_light, width=1)


def _draw_antennae(draw, head_cx, head_top_y, c_seg, c_tip, frame):
    """膝状触角，带帧动画摆动"""
    # 摆动角度（周期略短于步态，增加自然感）
    phase_l = frame / FRAME_COUNT * 2 * math.pi * 1.15  # 左触角相位
    phase_r = phase_l + 0.52  # 右触角相位差约30°
    amp = 4.0  # 摆动幅度（像素偏移）

    # 左触角
    b_l = (head_cx - 5, head_top_y)
    sway_l = math.sin(phase_l) * amp
    e_l = (head_cx - 16 + sway_l * 0.6, head_top_y - 20)
    t_l = (head_cx - 24 + sway_l, head_top_y - 36)
    draw.line([b_l, e_l], fill=c_seg, width=3)
    draw.ellipse([e_l[0] - 3, e_l[1] - 3, e_l[0] + 3, e_l[1] + 3], fill=c_seg)
    draw.line([e_l, t_l], fill=c_tip, width=2)
    draw.ellipse([t_l[0] - 3, t_l[1] - 3, t_l[0] + 3, t_l[1] + 3], fill=c_tip)

    # 右触角
    b_r = (head_cx + 5, head_top_y)
    sway_r = math.sin(phase_r) * amp
    e_r = (head_cx + 16 + sway_r * 0.6, head_top_y - 20)
    t_r = (head_cx + 24 + sway_r, head_top_y - 36)
    draw.line([b_r, e_r], fill=c_seg, width=3)
    draw.ellipse([e_r[0] - 3, e_r[1] - 3, e_r[0] + 3, e_r[1] + 3], fill=c_seg)
    draw.line([e_r, t_r], fill=c_tip, width=2)
    draw.ellipse([t_r[0] - 3, t_r[1] - 3, t_r[0] + 3, t_r[1] + 3], fill=c_tip)


def _compute_leg_positions(cx, cy, frame):
    """计算24帧中6条腿的关节位置。返回 (front_l, front_r, mid_l, mid_r, back_l, back_r)
    每条腿为 (ax, ay, jx, jy, fx, fy, lifted)
    """
    # 正弦步态：用平滑函数控制腿部前摆/后摆
    # 对角步态：左前+右后 同相，右前+左后 同相（差180°）
    phase = frame / FRAME_COUNT * 2 * math.pi

    # 腿摆动参数
    swing_amp = 18  # 前后摆动幅度（像素）
    lift_amp = 8    # 抬腿幅度（y方向偏移）

    def leg_offset(p, swing_a=swing_amp, lift_a=lift_amp):
        """根据相位返回 (dx, dy, lifted)"""
        dx = math.sin(p) * swing_a
        dy = -abs(math.sin(p)) * lift_a  # 抬腿时向上偏移
        lifted = math.sin(p) > 0.3  # 抬腿判定
        return dx, dy, lifted

    # 基础腿部位置（与 gen_grass_ant.py 一致，胸节两侧出发）
    # 前腿：连接第三节（靠近头部）
    fl_base = (cx - 14, cy - 40)
    fr_base = (cx + 14, cy - 40)
    # 中腿：连接第一节
    ml_base = (cx - 18, cy - 6)
    mr_base = (cx + 18, cy - 6)
    # 后腿：连接腹部上方
    bl_base = (cx - 16, cy + 20)
    br_base = (cx + 16, cy + 20)

    # 对角步态相位
    # 左前 + 右后 = phase
    # 右前 + 左后 = phase + pi
    fl_off = leg_offset(phase)
    br_off = leg_offset(phase)
    fr_off = leg_offset(phase + math.pi)
    ml_off = leg_offset(phase + math.pi * 0.5)   # 中腿相位差90°
    mr_off = leg_offset(phase + math.pi * 1.5)
    bl_off = leg_offset(phase + math.pi)

    def make_leg(base, off, jdx=30, jdy=-10, fdx=48, fdy=6):
        ax, ay = base
        jx = ax + jdx + off[0] * 0.5
        jy = ay + jdy + off[1]
        fx = ax + fdx + off[0]
        fy = ay + fdy + off[1] * 0.3
        return (ax, ay, jx, jy, fx, fy, off[2])

    return (
        make_leg(fl_base, fl_off, -22, -18, -38, -16),
        make_leg(fr_base, fr_off, 22, -18, 38, -16),
        make_leg(ml_base, ml_off, -26, -6, -40, 2),
        make_leg(mr_base, mr_off, 26, -6, 40, 2),
        make_leg(bl_base, bl_off, -24, 10, -38, 16),
        make_leg(br_base, br_off, 24, 10, 38, 16),
    )


def draw_walk_frame(frame):
    """绘制单帧行走蚂蚁，返回 Image"""
    img = Image.new('RGBA', (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img, 'RGBA')
    w, h = img.size
    cx, cy = w // 2, h // 2 + 15

    # 身体微动：随步态有1-2像素上下起伏
    bob = math.sin(frame / FRAME_COUNT * 2 * math.pi * 2) * 1.5  # 双周期微动
    cy += bob

    # === 色彩系统 ===
    ABD_C = (82, 95, 48)
    ABD_E = (48, 56, 28)
    ABD_SEG = (42, 50, 24)
    THOR_C = (90, 102, 52)
    THOR_E = (55, 64, 32)
    HEAD_C = (78, 88, 42)
    HEAD_E = (45, 52, 25)
    LEG_D = (58, 66, 32)
    LEG_L = (95, 108, 52)
    ANT_C = (52, 60, 28)
    ANT_T = (70, 80, 40)
    EYE_C = (18, 14, 10)

    # === 计算腿部位置 ===
    legs = _compute_leg_positions(cx, cy, frame)
    fl, fr, ml, mr, bl, br = legs

    # === 先画腿（在身体下面） ===
    for ax, ay, jx, jy, fx, fy, lifted in [fl, fr, ml, mr, bl, br]:
        _draw_leg(draw, ax, ay, jx, jy, fx, fy, LEG_D, LEG_L, lifted)

    # === 阴影 ===
    _draw_shadow(draw, cx + 5, cy + 58, 44, 14, 45)

    # === 腹部 ===
    abd_rx, abd_ry = 42, 48
    abd_cx, abd_cy = cx, cy + 42

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

    # 腹部高光
    _draw_highlight(draw, abd_cx - 14, abd_cy - 20, 16, 10, ABD_C, 0.30)
    _draw_highlight(draw, abd_cx - 8, abd_cy - 26, 8, 5, ABD_C, 0.20)

    # 腹部末端尖
    tip_y = abd_cy + abd_ry - 4
    draw.polygon(
        [(abd_cx - 7, tip_y - 2), (abd_cx, tip_y + 10), (abd_cx + 7, tip_y - 2)],
        fill=ABD_E
    )

    # === 腹-胸连接 ===
    waist_y = abd_cy - abd_ry + 6
    draw.ellipse([cx - 8, waist_y - 4, cx + 8, waist_y + 4], fill=THOR_E)
    draw.line([(cx - 6, waist_y), (cx - 7, waist_y - 10)], fill=THOR_E, width=2)
    draw.line([(cx + 6, waist_y), (cx + 7, waist_y - 10)], fill=THOR_E, width=2)

    # === 胸部（三段） ===
    t1_cx, t1_cy = cx, cy - 2
    t1_rx, t1_ry = 20, 16
    _draw_gradient_ellipse(draw, (t1_cx - t1_rx, t1_cy - t1_ry, t1_cx + t1_rx, t1_cy + t1_ry), THOR_C, THOR_E, 22)
    draw.ellipse([t1_cx - t1_rx, t1_cy - t1_ry, t1_cx + t1_rx, t1_cy + t1_ry], outline=THOR_E, width=1)
    _draw_highlight(draw, t1_cx - 6, t1_cy - 6, 9, 5, THOR_C, 0.28)

    t2_cx, t2_cy = cx, cy - 24
    t2_rx, t2_ry = 18, 14
    _draw_gradient_ellipse(draw, (t2_cx - t2_rx, t2_cy - t2_ry, t2_cx + t2_rx, t2_cy + t2_ry), THOR_C, THOR_E, 20)
    draw.ellipse([t2_cx - t2_rx, t2_cy - t2_ry, t2_cx + t2_rx, t2_cy + t2_ry], outline=THOR_E, width=1)
    _draw_highlight(draw, t2_cx - 5, t2_cy - 5, 8, 4, THOR_C, 0.25)

    t3_cx, t3_cy = cx, cy - 40
    t3_rx, t3_ry = 15, 11
    _draw_gradient_ellipse(draw, (t3_cx - t3_rx, t3_cy - t3_ry, t3_cx + t3_rx, t3_cy + t3_ry), THOR_C, THOR_E, 18)
    draw.ellipse([t3_cx - t3_rx, t3_cy - t3_ry, t3_cx + t3_rx, t3_cy + t3_ry], outline=THOR_E, width=1)
    _draw_highlight(draw, t3_cx - 4, t3_cy - 4, 6, 3, THOR_C, 0.22)

    # 胸段连接
    draw.ellipse([cx - 10, t1_cy - t1_ry - 2, cx + 10, t1_cy - t1_ry + 4], fill=THOR_E)
    draw.ellipse([cx - 9, t2_cy - t2_ry - 2, cx + 9, t2_cy - t2_ry + 4], fill=THOR_E)

    # === 头-胸连接 ===
    draw.line([(cx - 5, t3_cy - t3_ry), (cx - 4, t3_cy - t3_ry - 8)], fill=HEAD_E, width=2)
    draw.line([(cx + 5, t3_cy - t3_ry), (cx + 4, t3_cy - t3_ry - 8)], fill=HEAD_E, width=2)

    # === 头部 ===
    head_cx, head_cy = cx, cy - 58
    head_r = 24

    _draw_gradient_ellipse(
        draw,
        (head_cx - head_r, head_cy - head_r, head_cx + head_r, head_cy + head_r),
        HEAD_C, HEAD_E, 26
    )
    draw.ellipse(
        [head_cx - head_r, head_cy - head_r, head_cx + head_r, head_cy + head_r],
        outline=HEAD_E, width=2
    )
    _draw_highlight(draw, head_cx - 7, head_cy - 10, 12, 8, HEAD_C, 0.30)

    # === 复眼 ===
    for sign in [-1, 1]:
        ex = head_cx + sign * 15
        ey = head_cy - 2
        draw.ellipse([ex - 7, ey - 8, ex + 7, ey + 8], fill=EYE_C)
        for ox, oy in [(-2, -3), (0, -4), (2, -3), (-3, 0), (0, -1), (3, 0), (-2, 2), (0, 3)]:
            draw.ellipse([ex + ox - 1, ey + oy - 1, ex + ox + 1, ey + oy + 1], fill=(30, 25, 18))
        draw.ellipse([ex + sign * 2 - 2, ey - 5, ex + sign * 2 + 1, ey - 2], fill=(120, 110, 95, 180))

    # === 单眼 ===
    for dx_off in [-4, 0, 4]:
        draw.ellipse(
            [head_cx + dx_off - 1, head_cy - head_r + 5,
             head_cx + dx_off + 1, head_cy - head_r + 7],
            fill=(35, 30, 20)
        )

    # === 大颚 ===
    mand_c = (52, 58, 28)
    # 颚部微动
    mand_open = math.sin(frame / FRAME_COUNT * 2 * math.pi * 3) * 1.5
    draw.polygon(
        [(head_cx - 5, head_cy + head_r - 5),
         (head_cx - 16, head_cy + head_r + 4 + mand_open),
         (head_cx - 12, head_cy + head_r + 9 + mand_open),
         (head_cx - 3, head_cy + head_r)],
        fill=mand_c, outline=LEG_D
    )
    draw.polygon(
        [(head_cx + 5, head_cy + head_r - 5),
         (head_cx + 16, head_cy + head_r + 4 + mand_open),
         (head_cx + 12, head_cy + head_r + 9 + mand_open),
         (head_cx + 3, head_cy + head_r)],
        fill=mand_c, outline=LEG_D
    )

    # === 触角（带动画） ===
    _draw_antennae(draw, head_cx, head_cy - head_r + 3, ANT_C, ANT_T, frame)

    return img


def generate():
    os.makedirs(OUT_DIR, exist_ok=True)

    frames = []
    for i in range(FRAME_COUNT):
        img = draw_walk_frame(i)
        img = img.filter(ImageFilter.SHARPEN)
        frames.append(img)

        # 保存序列帧
        fname = f'ant_walk_{i + 1:03d}.png'
        fpath = os.path.join(OUT_DIR, fname)
        img.save(fpath, 'PNG')
        print(f'  [{i + 1:02d}/{FRAME_COUNT}] {fname}')

    print(f'\n✓ 序列帧已保存: {OUT_DIR}/')

    # 生成 Sprite Sheet（8列 x 3行）
    cols, rows = 8, 3
    sheet_w = SIZE * cols
    sheet_h = SIZE * rows
    sheet = Image.new('RGBA', (sheet_w, sheet_h), (0, 0, 0, 0))
    for i, frame in enumerate(frames):
        r = i // cols
        c = i % cols
        sheet.paste(frame, (c * SIZE, r * SIZE))
    sheet.save(SHEET_PATH, 'PNG')
    print(f'✓ Sprite Sheet: {SHEET_PATH} ({sheet_w}x{sheet_h})')

    # 生成 40x40 游戏尺寸预览（拼成一条预览带）
    preview_dir = os.path.join(SCRIPT_DIR, '..', 'images', 'ant', 'ant1_walk_preview')
    os.makedirs(preview_dir, exist_ok=True)
    for i, frame in enumerate(frames):
        small = frame.resize((40, 40), Image.LANCZOS)
        small.save(os.path.join(preview_dir, f'frame_{i + 1:03d}.png'), 'PNG')
    print(f'✓ 40x40 预览: {preview_dir}/')

    print(f'\n完成! 共生成 {FRAME_COUNT} 帧行走动画。')


if __name__ == '__main__':
    generate()
