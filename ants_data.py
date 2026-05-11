"""26只蚂蚁完整数据体系

每只蚂蚁包含：
- 序号、名称、基础搬运/速度/防御、购买金币、解锁关卡
- 核心定位、专属特性代码
- 三属性独立升级金币梯度（200级）
"""

# ── 升级金币生成 ──

def _gen_upgrade_costs(base_price, ant_index):
    """生成200级升级金币梯度（搬运属性用）"""
    costs = []
    for i in range(50):
        costs.append(int(base_price * (1.0 + i * 0.08)))
    for i in range(50):
        costs.append(int(base_price * (5.0 + i * 0.18)))
    for i in range(50):
        costs.append(int(base_price * (14.0 + i * 0.35)))
    for i in range(50):
        costs.append(int(base_price * (31.5 + i * 0.55)))
    return costs


def _gen_speed_costs(base_price):
    """速度升级金币梯度（比搬运便宜40%）"""
    costs = []
    for i in range(50):
        costs.append(int(base_price * 0.6 * (1.0 + i * 0.06)))
    for i in range(50):
        costs.append(int(base_price * 0.6 * (4.0 + i * 0.15)))
    for i in range(50):
        costs.append(int(base_price * 0.6 * (11.0 + i * 0.28)))
    for i in range(50):
        costs.append(int(base_price * 0.6 * (25.0 + i * 0.45)))
    return costs


def _gen_defense_costs(base_price):
    """防御升级金币梯度（比搬运便宜30%）"""
    costs = []
    for i in range(50):
        costs.append(int(base_price * 0.7 * (1.0 + i * 0.07)))
    for i in range(50):
        costs.append(int(base_price * 0.7 * (4.5 + i * 0.16)))
    for i in range(50):
        costs.append(int(base_price * 0.7 * (12.0 + i * 0.30)))
    for i in range(50):
        costs.append(int(base_price * 0.7 * (28.0 + i * 0.48)))
    return costs


# 蚂蚁序号 -> 基础价格映射
_ANT_BASE_PRICES = [
    100, 200, 300, 400, 500, 600, 1200, 1500, 2700, 2900,
    3000, 3400, 4000, 5700, 6000, 6400, 6700, 7500, 8000, 8400,
    8900, 9000, 9100, 9300, 9900, 10000,
]

# ── 特性类型常量 ──
TRAIT_EXP_BONUS = 'exp_bonus'
TRAIT_DESERT_IMMUNE = 'desert_immune'
TRAIT_GROUND_SPEED = 'ground_speed'
TRAIT_FOREST_EAT = 'forest_eat'
TRAIT_ICE_IMMUNE = 'ice_immune'
TRAIT_STUN_HALF = 'stun_half'
TRAIT_TROPICAL_HALF = 'tropical_half'
TRAIT_DESERT_FULL = 'desert_full'
TRAIT_ALL_TERRAIN = 'all_terrain'
TRAIT_COLD_IMMUNE = 'cold_immune'
TRAIT_KNOCKBACK_10 = 'knockback_10'
TRAIT_PLAIN_BONUS = 'plain_bonus'
TRAIT_MOUNTAIN_SPEED = 'mountain_speed'
TRAIT_TROPICAL_EAT = 'tropical_eat'
TRAIT_STUN_IMMUNE = 'stun_immune'
TRAIT_KNOCKBACK_20 = 'knockback_20'
TRAIT_HEAVY_CARRY = 'heavy_carry'
TRAIT_ALL_CARRY_15 = 'all_carry_15'
TRAIT_DEBUFF_IMMUNE = 'debuff_immune'
TRAIT_STUN_30 = 'stun_30'
TRAIT_EAT_50 = 'eat_50'
TRAIT_ALL_CARRY_20 = 'all_carry_20'
TRAIT_CLIMB_SPEED = 'climb_speed'
TRAIT_STEAL_50 = 'steal_50'
TRAIT_ALL_15 = 'all_15'
TRAIT_SUPREME = 'supreme'

