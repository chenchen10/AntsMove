"""加载游戏精灵资源（优先使用真实PNG，否则用代码生成）"""

import pygame
import math
import random
import os

ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'images')
SOUNDS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sounds')
DECO_DIR = os.path.join(ASSETS_DIR, 'deco')

# 障碍物装饰图片路径
DECO_IMAGE_PATHS = {
    'flower_low':  os.path.join(DECO_DIR, 'flower_low.png'),
    'flower_tall': os.path.join(DECO_DIR, 'flower_tall.png'),
    'grass':       os.path.join(DECO_DIR, 'grass.png'),
    'mushroom':    os.path.join(DECO_DIR, 'mushroom.png'),
    'rock':        os.path.join(DECO_DIR, 'rock.png'),
    'rock_pile':   os.path.join(DECO_DIR, 'rock_pile.png'),
    'mat_picnic':  os.path.join(DECO_DIR, 'mat_picnic.png'),
}

# 图片路径映射
ANT_DIR = os.path.join(ASSETS_DIR, 'ant')
ANT_PROCESSED_DIR = os.path.join(ASSETS_DIR, 'ant_processed')
IMAGE_PATHS = {
    'blue_ant_up1': os.path.join(ANT_DIR, 'blue_ant_up1.png'),
    'blue_ant_up2': os.path.join(ANT_DIR, 'blue_ant_up2.png'),
    'blue_ant_up3': os.path.join(ANT_DIR, 'blue_ant_up3.png'),
    'blue_ant_down1': os.path.join(ANT_DIR, 'blue_ant_down1.png'),
    'blue_ant_down2': os.path.join(ANT_DIR, 'blue_ant_down2.png'),
    'blue_ant_down3': os.path.join(ANT_DIR, 'blue_ant_down3.png'),
    'red_ant': os.path.join(ANT_DIR, 'red_ant.png'),
    # 每只蚂蚁的独立原型图（ant_id → 图片路径，使用已去背的RGBA图）
    'ant_1': os.path.join(ANT_PROCESSED_DIR, 'ant1.png'),
    'ant_2': os.path.join(ANT_PROCESSED_DIR, 'ant2.png'),
    'ant_3': os.path.join(ANT_PROCESSED_DIR, 'ant3.png'),
    'ant_4': os.path.join(ANT_PROCESSED_DIR, 'ant4.png'),
    'ant_5': os.path.join(ANT_PROCESSED_DIR, 'ant5.png'),
    'candy_full': os.path.join(ASSETS_DIR, 'candy', 'candy_full.png'),
    'candy_60': os.path.join(ASSETS_DIR, 'candy', 'candy_60.png'),
    'candy_30': os.path.join(ASSETS_DIR, 'candy', 'candy_30.png'),
    'cookie_full': os.path.join(ASSETS_DIR, 'cookie', 'cookie_full.png'),
    'cookie_60': os.path.join(ASSETS_DIR, 'cookie', 'cookie_60.png'),
    'cookie_30': os.path.join(ASSETS_DIR, 'cookie', 'cookie_30.png'),
    'cake_full': os.path.join(ASSETS_DIR, 'cake', 'cake_full.png'),
    'cake_60': os.path.join(ASSETS_DIR, 'cake', 'cake_60.png'),
    'cake_30': os.path.join(ASSETS_DIR, 'cake', 'cake_30.png'),
    'donut_full': os.path.join(ASSETS_DIR, 'donut', 'donut_full.png'),
    'donut_60': os.path.join(ASSETS_DIR, 'donut', 'donut_60.png'),
    'donut_30': os.path.join(ASSETS_DIR, 'donut', 'donut_30.png'),
    'cream_cup_full': os.path.join(ASSETS_DIR, 'cream_cup', 'cream_cup_full.png'),
    'cream_cup_60': os.path.join(ASSETS_DIR, 'cream_cup', 'cream_cup_60.png'),
    'cream_cup_30': os.path.join(ASSETS_DIR, 'cream_cup', 'cream_cup_30.png'),
    'chocolate_full': os.path.join(ASSETS_DIR, 'chocolate', 'chocolate_full.png'),
    'chocolate_60': os.path.join(ASSETS_DIR, 'chocolate', 'chocolate_60.png'),
    'chocolate_30': os.path.join(ASSETS_DIR, 'chocolate', 'chocolate_30.png'),
    # 新手引导素材
    'guide_overlay': os.path.join(ASSETS_DIR, 'guide', 'guide_overlay.png'),
    'guide_circle': os.path.join(ASSETS_DIR, 'guide', 'guide_circle.png'),
    # 道具HUD图标
    'item_speed': os.path.join(ASSETS_DIR, 'item', 'item_speed.png'),
    'item_double': os.path.join(ASSETS_DIR, 'item', 'item_double.png'),
    'item_stun': os.path.join(ASSETS_DIR, 'item', 'item_stun.png'),
    # 结算星级图标
    'star_full': os.path.join(ASSETS_DIR, 'star', 'star_full.png'),
    'star_empty': os.path.join(ASSETS_DIR, 'star', 'star_empty.png'),
}

