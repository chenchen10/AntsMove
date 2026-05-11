"""成就系统单元测试 — 数据定义、进度评估、领取逻辑"""

import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import save_manager
from save_manager import SaveManager
from achievements_data import (
    ACHIEVE_CATEGORIES, ACHIEVEMENTS, ACHIEVEMENT_BY_ID,
    ACHIEVEMENTS_BY_CATEGORY, ConditionType,
    evaluate_achievements, claim_achievement, get_total_progress,
    _get_condition_stat,
)


@pytest.fixture
def fresh_sm():
    """创建全新 SaveManager（无存档文件）"""
    sm = SaveManager()
    sm.loaded = True
    return sm


# ══════════════════════════════════════════════
# 1. 数据定义测试
# ══════════════════════════════════════════════

class TestAchievementDefinitions:
    def test_categories_count(self):
        assert len(ACHIEVE_CATEGORIES) == 5

    def test_categories_names(self):
        expected = ['收集', '挑战', '星级', '探索', '养成']
        assert ACHIEVE_CATEGORIES == expected

    def test_all_achievements_have_required_fields(self):
        required = {'id', 'category', 'name', 'desc', 'condition_type',
                     'threshold', 'rewards', 'icon_text'}
        for ach in ACHIEVEMENTS:
            missing = required - set(ach.keys())
            assert not missing, f"Achievement {ach.get('id', '?')} missing: {missing}"

    def test_unique_ids(self):
        ids = [a['id'] for a in ACHIEVEMENTS]
        assert len(ids) == len(set(ids))

    def test_all_categories_populated(self):
        for cat in ACHIEVE_CATEGORIES:
            assert cat in ACHIEVEMENTS_BY_CATEGORY
            assert len(ACHIEVEMENTS_BY_CATEGORY[cat]) > 0

    def test_by_id_index(self):
        for ach in ACHIEVEMENTS:
            assert ach['id'] in ACHIEVEMENT_BY_ID
            assert ACHIEVEMENT_BY_ID[ach['id']]['name'] == ach['name']

    def test_thresholds_positive(self):
        for ach in ACHIEVEMENTS:
            assert ach['threshold'] > 0, f"{ach['id']} has non-positive threshold"

    def test_rewards_have_coins(self):
        for ach in ACHIEVEMENTS:
            assert 'coins' in ach['rewards'], f"{ach['id']} missing coins reward"

    def test_condition_types_are_valid(self):
        valid_types = set(ConditionType)
        for ach in ACHIEVEMENTS:
            assert ach['condition_type'] in valid_types, \
                f"{ach['id']} has invalid condition_type"

    def test_20_achievements(self):
        assert len(ACHIEVEMENTS) == 20


# ══════════════════════════════════════════════
# 2. _get_condition_stat 测试
# ══════════════════════════════════════════════

