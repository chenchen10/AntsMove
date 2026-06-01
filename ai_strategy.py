"""AI智能策略模块：区域权重打分 + 兵力分配 + 蚂蚁类型偏好 + 昆虫目标评分

核心规则：
- AI目标选择基于区域权重打分（基础分 = 倍率/距离）
- 高速蚂蚁偏好远距离高倍率区域
- 高负重蚂蚁偏好就近基础区域
- 20%随机扰动避免AI过于一致
- 4种兵力分配策略根据战场态势切换
- 第二期：昆虫目标评分（甜点权重 vs 昆虫权重统一选择）
"""

import math
import random
from config import ZONE_CONFIG, SCREEN_WIDTH, WORLD_WIDTH
from region import get_zone_for_x
from balance_config import (
    get_stage_scaling, get_ai_difficulty_coeff, get_high_value_bonus,
    DEFAULT_AI_DIFFICULTY,
)
from creature_sprite import Creature


# ── 蚂蚁类型分类阈值（基于base_stats） ──

SPEED_HIGH_THRESHOLD = 220   # base_speed >= 220 视为高速蚂蚁
CARRY_HIGH_THRESHOLD = 75    # base_carry >= 75 视为高负重蚂蚁

# ── 权重配置 ──

ZONE_DISTANCE_PENALTY = 0.0003   # 距离衰减系数
HOME_TERRITORY_BONUS = 1.30      # 主场加成 +30%
SPEED_LONG_RANGE_BONUS = 1.20    # 高速蚂蚁远距离偏好
CARRY_LOCAL_BONUS = 1.10         # 高负重蚂蚁就近偏好
RANDOM_PERTURBATION = 0.20       # 随机扰动幅度 ±20%

# ── 兵力分配策略常量 ──

# 开局前15秒：争夺中路
RUSH_CENTER_DURATION = 15.0
RUSH_CENTER_RATIO = {'center': 0.50, 'left': 0.30, 'right': 0.20}

# 中路甜点清空时：分散发育
SCATTER_RATIO = {'center': 0.20, 'left': 0.40, 'right': 0.40}

# 敌方兵力集中时：集中突袭
RAID_ENEMY_RATIO = {'center': 0.20, 'left': 0.10, 'right': 0.70}  # 30%突袭右侧空虚区

# 本方基地附近有敌方时：稳守主场
DEFEND_HOME_RATIO = {'center': 0.30, 'left': 0.50, 'right': 0.20}  # 50%留守左侧主场


def classify_ant_type(ant):
    """根据基础属性分类蚂蚁类型

    Returns:
        'speed' | 'carry' | 'balanced'
    """
    base_speed = ant.ant_data['base_speed']
    base_carry = ant.ant_data['base_carry']

    if base_speed >= SPEED_HIGH_THRESHOLD:
        return 'speed'
    if base_carry >= CARRY_HIGH_THRESHOLD:
        return 'carry'
    return 'balanced'


def _zone_center_x(zone_name):
    """获取区域中心X坐标"""
    x_min, x_max = ZONE_CONFIG[zone_name]['x_range']
    return (x_min + x_max) / 2


def _dist_to_zone(ant_x, ant_y, zone_name):
    """计算蚂蚁到区域中心的距离"""
    cx = _zone_center_x(zone_name)
    y_min, y_max = ZONE_CONFIG[zone_name]['y_range']
    cy = (y_min + y_max) / 2
    return math.hypot(cx - ant_x, cy - ant_y)


def _is_home_territory(zone_name, ant_team):
    """判断区域是否为本方主场

    玩家（player）主场在左侧区域
    AI（ai）主场在右侧区域
    """
    if ant_team == 'player':
        return zone_name == 'left'
    else:
        return zone_name == 'right'


