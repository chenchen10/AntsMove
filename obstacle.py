"""障碍物系统：装饰物与碰撞障碍物，支持AABB碰撞检测"""

import pygame
import random
import math
from config import (
    WORLD_WIDTH, WORLD_HEIGHT, ZONE_CONFIG,
)


# ── 障碍物类型定义 ──

OBSTACLE_TYPES = {
    # 左区纯装饰（无碰撞）
    'flower_low':    {'w': 50, 'h': 45, 'collidable': False, 'color': (200, 120, 160)},
    'mushroom':      {'w': 40, 'h': 45, 'collidable': False, 'color': (180, 80, 60)},
    'grass':         {'w': 40, 'h': 35, 'collidable': False, 'color': (100, 180, 80)},
    'mat_picnic':    {'w': 70, 'h': 65, 'collidable': False, 'color': (220, 180, 140)},
    # 中区碰撞障碍
    'rock':          {'w': 50, 'h': 45, 'collidable': True,  'color': (130, 130, 140)},
    'rock_pile':     {'w': 60, 'h': 55, 'collidable': True,  'color': (110, 110, 120)},
    'grass_tall':    {'w': 45, 'h': 50, 'collidable': True,  'color': (80, 160, 60)},
    # 右区碰撞障碍
    'flower_tall':   {'w': 60, 'h': 65, 'collidable': True,  'color': (180, 100, 140)},
    'bush':          {'w': 55, 'h': 50, 'collidable': True,  'color': (70, 140, 50)},
}

# 各区域可使用的障碍物类型
ZONE_OBSTACLE_TYPES = {
    'left':   ['flower_low', 'mushroom', 'grass', 'mat_picnic'],
    'center': ['rock', 'rock_pile', 'grass_tall'],
    'right':  ['flower_tall', 'rock_pile', 'bush'],
}

# 各区域障碍物数量范围
ZONE_OBSTACLE_COUNT = {
    'left':   (6, 8),
    'center': (7, 9),
    'right':  (5, 7),
}

# 甜点安全半径：障碍物不生成在甜点附近
SWEET_SAFE_RADIUS = 120
# 巢穴安全半径：障碍物不生成在巢穴附近
NEST_SAFE_RADIUS = 100


