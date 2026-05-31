"""昆虫数据定义（第一期：瓢虫+毛毛虫）

配置化设计，支持后续扩展更多昆虫类型。
每个昆虫定义包含：HP、移速、金币奖励、特殊机制（预留）。
"""

CREATURE_BY_ID = {
    'ladybug': {
        'id': 'ladybug',
        'name': '瓢虫',
        'hp': 3,
        'speed': 180,
        'coin_per': 5,
        'special': None,          # 无特殊机制
        'color_key': 'ladybug',   # 回退绘制颜色key
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
