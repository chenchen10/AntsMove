"""地形系统：8种地形类型、克制关系、负面效果"""

from enum import Enum


class TerrainType(Enum):
    PLAIN = 'plain'           # 平原
    FOREST = 'forest'         # 林地
    DESERT = 'desert'         # 沙漠
    MOUNTAIN = 'mountain'     # 山地
    TROPICAL = 'tropical'     # 热带丛林
    CONSTRUCTION = 'construction'  # 工地
    TREE_TOP = 'tree_top'     # 树栖高空
    ICE = 'ice'               # 寒冰高原


# 地形显示名称
TERRAIN_NAMES = {
    TerrainType.PLAIN: '平原',
    TerrainType.FOREST: '林地',
    TerrainType.DESERT: '沙漠',
    TerrainType.MOUNTAIN: '山地',
    TerrainType.TROPICAL: '热带丛林',
    TerrainType.CONSTRUCTION: '工地',
    TerrainType.TREE_TOP: '树栖高空',
    TerrainType.ICE: '寒冰高原',
}

# 地形背景色
TERRAIN_COLORS = {
    TerrainType.PLAIN: (120, 180, 80),
    TerrainType.FOREST: (60, 120, 50),
    TerrainType.DESERT: (220, 200, 140),
    TerrainType.MOUNTAIN: (140, 130, 120),
    TerrainType.TROPICAL: (40, 140, 60),
    TerrainType.CONSTRUCTION: (160, 150, 130),
    TerrainType.TREE_TOP: (80, 150, 70),
    TerrainType.ICE: (200, 220, 240),
}

# 负面效果类型
class DebuffType(Enum):
    SLOW = 'slow'             # 减速
    STUN = 'stun'             # 僵直
    HEAT = 'heat'             # 高温（沙漠）
    DROUGHT = 'drought'       # 干旱（沙漠）
    FREEZE = 'freeze'         # 冰冻（寒冰）
    HEAVY = 'heavy'           # 重物减负（工地）
    CLIMB_SLOW = 'climb_slow' # 攀爬减速（树栖）


# 每种地形对非适配蚂蚁施加的负面效果
TERRAIN_DEBUFFS = {
    TerrainType.PLAIN: [],
    TerrainType.FOREST: [DebuffType.SLOW],
    TerrainType.DESERT: [DebuffType.SLOW, DebuffType.HEAT, DebuffType.DROUGHT],
    TerrainType.MOUNTAIN: [DebuffType.SLOW],
    TerrainType.TROPICAL: [DebuffType.SLOW, DebuffType.HEAT],
    TerrainType.CONSTRUCTION: [DebuffType.HEAVY],
    TerrainType.TREE_TOP: [DebuffType.CLIMB_SLOW],
    TerrainType.ICE: [DebuffType.FREEZE, DebuffType.SLOW],
}

# 负面效果参数（PRD v2.0 数值策划调整）
DEBUFF_PARAMS = {
    DebuffType.SLOW: {'speed_mult': 0.75, 'duration': None},      # 持续生效（林地0.75）
    DebuffType.STUN: {'speed_mult': 0.0, 'duration': 1.5},        # 僵直1.5秒
    DebuffType.HEAT: {'eat_speed_mult': 0.75, 'duration': None},  # 啃食减速（0.8→0.75）
    DebuffType.DROUGHT: {'stun_chance': 0.12, 'duration': None},  # 12%概率僵直（0.1→0.12）
    DebuffType.FREEZE: {'speed_mult': 0.60, 'duration': None},    # 冻结减速（0.5→0.6）
    DebuffType.HEAVY: {'carry_mult': 0.75, 'duration': None},     # 搬运效率降低（0.8→0.75）
    DebuffType.CLIMB_SLOW: {'speed_mult': 0.55, 'duration': None},# 攀爬减速（0.6→0.55）
}


