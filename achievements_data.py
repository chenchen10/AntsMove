"""成就系统数据：5大维度成就定义与进度检测

数据结构说明：
  ConditionType: 成就解锁条件类型枚举
  ACHIEVEMENTS:  成就配置表，约20个成就覆盖5大维度
  每个成就字段：
    - id:              成就唯一ID（前缀: C=收集, H=挑战, S=星级, E=探索, G=养成）
    - category:        所属维度（收集/挑战/星级/探索/养成）
    - name:            成就名称
    - desc:            成就描述（展示给玩家）
    - condition_type:  解锁条件类型（ConditionType枚举）
    - threshold:       解锁阈值（与condition_type配合判定）
    - rewards:         奖励内容 {'coins': int, 'exp': int, 'special': str|None}
    - icon_text:       成就图标（UI中显示的emoji）

存档格式（v5）：
  achievements: {achievement_id: {'progress': int, 'claimed': bool}}
"""

from enum import Enum


# ── 解锁条件类型枚举 ──

class ConditionType(Enum):
    """成就解锁条件类型

    每种类型对应一个可从SaveManager读取的统计指标，
    evaluate_achievements() 根据类型调用对应的统计函数。
    """
    TOTAL_LEVELS_CLEARED = 'total_levels_cleared'   # 累计通关次数（含重复挑战）
    STARS_EARNED         = 'stars_earned'            # 累计获得星级总数
    ANTS_OWNED           = 'ants_owned'              # 拥有蚂蚁总数量
    ANTS_UNIQUE          = 'ants_unique'             # 拥有蚂蚁种类数
    TERRAINS_EXPLORED    = 'terrains_explored'       # 探索地形种类数
    COINS_EARNED         = 'coins_earned'            # 累计获得金币数
    MAX_LEVEL            = 'max_level'               # 最高通关关卡编号
    MAX_CARRY_LEVEL      = 'max_carry_level'         # 蚂蚁搬运属性最高等级
    MAX_SPEED_LEVEL      = 'max_speed_level'         # 蚂蚁速度属性最高等级
    MAX_DEFENSE_LEVEL    = 'max_defense_level'       # 蚂蚁防御属性最高等级
    MAXED_ANTS           = 'maxed_ants'              # 满级蚂蚁种类数


# ── 成就维度（Tab分类）──

ACHIEVE_CATEGORIES = ['收集', '挑战', '星级', '探索', '养成']


# ── 成就配置表 ──
# 每个维度覆盖不同难度梯度，共20个成就

