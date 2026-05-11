"""200关关卡配置生成器

四大阶段：
- 第一阶段 1-50：新手开荒，平原/林地/轻度沙漠
- 第二阶段 51-100：过渡养成，大平原/高原山地/热带丛林/简易工地
- 第三阶段 101-150：中期攻坚，极限热带/寒冰/重型工地/强对抗
- 第四阶段 151-200：终极挑战，复合极限地形

数值规则：
- 每10关小梯度：目标金币+15%，敌方强度+12%
- 每50关大梯度：地形复杂度/负面效果/甜食血量全面升级
- 关卡限时：1-50关90秒，51-100关80秒，101-150关70秒，151-200关60秒
"""

import random
from terrain import TerrainType, TERRAIN_NAMES


# ── 阶段定义 ──

STAGES = [
    # (起始关, 结束关, 主要地形, 甜点基础HP, 敌方基础速度, 敌方基础storage)
    (1,  50,  [TerrainType.PLAIN, TerrainType.FOREST, TerrainType.DESERT], 30, 170, 12),
    (51, 100, [TerrainType.PLAIN, TerrainType.MOUNTAIN, TerrainType.TROPICAL, TerrainType.CONSTRUCTION], 60, 200, 22),
    (101, 150, [TerrainType.TROPICAL, TerrainType.ICE, TerrainType.CONSTRUCTION, TerrainType.MOUNTAIN], 100, 230, 38),
    (151, 200, [TerrainType.DESERT, TerrainType.ICE, TerrainType.TROPICAL, TerrainType.TREE_TOP, TerrainType.MOUNTAIN], 150, 260, 55),
]

# 每阶段的限时（秒）
STAGE_TIMERS = {
    (1, 50): 90,
    (51, 100): 80,
    (101, 150): 70,
    (151, 200): 60,
}

# 甜点类型按阶段解锁
STAGE_SWEETS = {
    (1, 50): ['candy', 'cookie'],
    (51, 100): ['candy', 'cookie', 'cake'],
    (101, 150): ['cake', 'donut', 'cream_cup'],
    (151, 200): ['donut', 'cream_cup', 'chocolate'],
}


def _get_stage(level):
    """获取关卡所属阶段"""
    for start, end, *_ in STAGES:
        if start <= level <= end:
            return start, end
    return 1, 50


def _get_timer(level):
    """获取关卡限时"""
    for (start, end), timer in STAGE_TIMERS.items():
        if start <= level <= end:
            return timer
    return 90


