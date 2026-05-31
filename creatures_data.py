"""昆虫数据定义（第一期：瓢虫+毛毛虫 + 第二期：蟋蟀/甲虫/蜻蜓/蜜蜂）

配置化设计，支持后续扩展更多昆虫类型。
每个昆虫定义包含：HP、移速、金币奖励、特殊机制。

第二期特殊机制：
- 蟋蟀(cricket): 跳跃闪避 — 被攻击时20%概率闪避，随机位移30像素
- 甲虫(beetle): 护甲 — 使用浮点HP，每次啃食伤害=0.8（减伤20%）
- 蜻蜓(dragonfly): 飞行 — 仅树顶(Tree_Top)地形蚂蚁可攻击
- 蜜蜂(bee): 反击 — 10%概率僵直攻击者0.5秒
"""

CREATURE_BY_ID = {
    # ── 第一期 ──
    'ladybug': {
        'id': 'ladybug',
        'name': '瓢虫',
        'hp': 3,
        'speed': 180,
        'coin_per': 6,
        'special': None,
        'color_key': 'ladybug',
    },
    'caterpillar': {
        'id': 'caterpillar',
        'name': '毛毛虫',
        'hp': 8,
        'speed': 80,
        'coin_per': 18,
        'special': None,
        'color_key': 'caterpillar',
    },
    # ── 第二期 ──
    'cricket': {
        'id': 'cricket',
        'name': '蟋蟀',
        'hp': 5,
        'speed': 150,
        'coin_per': 10,
        'special': 'dodge',           # 跳跃闪避
        'dodge_chance': 0.20,         # 20%闪避概率
        'dodge_distance': 30,         # 闪避位移30像素
        'color_key': 'cricket',
    },
    'beetle': {
        'id': 'beetle',
        'name': '甲虫',
        'hp': 12.0,                   # 浮点HP，避免int(0.8)=0的bug
        'speed': 100,
        'coin_per': 24,
        'special': 'armor',           # 护甲
        'armor_ratio': 0.20,          # 护甲比例20%，实际伤害=1×0.8=0.8
        'color_key': 'beetle',
    },
    'dragonfly': {
        'id': 'dragonfly',
        'name': '蜻蜓',
        'hp': 4,
        'speed': 220,
        'coin_per': 15,
        'special': 'flight',          # 飞行（仅树顶地形蚂蚁可攻击）
        'color_key': 'dragonfly',
    },
    'bee': {
        'id': 'bee',
        'name': '蜜蜂',
        'hp': 6,
        'speed': 190,
        'coin_per': 12,
        'special': 'counter_attack',  # 反击
        'counter_chance': 0.10,       # 10%反击概率
        'counter_stun_duration': 0.5, # 僵直0.5秒（固定，不受防御影响）
        'color_key': 'bee',
    },
}

# 昆虫类型列表，用于随机刷新选择
CREATURE_TYPE_IDS = list(CREATURE_BY_ID.keys())


def get_creature_data(creature_id):
    """获取指定昆虫的数据定义"""
    return CREATURE_BY_ID[creature_id]


def get_creature_hp(creature_id):
    """获取昆虫最大HP"""
    return CREATURE_BY_ID[creature_id]['hp']


def get_creature_speed(creature_id):
    """获取昆虫移速"""
    return CREATURE_BY_ID[creature_id]['speed']


def get_creature_coin(creature_id):
    """获取昆虫单次被啃食金币奖励"""
    return CREATURE_BY_ID[creature_id]['coin_per']


def get_creature_special(creature_id):
    """获取昆虫特殊机制类型"""
    return CREATURE_BY_ID[creature_id].get('special')