def score_sweet(ant, sweet, zone_manager, game_time=0.0, ai_ants=None, player_ants=None):
    """为单个甜点计算权重打分

    基础分 = 区域倍率 / 距离衰减
    叠加主场加成、类型偏好、随机扰动

    Returns:
        float: 甜点得分（越高越优先）
    """
    if zone_manager is None:
        zone = None
        multiplier = 1.0
    else:
        zone = zone_manager.get_zone_for_sweet(sweet)
        multiplier = zone_manager.get_multiplier_for_sweet(sweet)

    dist = math.hypot(sweet.x - ant.x, sweet.y - ant.y)
    dist = max(dist, 1.0)  # 避免除零

    # 基础分 = 倍率 / 距离衰减
    base_score = multiplier / (1.0 + dist * ZONE_DISTANCE_PENALTY)

    # 主场加成
    if zone and _is_home_territory(zone, ant.team):
        base_score *= HOME_TERRITORY_BONUS

    # 蚂蚁类型偏好
    ant_type = classify_ant_type(ant)
    if ant_type == 'speed':
        # 高速蚂蚁：远距离高倍率区域偏好
        if dist > 800:
            base_score *= SPEED_LONG_RANGE_BONUS
        # 高速蚂蚁略偏好高倍率区域
        if multiplier >= 1.5:
            base_score *= 1.10
    elif ant_type == 'carry':
        # 高负重蚂蚁：就近基础区域偏好
        if dist < 500:
            base_score *= CARRY_LOCAL_BONUS
        # 高负重蚂蚁略偏好低倍率（近）区域
        if multiplier <= 1.0:
            base_score *= 1.05

    # 20%随机扰动
    perturbation = 1.0 + random.uniform(-RANDOM_PERTURBATION, RANDOM_PERTURBATION)
    base_score *= perturbation

    return base_score


def choose_target_sweet(ant, alive_sweets, zone_manager, game_time=0.0,
                        ai_ants=None, player_ants=None):
    """为AI蚂蚁选择最优目标甜点

    对所有存活甜点进行加权打分，返回得分最高的甜点。

    Returns:
        sweet object or None
    """
    if not alive_sweets:
        return None

    scored = []
    for sweet in alive_sweets:
        score = score_sweet(ant, sweet, zone_manager, game_time, ai_ants, player_ants)
        scored.append((score, sweet))

    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[0][1]


# ── 第二期：昆虫目标评分 ──

INSECT_DISTANCE_PENALTY = 0.0005  # 昆虫距离衰减系数（与甜点接近，确保AI蚂蚁能有效选择远处昆虫）


def score_creature(ant, creature, zone_manager, game_time=0.0,
                   ai_difficulty=None):
    """为单个昆虫计算权重打分

    AI权重公式：
    昆虫权重 = insect金币 × 区域倍率 × 阶段倍率 × 难度系数 / (1 + 距离/500)
    高价值加成：额外 ×1.3

    Returns:
        float: 昆虫得分（越高越优先）
    """
    dist = math.hypot(creature.x - ant.x, creature.y - ant.y)
    dist = max(dist, 1.0)

    # 区域倍率
    if zone_manager:
        multiplier = zone_manager.get_multiplier_for_sweet(creature)
    else:
        multiplier = 1.0

    # 阶段倍率
    stage_mult = get_stage_scaling(game_time)

    # 难度系数
    diff_coeff = get_ai_difficulty_coeff(ai_difficulty)

    # 高价值加成
    high_value = get_high_value_bonus(creature.coin_per)

    # 基础分 = 金币 × 区域倍率 × 阶段倍率 × 难度系数 / (1 + 距离/500)
    base_score = (creature.coin_per * multiplier * stage_mult * diff_coeff * high_value
                  / (1.0 + dist * INSECT_DISTANCE_PENALTY))

    # 主场加成
    zone = get_zone_for_x(creature.x)
    if _is_home_territory(zone, ant.team):
        base_score *= HOME_TERRITORY_BONUS

    # 蚂蚁类型偏好（同甜点逻辑）
    ant_type = classify_ant_type(ant)
    if ant_type == 'speed':
        if dist > 800:
            base_score *= SPEED_LONG_RANGE_BONUS
        if multiplier >= 1.5:
            base_score *= 1.10
    elif ant_type == 'carry':
        if dist < 500:
            base_score *= CARRY_LOCAL_BONUS
        if multiplier <= 1.0:
            base_score *= 1.05

    # 20%随机扰动
    perturbation = 1.0 + random.uniform(-RANDOM_PERTURBATION, RANDOM_PERTURBATION)
    base_score *= perturbation

    return base_score