# 目标缩放尺寸
TARGET_SIZES = {
    'ant': (40, 40),
    'sweet_full': (150, 150),
    'sweet_60': (100, 100),
    'sweet_30': (60, 60),
    'sweet_icon': (12, 12),  # 蚂蚁头顶小图标尺寸
    'item_icon': (32, 32),   # 道具HUD图标
    'star_icon': (48, 48),   # 结算星级图标
}

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)


# ─── 代码生成回退 ────────────────────────────────────

def _draw_ant(surf, body_color, dark_color):
    w, h = surf.get_size()
    cx, cy = w // 2, h // 2
    pygame.draw.ellipse(surf, body_color, (cx - 14, cy - 7, 28, 14))
    pygame.draw.circle(surf, dark_color, (cx + 16, cy), 7)
    pygame.draw.circle(surf, WHITE, (cx + 19, cy - 2), 2)
    pygame.draw.circle(surf, BLACK, (cx + 20, cy - 2), 1)
    for dx in (-10, 0, 10):
        pygame.draw.line(surf, dark_color, (cx + dx, cy + 7), (cx + dx - 4, cy + 14), 2)
        pygame.draw.line(surf, dark_color, (cx + dx, cy - 7), (cx + dx - 4, cy - 14), 2)
    pygame.draw.line(surf, dark_color, (cx + 20, cy - 5), (cx + 27, cy - 12), 1)
    pygame.draw.line(surf, dark_color, (cx + 20, cy + 5), (cx + 27, cy + 12), 1)


def _draw_sweet_circle(surf, color, radius):
    cx, cy = surf.get_size()[0] // 2, surf.get_size()[1] // 2
    pygame.draw.circle(surf, color, (cx, cy), radius)
    pygame.draw.circle(surf, WHITE, (cx, cy), radius, 2)
    for ang in range(0, 360, 120):
        rad = math.radians(ang)
        sx = cx + int(radius * 0.4 * math.cos(rad))
        sy = cy + int(radius * 0.4 * math.sin(rad))
        pygame.draw.circle(surf, WHITE, (sx, sy), 3)


def _draw_sweet_cookie(surf, color, radius):
    cx, cy = surf.get_size()[0] // 2, surf.get_size()[1] // 2
    pygame.draw.circle(surf, color, (cx, cy), radius)
    rng = random.Random(42)
    for _ in range(6):
        dx = rng.randint(-radius + 6, radius - 6)
        dy = rng.randint(-radius + 6, radius - 6)
        if dx * dx + dy * dy < (radius - 4) ** 2:
            pygame.draw.circle(surf, (80, 40, 10), (cx + dx, cy + dy), 3)


