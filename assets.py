"""加载游戏精灵资源（优先使用真实PNG，否则用代码生成）"""

import pygame
import math
import random
import os

ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'images')
SOUNDS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sounds')
DECO_DIR = os.path.join(ASSETS_DIR, 'deco')
INSECT_DIR = os.path.join(ASSETS_DIR, 'insect')

# 昆虫精灵定义：名称、尺寸、帧数
INSECTS = {
    'ladybug': {'size': (64, 64), 'frames': 3},
    'caterpillar': {'size': (80, 40), 'frames': 4},
    'cricket': {'size': (64, 64), 'frames': 3},
    'beetle': {'size': (64, 64), 'frames': 3},
    'dragonfly': {'size': (64, 72), 'frames': 3},
    'bee': {'size': (64, 64), 'frames': 3},
}
INSECT_DIRS = ['n', 'ne', 'e', 'se', 's', 'sw', 'w', 'nw']

# 自动生成昆虫精灵路径映射
INSECT_IMAGE_PATHS = {}
for _name, _cfg in INSECTS.items():
    for _dir in INSECT_DIRS:
        for _f in range(1, _cfg['frames'] + 1):
            _key = f'{_name}_{_dir}_{_f}'
            INSECT_IMAGE_PATHS[_key] = os.path.join(INSECT_DIR, _name, f'{_key}.png')

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
    # cookie/cake/donut/cream_cup/chocolate 暂时复用 candy 目录素材
    'cookie_full': os.path.join(ASSETS_DIR, 'candy', 'candy_full.png'),
    'cookie_60': os.path.join(ASSETS_DIR, 'candy', 'candy_60.png'),
    'cookie_30': os.path.join(ASSETS_DIR, 'candy', 'candy_30.png'),
    'cake_full': os.path.join(ASSETS_DIR, 'candy', 'candy_full.png'),
    'cake_60': os.path.join(ASSETS_DIR, 'candy', 'candy_60.png'),
    'cake_30': os.path.join(ASSETS_DIR, 'candy', 'candy_30.png'),
    'donut_full': os.path.join(ASSETS_DIR, 'candy', 'candy_full.png'),
    'donut_60': os.path.join(ASSETS_DIR, 'candy', 'candy_60.png'),
    'donut_30': os.path.join(ASSETS_DIR, 'candy', 'candy_30.png'),
    'cream_cup_full': os.path.join(ASSETS_DIR, 'candy', 'candy_full.png'),
    'cream_cup_60': os.path.join(ASSETS_DIR, 'candy', 'candy_60.png'),
    'cream_cup_30': os.path.join(ASSETS_DIR, 'candy', 'candy_30.png'),
    'chocolate_full': os.path.join(ASSETS_DIR, 'candy', 'candy_full.png'),
    'chocolate_60': os.path.join(ASSETS_DIR, 'candy', 'candy_60.png'),
    'chocolate_30': os.path.join(ASSETS_DIR, 'candy', 'candy_30.png'),
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


def _is_already_transparent(surf):
    """检测图片是否已经有良好的透明通道（采样检测，加速）"""
    w, h = surf.get_size()
    total = w * h
    if total == 0:
        return False
    sample_step = max(1, min(w, h) // 20)
    transparent = 0
    sampled = 0
    for y in range(0, h, sample_step):
        for x in range(0, w, sample_step):
            sampled += 1
            _, _, _, a = surf.get_at((x, y))
            if a < 128:
                transparent += 1
    return sampled > 0 and transparent / sampled > 0.3


def _remove_background(surf):
    """去除白色/浅色背景。对于已有透明通道的PNG（如deco素材），跳过处理。

    对于不透明图片，使用 flood-fill 从四角向内填充去除连通的背景像素。
    """
    # 如果图片已经有良好的透明通道（RGBA PNG），不做处理
    if _is_already_transparent(surf):
        return surf

    w, h = surf.get_size()
    if w == 0 or h == 0:
        return surf

    # 采样四角确定背景色
    corners = [
        surf.get_at((0, 0)),
        surf.get_at((w - 1, 0)),
        surf.get_at((0, h - 1)),
        surf.get_at((w - 1, h - 1)),
    ]
    bg_r = sum(p[0] for p in corners) // len(corners)
    bg_g = sum(p[1] for p in corners) // len(corners)
    bg_b = sum(p[2] for p in corners) // len(corners)

    def _is_bg(r, g, b, a):
        """判断像素是否为背景色（容差 40，覆盖 anti-aliasing 混合像素）"""
        if a == 0:
            return True
        if abs(r - bg_r) < 40 and abs(g - bg_g) < 40 and abs(b - bg_b) < 40:
            return True
        # 高亮度 + 低饱和度 = 近白色像素
        max_c = max(r, g, b)
        min_c = min(r, g, b)
        if max_c > 225 and (max_c - min_c) < 40:
            return True
        return False

    # 从四个角落 flood-fill
    visited = set()
    queue = []
    for sx, sy in [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1),
                   (w // 2, 0), (w // 2, h - 1), (0, h // 2), (w - 1, h // 2)]:
        r, g, b, a = surf.get_at((sx, sy))
        if _is_bg(r, g, b, a) and (sx, sy) not in visited:
            queue.append((sx, sy))
            visited.add((sx, sy))

    while queue:
        x, y = queue.pop()
        surf.set_at((x, y), (0, 0, 0, 0))
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < w and 0 <= ny < h and (nx, ny) not in visited:
                r, g, b, a = surf.get_at((nx, ny))
                if _is_bg(r, g, b, a):
                    visited.add((nx, ny))
                    queue.append((nx, ny))

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

    # 加载昆虫精灵（insect_sprites[insect_name][direction] = [frame1, frame2, ...]）
    insect_sprites = {}
    for insect_name, insect_cfg in INSECTS.items():
        insect_sprites[insect_name] = {}
        target_size = insect_cfg['size']
        for direction in INSECT_DIRS:
            frames = []
            for frame_idx in range(1, insect_cfg['frames'] + 1):
                key = f'{insect_name}_{direction}_{frame_idx}'
                path = INSECT_IMAGE_PATHS.get(key)
                if path and os.path.exists(path):
                    try:
                        img = pygame.image.load(path).convert_alpha()
                        img = pygame.transform.smoothscale(img, target_size)
                        frames.append(img)
                    except Exception:
                        pass
            insect_sprites[insect_name][direction] = frames
    assets['insect_sprites'] = insect_sprites

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