class TestGetConditionStat:
    def test_ants_owned(self, fresh_sm):
        sm = fresh_sm
        sm.data['ants'] = {
            '1': {'count': 2, 'carry': 0, 'speed': 0, 'defense': 0},
            '3': {'count': 1, 'carry': 0, 'speed': 0, 'defense': 0},
        }
        assert _get_condition_stat(ConditionType.ANTS_OWNED, sm) == 3

    def test_ants_unique(self, fresh_sm):
        sm = fresh_sm
        sm.data['ants'] = {
            '1': {'count': 2, 'carry': 0, 'speed': 0, 'defense': 0},
            '3': {'count': 1, 'carry': 0, 'speed': 0, 'defense': 0},
        }
        assert _get_condition_stat(ConditionType.ANTS_UNIQUE, sm) == 2

    def test_max_level(self, fresh_sm):
        sm = fresh_sm
        sm.data['max_level_passed'] = 42
        assert _get_condition_stat(ConditionType.MAX_LEVEL, sm) == 42

    def test_stars_earned(self, fresh_sm):
        sm = fresh_sm
        sm.data['levels'] = {
            '1': {'best_stars': 3},
            '2': {'best_stars': 1},
        }
        assert _get_condition_stat(ConditionType.STARS_EARNED, sm) == 4

    def test_total_levels_cleared(self, fresh_sm):
        sm = fresh_sm
        sm.data['levels'] = {
            '1': {'best_stars': 1, 'times_won': 3},
            '2': {'best_stars': 2, 'times_won': 1},
        }
        assert _get_condition_stat(ConditionType.TOTAL_LEVELS_CLEARED, sm) == 4

    def test_coins_earned(self, fresh_sm):
        sm = fresh_sm
        sm.data['total_coins'] = 9999
        assert _get_condition_stat(ConditionType.COINS_EARNED, sm) == 9999

    def test_max_carry_level(self, fresh_sm):
        sm = fresh_sm
        sm.data['ants'] = {
            '1': {'count': 1, 'carry': 50, 'speed': 10, 'defense': 5},
            '2': {'count': 1, 'carry': 30, 'speed': 20, 'defense': 10},
        }
        assert _get_condition_stat(ConditionType.MAX_CARRY_LEVEL, sm) == 50

    def test_max_speed_level(self, fresh_sm):
        sm = fresh_sm
        sm.data['ants'] = {
            '1': {'count': 1, 'carry': 10, 'speed': 80, 'defense': 5},
        }
        assert _get_condition_stat(ConditionType.MAX_SPEED_LEVEL, sm) == 80

    def test_maxed_ants(self, fresh_sm):
        sm = fresh_sm
        sm.data['ants'] = {
            '1': {'count': 1, 'carry': 200, 'speed': 0, 'defense': 0},
            '2': {'count': 1, 'carry': 200, 'speed': 0, 'defense': 0},
        }
        assert _get_condition_stat(ConditionType.MAXED_ANTS, sm) == 2


# ══════════════════════════════════════════════
# 3. 进度评估测试
# ══════════════════════════════════════════════

class TestEvaluateAchievements:
    def test_fresh_save_no_unlocks(self, fresh_sm):
        stats = evaluate_achievements(fresh_sm)
        for aid, st in stats.items():
            assert st['current'] >= 0
            assert st['claimed'] is False

    def test_ants_owned_progress(self, fresh_sm):
        sm = fresh_sm
        sm.data['ants'] = {
            '1': {'count': 1, 'carry': 0, 'speed': 0, 'defense': 0},
            '2': {'count': 1, 'carry': 0, 'speed': 0, 'defense': 0},
        }
        stats = evaluate_achievements(sm)
        assert stats['C1']['unlocked'] is True    # 拥有1只
        assert stats['C2']['unlocked'] is False   # 需要5只

    def test_max_level_progress(self, fresh_sm):
        sm = fresh_sm
        sm.data['max_level_passed'] = 10
        stats = evaluate_achievements(sm)
        assert stats['H1']['unlocked'] is True    # 通关第10关
        assert stats['H2']['unlocked'] is False   # 需要50关

    def test_total_stars_progress(self, fresh_sm):
        sm = fresh_sm
        sm.data['levels'] = {
            '1': {'best_stars': 3},
            '2': {'best_stars': 2},
        }
        stats = evaluate_achievements(sm)
        # 3+2=5 stars, S1 needs 10, not unlocked
        assert stats['S1']['unlocked'] is False
        # Give more stars to unlock S1
        sm.data['levels'] = {
            '1': {'best_stars': 3},
            '2': {'best_stars': 3},
            '3': {'best_stars': 3},
            '4': {'best_stars': 3},
        }
        stats = evaluate_achievements(sm)
        # 3*4=12 stars, S1 needs 10
        assert stats['S1']['unlocked'] is True

    def test_claimed_status(self, fresh_sm):
        sm = fresh_sm
        sm.data['achievements'] = {
            'C1': {'current': 1, 'claimed': True}
        }
        stats = evaluate_achievements(sm)
        assert stats['C1']['claimed'] is True

    def test_total_progress(self, fresh_sm):
        sm = fresh_sm
        sm.data['max_level_passed'] = 10
        unlocked, total, claimed = get_total_progress(sm)
        assert total == len(ACHIEVEMENTS)
        assert unlocked >= 1  # H1: 通关第10关
        assert claimed == 0