ACHIEVEMENTS = [
    # ── 收集维度（4个）── 拥有蚂蚁数量 / 种类
    {
        'id': 'C1', 'category': '收集', 'name': '初出茅庐',
        'desc': '拥有1只蚂蚁',
        'condition_type': ConditionType.ANTS_OWNED, 'threshold': 1,
        'rewards': {'coins': 50, 'exp': 0, 'special': None},
        'icon_text': '🐜',
    },
    {
        'id': 'C2', 'category': '收集', 'name': '小有积蓄',
        'desc': '拥有5只蚂蚁',
        'condition_type': ConditionType.ANTS_OWNED, 'threshold': 5,
        'rewards': {'coins': 200, 'exp': 0, 'special': None},
        'icon_text': '🐜',
    },
    {
        'id': 'C3', 'category': '收集', 'name': '种类收藏家',
        'desc': '拥有10种不同蚂蚁',
        'condition_type': ConditionType.ANTS_UNIQUE, 'threshold': 10,
        'rewards': {'coins': 500, 'exp': 0, 'special': None},
        'icon_text': '📦',
    },
    {
        'id': 'C4', 'category': '收集', 'name': '全种类收集',
        'desc': '拥有全部26种蚂蚁',
        'condition_type': ConditionType.ANTS_UNIQUE, 'threshold': 26,
        'rewards': {'coins': 3000, 'exp': 0, 'special': None},
        'icon_text': '🏆',
    },

    # ── 挑战维度（4个）── 通关进度 / 通关次数
    {
        'id': 'H1', 'category': '挑战', 'name': '小试牛刀',
        'desc': '通关第10关',
        'condition_type': ConditionType.MAX_LEVEL, 'threshold': 10,
        'rewards': {'coins': 100, 'exp': 0, 'special': None},
        'icon_text': '⭐',
    },
    {
        'id': 'H2', 'category': '挑战', 'name': '身经百战',
        'desc': '通关第50关',
        'condition_type': ConditionType.MAX_LEVEL, 'threshold': 50,
        'rewards': {'coins': 500, 'exp': 0, 'special': None},
        'icon_text': '⭐',
    },
    {
        'id': 'H3', 'category': '挑战', 'name': '百战百胜',
        'desc': '通关第100关',
        'condition_type': ConditionType.MAX_LEVEL, 'threshold': 100,
        'rewards': {'coins': 1500, 'exp': 0, 'special': None},
        'icon_text': '🏆',
    },
    {
        'id': 'H4', 'category': '挑战', 'name': '终极挑战者',
        'desc': '通关第200关',
        'condition_type': ConditionType.MAX_LEVEL, 'threshold': 200,
        'rewards': {'coins': 3000, 'exp': 0, 'special': None},
        'icon_text': '👑',
    },

    # ── 星级维度（4个）── 累计获得星级
    {
        'id': 'S1', 'category': '星级', 'name': '初获星光',
        'desc': '累计获得10颗星',
        'condition_type': ConditionType.STARS_EARNED, 'threshold': 10,
        'rewards': {'coins': 100, 'exp': 0, 'special': None},
        'icon_text': '🌟',
    },
    {
        'id': 'S2', 'category': '星级', 'name': '星光璀璨',
        'desc': '累计获得50颗星',
        'condition_type': ConditionType.STARS_EARNED, 'threshold': 50,
        'rewards': {'coins': 500, 'exp': 0, 'special': None},
        'icon_text': '🌟',
    },
    {
        'id': 'S3', 'category': '星级', 'name': '满天星光',
        'desc': '累计获得150颗星',
        'condition_type': ConditionType.STARS_EARNED, 'threshold': 150,
        'rewards': {'coins': 1500, 'exp': 0, 'special': None},
        'icon_text': '🌟',
    },
    {
        'id': 'S4', 'category': '星级', 'name': '星级大师',
        'desc': '累计获得300颗星',
        'condition_type': ConditionType.STARS_EARNED, 'threshold': 300,
        'rewards': {'coins': 3000, 'exp': 0, 'special': None},
        'icon_text': '👑',
    },

    # ── 探索维度（4个）── 地形探索 / 金币积累
    {
        'id': 'E1', 'category': '探索', 'name': '踏出第一步',
        'desc': '通关1个不同地形关卡',
        'condition_type': ConditionType.TERRAINS_EXPLORED, 'threshold': 1,
        'rewards': {'coins': 50, 'exp': 0, 'special': None},
        'icon_text': '🗺️',
    },
    {
        'id': 'E2', 'category': '探索', 'name': '地形探索者',
        'desc': '通关3种不同地形关卡',
        'condition_type': ConditionType.TERRAINS_EXPLORED, 'threshold': 3,
        'rewards': {'coins': 200, 'exp': 0, 'special': None},
        'icon_text': '🗺️',
    },
    {
        'id': 'E3', 'category': '探索', 'name': '全地形征服',
        'desc': '通关全部5种地形关卡',
        'condition_type': ConditionType.TERRAINS_EXPLORED, 'threshold': 5,
        'rewards': {'coins': 800, 'exp': 0, 'special': None},
        'icon_text': '🏆',
    },
    {
        'id': 'E4', 'category': '探索', 'name': '财富大亨',
        'desc': '累计获得50000金币',
        'condition_type': ConditionType.COINS_EARNED, 'threshold': 50000,
        'rewards': {'coins': 2000, 'exp': 0, 'special': None},
        'icon_text': '💰',
    },

    # ── 养成维度（4个）── 蚂蚁属性升级 / 满级
    {
        'id': 'G1', 'category': '养成', 'name': '初窥门径',
        'desc': '将任意蚂蚁搬运升到10级',
        'condition_type': ConditionType.MAX_CARRY_LEVEL, 'threshold': 10,
        'rewards': {'coins': 100, 'exp': 0, 'special': None},
        'icon_text': '⬆️',
    },
    {
        'id': 'G2', 'category': '养成', 'name': '速度之星',
        'desc': '将任意蚂蚁速度升到100级',
        'condition_type': ConditionType.MAX_SPEED_LEVEL, 'threshold': 100,
        'rewards': {'coins': 500, 'exp': 0, 'special': None},
        'icon_text': '🏃',
    },
    {
        'id': 'G3', 'category': '养成', 'name': '登峰造极',
        'desc': '将任意蚂蚁搬运升到100级',
        'condition_type': ConditionType.MAX_CARRY_LEVEL, 'threshold': 100,
        'rewards': {'coins': 1000, 'exp': 0, 'special': None},
        'icon_text': '⬆️',
    },
    {
        'id': 'G4', 'category': '养成', 'name': '全面发展',
        'desc': '拥有3只满级蚂蚁',
        'condition_type': ConditionType.MAXED_ANTS, 'threshold': 3,
        'rewards': {'coins': 2000, 'exp': 0, 'special': None},
        'icon_text': '🏅',
    },
]


# ── 索引表（模块加载时自动计算）──

