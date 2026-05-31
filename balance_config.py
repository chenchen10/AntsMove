"""甜点 vs 昆虫经济平衡参数

控制AI对甜点和昆虫的目标选择权重，确保两种资源的经济价值合理匹配。
AI难度系数影响昆虫权重，高难度下AI更积极攻击昆虫。

阶段缩放：游戏不同阶段的经济倍率
- 阶段1（前期）: ×1.0
- 阶段2（中期）: ×2.5
- 阶段3（后期）: ×5.0
- 阶段4（终局）: ×8.0
"""

# ── 阶段缩放 ──

STAGE_SCALING = {
    1: 1.0,
    2: 2.5,
    3: 5.0,
    4: 8.0,
}


def get_stage_for_time(game_time):
    """根据游戏时间返回当前阶段

    Args:
        game_time: 游戏已进行时间（秒）

    Returns:
        int: 阶段编号（1-4）
    """
    if game_time < 60:
        return 1
    elif game_time < 180:
        return 2
    elif game_time < 360:
        return 3
    else:
        return 4


def get_stage_scaling(game_time):
    """获取当前阶段的经济缩放倍率"""
    stage = get_stage_for_time(game_time)
    return STAGE_SCALING[stage]


# ── AI难度系数 ──

AI_DIFFICULTY_COEFF = {
    'easy': 0.3,
    'medium': 0.6,
    'hard': 1.0,
}

# 默认难度（可在关卡数据中覆盖）
DEFAULT_AI_DIFFICULTY = 'medium'


def get_ai_difficulty_coeff(difficulty=None):
    """获取AI难度系数"""
    if difficulty is None:
        difficulty = DEFAULT_AI_DIFFICULTY
    return AI_DIFFICULTY_COEFF.get(difficulty, 0.6)


# ── 高价值目标加成 ──

HIGH_VALUE_BONUS = 1.3   # 金币>=15的昆虫额外×1.3加成
HIGH_VALUE_THRESHOLD = 15  # 高价值金币阈值


def get_high_value_bonus(coin_per):
    """判断昆虫是否为高价值目标，返回加成倍率"""
    if coin_per >= HIGH_VALUE_THRESHOLD:
        return HIGH_VALUE_BONUS
    return 1.0