# ══════════════════════════════════════════════
# 4. 领取逻辑测试
# ══════════════════════════════════════════════

class TestClaimAchievement:
    def test_claim_unlocked_achievement(self, fresh_sm):
        sm = fresh_sm
        sm.data['max_level_passed'] = 10
        success, reward = claim_achievement('H1', sm)
        assert success is True
        assert reward == 100  # H1 reward

    def test_claim_gives_coins(self, fresh_sm):
        sm = fresh_sm
        sm.data['max_level_passed'] = 10
        initial_coins = sm.get_total_coins()
        claim_achievement('H1', sm)
        assert sm.get_total_coins() == initial_coins + 100

    def test_claim_already_claimed(self, fresh_sm):
        sm = fresh_sm
        sm.data['max_level_passed'] = 10
        sm.data['achievements'] = {
            'H1': {'current': 10, 'claimed': True}
        }
        success, reward = claim_achievement('H1', sm)
        assert success is False
        assert reward == 0

    def test_claim_not_unlocked(self, fresh_sm):
        sm = fresh_sm
        # max_level = 0, H1 needs 10
        success, reward = claim_achievement('H1', sm)
        assert success is False
        assert reward == 0

    def test_claim_invalid_id(self, fresh_sm):
        sm = fresh_sm
        success, reward = claim_achievement('INVALID', sm)
        assert success is False
        assert reward == 0

    def test_claim_persists_state(self, fresh_sm):
        sm = fresh_sm
        sm.data['max_level_passed'] = 10
        claim_achievement('H1', sm)
        ach_data = sm.data['achievements']['H1']
        assert ach_data['claimed'] is True


# ══════════════════════════════════════════════
# 5. evaluate_all_achievements（批量检测）测试
# ══════════════════════════════════════════════

class TestEvaluateAllAchievements:
    def test_no_new_when_fresh(self, fresh_sm):
        newly = fresh_sm.evaluate_all_achievements()
        assert newly == []

    def test_detects_newly_unlocked(self, fresh_sm):
        sm = fresh_sm
        sm.data['max_level_passed'] = 10
        newly = sm.evaluate_all_achievements()
        assert 'H1' in newly

    def test_no_double_notify(self, fresh_sm):
        sm = fresh_sm
        sm.data['max_level_passed'] = 10
        sm.evaluate_all_achievements()
        newly = sm.evaluate_all_achievements()
        assert 'H1' not in newly

    def test_claimed_achievement_not_notified(self, fresh_sm):
        sm = fresh_sm
        sm.data['max_level_passed'] = 10
        sm.data['achievements'] = {
            'H1': {'current': 10, 'claimed': True}
        }
        newly = sm.evaluate_all_achievements()
        assert 'H1' not in newly


# ══════════════════════════════════════════════
# 6. get_pending_achievements 测试
# ══════════════════════════════════════════════

class TestGetPendingAchievements:
    def test_no_pending_when_fresh(self, fresh_sm):
        pending = fresh_sm.get_pending_achievements()
        assert pending == []

    def test_pending_after_unlock(self, fresh_sm):
        sm = fresh_sm
        sm.data['max_level_passed'] = 10
        sm.evaluate_all_achievements()
        pending = sm.get_pending_achievements()
        assert 'H1' in pending

    def test_no_pending_after_claim(self, fresh_sm):
        sm = fresh_sm
        sm.data['max_level_passed'] = 10
        sm.evaluate_all_achievements()
        claim_achievement('H1', sm)
        pending = sm.get_pending_achievements()
        assert 'H1' not in pending