ACHIEVEMENT_BY_ID = {a['id']: a for a in ACHIEVEMENTS}

ACHIEVEMENTS_BY_CATEGORY = {}
for cat in ACHIEVE_CATEGORIES:
    ACHIEVEMENTS_BY_CATEGORY[cat] = [a for a in ACHIEVEMENTS if a['category'] == cat]


# ── 条件类型 → 统计函数映射 ──

def _get_condition_stat(condition_type, sm):
    """根据条件类型从 SaveManager 读取当前统计值"""
    if condition_type == ConditionType.ANTS_OWNED:
        return sm.get_owned_count()
    elif condition_type == ConditionType.ANTS_UNIQUE:
        return len(sm.get_unique_owned_ants())
    elif condition_type == ConditionType.MAX_LEVEL:
        return sm.get_max_level()
    elif condition_type == ConditionType.STARS_EARNED:
        return sm.get_total_stars()
    elif condition_type == ConditionType.TOTAL_LEVELS_CLEARED:
        return sm.get_total_levels_won()
    elif condition_type == ConditionType.COINS_EARNED:
        return sm.get_total_coins()
    elif condition_type == ConditionType.TERRAINS_EXPLORED:
        return _count_terrains_explored(sm)
    elif condition_type == ConditionType.MAX_CARRY_LEVEL:
        return _get_max_attr(sm, 'carry')
    elif condition_type == ConditionType.MAX_SPEED_LEVEL:
        return _get_max_attr(sm, 'speed')
    elif condition_type == ConditionType.MAX_DEFENSE_LEVEL:
        return _get_max_attr(sm, 'defense')
    elif condition_type == ConditionType.MAXED_ANTS:
        return sm.get_maxed_count(200)
    return 0


def _get_max_attr(sm, attr):
    """获取所有蚂蚁中某属性的最高等级"""
    max_val = 0
    for ant_id in sm.get_unique_owned_ants():
        val = sm.get_ant_attr(ant_id, attr)
        if val > max_val:
            max_val = val
    return max_val


def _count_terrains_explored(sm):
    """统计已探索的不同地形数量"""
    terrains = set()
    from levels_data import get_level
    for lv in range(1, sm.get_max_level() + 1):
        try:
            level_data = get_level(lv)
            terrain = level_data.get('terrain_name', '')
            if terrain:
                terrains.add(terrain)
        except Exception:
            pass
    return len(terrains)


# ── 公共接口 ──

def evaluate_achievements(sm):
    """评估所有成就的当前进度

    Returns:
        dict: {achievement_id: {'current': int, 'unlocked': bool, 'claimed': bool}}
    """
    result = {}
    for ach in ACHIEVEMENTS:
        aid = ach['id']
        current = _get_condition_stat(ach['condition_type'], sm)
        claimed = sm.is_achievement_claimed(aid)
        unlocked = current >= ach['threshold']
        result[aid] = {
            'current': current,
            'unlocked': unlocked,
            'claimed': claimed,
        }
    return result


def claim_achievement(achievement_id, sm):
    """领取成就奖励（委托给SaveManager处理）

    先同步当前进度到持久化存储，再执行领取。
    Returns:
        (success: bool, reward_coins: int)
    """
    ach = ACHIEVEMENT_BY_ID.get(achievement_id)
    if ach:
        current = _get_condition_stat(ach['condition_type'], sm)
        sm.update_achievement_progress(achievement_id, current)
    return sm.claim_achievement_reward(achievement_id)


def get_total_progress(sm):
    """获取成就总进度

    Returns:
        (unlocked_count, total_count, claimed_count)
    """
    stats = evaluate_achievements(sm)
    unlocked = sum(1 for v in stats.values() if v['unlocked'])
    claimed = sum(1 for v in stats.values() if v['claimed'])
    return unlocked, len(ACHIEVEMENTS), claimed


def check_newly_unlocked(sm):
    """检测新解锁的成就（条件满足但尚未领取的）

    通过比较当前实时进度与存档中已记录的领取状态，
    找出所有已解锁但未领取的成就，用于触发解锁通知。

    Returns:
        list of dict: 新解锁成就列表，每项包含 id/name/desc/reward/icon_text/category
    """
    newly_unlocked = []
    for ach in ACHIEVEMENTS:
        aid = ach['id']
        current = _get_condition_stat(ach['condition_type'], sm)
        claimed = sm.is_achievement_claimed(aid)
        if current >= ach['threshold'] and not claimed:
            newly_unlocked.append({
                'id': aid,
                'name': ach['name'],
                'desc': ach['desc'],
                'reward': ach['rewards'].get('coins', 0),
                'icon_text': ach['icon_text'],
                'category': ach['category'],
            })
    return newly_unlocked