# ── 地形适配标签 ──
TERRAIN_PLAIN = 'plain'
TERRAIN_FOREST = 'forest'
TERRAIN_DESERT = 'desert'
TERRAIN_MOUNTAIN = 'mountain'
TERRAIN_TROPICAL = 'tropical'
TERRAIN_CONSTRUCTION = 'construction'
TERRAIN_TREE_TOP = 'tree_top'
TERRAIN_ICE = 'ice'

# ── 26只蚂蚁完整数据（顺序不可更改）──
# base_carry: 基础搬运量
# base_speed: 基础移动速度
# base_defense: 基础防御值（减少被碰撞伤害/僵直时间）

ANTS = [
    {'id': 1,  'name': '普通路边小草蚁', 'base_carry': 1,   'base_speed': 180, 'base_defense': 5,
     'buy_cost': 100,   'unlock_level': 1,   'role': '新手入门',
     'trait': TRAIT_EXP_BONUS,       'trait_desc': '搬运量+20%',                  'terrain': TERRAIN_PLAIN},
    {'id': 2,  'name': '沙蚁',          'base_carry': 2,   'base_speed': 190, 'base_defense': 8,
     'buy_cost': 200,   'unlock_level': 2,   'role': '沙漠适配',
     'trait': TRAIT_DESERT_IMMUNE,   'trait_desc': '沙漠地形无减速，免干旱僵直',   'terrain': TERRAIN_DESERT},
    {'id': 3,  'name': '土蚁',          'base_carry': 3,   'base_speed': 185, 'base_defense': 12,
     'buy_cost': 300,   'unlock_level': 3,   'role': '平原地面',
     'trait': TRAIT_GROUND_SPEED,    'trait_desc': '地面关卡返回速度+20%',         'terrain': TERRAIN_PLAIN},
    {'id': 4,  'name': '野生小黑林蚁',  'base_carry': 4,   'base_speed': 195, 'base_defense': 10,
     'buy_cost': 400,   'unlock_level': 4,   'role': '林地适配',
     'trait': TRAIT_FOREST_EAT,      'trait_desc': '林地甜食啃食速度+20%',         'terrain': TERRAIN_FOREST},
    {'id': 5,  'name': '欧洲毛蚁',      'base_carry': 5,   'base_speed': 200, 'base_defense': 15,
     'buy_cost': 500,   'unlock_level': 5,   'role': '山地寒冰',
     'trait': TRAIT_ICE_IMMUNE,      'trait_desc': '免冰冻减速，山地适配',         'terrain': TERRAIN_ICE},
    {'id': 6,  'name': '欧洲举腹蚁',    'base_carry': 6,   'base_speed': 185, 'base_defense': 18,
     'buy_cost': 600,   'unlock_level': 6,   'role': '新手过渡',
     'trait': TRAIT_STUN_HALF,       'trait_desc': '碰撞僵直时间减半',             'terrain': TERRAIN_PLAIN},
    {'id': 7,  'name': '澳洲多刺蚁',    'base_carry': 12,  'base_speed': 190, 'base_defense': 20,
     'buy_cost': 1200,  'unlock_level': 7,   'role': '热带丛林',
     'trait': TRAIT_TROPICAL_HALF,   'trait_desc': '热带负面效果时长减半',         'terrain': TERRAIN_TROPICAL},
    {'id': 8,  'name': '沙漠家蚁',      'base_carry': 15,  'base_speed': 200, 'base_defense': 22,
     'buy_cost': 1500,  'unlock_level': 8,   'role': '极限沙漠',
     'trait': TRAIT_DESERT_FULL,     'trait_desc': '免疫沙漠所有干旱高温效果',     'terrain': TERRAIN_DESERT},
    {'id': 9,  'name': '中华毛蚁',      'base_carry': 27,  'base_speed': 210, 'base_defense': 25,
     'buy_cost': 2700,  'unlock_level': 9,   'role': '全地形通用',
     'trait': TRAIT_ALL_TERRAIN,     'trait_desc': '全地形无负面减速',             'terrain': None},
    {'id': 10, 'name': '长毛蚁',        'base_carry': 29,  'base_speed': 205, 'base_defense': 28,
     'buy_cost': 2900,  'unlock_level': 10,  'role': '寒冰山地',
     'trait': TRAIT_COLD_IMMUNE,     'trait_desc': '免疫冰冻减速，耐寒拉满',       'terrain': TERRAIN_ICE},
    {'id': 11, 'name': '红毛蚁',        'base_carry': 30,  'base_speed': 210, 'base_defense': 30,
     'buy_cost': 3000,  'unlock_level': 11,  'role': '基础对抗',
     'trait': TRAIT_KNOCKBACK_10,    'trait_desc': '10%概率击退敌方蚂蚁',          'terrain': TERRAIN_PLAIN},
    {'id': 12, 'name': '平原弓背蚁',    'base_carry': 34,  'base_speed': 215, 'base_defense': 32,
     'buy_cost': 3400,  'unlock_level': 51,  'role': '平原核心',
     'trait': TRAIT_PLAIN_BONUS,     'trait_desc': '平原搬运能力+10%',             'terrain': TERRAIN_PLAIN},
    {'id': 13, 'name': '山地弓背蚁',    'base_carry': 40,  'base_speed': 225, 'base_defense': 35,
     'buy_cost': 4000,  'unlock_level': 61,  'role': '山地核心',
     'trait': TRAIT_MOUNTAIN_SPEED,  'trait_desc': '山地爬坡无减速，移速+20%',     'terrain': TERRAIN_MOUNTAIN},
    {'id': 14, 'name': '热带切叶蚁',    'base_carry': 57,  'base_speed': 200, 'base_defense': 25,
     'buy_cost': 5700,  'unlock_level': 71,  'role': '热带切割',
     'trait': TRAIT_TROPICAL_EAT,    'trait_desc': '热带甜食啃食效率+30%',         'terrain': TERRAIN_TROPICAL},
    {'id': 15, 'name': '刺猛蚁',        'base_carry': 60,  'base_speed': 195, 'base_defense': 40,
     'buy_cost': 6000,  'unlock_level': 81,  'role': '防御对抗',
     'trait': TRAIT_STUN_IMMUNE,     'trait_desc': '免碰撞僵直，反弹10%干扰',      'terrain': TERRAIN_MOUNTAIN},
    {'id': 16, 'name': '兵猛蚁',        'base_carry': 64,  'base_speed': 210, 'base_defense': 38,
     'buy_cost': 6400,  'unlock_level': 85,  'role': '强攻击对抗',
     'trait': TRAIT_KNOCKBACK_20,    'trait_desc': '20%概率主动击退敌方',          'terrain': TERRAIN_CONSTRUCTION},
    {'id': 17, 'name': '工地大头蚁',    'base_carry': 67,  'base_speed': 190, 'base_defense': 35,
     'buy_cost': 6700,  'unlock_level': 91,  'role': '工地适配',
     'trait': TRAIT_HEAVY_CARRY,     'trait_desc': '搬运重物无减速，效率+20%',     'terrain': TERRAIN_CONSTRUCTION},
    {'id': 18, 'name': '黑褐举腹蚁',    'base_carry': 75,  'base_speed': 205, 'base_defense': 30,
     'buy_cost': 7500,  'unlock_level': 100, 'role': '中期核心',
     'trait': TRAIT_ALL_CARRY_15,    'trait_desc': '全地形搬运+15%',               'terrain': None},
    {'id': 19, 'name': '长刺多刺蚁',    'base_carry': 80,  'base_speed': 200, 'base_defense': 45,
     'buy_cost': 8000,  'unlock_level': 101, 'role': '极限防御',
     'trait': TRAIT_DEBUFF_IMMUNE,   'trait_desc': '免疫所有敌方负面效果',         'terrain': None},
    {'id': 20, 'name': '热带火蚁',      'base_carry': 84,  'base_speed': 215, 'base_defense': 35,
     'buy_cost': 8400,  'unlock_level': 111, 'role': '热带对抗',
     'trait': TRAIT_STUN_30,         'trait_desc': '30%概率让敌方僵直2秒',        'terrain': TERRAIN_TROPICAL},
    {'id': 21, 'name': '巨首切叶蚁',    'base_carry': 89,  'base_speed': 200, 'base_defense': 40,
     'buy_cost': 8900,  'unlock_level': 121, 'role': '高血量甜食',
     'trait': TRAIT_EAT_50,          'trait_desc': '甜食啃食效率+50%，高血量+20%', 'terrain': TERRAIN_TROPICAL},
    {'id': 22, 'name': '美洲切叶蚁',    'base_carry': 90,  'base_speed': 210, 'base_defense': 38,
     'buy_cost': 9000,  'unlock_level': 131, 'role': '后期通用',
     'trait': TRAIT_ALL_CARRY_20,    'trait_desc': '全地形搬运+20%，无负面',       'terrain': None},
    {'id': 23, 'name': '黑织叶蚁',      'base_carry': 91,  'base_speed': 230, 'base_defense': 30,
     'buy_cost': 9100,  'unlock_level': 141, 'role': '树栖高空',
     'trait': TRAIT_CLIMB_SPEED,     'trait_desc': '攀爬无减速，移速+30%',         'terrain': TERRAIN_TREE_TOP},
    {'id': 24, 'name': '长颚猛蚁',      'base_carry': 93,  'base_speed': 220, 'base_defense': 35,
     'buy_cost': 9300,  'unlock_level': 151, 'role': '掠夺竞速',
     'trait': TRAIT_STEAL_50,        'trait_desc': '50%概率抢夺敌方甜食',          'terrain': TERRAIN_DESERT},
    {'id': 25, 'name': '横纹猛蚁',      'base_carry': 99,  'base_speed': 225, 'base_defense': 42,
     'buy_cost': 9900,  'unlock_level': 166, 'role': '均衡后期',
     'trait': TRAIT_ALL_15,          'trait_desc': '全属性+15%，无短板',           'terrain': None},
    {'id': 26, 'name': '大齿猛蚁',      'base_carry': 100, 'base_speed': 235, 'base_defense': 48,
     'buy_cost': 10000, 'unlock_level': 200, 'role': '终极顶级',
     'trait': TRAIT_SUPREME,         'trait_desc': '搬运+30%，啃食+50%，免疫所有', 'terrain': None},
]