def choose_target(ant, alive_sweets, alive_creatures, zone_manager,
                  game_time=0.0, ai_ants=None, player_ants=None,
                  ai_difficulty=None):
    """统一目标选择：对甜点和昆虫进行加权打分，返回得分最高的目标

    甜点权重 = sweet.coin_per × 区域倍率 / (1 + 距离/500)
    昆虫权重 = insect金币 × 区域倍率 × 阶段倍率 × 难度系数 / (1 + 距离/500)

    Returns:
        sweet/creature object or None
    """
    best_target = None
    best_score = -1.0

    # 甜点评分（使用现有逻辑）
    for sweet in alive_sweets:
        score = score_sweet(ant, sweet, zone_manager, game_time, ai_ants, player_ants)
        if score > best_score:
            best_score = score
            best_target = sweet

    # 昆虫评分
    for creature in alive_creatures:
        score = score_creature(ant, creature, zone_manager, game_time, ai_difficulty)
        if score > best_score:
            best_score = score
            best_target = creature

    return best_target


def determine_army_strategy(game_time, ai_ants, player_ants, ai_grinder,
                            zone_sweet_counts=None):
    """根据战场态势决定兵力分配策略

    Returns:
        dict: {zone_name: ratio} 各区域兵力分配比例
    """
    # 策略1：争夺中路（开局前15秒）
    if game_time < RUSH_CENTER_DURATION:
        return RUSH_CENTER_RATIO.copy()

    # 策略2：稳守主场（本方基地附近有敌方）
    if ai_grinder and player_ants:
        for p_ant in player_ants:
            if p_ant.state in ('idle', 'moving_to_sweet'):
                dist = math.hypot(p_ant.x - ai_grinder.x, p_ant.y - ai_grinder.y)
                if dist < 400:
                    return DEFEND_HOME_RATIO.copy()

    # 策略3：集中突袭（检测敌方兵力集中）
    if player_ants and zone_sweet_counts:
        # 检查玩家是否集中在某个区域
        zone_counts = {'left': 0, 'center': 0, 'right': 0}
        for p_ant in player_ants:
            for zone_name, cfg in ZONE_CONFIG.items():
                x_min, x_max = cfg['x_range']
                if x_min <= p_ant.x <= x_max:
                    zone_counts[zone_name] += 1
                    break

        # 如果玩家集中在某个区域（>60%兵力），则突袭空虚区域
        total = len(player_ants) or 1
        for zone_name, count in zone_counts.items():
            if count / total > 0.6:
                # 找到玩家最少的区域
                empty_zone = min(zone_counts, key=zone_counts.get)
                ratios = {'center': 0.20, 'left': 0.20, 'right': 0.60}
                ratios[empty_zone] = 0.60
                ratios[zone_name] = 0.10
                # 确保总和为1
                total_r = sum(ratios.values())
                ratios = {k: v / total_r for k, v in ratios.items()}
                return ratios

    # 策略4：分散发育（中路甜点被清空时）
    if zone_sweet_counts:
        center_count = zone_sweet_counts.get('center', 0)
        if center_count <= 2:
            return SCATTER_RATIO.copy()

    # 默认：均衡分配
    return {'center': 0.40, 'left': 0.30, 'right': 0.30}


def assign_zone_for_ant(ant, strategy_ratios, zone_manager, game_time=0.0):
    """根据兵力分配策略为蚂蚁指定目标区域

    使用随机加权选择，使蚂蚁分散到各区域。

    Returns:
        str: 目标区域名称
    """
    zones = list(strategy_ratios.keys())
    weights = list(strategy_ratios.values())

    # 归一化权重
    total_w = sum(weights)
    if total_w <= 0:
        return random.choice(zones)
    weights = [w / total_w for w in weights]

    # 加权随机选择
    r = random.random()
    cumulative = 0.0
    for zone, weight in zip(zones, weights):
        cumulative += weight
        if r <= cumulative:
            return zone
    return zones[-1]


def filter_sweets_by_zone(sweets, zone_name):
    """筛选指定区域内的甜点"""
    cfg = ZONE_CONFIG.get(zone_name)
    if not cfg:
        return []
    x_min, x_max = cfg['x_range']
    return [s for s in sweets if s.alive and x_min <= s.x <= x_max]
