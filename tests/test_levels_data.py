"""levels_data.py 单元测试 — Sprint 1 星级计算逻辑"""

import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from levels_data import (
    calc_stars, get_star3_time_threshold, get_level,
    _calc_target_coins, _calc_sweet_hp, _calc_sweet_quantity,
    STAR3_TIME_THRESHOLDS, STAR3_COLLECT_RATE,
    ALL_LEVELS,
)


# ══════════════════════════════════════════════
# 1. 星级计算基础测试
# ══════════════════════════════════════════════

class TestCalcStarsBasic:
    def test_fail_returns_0(self):
        """未达标 → 0星"""
        result = calc_stars(1, level_coins=50, target_coins=100,
                           remaining_time=50, total_time=90, collection_rate=0.9)
        assert result == 0

    def test_pass_with_no_bonus(self):
        """仅通关 → 1星"""
        result = calc_stars(1, level_coins=100, target_coins=100,
                           remaining_time=10, total_time=90, collection_rate=0.5)
        assert result == 1

    def test_pass_with_time_bonus(self):
        """通关 + 剩余≥30% → 2星"""
        result = calc_stars(1, level_coins=100, target_coins=100,
                           remaining_time=30, total_time=90, collection_rate=0.5)
        assert result == 2

    def test_pass_with_all_bonus(self):
        """通关 + 剩余≥50% + 收集率≥80% → 3星（Stage 1）"""
        result = calc_stars(1, level_coins=100, target_coins=100,
                           remaining_time=50, total_time=90, collection_rate=0.85)
        assert result == 3

    def test_pass_with_high_coins(self):
        """超额通关不影响星级"""
        result = calc_stars(1, level_coins=200, target_coins=100,
                           remaining_time=50, total_time=90, collection_rate=0.9)
        assert result == 3


# ══════════════════════════════════════════════
# 2. 2星阈值测试（固定30%）
# ══════════════════════════════════════════════

class TestTwoStarThreshold:
    def test_exactly_30_percent(self):
        """剩余时间恰好30% → 2星"""
        result = calc_stars(1, level_coins=100, target_coins=100,
                           remaining_time=27, total_time=90, collection_rate=0.5)
        assert result == 2

    def test_just_below_30_percent(self):
        """剩余时间略低于30% → 1星"""
        result = calc_stars(1, level_coins=100, target_coins=100,
                           remaining_time=26.9, total_time=90, collection_rate=0.5)
        assert result == 1

    def test_29_percent_is_1_star(self):
        """29% → 1星"""
        result = calc_stars(1, level_coins=100, target_coins=100,
                           remaining_time=26, total_time=90, collection_rate=0.5)
        assert result == 1

    def test_31_percent_is_2_stars(self):
        """31% → 2星"""
        result = calc_stars(1, level_coins=100, target_coins=100,
                           remaining_time=28, total_time=90, collection_rate=0.5)
        assert result == 2


# ══════════════════════════════════════════════
# 3. 3星分阶段时间阈值测试
# ══════════════════════════════════════════════

class TestThreeStarThresholds:
    """PRD v1.1: 1-50关≥50%, 51-100关≥40%, 101-150关≥35%, 151-200关≥30%"""

    def test_stage1_50_percent_threshold(self):
        """第1关: 50%剩余 + 80%收集 → 3星"""
        result = calc_stars(1, level_coins=100, target_coins=100,
                           remaining_time=45, total_time=90, collection_rate=0.80)
        assert result == 3

    def test_stage1_below_50_percent(self):
        """第1关: 49%剩余 + 80%收集 → 2星（不够50%）"""
        result = calc_stars(1, level_coins=100, target_coins=100,
                           remaining_time=44, total_time=90, collection_rate=0.80)
        assert result == 2

    def test_stage2_40_percent_threshold(self):
        """第60关: 40%剩余 + 80%收集 → 3星"""
        result = calc_stars(60, level_coins=100, target_coins=100,
                           remaining_time=32, total_time=80, collection_rate=0.80)
        assert result == 3

    def test_stage2_below_40_percent(self):
        """第60关: 39%剩余 + 80%收集 → 2星"""
        result = calc_stars(60, level_coins=100, target_coins=100,
                           remaining_time=31, total_time=80, collection_rate=0.80)
        assert result == 2

    def test_stage3_35_percent_threshold(self):
        """第120关: 35%剩余 + 80%收集 → 3星"""
        result = calc_stars(120, level_coins=100, target_coins=100,
                           remaining_time=24.5, total_time=70, collection_rate=0.80)
        assert result == 3

    def test_stage3_below_35_percent(self):
        """第120关: 34%剩余 + 80%收集 → 2星"""
        result = calc_stars(120, level_coins=100, target_coins=100,
                           remaining_time=23.8, total_time=70, collection_rate=0.80)
        assert result == 2

    def test_stage4_30_percent_threshold(self):
        """第180关: 30%剩余 + 80%收集 → 3星"""
        result = calc_stars(180, level_coins=100, target_coins=100,
                           remaining_time=18, total_time=60, collection_rate=0.80)
        assert result == 3

    def test_stage4_below_30_percent(self):
        """第180关: 29%剩余(17.4/60) + 80%收集 → 1星（29% < 30%固定阈值，不够2星）"""
        result = calc_stars(180, level_coins=100, target_coins=100,
                           remaining_time=17.4, total_time=60, collection_rate=0.80)
        assert result == 1


# ══════════════════════════════════════════════
# 4. 收集率阈值测试
# ══════════════════════════════════════════════