def _draw_sweet_cake(surf, color, radius):
    cx, cy = surf.get_size()[0] // 2, surf.get_size()[1] // 2
    pygame.draw.circle(surf, (255, 230, 240), (cx, cy), radius)
    pygame.draw.rect(surf, color, (cx - radius, cy - 2, radius * 2, 5))
    pygame.draw.circle(surf, (200, 30, 30), (cx, cy - radius + 6), max(3, radius // 6))


def _draw_sweet_donut(surf, color, radius):
    cx, cy = surf.get_size()[0] // 2, surf.get_size()[1] // 2
    pygame.draw.circle(surf, color, (cx, cy), radius)
    inner_r = max(2, radius // 3)
    pygame.draw.circle(surf, (255, 220, 180), (cx, cy), inner_r)
    for x in range(cx - radius, cx + radius + 1):
        for y in range(cy - radius, cy + 1):
            dist_sq = (x - cx) ** 2 + (y - cy) ** 2
            if dist_sq <= radius ** 2 and dist_sq > inner_r ** 2:
                if 0 <= x < surf.get_width() and 0 <= y < surf.get_height():
                    surf.set_at((x, y), (255, 180, 100))


def _draw_sweet_cup(surf, color, radius):
    cx, cy = surf.get_size()[0] // 2, surf.get_size()[1] // 2
    cup_color = (200, 180, 180)
    pygame.draw.polygon(surf, cup_color, [
        (cx - radius, cy), (cx + radius, cy),
        (cx + radius - 4, cy + radius), (cx - radius + 4, cy + radius)
    ])
    cream_h = max(4, radius // 2)
    pygame.draw.ellipse(surf, color, (cx - radius, cy - cream_h, radius * 2, cream_h * 2))


def _draw_sweet_chocolate(surf, color, radius):
    cx, cy = surf.get_size()[0] // 2, surf.get_size()[1] // 2
    rect = pygame.Rect(cx - radius, cy - radius, radius * 2, radius * 2)
    pygame.draw.rect(surf, color, rect, border_radius=4)
    grid_color = (70, 40, 20)
    for i in range(1, 3):
        lx = cx - radius + (radius * 2 * i) // 3
        pygame.draw.line(surf, grid_color, (lx, cy - radius + 3), (lx, cy + radius - 3), 1)
    for i in range(1, 3):
        ly = cy - radius + (radius * 2 * i) // 3
        pygame.draw.line(surf, grid_color, (cx - radius + 3, ly), (cx + radius - 3, ly), 1)


SWEET_DRAW_FUNCS = {
    'candy': _draw_sweet_circle,
    'cookie': _draw_sweet_cookie,
    'cake': _draw_sweet_cake,
    'donut': _draw_sweet_donut,
    'cream_cup': _draw_sweet_cup,
    'chocolate': _draw_sweet_chocolate,
}

SWEET_COLORS_MAP = {
    'candy': (255, 150, 200),
    'cookie': (210, 160, 80),
    'cake': (255, 180, 220),
    'donut': (200, 120, 60),
    'cream_cup': (255, 200, 200),
    'chocolate': (100, 60, 30),
}


def _generate_fallback(key):
    """当PNG不存在时，用代码生成替代精灵"""
    surf = None

    if key == 'blue_ant':
        surf = pygame.Surface(TARGET_SIZES['ant'], pygame.SRCALPHA)
        _draw_ant(surf, (50, 100, 200), (30, 70, 150))
    elif key == 'red_ant':
        surf = pygame.Surface(TARGET_SIZES['ant'], pygame.SRCALPHA)
        _draw_ant(surf, (200, 50, 50), (150, 30, 30))
    else:
        # 甜点回退
        parts = key.rsplit('_', 1)
        if len(parts) == 2:
            sweet_name, state = parts
            if sweet_name in SWEET_DRAW_FUNCS and state in ('full', '60', '30'):
                size = TARGET_SIZES[f'sweet_{state}']
                surf = pygame.Surface(size, pygame.SRCALPHA)
                color = SWEET_COLORS_MAP.get(sweet_name, (200, 200, 200))
                SWEET_DRAW_FUNCS[sweet_name](surf, color, size[0] // 2 - 2)

    return surf


def _remove_background(surf):
    """去除白色/浅色背景，使其透明。采样边缘像素确定背景色，双策略去除。"""
    w, h = surf.get_size()
    # 采样四边中点 + 四角，更准确地确定背景色
    edge_samples = [
        surf.get_at((0, 0)),
        surf.get_at((w - 1, 0)),
        surf.get_at((0, h - 1)),
        surf.get_at((w - 1, h - 1)),
        surf.get_at((w // 2, 0)),
        surf.get_at((w // 2, h - 1)),
        surf.get_at((0, h // 2)),
        surf.get_at((w - 1, h // 2)),
    ]
    bg_r = sum(p[0] for p in edge_samples) // len(edge_samples)
    bg_g = sum(p[1] for p in edge_samples) // len(edge_samples)
    bg_b = sum(p[2] for p in edge_samples) // len(edge_samples)

    for y in range(h):
        for x in range(w):
            r, g, b, a = surf.get_at((x, y))
            if a == 0:
                continue
            # 策略1：接近背景色（白色）的像素 → 透明
            if abs(r - bg_r) < 30 and abs(g - bg_g) < 30 and abs(b - bg_b) < 30:
                surf.set_at((x, y), (0, 0, 0, 0))
                continue
            # 策略2：高亮度 + 低饱和度 = 近白色像素 → 透明
            max_c = max(r, g, b)
            min_c = min(r, g, b)
            if max_c > 230 and (max_c - min_c) < 30:
                surf.set_at((x, y), (0, 0, 0, 0))
    return surf


def load_assets():
    """加载所有游戏精灵。优先加载PNG（去除背景），不存在则用代码生成。"""
    assets = {}

    for key, path in IMAGE_PATHS.items():
        if os.path.exists(path):
            try:
                img = pygame.image.load(path).convert_alpha()
                # 确定目标尺寸
                if key.startswith('ant_'):
                    target = TARGET_SIZES['ant']
                elif '_ant' in key:
                    target = TARGET_SIZES['ant']
                elif key.startswith('item_'):
                    target = TARGET_SIZES['item_icon']
                elif key.startswith('star_'):
                    target = TARGET_SIZES['star_icon']
                elif key.startswith('guide_'):
                    # 引导素材保持原始尺寸
                    target = img.get_size()
                elif key.endswith('_full'):
                    target = TARGET_SIZES['sweet_full']
                elif key.endswith('_60'):
                    target = TARGET_SIZES['sweet_60']
                else:
                    target = TARGET_SIZES['sweet_30']
                img = pygame.transform.smoothscale(img, target)
                # 去除背景（引导遮罩层不做去背处理）
                if not key.startswith('guide_'):
                    img = _remove_background(img)
                assets[key] = img
                continue
            except Exception:
                pass
        # PNG不存在或加载失败，用代码生成
        fallback = _generate_fallback(key)
        if fallback:
            assets[key] = fallback

    # 构建蚂蚁动画帧列表（上行/下行）
    up_frames = [assets[k] for k in ['blue_ant_up1', 'blue_ant_up2', 'blue_ant_up3'] if k in assets]
    down_frames = [assets[k] for k in ['blue_ant_down1', 'blue_ant_down2', 'blue_ant_down3'] if k in assets]
    assets['blue_ant_up_frames'] = up_frames or down_frames or [assets.get('red_ant')]
    assets['blue_ant_down_frames'] = down_frames or up_frames or [assets.get('red_ant')]

    # 构建每只蚂蚁的独立图片映射（ant_id → image）
    # 已有原型图的蚂蚁直接使用，其余回退到 blue_ant
    ant_images = {}
    fallback_img = assets.get('blue_ant_up_frames', [None])[0] or assets.get('red_ant')
    for ant_id in range(1, 27):
        key = f'ant_{ant_id}'
        ant_images[ant_id] = assets.get(key, fallback_img)
    assets['ant_images'] = ant_images

    # 加载障碍物装饰图片（deco_*），缩放至OBSTACLE_TYPES定义的目标尺寸并去背
    from obstacle import OBSTACLE_TYPES
    for deco_key, deco_path in DECO_IMAGE_PATHS.items():
        asset_key = f'deco_{deco_key}'
        if os.path.exists(deco_path):
            try:
                img = pygame.image.load(deco_path).convert_alpha()
                # 按OBSTACLE_TYPES中定义的目标尺寸缩放
                if deco_key in OBSTACLE_TYPES:
                    tw = OBSTACLE_TYPES[deco_key]['w']
                    th = OBSTACLE_TYPES[deco_key]['h']
                    img = pygame.transform.smoothscale(img, (tw, th))
                # 去除背景
                img = _remove_background(img)
                assets[asset_key] = img
            except Exception:
                pass  # 由 obstacle.py 代码生成回退

    # 生成小图标版本的甜点（用于蚂蚁头顶存储显示）
    sweet_types = ['candy', 'cookie', 'cake', 'donut', 'cream_cup', 'chocolate']
    icon_size = TARGET_SIZES['sweet_icon']
    for sweet in sweet_types:
        full_key = f'{sweet}_full'
        icon_key = f'{sweet}_icon'
        if full_key in assets:
            assets[icon_key] = pygame.transform.smoothscale(assets[full_key], icon_size)
        else:
            # 创建简单的小圆点作为回退
            icon_surf = pygame.Surface(icon_size, pygame.SRCALPHA)
            from config import SWEET_COLORS
            color = SWEET_COLORS.get(sweet, (200, 200, 200))
            pygame.draw.circle(icon_surf, color, (icon_size[0] // 2, icon_size[1] // 2), icon_size[0] // 2)
            assets[icon_key] = icon_surf

    return assets


# ─── 音效资源 ─────────────────────────────────────────

SOUND_PATHS = {
    'sfx_speed': os.path.join(SOUNDS_DIR, 'sfx_speed.wav'),
    'sfx_double': os.path.join(SOUNDS_DIR, 'sfx_double.wav'),
    'sfx_stun': os.path.join(SOUNDS_DIR, 'sfx_stun.wav'),
}


def load_sounds():
    """加载所有道具音效。优先加载WAV文件，不存在则返回空dict。"""
    sounds = {}
    for key, path in SOUND_PATHS.items():
        if os.path.exists(path):
            try:
                sounds[key] = pygame.mixer.Sound(path)
            except Exception:
                pass
    return sounds
