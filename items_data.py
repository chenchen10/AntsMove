"""道具数据定义"""

ITEMS = [
    {
        'name': '加速药水',
        'cost': 50,
        'description': '蚂蚁移动速度翻倍，持续10秒',
        'tip': '适合快速搬运长距离甜点',
        'max_uses': 3,
    },
    {
        'name': '双倍收益券',
        'cost': 80,
        'description': '下一次交付甜点获得双倍金币',
        'tip': '在高倍率区域使用收益最大化',
        'max_uses': 3,
    },
    {
        'name': '干扰粉尘',
        'cost': 60,
        'description': '眩晕所有敌方蚂蚁2秒',
        'tip': '在敌方搬运关键甜点时使用',
        'max_uses': 2,
    },
]

ITEM_BY_NAME = {item['name']: item for item in ITEMS}
