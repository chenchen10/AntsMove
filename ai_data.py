"""AI蚂蚁系统：固定梯队池 + 独立属性成长 + 后期Buff

核心规则：
- 只镜像玩家【数量】，不镜像种类和属性
- 敌方从当前梯队固定池中生成，固定种子保证同关卡永远同样阵容
- 敌方属性 = 蚂蚁base × 阶段倍率 × 每10关1.12递进，封顶90%满级
- 151关后全体敌方额外Buff
"""

import random
from ants_data import (
    ANTS, ANT_BY_ID, MAX_ATTR_LEVEL,
    get_carry_capacity, get_speed, get_defense,
)


# ── 配置数据 ──

# 上阵上限表（起始关, 结束关, 起始上限, 结束上限）
_TEAM_SIZE_TABLE = [
    (1,   10,  1,  3),
    (11,  20,  4,  4),
    (21,  35,  5,  5),
    (36,  50,  7,  7),
    (51,  70,  8,  10),
    (71,  90,  11, 13),
    (91,  100, 15, 15),
    (101, 120, 16, 18),
    (121, 140, 19, 21),
    (141, 150, 22, 22),
    (151, 170, 23, 26),
    (171, 199, 27, 29),
    (200, 200, 30, 30),
]

# 阶段基准倍率（起始关, 结束关, 倍率）
_STAGE_DIFF_MULT = [
    (1,   50,  1.00),
    (51,  100, 1.05),
    (101, 150, 1.10),
    (151, 200, 1.15),
]

# 梯队区间（梯队号, 起始关, 结束关）
_STAGE_TIERS = [
    (1, 1,   50),
    (2, 51,  100),
    (3, 101, 150),
    (4, 151, 200),
]


def get_max_team_size(level):
    """根据关卡返回上阵上限（1-30只）"""
    if level <= 10:
        _early = [1, 1, 2, 2, 2, 2, 3, 3, 3, 3]
        return _early[level - 1]
    for start, end, size_start, size_end in _TEAM_SIZE_TABLE:
        if start <= level <= end:
            if size_start == size_end:
                return size_start
            ratio = (level - start) / max(1, (end - start))
            return round(size_start + ratio * (size_end - size_start))
    return 30


# ── 固定梯队池（每关卡只从当前梯队选最强蚂蚁）──

_TIER_POOLS = {
    1: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],      # 1-50关
    2: [12, 13, 14, 15, 16, 17, 18],                # 51-100关
    3: [19, 20, 21, 22, 23],                         # 101-150关
    4: [24, 25, 26],                                 # 151-200关
}


def _get_tier(level):
    """获取关卡所属梯队（1-4）"""
    for tier, start, end in _STAGE_TIERS:
        if start <= level <= end:
            return tier
    return 4


def _get_stage_mult(level):
    """获取关卡阶段基准倍率"""
    for start, end, mult in _STAGE_DIFF_MULT:
        if start <= level <= end:
            return mult
    return 1.15


def get_ai_level_multiplier(level):
    """敌方递进系数：每10关 ×1.12

    1-10关=1.0, 11-20关=1.12, 21-30关=1.2544, ...
    """
    decile = (level - 1) // 10
    return 1.12 ** decile


def generate_ai_team(level, count):
    """生成AI出战队伍（固定种子，同关卡永远同样阵容）

    从当前梯队池中抽取，不镜像玩家种类。

    Returns:
        list of ant_id
    """
    tier = _get_tier(level)
    pool = _TIER_POOLS[tier]

    team = []
    rng = random.Random(level * 1000 + count)  # 固定种子，可重现
    for _ in range(count):
        ant_id = rng.choice(pool)
        team.append(ant_id)
    return team


# ── AI独立属性计算 ──


def get_ai_ant_stats(ant_id, level):
    """计算AI蚂蚁在指定关卡的最终属性

    公式：base × 阶段倍率 × 递进系数，封顶90%满级值
    注意：封顶值需预扣特性加成（如TRAIT_SUPREME +30%搬运），
    因为 _apply_trait_bonuses 会在 main.py 设置属性后再应用特性。

    Returns:
        (carry, speed, defense) 三元组
    """
    ant = ANT_BY_ID[ant_id]

    stage_mult = _get_stage_mult(level)
    level_mult = get_ai_level_multiplier(level)
    total_mult = stage_mult * level_mult

    # 90%封顶，预扣特性加成
    from ants_data import (
        TRAIT_SUPREME, TRAIT_ALL_15, TRAIT_ALL_CARRY_15, TRAIT_ALL_CARRY_20,
    )
    trait = ant['trait']

    # 搬运封顶：预扣特性倍率，确保特性加成后仍≤90%
    carry_trait_mult = 1.0
    if trait == TRAIT_SUPREME:
        carry_trait_mult = 1.3
    elif trait == TRAIT_ALL_15:
        carry_trait_mult = 1.15
    elif trait == TRAIT_ALL_CARRY_15:
        carry_trait_mult = 1.15
    elif trait == TRAIT_ALL_CARRY_20:
        carry_trait_mult = 1.20
    max_carry = get_carry_capacity(ant_id, MAX_ATTR_LEVEL) * 0.9 / carry_trait_mult

    # 速度封顶：预扣特性倍率
    speed_trait_mult = 1.0
    if trait == TRAIT_ALL_15:
        speed_trait_mult = 1.15
    max_speed = get_speed(ant_id, MAX_ATTR_LEVEL) * 0.9 / speed_trait_mult

    # 防御无特性加成
    max_defense = get_defense(ant_id, MAX_ATTR_LEVEL) * 0.9

    carry = int(min(ant['base_carry'] * total_mult, max_carry))
    speed = int(min(ant['base_speed'] * total_mult, max_speed))
    defense = int(min(ant['base_defense'] * total_mult, max_defense))

    return carry, speed, defense


def get_ai_late_buffs(level):
    """获取151关后敌方全体额外Buff参数

    Returns:
        dict with buff values, empty dict if no buffs
    """
    if level < 151:
        return {}
    return {
        'terrain_debuff_reduction': 0.20,   # 地形负面减免20%
        'stun_reduction': 0.15,             # 碰撞僵直时长减15%
    }


def is_ai_boss_level(level):
    """是否为200关Boss关"""
    return level == 200