class Obstacle:
    """单个障碍物：支持AABB碰撞检测"""

    def __init__(self, obs_type, x, y, assets=None):
        type_def = OBSTACLE_TYPES[obs_type]
        self.obs_type = obs_type
        self.x = float(x)
        self.y = float(y)
        self.width = type_def['w']
        self.height = type_def['h']
        self.collidable = type_def['collidable']
        self.color = type_def['color']

        # AABB碰撞框（世界坐标）
        self.rect = pygame.Rect(
            int(self.x - self.width // 2),
            int(self.y - self.height // 2),
            self.width,
            self.height,
        )

        # 加载或生成图片
        self.image = self._load_image(assets)

    def _load_image(self, assets):
        """加载障碍物图片，失败则用代码生成"""
        if assets:
            key = f'deco_{self.obs_type}'
            if key in assets:
                return assets[key]

        # 代码生成回退
        surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        cx = self.width // 2
        cy = self.height // 2

        if 'rock' in self.obs_type:
            # 石头：不规则椭圆
            pygame.draw.ellipse(surf, self.color, (4, 6, self.width - 8, self.height - 10))
            highlight = tuple(min(255, c + 30) for c in self.color)
            pygame.draw.ellipse(surf, highlight, (6, 4, self.width // 2, self.height // 3))
        elif 'flower' in self.obs_type:
            # 花朵：茎+花瓣
            stem_color = (80, 140, 60)
            pygame.draw.line(surf, stem_color, (cx, self.height - 2), (cx, cy), 3)
            petal_color = self.color
            for angle in range(0, 360, 72):
                rad = math.radians(angle)
                px = cx + int(12 * math.cos(rad))
                py = cy + int(12 * math.sin(rad))
                pygame.draw.circle(surf, petal_color, (px, py), 7)
            pygame.draw.circle(surf, (255, 220, 80), (cx, cy), 5)
        elif 'mushroom' in self.obs_type:
            # 蘑菇：伞盖+茎
            pygame.draw.rect(surf, (200, 180, 150), (cx - 4, cy, 8, self.height - cy))
            pygame.draw.ellipse(surf, self.color, (cx - 14, cy - 10, 28, 18))
            for dx in [-8, 0, 8]:
                pygame.draw.circle(surf, (255, 255, 240), (cx + dx, cy - 4), 3)
        elif 'grass' in self.obs_type:
            # 草丛：多根草叶
            for dx in range(-10, 12, 5):
                h = random.randint(self.height // 2, self.height - 4)
                pygame.draw.line(surf, self.color, (cx + dx, self.height), (cx + dx + random.randint(-3, 3), self.height - h), 2)
        elif 'mat' in self.obs_type:
            # 野餐垫：矩形格子
            pygame.draw.rect(surf, self.color, (4, 4, self.width - 8, self.height - 8), border_radius=4)
            line_color = tuple(max(0, c - 40) for c in self.color)
            for i in range(1, 3):
                lx = 4 + (self.width - 8) * i // 3
                pygame.draw.line(surf, line_color, (lx, 6), (lx, self.height - 6), 1)
                ly = 4 + (self.height - 8) * i // 3
                pygame.draw.line(surf, line_color, (6, ly), (self.width - 6, ly), 1)
        elif 'bush' in self.obs_type:
            # 灌木丛：多个重叠圆
            for dx, dy, r in [(-8, -4, 14), (8, -2, 12), (0, 4, 16), (-4, -8, 10)]:
                pygame.draw.circle(surf, self.color, (cx + dx, cy + dy), r)
            highlight = tuple(min(255, c + 20) for c in self.color)
            pygame.draw.circle(surf, highlight, (cx - 4, cy - 8), 6)
        else:
            # 通用：圆形
            pygame.draw.circle(surf, self.color, (cx, cy), min(cx, cy) - 2)

        return surf

    def draw(self, screen, camera):
        """绘制障碍物（使用摄像机偏移）"""
        sx, sy = camera.world_to_screen(self.x, self.y)
        draw_rect = self.image.get_rect(center=(int(sx), int(sy)))
        screen.blit(self.image, draw_rect)

    def check_collision(self, x, y, radius=16):
        """检查圆形（蚂蚁）与矩形（障碍物）碰撞"""
        if not self.collidable:
            return False
        # 圆形 vs AABB
        closest_x = max(self.rect.left, min(x, self.rect.right))
        closest_y = max(self.rect.top, min(y, self.rect.bottom))
        dx = x - closest_x
        dy = y - closest_y
        return (dx * dx + dy * dy) < (radius * radius)


def generate_obstacles(assets=None, nest_positions=None):
    """为整个世界生成障碍物列表

    Args:
        assets: 资源字典
        nest_positions: 巢穴位置列表 [(x, y), ...]，障碍物不会生成在巢穴附近

    Returns:
        list of Obstacle
    """
    if nest_positions is None:
        nest_positions = []

    obstacles = []
    rng = random.Random(42)  # 固定种子，保证可重现

    for zone_name, cfg in ZONE_CONFIG.items():
        count_min, count_max = ZONE_OBSTACLE_COUNT[zone_name]
        count = rng.randint(count_min, count_max)
        types = ZONE_OBSTACLE_TYPES[zone_name]

        x_min, x_max = cfg['x_range']
        y_min, y_max = cfg['y_range']

        placed = 0
        attempts = 0
        while placed < count and attempts < count * 10:
            attempts += 1
            obs_type = rng.choice(types)
            type_def = OBSTACLE_TYPES[obs_type]

            x = rng.randint(x_min + 60, x_max - 60)
            y = rng.randint(y_min + 60, y_max - 60)

            # 检查与巢穴的距离
            too_close = False
            for nx, ny in nest_positions:
                if math.hypot(x - nx, y - ny) < NEST_SAFE_RADIUS:
                    too_close = True
                    break
            if too_close:
                continue

            # 检查与已有障碍物的距离（避免重叠）
            too_close = False
            for existing in obstacles:
                if math.hypot(x - existing.x, y - existing.y) < 80:
                    too_close = True
                    break
            if too_close:
                continue

            obs = Obstacle(obs_type, x, y, assets)
            obstacles.append(obs)
            placed += 1

    return obstacles