class TestCollectionRateThreshold:
    def test_exactly_80_percent(self):
        """收集率恰好80% → 3星"""
        result = calc_stars(1, level_coins=100, target_coins=100,
                           remaining_time=50, total_time=90, collection_rate=0.80)
        assert result == 3

    def test_just_below_80_percent(self):
        """收集率79% → 2星"""
        result = calc_stars(1, level_coins=100, target_coins=100,
                           remaining_time=50, total_time=90, collection_rate=0.79)
        assert result == 2

    def test_100_percent_collection(self):
        """收集率100% → 3星"""
        result = calc_stars(1, level_coins=100, target_coins=100,
                           remaining_time=50, total_time=90, collection_rate=1.0)
        assert result == 3


# ══════════════════════════════════════════════
# 5. get_star3_time_threshold 测试
# ══════════════════════════════════════════════

class TestGetStar3TimeThreshold:
    def test_level_1(self):
        assert get_star3_time_threshold(1) == 0.50

    def test_level_50(self):
        assert get_star3_time_threshold(50) == 0.50

    def test_level_51(self):
        assert get_star3_time_threshold(51) == 0.40

    def test_level_100(self):
        assert get_star3_time_threshold(100) == 0.40

    def test_level_101(self):
        assert get_star3_time_threshold(101) == 0.35

    def test_level_150(self):
        assert get_star3_time_threshold(150) == 0.35

    def test_level_151(self):
        assert get_star3_time_threshold(151) == 0.30

    def test_level_200(self):
        assert get_star3_time_threshold(200) == 0.30

    def test_out_of_range_defaults_to_50(self):
        """超出范围默认50%"""
        assert get_star3_time_threshold(0) == 0.50
        assert get_star3_time_threshold(201) == 0.50
        assert get_star3_time_threshold(-1) == 0.50


# ══════════════════════════════════════════════
# 6. 特殊边界条件测试
# ══════════════════════════════════════════════

class TestEdgeCases:
    def test_zero_total_time(self):
        """total_time为0时不崩溃"""
        result = calc_stars(1, level_coins=100, target_coins=100,
                           remaining_time=0, total_time=0, collection_rate=0.9)
        assert result == 1  # 通关即1星，时间检查跳过

    def test_zero_target_coins(self):
        """目标金币为0，通关即达标"""
        result = calc_stars(1, level_coins=1, target_coins=0,
                           remaining_time=50, total_time=90, collection_rate=0.9)
        assert result == 3

    def test_exact_boundary_coins(self):
        """金币恰好等于目标"""
        result = calc_stars(1, level_coins=100, target_coins=100,
                           remaining_time=0, total_time=90, collection_rate=0)
        assert result == 1

    def test_coins_one_less_than_target(self):
        """差1金币不达标"""
        result = calc_stars(1, level_coins=99, target_coins=100,
                           remaining_time=80, total_time=90, collection_rate=1.0)
        assert result == 0

    def test_negative_remaining_time(self):
        """负剩余时间不崩溃"""
        result = calc_stars(1, level_coins=100, target_coins=100,
                           remaining_time=-10, total_time=90, collection_rate=0.9)
        assert result == 1  # 通关但时间检查不通过

    def test_collection_rate_over_1(self):
        """收集率>1（理论不可能，但不崩溃）"""
        result = calc_stars(1, level_coins=100, target_coins=100,
                           remaining_time=50, total_time=90, collection_rate=1.5)
        assert result == 3

    def test_all_levels_generate_correctly(self):
        """200关全部生成正确"""
        assert len(ALL_LEVELS) == 200
        for i, level in enumerate(ALL_LEVELS):
            assert level['id'] == i + 1
            assert level['timer'] > 0
            assert level['target_coins'] > 0
            assert level['sweet']['hp'] > 0
            assert level['sweet']['quantity'] > 0

    def test_3_star_is_progressive(self):
        """3星条件随阶段递减（更容易达成）"""
        t1 = get_star3_time_threshold(25)
        t2 = get_star3_time_threshold(75)
        t3 = get_star3_time_threshold(125)
        t4 = get_star3_time_threshold(175)
        assert t1 > t2 > t3 > t4


# ══════════════════════════════════════════════
# 7. 星级组合场景测试
# ══════════════════════════════════════════════

class TestStarCombinations:
    """测试各种星级组合的合理性"""

    def test_fast_but_low_collection(self):
        """快速通关但收集率低 → 2星"""
        result = calc_stars(1, level_coins=100, target_coins=100,
                           remaining_time=60, total_time=90, collection_rate=0.5)
        assert result == 2

    def test_slow_but_high_collection(self):
        """慢速通关但收集率高 → 2星（30%≥30%固定阈值够2星，但30%<50%不够3星）"""
        result = calc_stars(1, level_coins=100, target_coins=100,
                           remaining_time=30, total_time=90, collection_rate=0.95)
        assert result == 2  # 30%刚好达到2星固定阈值，但不够50%的3星阈值

    def test_late_game_30_percent_enough(self):
        """后期30%剩余就足够3星"""
        result = calc_stars(180, level_coins=100, target_coins=100,
                           remaining_time=18, total_time=60, collection_rate=0.85)
        assert result == 3

    def test_early_game_30_percent_not_enough(self):
        """前期30%剩余不够3星（需要50%）"""
        result = calc_stars(10, level_coins=100, target_coins=100,
                           remaining_time=27, total_time=90, collection_rate=0.9)
        assert result == 2  # 30%够2星但不够50%

    def test_mid_game_40_percent_enough(self):
        """中期40%剩余足够3星"""
        result = calc_stars(70, level_coins=100, target_coins=100,
                           remaining_time=32, total_time=80, collection_rate=0.82)
        assert result == 3