def _get_terrain(level):
    """根据关卡选择地形，每10关切换"""
    for start, end, terrains, *_ in STAGES:
        if start <= level <= end:
            # 每10关选不同地形，保证多样性
            idx = ((level - start) // 10) % len(terrains)
            return terrains[idx]
    return TerrainType.PLAIN


def _get_sweet_type(level):
    """根据关卡选择甜点类型"""
    for (start, end), sweets in STAGE_SWEETS.items():
        if start <= level <= end:
            rng = random.Random(level)  # 固定种子，保证可重现
            return rng.choice(sweets)
    return 'candy'


def _calc_target_coins(level):
    """计算目标金币：基准值的1/10，作为最低达标线"""
    if level <= 50:
        base = 1000 + (level - 1) * 280
    elif level <= 100:
        base = 15000 + (level - 51) * 500
    elif level <= 150:
        base = 40000 + (level - 101) * 1200
    else:
        base = 100000 + (level - 151) * 3000
    decade = (level - 1) // 10
    multiplier = 1.0 + decade * 0.15
    return int(base * multiplier) // 10


def _calc_sweet_hp(level):
    """甜点血量随关卡递增"""
    for start, end, _, base_hp, *_ in STAGES:
        if start <= level <= end:
            # 每10关 +20%
            decade = (level - start) // 10
            return int(base_hp * (1.0 + decade * 0.2))
    return 30


def _calc_sweet_quantity(level):
    """甜点数量：前期多后期少"""
    if level <= 50:
        return 25
    elif level <= 100:
        return 20
    elif level <= 150:
        return 15
    else:
        return 10


def _calc_sweet_coin_per(level):
    """每颗甜点价值"""
    if level <= 50:
        return max(1, level // 10 + 1)
    elif level <= 100:
        return max(3, level // 8)
    elif level <= 150:
        return max(5, level // 6)
    else:
        return max(8, level // 5)


def _calc_ai_speed(level):
    """敌方蚂蚁速度"""
    for start, end, _, _, base_speed, *_ in STAGES:
        if start <= level <= end:
            decade = (level - start) // 10
            return int(base_speed * (1.0 + decade * 0.12))
    return 140


def _calc_ai_storage(level):
    """敌方蚂蚁运载量"""
    for start, end, _, _, _, base_storage in STAGES:
        if start <= level <= end:
            decade = (level - start) // 10
            return int(base_storage * (1.0 + decade * 0.15))
    return 8


def _calc_ai_ant_count(level):
    """敌方蚂蚁数量"""
    if level <= 10:
        return 1
    elif level <= 30:
        return 2
    elif level <= 60:
        return 3
    elif level <= 100:
        return 4
    elif level <= 150:
        return 5
    else:
        return 6


def _calc_reward_coins(level):
    """通关奖励金币"""
    base = _calc_target_coins(level)
    return int(base * 0.3)  # 奖励为目标金币的30%


def _calc_debuff_level(level):
    """负面效果等级（0-3），控制地形负面强度"""
    if level <= 50:
        return 0
    elif level <= 100:
        return 1
    elif level <= 150:
        return 2
    else:
        return 3


def generate_level(level_num):
    """生成单个关卡配置"""
    terrain = _get_terrain(level_num)
    sweet_type = _get_sweet_type(level_num)

    return {
        'id': level_num,
        'name': f'第{level_num}关',
        'terrain': terrain,
        'terrain_name': TERRAIN_NAMES[terrain],
        'timer': _get_timer(level_num),
        'target_coins': _calc_target_coins(level_num),
        'reward_coins': _calc_reward_coins(level_num),
        'sweet': {
            'type': sweet_type,
            'hp': _calc_sweet_hp(level_num),
            'quantity': _calc_sweet_quantity(level_num),
            'coin_per': _calc_sweet_coin_per(level_num),
        },
        'ai': {
            'ant_count': _calc_ai_ant_count(level_num),
            'speed': _calc_ai_speed(level_num),
            'storage': _calc_ai_storage(level_num),
        },
        'debuff_level': _calc_debuff_level(level_num),
    }


# 预生成全部200关
ALL_LEVELS = [generate_level(i) for i in range(1, 201)]


def get_level(level_num):
    """获取指定关卡配置（1-200）"""
    if 1 <= level_num <= 200:
        return ALL_LEVELS[level_num - 1]
    return ALL_LEVELS[0]


def get_stage_info(level_num):
    """获取关卡所在阶段信息"""
    for start, end, terrains, *_ in STAGES:
        if start <= level_num <= end:
            stage_idx = STAGES.index((start, end, terrains, *_)) + 1
            return {
                'stage': stage_idx,
                'start': start,
                'end': end,
                'terrains': terrains,
            }
    return {'stage': 1, 'start': 1, 'end': 50, 'terrains': [TerrainType.PLAIN]}


# ── 3星时间阈值（PRD v1.1 分阶段放宽）──

STAR3_TIME_THRESHOLDS = {
    (1, 50): 0.50,      # 剩余时间 ≥ 50%
    (51, 100): 0.40,    # 剩余时间 ≥ 40%
    (101, 150): 0.35,   # 剩余时间 ≥ 35%
    (151, 200): 0.30,   # 剩余时间 ≥ 30%
}

STAR3_COLLECT_RATE = 0.80  # 收集率 ≥ 80%


def get_star3_time_threshold(level_num):
    """获取关卡3星时间阈值（剩余时间占比）"""
    for (start, end), threshold in STAR3_TIME_THRESHOLDS.items():
        if start <= level_num <= end:
            return threshold
    return 0.50


def calc_stars(level_num, level_coins, target_coins, remaining_time, total_time, collection_rate):
    """计算关卡星级

    Args:
        level_num: 关卡号
        level_coins: 玩家对战金币
        target_coins: 目标金币
        remaining_time: 剩余时间（秒）
        total_time: 总时间（秒）
        collection_rate: 收集率（0-1）

    Returns:
        星级（0-3）
    """
    if level_coins < target_coins:
        return 0  # 未通关

    stars = 1  # ★☆☆ 通关

    if total_time > 0 and remaining_time / total_time >= 0.30:
        stars = 2  # ★★☆ 剩余≥30%

    time_threshold = get_star3_time_threshold(level_num)
    if (total_time > 0
            and remaining_time / total_time >= time_threshold
            and collection_rate >= STAR3_COLLECT_RATE):
        stars = 3  # ★★★ 满足阶段时间阈值 + 收集率≥80%

    return stars
