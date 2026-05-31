"""昆虫管理器（第一期+第二期）：刷新逻辑、区域管理、碰撞检测

关键规则：
- 昆虫与甜点共享区域刷新计时器，每次刷新只生成一种
- 同一区域同时存在的昆虫数量上限为2只（CREATURE_MAX_PER_ZONE）
- 昆虫金币直接加到蚂蚁storage，受区域倍率影响
- 第二期新增：刷新概率按区域差异化、蜻蜓地形判定、蜜蜂反击僵直

刷新概率（第二期调整）：
- 左区: 14%
- 中区: 29%
- 右区: 10%
"""

import random
from config import ZONE_CONFIG, CREATURE_MAX_PER_ZONE
from creature_sprite import Creature
from creatures_data import CREATURE_TYPE_IDS, get_creature_special
from region import get_zone_for_x, get_random_sweet_pos

# 第二期：各区域昆虫刷新概率（与甜点共享刷新机会）
CREATURE_SPAWN_PROB = {
    'left': 0.14,
    'center': 0.29,
    'right': 0.10,
}


class CreatureManager:
    """管理三区域昆虫的刷新、存活、倍率判定"""

    def __init__(self, assets):
        self.assets = assets

        # 每个区域当前存活的昆虫列表（最多CREATURE_MAX_PER_ZONE只）
        self._zone_creatures = {
            'left': [],
            'center': [],
            'right': [],
        }

    def get_zone_creature_count(self, zone_name):
        """获取指定区域存活的昆虫数量"""
        creatures = self._zone_creatures.get(zone_name, [])
        return sum(1 for c in creatures if c.alive)

    def can_spawn_in_zone(self, zone_name):
        """判断指定区域是否还能刷新昆虫"""
        return self.get_zone_creature_count(zone_name) < CREATURE_MAX_PER_ZONE

    def try_spawn(self, zone_name):
        """尝试在指定区域生成一只昆虫（概率性）。

        与甜点共享区域刷新计时器，由SweetZoneManager的update调用。
        每次刷新按spawn_prob概率决定生成昆虫还是甜点。
        返回生成的昆虫对象，或None表示不生成。
        """
        if not self.can_spawn_in_zone(zone_name):
            return None

        # 第二期：使用区域差异化刷新概率
        creature_prob = CREATURE_SPAWN_PROB.get(zone_name, 0.14)
        if random.random() >= creature_prob:
            return None

        # 随机选择昆虫类型
        creature_id = random.choice(CREATURE_TYPE_IDS)

        # 在区域内随机生成位置
        x, y = self._get_random_creature_pos(zone_name)

        creature = Creature(creature_id, x, y, zone_name, self.assets)
        self._zone_creatures[zone_name].append(creature)
        return creature

    def spawn_initial_creatures(self):
        """初始刷新：每个区域各生成0-1只昆虫（概率性）"""
        creatures = []
        for zone_name in ['left', 'center', 'right']:
            creature = self.try_spawn(zone_name)
            if creature:
                creatures.append(creature)
        return creatures

    def update(self, dt):
        """每帧更新：昆虫移动 + 死亡动画。返回已完成死亡动画的昆虫列表（用于清理）。"""
        finished = []
        for zone_name, creatures in self._zone_creatures.items():
            cfg = ZONE_CONFIG[zone_name]
            x_range = cfg['x_range']
            for creature in creatures:
                if creature.alive:
                    creature.update_blink(dt)
                    creature.update(dt, zone_x_range=x_range)
                elif creature._dying:
                    done = creature.update(dt, zone_x_range=x_range)
                    if done:
                        finished.append(creature)
        return finished

    def get_all_creatures(self):
        """获取所有存活+死亡动画中的昆虫"""
        result = []
        for creatures in self._zone_creatures.values():
            result.extend(creatures)
        return result

    def get_alive_creatures(self):
        """获取所有存活的昆虫"""
        result = []
        for creatures in self._zone_creatures.values():
            result.extend(c for c in creatures if c.alive)
        return result

    def get_multiplier_for_creature(self, creature):
        """获取指定昆虫所在区域的倍率"""
        zone = get_zone_for_x(creature.x)
        return ZONE_CONFIG[zone]['multiplier']

    def on_creature_destroyed(self, creature):
        """昆虫被消灭后回调：从区域列表中清除"""
        zone = creature.zone_name
        if creature in self._zone_creatures.get(zone, []):
            self._zone_creatures[zone].remove(creature)

    def on_creature_death_anim_done(self, creature):
        """死亡动画完成后清理"""
        zone = creature.zone_name
        if creature in self._zone_creatures.get(zone, []):
            self._zone_creatures[zone].remove(creature)

    def _get_random_creature_pos(self, zone_name):
        """在指定区域内随机生成昆虫世界坐标"""
        cfg = ZONE_CONFIG[zone_name]
        x_min, x_max = cfg['x_range']
        y_min, y_max = cfg['y_range']
        x = random.randint(x_min + 50, x_max - 50)
        y = random.randint(y_min + 60, y_max - 60)
        return x, y