def get_terrain_debuffs(terrain_type, ant_terrain_tag, ant_trait):
    """计算蚂蚁在特定地形受到的负面效果列表。

    Args:
        terrain_type: 当前地形
        ant_terrain_tag: 蚂蚁的适配地形标签
        ant_trait: 蚂蚁的特性代码

    Returns:
        list of (DebuffType, params) 受到的负面效果
    """
    from ants_data import (
        TRAIT_ALL_TERRAIN, TRAIT_DESERT_IMMUNE, TRAIT_DESERT_FULL,
        TRAIT_ICE_IMMUNE, TRAIT_COLD_IMMUNE, TRAIT_DEBUFF_IMMUNE,
        TRAIT_SUPREME, TRAIT_STUN_HALF, TRAIT_TROPICAL_HALF,
    )

    # 免疫所有负面
    if ant_trait in (TRAIT_DEBUFF_IMMUNE, TRAIT_SUPREME):
        return []

    # 全地形无负面
    if ant_trait == TRAIT_ALL_TERRAIN:
        return []

    # 适配地形：免疫该地形所有负面
    if ant_terrain_tag == terrain_type.value:
        return []

    # 获取该地形的默认负面效果
    debuffs = TERRAIN_DEBUFFS.get(terrain_type, [])
    result = []

    for debuff in debuffs:
        # 沙漠适配：免疫沙漠所有效果
        if ant_trait == TRAIT_DESERT_IMMUNE and terrain_type == TerrainType.DESERT:
            continue
        if ant_trait == TRAIT_DESERT_FULL and terrain_type == TerrainType.DESERT:
            continue

        # 冰冻免疫
        if ant_trait in (TRAIT_ICE_IMMUNE, TRAIT_COLD_IMMUNE) and debuff == DebuffType.FREEZE:
            continue

        # 热带负面减半（时长减半）
        if ant_trait == TRAIT_TROPICAL_HALF and terrain_type == TerrainType.TROPICAL:
            params = dict(DEBUFF_PARAMS[debuff])
            if params.get('duration'):
                params['duration'] *= 0.5
            result.append((debuff, params))
            continue

        # 僵直减半
        if ant_trait == TRAIT_STUN_HALF and debuff == DebuffType.STUN:
            params = dict(DEBUFF_PARAMS[debuff])
            params['duration'] *= 0.5
            result.append((debuff, params))
            continue

        result.append((debuff, DEBUFF_PARAMS[debuff]))

    return result


# 各地形对非适配蚂蚁的最终移动速度乘数（PRD v2.0 数值策划方案）
# 覆盖 debuff_params 中 SLOW 的统一值，实现地形区分度
TERRAIN_SPEED_OVERRIDE = {
    TerrainType.PLAIN: 1.0,
    TerrainType.FOREST: 0.75,        # 入门级困难地形
    TerrainType.DESERT: 0.65,        # 3种debuff，综合威胁
    TerrainType.MOUNTAIN: 0.70,      # 中等难度
    TerrainType.TROPICAL: 0.60,      # 高温+密林双重阻碍
    TerrainType.CONSTRUCTION: 0.85,  # 新增少量速度减益
    TerrainType.TREE_TOP: 0.55,      # 高空攀爬额外困难
    TerrainType.ICE: 0.45,           # 冻结+减速（0.60×0.75=0.45）
}


def get_speed_multiplier(debuffs, terrain_type=None):
    """根据负面效果列表计算速度倍率。

    当提供 terrain_type 时，使用地形专属速度乘数替代 debuff 中的 SLOW/CLIMB_SLOW 叠乘，
    以实现各地形之间的速度区分度。
    """
    if terrain_type and terrain_type in TERRAIN_SPEED_OVERRIDE:
        # 检查是否有速度类负面效果（SLOW 或 CLIMB_SLOW）
        has_speed_debuff = any(
            'speed_mult' in params
            for _, params in debuffs
        )
        if has_speed_debuff:
            return TERRAIN_SPEED_OVERRIDE[terrain_type]

    mult = 1.0
    for debuff, params in debuffs:
        if 'speed_mult' in params:
            mult *= params['speed_mult']
    return mult


def get_carry_multiplier(debuffs):
    """根据负面效果列表计算搬运效率倍率"""
    mult = 1.0
    for debuff, params in debuffs:
        if 'carry_mult' in params:
            mult *= params['carry_mult']
    return mult


def get_eat_speed_multiplier(debuffs):
    """根据负面效果列表计算啃食速度倍率"""
    mult = 1.0
    for debuff, params in debuffs:
        if 'eat_speed_mult' in params:
            mult *= params['eat_speed_mult']
    return mult
