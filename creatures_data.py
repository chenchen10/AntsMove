"""昆虫数据定义（全部6种：瓢虫/蟋蟀/毛毛虫/甲虫/蜻蜓/蜜蜂）

配置化设计，支持后续扩展更多昆虫类型。
每个昆虫定义包含：HP、移速、金币奖励、特殊机制。
"""

CREATURE_BY_ID = {
    'ladybug': {
        'id': 'ladybug',
        'name': '瓢虫',
        'hp': 3,
        'speed': 180,
        'coin_per': 5,
        'special': None,
        'color_key': 'ladybug',
    },
    'cricket': {
        'id': 'cricket',
        'name': '蟋蟀',
        'hp': 5,
        'speed': 150,
        'coin_per': 10,
        'special': 'dodge',       # 跳跃闪避：20%概率闪避攻击
        'dodge_chance': 0.20,
        'color_key': 'cricket',
    },
    'caterpillar': {
        'id': 'caterpillar',
        'name': '毛毛虫',
        'hp': 8,
        'speed': 80,
        'coin_per': 15,
        'special': None,
        'color_key': 'caterpillar',
    },
    'beetle': {
        'id': 'beetle',
        'name': '甲虫',
        'hp': 12,
        'speed': 100,
        'coin_per': 24,
        'special': 'armor',       # 护甲：减伤20%
        'armor_reduction': 0.20,
        'color_key': 'beetle',
    },
    'dragonfly': {
        'id': 'dragonfly',
        'name': '蜻蜓',
        'hp': 4,
        'speed': 220,
        'coin_per': 15,
        'special': 'flying',      # 飞行：仅树顶地形可攻击
        'color_key': 'dragonfly',
    },
    'bee': {
        'id': 'bee',
        'name': '蜜蜂',
        'hp': 6,
        'speed': 190,
        'coin_per': 12,
        'special': 'counter',     # 反击：被攻击时10%概率反击僵直
        'counter_chance': 0.10,
        'counter_stun_duration': 0.5,
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
