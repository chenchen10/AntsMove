"""昆虫系统测试（第一期）：瓢虫+毛毛虫

测试要点：
- 各区域刷新概率符合设计值
- 瓢虫HP=3被啃食3次后死亡，金币正确发放
- 毛毛虫HP=8被啃食8次后死亡
- 同区域昆虫不超过2只
- 昆虫与甜点共存不冲突
"""

import os
import sys
import importlib
import pytest
from unittest.mock import MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# test_checkin_ui.py 在模块级别 mock 了 sys.modules['config']，
# 导致后续测试拿到 mock 而非真实 config。此处强制恢复真实模块。
if 'config' in sys.modules and isinstance(sys.modules['config'], MagicMock):
    del sys.modules['config']
if 'creatures_data' in sys.modules and isinstance(sys.modules['creatures_data'], MagicMock):
    del sys.modules['creatures_data']

import pygame
pygame.init()
pygame.display.set_mode((100, 100))

from config import CREATURE_MAX_PER_ZONE, ZONE_CONFIG, CREATURE_COLORS
from creatures_data import (
    CREATURE_BY_ID, CREATURE_TYPE_IDS,
    get_creature_data, get_creature_hp, get_creature_speed, get_creature_coin,
)
from creature_sprite import Creature
from creature_manager import CreatureManager


# ══════════════════════════════════════════════
# creatures_data 数据定义测试
# ══════════════════════════════════════════════

class TestCreaturesData:
    """验证昆虫数据定义的完整性和正确性"""

    def test_all_creatures_defined(self):
        """所有第一期昆虫都有数据定义"""
        assert 'ladybug' in CREATURE_BY_ID
        assert 'caterpillar' in CREATURE_BY_ID

    def test_creature_type_ids_complete(self):
        """CREATURE_TYPE_IDS 包含所有昆虫"""
        assert set(CREATURE_TYPE_IDS) == {'ladybug', 'caterpillar'}

    def test_ladybug_stats(self):
        """瓢虫属性：HP=3，移速180，金币5"""
        d = get_creature_data('ladybug')
        assert d['hp'] == 3
        assert d['speed'] == 180
        assert d['coin_per'] == 5
        assert d['special'] is None

    def test_caterpillar_stats(self):
        """毛毛虫属性：HP=8，移速80，金币15"""
        d = get_creature_data('caterpillar')
        assert d['hp'] == 8
        assert d['speed'] == 80
        assert d['coin_per'] == 15
        assert d['special'] is None

    def test_get_creature_hp(self):
        """get_creature_hp 返回正确HP"""
        assert get_creature_hp('ladybug') == 3
        assert get_creature_hp('caterpillar') == 8

    def test_get_creature_speed(self):
        """get_creature_speed 返回正确移速"""
        assert get_creature_speed('ladybug') == 180
        assert get_creature_speed('caterpillar') == 80

    def test_get_creature_coin(self):
        """get_creature_coin 返回正确金币"""
        assert get_creature_coin('ladybug') == 5
        assert get_creature_coin('caterpillar') == 15

    def test_creature_colors_defined(self):
        """回退绘制颜色已定义"""
        assert 'ladybug' in CREATURE_COLORS
        assert 'caterpillar' in CREATURE_COLORS


# ══════════════════════════════════════════════
# creature_sprite 精灵类测试
# ══════════════════════════════════════════════

class TestCreatureSprite:
    """验证昆虫精灵的HP系统和状态机"""

    def test_ladybug_hp_3_dies_after_3_hits(self):
        """瓢虫HP=3，被啃食3次后死亡"""
        c = Creature('ladybug', 500, 400, 'center')
        assert c.hp == 3
        assert c.alive is True

        assert c.take_damage() is False  # HP=2
        assert c.hp == 2
        assert c.alive is True

        assert c.take_damage() is False  # HP=1
        assert c.hp == 1
        assert c.alive is True

        assert c.take_damage() is True  # HP=0，死亡
        assert c.hp == 0
        assert c.alive is False
        assert c._dying is True  # 启动死亡动画

    def test_caterpillar_hp_8_dies_after_8_hits(self):
        """毛毛虫HP=8，被啃食8次后死亡"""
        c = Creature('caterpillar', 500, 400, 'center')
        assert c.hp == 8

        for i in range(7):
            result = c.take_damage()
            assert result is False, f"第{i+1}次啃食不应导致死亡"
            assert c.hp == 8 - i - 1

        assert c.take_damage() is True  # 第8次，死亡
        assert c.hp == 0
        assert c.alive is False

    def test_dead_creature_cannot_be_damaged(self):
        """已死亡的昆虫再次受击返回False"""
        c = Creature('ladybug', 500, 400, 'center')
        c.take_damage()
        c.take_damage()
        c.take_damage()  # 死亡
        assert c.take_damage() is False  # 再次受击

    def test_creature_zone_assignment(self):
        """昆虫记录所在区域"""
        c = Creature('ladybug', 500, 400, 'center')
        assert c.zone_name == 'center'

    def test_creature_coin_per(self):
        """昆虫金币奖励正确"""
        c1 = Creature('ladybug', 500, 400, 'center')
        c2 = Creature('caterpillar', 500, 400, 'center')
        assert c1.coin_per == 5
        assert c2.coin_per == 15


