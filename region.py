"""区域系统：三区域定义、巢穴位置、出生范围"""

import random
from config import (
    WORLD_WIDTH, WORLD_HEIGHT,
    ZONE_CONFIG,
)

# ── 巢穴位置（世界坐标）──
# 玩家巢穴：左区中心偏左
PLAYER_NEST_X = 300
PLAYER_NEST_Y = WORLD_HEIGHT // 2

# 敌方巢穴：右区中心偏右
AI_NEST_X = WORLD_WIDTH - 300
AI_NEST_Y = WORLD_HEIGHT // 2

# ── 蚂蚁出生范围（世界坐标）──
# 玩家出生在玩家巢穴附近
PLAYER_SPAWN_X_RANGE = (PLAYER_NEST_X - 30, PLAYER_NEST_X + 30)
PLAYER_SPAWN_Y_RANGE = (PLAYER_NEST_Y - 40, PLAYER_NEST_Y + 40)

# 敌方出生在敌方巢穴附近
AI_SPAWN_X_RANGE = (AI_NEST_X - 30, AI_NEST_X + 30)
AI_SPAWN_Y_RANGE = (AI_NEST_Y - 40, AI_NEST_Y + 40)


def get_zone_for_x(world_x):
    """根据世界坐标X值返回区域key"""
    for zone_name, cfg in ZONE_CONFIG.items():
        x_min, x_max = cfg['x_range']
        if x_min <= world_x <= x_max:
            return zone_name
    return 'center'


def get_multiplier_for_x(world_x):
    """根据世界坐标X值获取倍率"""
    zone = get_zone_for_x(world_x)
    return ZONE_CONFIG[zone]['multiplier']


def choose_refresh_region():
    """按概率随机选择刷新区域，返回区域key"""
    roll = random.random()
    cumulative = 0.0
    for zone_name, cfg in ZONE_CONFIG.items():
        cumulative += cfg['spawn_prob']
        if roll < cumulative:
            return zone_name
    return 'center'


def get_random_sweet_pos(zone_name):
    """在指定区域内随机生成甜点世界坐标"""
    cfg = ZONE_CONFIG[zone_name]
    x_min, x_max = cfg['x_range']
    y_min, y_max = cfg['y_range']
    x = random.randint(x_min + 50, x_max - 50)
    y = random.randint(y_min + 60, y_max - 60)
    return x, y