# ── 预计算升级金币 ──
for ant in ANTS:
    bp = ant['buy_cost']
    ant['carry_costs'] = _gen_upgrade_costs(bp, ant['id'])
    ant['speed_costs'] = _gen_speed_costs(bp)
    ant['defense_costs'] = _gen_defense_costs(bp)

# ── 便捷查询 ──
ANT_BY_ID = {ant['id']: ant for ant in ANTS}
ANT_BY_NAME = {ant['name']: ant for ant in ANTS}

MAX_ATTR_LEVEL = 200
MAX_TEAM_SIZE = 30


# ── 属性计算函数 ──

def get_carry_capacity(ant_id, carry_level):
    """实际搬运量 = base_carry + carry_level"""
    ant = ANT_BY_ID[ant_id]
    return ant['base_carry'] + carry_level


def get_speed(ant_id, speed_level):
    """实际速度 = base_speed + speed_level * 2"""
    ant = ANT_BY_ID[ant_id]
    return ant['base_speed'] + speed_level * 2


def get_defense(ant_id, defense_level):
    """实际防御 = base_defense + defense_level"""
    ant = ANT_BY_ID[ant_id]
    return min(100, ant['base_defense'] + defense_level)


def get_upgrade_cost(ant_id, attr, current_level):
    """获取某属性下一级升级费用，满级返回 None"""
    if current_level >= MAX_ATTR_LEVEL:
        return None
    ant = ANT_BY_ID[ant_id]
    costs_key = f'{attr}_costs'
    return ant[costs_key][current_level]


def get_total_upgrade_cost(ant_id, attr, from_level, to_level):
    """计算从 from_level 升到 to_level 的某属性总费用"""
    ant = ANT_BY_ID[ant_id]
    costs_key = f'{attr}_costs'
    total = 0
    for lv in range(from_level, to_level):
        if lv >= MAX_ATTR_LEVEL:
            break
        total += ant[costs_key][lv]
    return total
