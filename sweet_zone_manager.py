"""三区域甜点管理器：管理甜点刷新、区域倍率、刷新计时"""

import random
from config import ZONE_CONFIG, SWEET_COLORS
from sweet_sprite import Sweet
from region import get_zone_for_x, choose_refresh_region, get_random_sweet_pos


class SweetZoneManager:
    """管理三区域甜点的刷新、存活、倍率判定"""

    def __init__(self, level_data, assets):
        self.level_data = level_data
        self.assets = assets

        # 每个区域的刷新计时器（秒）
        self._refresh_timers = {
            'left': 0.0,
            'center': 0.0,
            'right': 0.0,
        }
        # 每个区域当前存活的甜点（单区域最多1个）
        self._zone_sweets = {
            'left': None,
            'center': None,
            'right': None,
        }

        # 甜点参数
        sweet_info = level_data['sweet']
        self.sweet_hp = sweet_info['hp']
        self.sweet_coin_per = sweet_info.get('coin_per', 1)
        self.sweet_types = list(SWEET_COLORS.keys())

    def spawn_initial_sweets(self):
        """初始刷新：每个区域各生成1个甜点"""
        sweets = []
        for zone_name in ['left', 'center', 'right']:
            sweet = self._spawn_sweet(zone_name)
            if sweet:
                self._zone_sweets[zone_name] = sweet
                sweets.append(sweet)
        return sweets

    def update(self, dt):
        """每帧更新：检查各区域刷新计时器，到时间则刷新甜点。返回新生成的甜点列表。"""
        new_sweets = []
        for zone_name, cfg in ZONE_CONFIG.items():
            # 如果该区域已有甜点，不刷新
            if self._zone_sweets[zone_name] and self._zone_sweets[zone_name].alive:
                continue

            # 累加计时器
            self._refresh_timers[zone_name] += dt
            interval = cfg['refresh_interval']

            if self._refresh_timers[zone_name] >= interval:
                self._refresh_timers[zone_name] = 0.0
                sweet = self._spawn_sweet(zone_name)
                if sweet:
                    self._zone_sweets[zone_name] = sweet
                    new_sweets.append(sweet)

        return new_sweets

    def get_zone_for_sweet(self, sweet):
        """获取指定甜点所在区域的key"""
        return get_zone_for_x(sweet.x)

    def get_multiplier_for_sweet(self, sweet):
        """获取指定甜点所在区域的倍率"""
        zone = get_zone_for_x(sweet.x)
        return ZONE_CONFIG[zone]['multiplier']

    def on_sweet_destroyed(self, sweet):
        """甜点被消灭后回调：清除区域引用，重置计时器"""
        zone = get_zone_for_x(sweet.x)
        if self._zone_sweets.get(zone) is sweet:
            self._zone_sweets[zone] = None
            self._refresh_timers[zone] = 0.0

    def _spawn_sweet(self, zone_name):
        """在指定区域生成一个甜点"""
        x, y = get_random_sweet_pos(zone_name)
        sweet_type = random.choice(self.sweet_types)
        sweet = Sweet(sweet_type, x, y, self.sweet_hp, self.sweet_coin_per, self.assets)
        return sweet