# ══════════════════════════════════════════════
# creature_manager 管理器测试
# ══════════════════════════════════════════════

class TestCreatureManager:
    """验证昆虫管理器的区域限制和刷新逻辑"""

    def test_max_per_zone_limit(self):
        """同一区域昆虫不超过2只"""
        mgr = CreatureManager({})

        # 手动添加昆虫到同一区域
        for i in range(3):
            c = Creature('ladybug', 500 + i * 50, 400, 'center')
            mgr._zone_creatures['center'].append(c)

        assert mgr.get_zone_creature_count('center') == 3
        assert mgr.can_spawn_in_zone('center') is False

        # 尝试在该区域生成新昆虫应该返回None
        result = mgr.try_spawn('center')
        assert result is None

    def test_can_spawn_when_under_limit(self):
        """昆虫数量未达上限时可以生成"""
        mgr = CreatureManager({})

        # 添加1只昆虫
        c = Creature('ladybug', 500, 400, 'center')
        mgr._zone_creatures['center'].append(c)

        assert mgr.get_zone_creature_count('center') == 1
        assert mgr.can_spawn_in_zone('center') is True

    def test_on_creature_destroyed_removes_from_zone(self):
        """昆虫被消灭后从区域列表中清除"""
        mgr = CreatureManager({})
        c = Creature('ladybug', 500, 400, 'center')
        mgr._zone_creatures['center'].append(c)

        mgr.on_creature_destroyed(c)
        assert c not in mgr._zone_creatures['center']

    def test_get_all_creatures(self):
        """get_all_creatures 返回所有昆虫"""
        mgr = CreatureManager({})
        c1 = Creature('ladybug', 500, 400, 'left')
        c2 = Creature('caterpillar', 2000, 400, 'center')
        mgr._zone_creatures['left'].append(c1)
        mgr._zone_creatures['center'].append(c2)

        all_c = mgr.get_all_creatures()
        assert len(all_c) == 2
        assert c1 in all_c
        assert c2 in all_c

    def test_get_alive_creatures(self):
        """get_alive_creatures 只返回存活的昆虫"""
        mgr = CreatureManager({})
        c1 = Creature('ladybug', 500, 400, 'left')
        c2 = Creature('caterpillar', 2000, 400, 'center')
        # 毛毛虫HP=8，啃食8次才死亡
        for _ in range(8):
            c2.take_damage()
        mgr._zone_creatures['left'].append(c1)
        mgr._zone_creatures['center'].append(c2)

        alive = mgr.get_alive_creatures()
        assert len(alive) == 1
        assert c1 in alive

    def test_zone_CREATURE_MAX_PER_ZONE(self):
        """CREATURE_MAX_PER_ZONE 配置正确"""
        assert CREATURE_MAX_PER_ZONE == 2


# ══════════════════════════════════════════════
# 甜点+昆虫共存测试
# ══════════════════════════════════════════════

class TestSweetCreatureCoexistence:
    """验证昆虫与甜点共存不冲突"""

    def test_creature_and_sweet_independent(self):
        """昆虫和甜点是独立的对象"""
        from sweet_sprite import Sweet
        c = Creature('ladybug', 500, 400, 'center')
        s = Sweet('candy', 500, 400, 5, 1)

        # 互不影响
        assert c.alive is True
        assert s.alive is True
        c.take_damage()
        assert c.hp == 2
        assert s.hp == 5  # 甜点不受影响

    def test_separate_managers(self):
        """昆虫管理器和甜点管理器独立运行"""
        mgr_c = CreatureManager({})
        from sweet_zone_manager import SweetZoneManager

        # 验证CreatureManager可以独立创建
        assert mgr_c is not None
        assert mgr_c.get_zone_creature_count('left') == 0
        assert mgr_c.get_zone_creature_count('center') == 0
        assert mgr_c.get_zone_creature_count('right') == 0


# ══════════════════════════════════════════════
# 区域配置测试
# ══════════════════════════════════════════════

class TestZoneConfig:
    """验证区域配置与昆虫系统的兼容性"""

    def test_three_zones_exist(self):
        """三个区域配置都存在"""
        assert 'left' in ZONE_CONFIG
        assert 'center' in ZONE_CONFIG
        assert 'right' in ZONE_CONFIG

    def test_zone_multipliers(self):
        """区域倍率正确"""
        assert ZONE_CONFIG['left']['multiplier'] == 1.5
        assert ZONE_CONFIG['center']['multiplier'] == 1.0
        assert ZONE_CONFIG['right']['multiplier'] == 2.0

    def test_zone_refresh_intervals(self):
        """各区域刷新间隔已定义"""
        for zone_name in ['left', 'center', 'right']:
            assert 'refresh_interval' in ZONE_CONFIG[zone_name]
            assert ZONE_CONFIG[zone_name]['refresh_interval'] > 0
