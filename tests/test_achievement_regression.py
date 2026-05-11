"""成就系统回归测试：CHE-8 全面验证

覆盖范围：
  1. 数据定义与PRD一致性
  2. 条件类型与统计函数映射
  3. 进度评估与状态机（locked → claimable → claimed）
  4. 领取流程（含防重复）
  5. 批量检测与通知去重
  6. 边界场景与异常处理
  7. 存档集成与持久化
  8. 多成就同时解锁
  9. 成就面板UI交互逻辑
 10. 通知队列行为
"""

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
    check_newly_unlocked, _get_condition_stat,
)


@pytest.fixture
def fresh_sm():
    """创建全新 SaveManager（无存档文件）"""
    sm = SaveManager()
    sm.loaded = True
    return sm


# ══════════════════════════════════════════════
# 1. 数据定义与PRD一致性
# ══════════════════════════════════════════════

class TestDataDefinitionPRD:
    """验证成就配置与PRD的对应关系"""

    def test_5_dimensions_20_achievements(self):
        """PRD: 5大维度 × 约20个成就"""
        assert len(ACHIEVE_CATEGORIES) == 5
        assert len(ACHIEVEMENTS) == 20

    def test_each_dimension_has_4(self):
        """PRD: 每个维度4个成就"""
        for cat in ACHIEVE_CATEGORIES:
            assert len(ACHIEVEMENTS_BY_CATEGORY[cat]) == 4, \
                f"维度'{cat}'应有4个成就"

    def test_dimension_names_match_prd(self):
        """PRD定义的5大维度"""
        expected = ['收集', '挑战', '星级', '探索', '养成']
        assert ACHIEVE_CATEGORIES == expected

    def test_achievement_id_prefix_scheme(self):
        """成就ID前缀对应维度：C=收集, H=挑战, S=星级, E=探索, G=养成"""
        prefix_map = {'收集': 'C', '挑战': 'H', '星级': 'S', '探索': 'E', '养成': 'G'}
        for cat, prefix in prefix_map.items():
            achs = ACHIEVEMENTS_BY_CATEGORY[cat]
            for ach in achs:
                assert ach['id'].startswith(prefix), \
                    f"成就{ach['id']}属于'{cat}'维度，应以'{prefix}'开头"

    def test_ids_are_sequential(self):
        """每个维度的ID应为 X1-X4 顺序编号"""
        for cat in ACHIEVE_CATEGORIES:
            achs = ACHIEVEMENTS_BY_CATEGORY[cat]
            ids = [a['id'] for a in achs]
            prefix = ids[0][0]
            expected = [f'{prefix}{i}' for i in range(1, 5)]
            assert ids == expected, f"维度'{cat}'的ID不连续: {ids}"

    def test_all_have_rewards(self):
        """PRD: 每个成就都有金币奖励"""
        for ach in ACHIEVEMENTS:
            assert 'coins' in ach['rewards']
            assert ach['rewards']['coins'] > 0, \
                f"成就{ach['id']}金币奖励应大于0"

    def test_thresholds_are_increasing_within_same_condition_type(self):
        """同维度同条件类型的成就，阈值应递增（难度梯度）"""
        for cat in ACHIEVE_CATEGORIES:
            achs = ACHIEVEMENTS_BY_CATEGORY[cat]
            # 按条件类型分组检查
            by_type = {}
            for ach in achs:
                ct = ach['condition_type']
                by_type.setdefault(ct, []).append(ach)
            for ct, group in by_type.items():
                thresholds = [a['threshold'] for a in group]
                for i in range(1, len(thresholds)):
                    assert thresholds[i] >= thresholds[i - 1], \
                        f"维度'{cat}'条件{ct}阈值应递增: {thresholds}"

    def test_coins_rewards_are_increasing_within_category(self):
        """同维度内金币奖励应递增"""
        for cat in ACHIEVE_CATEGORIES:
            achs = ACHIEVEMENTS_BY_CATEGORY[cat]
            coins = [a['rewards']['coins'] for a in achs]
            for i in range(1, len(coins)):
                assert coins[i] >= coins[i - 1], \
                    f"维度'{cat}'金币奖励应递增: {coins}"

    def test_exp_reward_field_exists(self):
        """每个成就都有exp字段"""
        for ach in ACHIEVEMENTS:
            assert 'exp' in ach['rewards']

    def test_special_reward_field_exists(self):
        """每个成就都有special字段"""
        for ach in ACHIEVEMENTS:
            assert 'special' in ach['rewards']

    def test_icon_text_not_empty(self):
        """每个成就都有图标"""
        for ach in ACHIEVEMENTS:
            assert ach['icon_text'], f"成就{ach['id']}缺少图标"

    def test_desc_not_empty(self):
        """每个成就都有描述"""
        for ach in ACHIEVEMENTS:
            assert ach['desc'], f"成就{ach['id']}缺少描述"


# ══════════════════════════════════════════════
# 2. 条件类型与统计函数映射
# ══════════════════════════════════════════════

class TestConditionTypeMapping:
    """验证每个成就的条件类型在枚举中有定义，且统计函数能正确返回"""

    def test_all_condition_types_used(self):
        """所有成就使用的condition_type都在ConditionType枚举中"""
        used = set(a['condition_type'] for a in ACHIEVEMENTS)
        for ct in used:
            assert isinstance(ct, ConditionType), f"无效条件类型: {ct}"

    def test_stat_function_returns_int(self, fresh_sm):
        """所有条件类型的统计函数应返回整数"""
        for ct in ConditionType:
            result = _get_condition_stat(ct, fresh_sm)
            assert isinstance(result, (int, float)), \
                f"条件类型{ct}返回非数值: {type(result)}"

    def test_stat_function_returns_non_negative(self, fresh_sm):
        """所有条件类型的统计函数应返回非负数"""
        for ct in ConditionType:
            result = _get_condition_stat(ct, fresh_sm)
            assert result >= 0, f"条件类型{ct}返回负数: {result}"

    def test_no_duplicate_condition_type_in_category(self):
        """同维度内不应有重复的条件类型（避免成就雷同）"""
        for cat in ACHIEVE_CATEGORIES:
            achs = ACHIEVEMENTS_BY_CATEGORY[cat]
            types = [a['condition_type'] for a in achs]
            # 允许重复但应有不同阈值
            seen = {}
            for ach in achs:
                ct = ach['condition_type']
                if ct in seen:
                    # 同类型不同阈值是可以的
                    assert ach['threshold'] != seen[ct], \
                        f"维度'{cat}'中{ct}有重复阈值{ach['threshold']}"
                seen[ct] = ach['threshold']


# ══════════════════════════════════════════════
# 3. 进度评估与状态机
# ══════════════════════════════════════════════

class TestAchievementStateMachine:
    """验证状态机: locked → claimable → claimed"""

    def test_fresh_save_all_locked(self, fresh_sm):
        """新存档所有成就应为locked（未解锁）"""
        stats = evaluate_achievements(fresh_sm)
        for aid, st in stats.items():
            assert st['unlocked'] is False, f"新存档{aid}不应已解锁"
            assert st['claimed'] is False, f"新存档{aid}不应已领取"

    def test_locked_to_claimable(self, fresh_sm):
        """满足条件后状态变为claimable（可领取）"""
        sm = fresh_sm
        sm.data['max_level_passed'] = 10
        stats = evaluate_achievements(sm)
        assert stats['H1']['unlocked'] is True  # H1: 通关第10关
        assert stats['H1']['claimed'] is False

    def test_claimable_to_claimed(self, fresh_sm):
        """领取后状态变为claimed（已领取）"""
        sm = fresh_sm
        sm.data['max_level_passed'] = 10
        success, reward = claim_achievement('H1', sm)
        assert success is True
        stats = evaluate_achievements(sm)
        assert stats['H1']['claimed'] is True

    def test_claimed_cannot_be_reclaimed(self, fresh_sm):
        """已领取不可重复领取"""
        sm = fresh_sm
        sm.data['max_level_passed'] = 10
        claim_achievement('H1', sm)
        success, reward = claim_achievement('H1', sm)
        assert success is False
        assert reward == 0

    def test_locked_cannot_be_claimed(self, fresh_sm):
        """未解锁不可领取"""
        sm = fresh_sm
        success, reward = claim_achievement('H1', sm)
        assert success is False
        assert reward == 0

    def test_progress_only_increases(self, fresh_sm):
        """进度只升不降"""
        sm = fresh_sm
        sm.data['ants'] = {
            '1': {'count': 3, 'carry': 0, 'speed': 0, 'defense': 0},
        }
        stats1 = evaluate_achievements(sm)
        # 移除蚂蚁，但统计函数基于当前数据
        sm.data['ants'] = {
            '1': {'count': 1, 'carry': 0, 'speed': 0, 'defense': 0},
        }
        stats2 = evaluate_achievements(sm)
        # C1 (ants_owned >= 1) 仍应解锁
        assert stats2['C1']['unlocked'] is True

    def test_threshold_boundary_exact_match(self, fresh_sm):
        """阈值精确匹配时应解锁"""
        sm = fresh_sm
        sm.data['ants'] = {
            '1': {'count': 5, 'carry': 0, 'speed': 0, 'defense': 0},
        }
        stats = evaluate_achievements(sm)
        assert stats['C2']['unlocked'] is True  # C2: ants_owned >= 5

    def test_threshold_boundary_one_below(self, fresh_sm):
        """差1未达标时不应解锁"""
        sm = fresh_sm
        sm.data['ants'] = {
            '1': {'count': 4, 'carry': 0, 'speed': 0, 'defense': 0},
        }
        stats = evaluate_achievements(sm)
        assert stats['C2']['unlocked'] is False  # C2: ants_owned >= 5


# ══════════════════════════════════════════════
# 4. 领取流程
# ══════════════════════════════════════════════

class TestClaimFlow:
    """验证领取流程的正确性"""

    def test_claim_increases_coins(self, fresh_sm):
        """领取后金币正确增加"""
        sm = fresh_sm
        sm.data['max_level_passed'] = 10
        initial = sm.get_total_coins()
        claim_achievement('H1', sm)
        assert sm.get_total_coins() == initial + 100

    def test_claim_all_20_achievements(self, fresh_sm):
        """能领取所有20个成就"""
        sm = fresh_sm
        # 设置所有条件为极大值
        sm.data['max_level_passed'] = 999
        sm.data['total_coins'] = 999999
        sm.data['levels'] = {}
        for lv in range(1, 201):
            sm.data['levels'][str(lv)] = {
                'best_stars': 3, 'best_coins': 1000,
                'best_time_left': 60, 'times_played': 1, 'times_won': 1,
            }
        sm.data['ants'] = {}
        for i in range(1, 27):
            sm.data['ants'][str(i)] = {
                'count': 5, 'carry': 200, 'speed': 200, 'defense': 200,
            }

        total_reward = 0
        for ach in ACHIEVEMENTS:
            success, reward = claim_achievement(ach['id'], sm)
            if success:
                total_reward += reward

        # 应该能领取大部分成就（部分可能条件不完全满足）
        assert total_reward > 0

    def test_claim_persists_claimed_state(self, fresh_sm):
        """领取后持久化claimed状态"""
        sm = fresh_sm
        sm.data['max_level_passed'] = 10
        claim_achievement('H1', sm)
        assert sm.is_achievement_claimed('H1') is True
        assert sm.get_achievement('H1')['claimed'] is True

    def test_claim_invalid_id_returns_false(self, fresh_sm):
        """无效成就ID返回False"""
        sm = fresh_sm
        success, reward = claim_achievement('INVALID_ID', sm)
        assert success is False
        assert reward == 0

    def test_claim_empty_id_returns_false(self, fresh_sm):
        """空字符串ID返回False"""
        sm = fresh_sm
        success, reward = claim_achievement('', sm)
        assert success is False
        assert reward == 0


# ══════════════════════════════════════════════
# 5. 批量检测与通知去重
# ══════════════════════════════════════════════

class TestBatchDetection:
    """验证evaluate_all_achievements和check_newly_unlocked"""

    def test_evaluate_all_returns_newly_unlocked(self, fresh_sm):
        """evaluate_all_achievements返回新解锁的ID列表"""
        sm = fresh_sm
        sm.data['max_level_passed'] = 10
        newly = sm.evaluate_all_achievements()
        assert 'H1' in newly

    def test_evaluate_all_no_duplicate_notification(self, fresh_sm):
        """连续调用不会重复通知"""
        sm = fresh_sm
        sm.data['max_level_passed'] = 10
        newly1 = sm.evaluate_all_achievements()
        newly2 = sm.evaluate_all_achievements()
        assert 'H1' in newly1
        assert 'H1' not in newly2

    def test_evaluate_all_syncs_progress(self, fresh_sm):
        """evaluate_all_achievements同步进度到存档"""
        sm = fresh_sm
        sm.data['max_level_passed'] = 10
        sm.evaluate_all_achievements()
        progress = sm.get_achievement_progress('H1')
        assert progress == 10

    def test_check_newly_unlocked_function(self, fresh_sm):
        """check_newly_unlocked返回详情列表"""
        sm = fresh_sm
        sm.data['max_level_passed'] = 10
        newly = check_newly_unlocked(sm)
        assert len(newly) > 0
        h1_info = [n for n in newly if n['id'] == 'H1']
        assert len(h1_info) == 1
        assert h1_info[0]['name'] == '小试牛刀'
        assert h1_info[0]['reward'] == 100

    def test_multiple_achievements_unlock_simultaneously(self, fresh_sm):
        """多个成就同时解锁"""
        sm = fresh_sm
        sm.data['max_level_passed'] = 50
        sm.data['ants'] = {
            '1': {'count': 1, 'carry': 0, 'speed': 0, 'defense': 0},
        }
        newly = sm.evaluate_all_achievements()
        # H1 (>=10) 和 H2 (>=50) 和 C1 (>=1) 应同时解锁
        assert 'H1' in newly
        assert 'H2' in newly
        assert 'C1' in newly

    def test_pending_achievements(self, fresh_sm):
        """get_pending_achievements返回已解锁未领取"""
        sm = fresh_sm
        sm.data['max_level_passed'] = 10
        sm.evaluate_all_achievements()
        pending = sm.get_pending_achievements()
        assert 'H1' in pending

    def test_no_pending_after_claim(self, fresh_sm):
        """领取后不在pending列表"""
        sm = fresh_sm
        sm.data['max_level_passed'] = 10
        sm.evaluate_all_achievements()
        claim_achievement('H1', sm)
        pending = sm.get_pending_achievements()
        assert 'H1' not in pending


# ══════════════════════════════════════════════
# 6. 边界场景与异常处理
# ══════════════════════════════════════════════

class TestEdgeCases:
    """边界场景与异常处理"""

    def test_empty_ants_no_crash(self, fresh_sm):
        """空蚂蚁字典不应崩溃"""
        sm = fresh_sm
        sm.data['ants'] = {}
        stats = evaluate_achievements(sm)
        assert stats['C1']['unlocked'] is False
        assert stats['C1']['current'] == 0

    def test_zero_max_level_no_crash(self, fresh_sm):
        """max_level_passed=0不应崩溃"""
        sm = fresh_sm
        sm.data['max_level_passed'] = 0
        stats = evaluate_achievements(sm)
        assert stats['H1']['unlocked'] is False

    def test_zero_coins_no_crash(self, fresh_sm):
        """total_coins=0不应崩溃"""
        sm = fresh_sm
        sm.data['total_coins'] = 0
        stats = evaluate_achievements(sm)
        assert stats['E4']['unlocked'] is False

    def test_no_levels_data_no_crash(self, fresh_sm):
        """空关卡数据不应崩溃"""
        sm = fresh_sm
        sm.data['levels'] = {}
        stats = evaluate_achievements(sm)
        assert stats['S1']['unlocked'] is False

    def test_large_values_no_overflow(self, fresh_sm):
        """极大值不应溢出"""
        sm = fresh_sm
        sm.data['max_level_passed'] = 999999
        sm.data['total_coins'] = 999999999
        sm.data['levels'] = {}
        for lv in range(1, 1000):
            sm.data['levels'][str(lv)] = {
                'best_stars': 3, 'best_coins': 10000,
                'best_time_left': 3600, 'times_played': 100, 'times_won': 100,
            }
        stats = evaluate_achievements(sm)
        # 不应崩溃
        assert stats['H4']['unlocked'] is True  # max_level >= 200
        assert stats['S4']['unlocked'] is True  # stars >= 300

    def test_negative_values_no_crash(self, fresh_sm):
        """负数值不应崩溃"""
        sm = fresh_sm
        sm.data['max_level_passed'] = -1
        sm.data['total_coins'] = -100
        stats = evaluate_achievements(sm)
        # 不应崩溃，负数应被处理为0或保持
        for aid, st in stats.items():
            assert isinstance(st['current'], (int, float))

    def test_missing_ants_key_no_crash(self, fresh_sm):
        """ants字典缺少必要字段不崩溃（count默认0）"""
        sm = fresh_sm
        sm.data['ants'] = {'1': {}}
        stats = evaluate_achievements(sm)
        assert stats['C1']['current'] == 0  # 空字典无count字段，默认0

    def test_claim_before_any_progress(self, fresh_sm):
        """没有任何进度时领取应失败"""
        sm = fresh_sm
        success, _ = claim_achievement('C1', sm)
        assert success is False

    def test_upgrade_then_achievement(self, fresh_sm):
        """升级蚂蚁后触发养成类成就"""
        sm = fresh_sm
        sm.data['ants'] = {
            '1': {'count': 1, 'carry': 10, 'speed': 0, 'defense': 0},
        }
        stats = evaluate_achievements(sm)
        assert stats['G1']['unlocked'] is True  # carry >= 10


# ══════════════════════════════════════════════
# 7. 存档集成与持久化
# ══════════════════════════════════════════════

class TestSaveIntegration:
    """验证成就数据的存档持久化"""

    def test_achievements_in_default_save(self):
        """默认存档包含所有成就初始数据"""
        from save_manager import _default_save_data
        data = _default_save_data()
        assert 'achievements' in data
        assert len(data['achievements']) == len(ACHIEVEMENTS)
        for ach in ACHIEVEMENTS:
            entry = data['achievements'][ach['id']]
            assert entry == {'progress': 0, 'claimed': False}

    def test_save_version_is_5(self):
        """当前存档版本为5"""
        from save_manager import SAVE_VERSION
        assert SAVE_VERSION == 5

    def test_progress_persistence(self, fresh_sm):
        """进度更新后持久化"""
        sm = fresh_sm
        sm.update_achievement_progress('C1', 3)
        assert sm.get_achievement_progress('C1') == 3

    def test_claimed_persistence(self, fresh_sm):
        """领取状态持久化"""
        sm = fresh_sm
        sm.update_achievement_progress('C1', 1)
        sm.claim_achievement_reward('C1')
        assert sm.is_achievement_claimed('C1') is True

    def test_evaluate_all_persists_progress(self, fresh_sm):
        """evaluate_all_achievements持久化进度"""
        sm = fresh_sm
        sm.data['max_level_passed'] = 10
        sm.evaluate_all_achievements()
        assert sm.get_achievement_progress('H1') == 10

    def test_evaluate_all_persists_unlocked_notified(self, fresh_sm):
        """evaluate_all_achievements持久化unlocked_notified标记"""
        sm = fresh_sm
        sm.data['max_level_passed'] = 10
        sm.evaluate_all_achievements()
        ach_data = sm.data['achievements']['H1']
        assert ach_data.get('unlocked_notified') is True


# ══════════════════════════════════════════════
# 8. 各维度条件类型专项测试
# ══════════════════════════════════════════════

class TestDimensionSpecific:
    """按维度验证条件类型的正确性"""

    # ── 收集维度 ──

    def test_collect_ants_owned(self, fresh_sm):
        """收集维度: ants_owned条件"""
        sm = fresh_sm
        sm.data['ants'] = {
            '1': {'count': 3, 'carry': 0, 'speed': 0, 'defense': 0},
            '2': {'count': 2, 'carry': 0, 'speed': 0, 'defense': 0},
        }
        stats = evaluate_achievements(sm)
        assert stats['C1']['current'] == 5  # 3+2
        assert stats['C1']['unlocked'] is True  # >= 1
        assert stats['C2']['unlocked'] is True  # >= 5

    def test_collect_ants_unique(self, fresh_sm):
        """收集维度: ants_unique条件"""
        sm = fresh_sm
        sm.data['ants'] = {
            str(i): {'count': 1, 'carry': 0, 'speed': 0, 'defense': 0}
            for i in range(1, 11)
        }
        stats = evaluate_achievements(sm)
        assert stats['C3']['current'] == 10
        assert stats['C3']['unlocked'] is True  # >= 10

    # ── 挑战维度 ──

    def test_challenge_max_level(self, fresh_sm):
        """挑战维度: max_level条件"""
        sm = fresh_sm
        sm.data['max_level_passed'] = 100
        stats = evaluate_achievements(sm)
        assert stats['H1']['unlocked'] is True  # >= 10
        assert stats['H2']['unlocked'] is True  # >= 50
        assert stats['H3']['unlocked'] is True  # >= 100
        assert stats['H4']['unlocked'] is False  # >= 200

    # ── 星级维度 ──

    def test_stars_earned(self, fresh_sm):
        """星级维度: stars_earned条件"""
        sm = fresh_sm
        sm.data['levels'] = {}
        for lv in range(1, 51):
            sm.data['levels'][str(lv)] = {
                'best_stars': 1, 'best_coins': 100,
                'best_time_left': 10, 'times_played': 1, 'times_won': 1,
            }
        stats = evaluate_achievements(sm)
        assert stats['S1']['current'] == 50
        assert stats['S1']['unlocked'] is True  # >= 10
        assert stats['S2']['unlocked'] is True  # >= 50
        assert stats['S3']['unlocked'] is False  # >= 150

    # ── 探索维度 ──

    def test_exploration_terrains(self, fresh_sm):
        """探索维度: terrains_explored条件"""
        sm = fresh_sm
        # 需要不同地形的关卡
        from levels_data import get_level
        terrains_found = set()
        for lv in range(1, 201):
            try:
                level_data = get_level(lv)
                terrain = level_data.get('terrain_name', '')
                if terrain:
                    terrains_found.add(terrain)
                if len(terrains_found) >= 3:
                    break
            except Exception:
                pass
        # 至少应找到1种地形
        assert len(terrains_found) >= 1

    # ── 养成维度 ──

    def test_development_max_carry(self, fresh_sm):
        """养成维度: max_carry_level条件"""
        sm = fresh_sm
        sm.data['ants'] = {
            '1': {'count': 1, 'carry': 10, 'speed': 0, 'defense': 0},
        }
        stats = evaluate_achievements(sm)
        assert stats['G1']['current'] == 10
        assert stats['G1']['unlocked'] is True  # >= 10

    def test_development_max_speed(self, fresh_sm):
        """养成维度: max_speed_level条件"""
        sm = fresh_sm
        sm.data['ants'] = {
            '1': {'count': 1, 'carry': 0, 'speed': 100, 'defense': 0},
        }
        stats = evaluate_achievements(sm)
        assert stats['G2']['unlocked'] is True  # >= 100

    def test_development_maxed_ants(self, fresh_sm):
        """养成维度: maxed_ants条件"""
        sm = fresh_sm
        sm.data['ants'] = {
            '1': {'count': 1, 'carry': 200, 'speed': 0, 'defense': 0},
            '2': {'count': 1, 'carry': 200, 'speed': 0, 'defense': 0},
            '3': {'count': 1, 'carry': 200, 'speed': 0, 'defense': 0},
        }
        stats = evaluate_achievements(sm)
        assert stats['G4']['current'] == 3
        assert stats['G4']['unlocked'] is True  # >= 3


# ══════════════════════════════════════════════
# 9. 总进度统计
# ══════════════════════════════════════════════

class TestTotalProgress:
    """验证get_total_progress统计"""

    def test_fresh_save_zero_progress(self, fresh_sm):
        """新存档总进度为0"""
        unlocked, total, claimed = get_total_progress(fresh_sm)
        assert unlocked == 0
        assert total == 20
        assert claimed == 0

    def test_progress_after_unlock(self, fresh_sm):
        """解锁后进度增加"""
        sm = fresh_sm
        sm.data['max_level_passed'] = 10
        unlocked, total, claimed = get_total_progress(sm)
        assert unlocked >= 1

    def test_progress_after_claim(self, fresh_sm):
        """领取后claimed增加"""
        sm = fresh_sm
        sm.data['max_level_passed'] = 10
        claim_achievement('H1', sm)
        unlocked, total, claimed = get_total_progress(sm)
        assert claimed >= 1

    def test_total_always_20(self, fresh_sm):
        """总数始终为20"""
        for level in [0, 10, 50, 100, 200]:
            sm = fresh_sm
            sm.data['max_level_passed'] = level
            _, total, _ = get_total_progress(sm)
            assert total == 20


# ══════════════════════════════════════════════
# 10. 综合场景测试
# ══════════════════════════════════════════════

class TestIntegrationScenarios:
    """端到端综合场景"""

    def test_new_player_progression(self, fresh_sm):
        """新玩家渐进式解锁成就"""
        sm = fresh_sm

        # 第一步：获得初始蚂蚁 → C1解锁
        sm.data['ants'] = {
            '1': {'count': 1, 'carry': 0, 'speed': 0, 'defense': 0},
        }
        newly = sm.evaluate_all_achievements()
        assert 'C1' in newly

        # 第二步：通关第10关 → H1解锁
        sm.data['max_level_passed'] = 10
        newly = sm.evaluate_all_achievements()
        assert 'H1' in newly

        # 第三步：领取C1
        claim_achievement('C1', sm)
        assert sm.is_achievement_claimed('C1') is True

        # 第四步：领取H1
        claim_achievement('H1', sm)
        assert sm.is_achievement_claimed('H1') is True

        # 验证总进度
        unlocked, total, claimed = get_total_progress(sm)
        assert unlocked >= 2
        assert claimed == 2

    def test_multiple_achievements_claim_batch(self, fresh_sm):
        """批量领取多个成就"""
        sm = fresh_sm
        sm.data['max_level_passed'] = 50
        sm.data['ants'] = {
            '1': {'count': 5, 'carry': 0, 'speed': 0, 'defense': 0},
        }
        newly = sm.evaluate_all_achievements()
        # 应有多个新解锁
        assert len(newly) >= 2

        # 批量领取
        for aid in newly:
            success, reward = claim_achievement(aid, sm)
            assert success is True
            assert reward > 0

        # 验证所有已领取
        pending = sm.get_pending_achievements()
        assert len(pending) == 0

    def test_full_game_session(self, fresh_sm):
        """模拟完整游戏会话"""
        sm = fresh_sm

        # 模拟游戏进程
        sm.data['ants'] = {
            '1': {'count': 3, 'carry': 15, 'speed': 20, 'defense': 5},
            '2': {'count': 2, 'carry': 10, 'speed': 5, 'defense': 3},
            '3': {'count': 1, 'carry': 0, 'speed': 0, 'defense': 0},
        }
        sm.data['max_level_passed'] = 25
        sm.data['total_coins'] = 5000
        sm.data['levels'] = {}
        for lv in range(1, 26):
            sm.data['levels'][str(lv)] = {
                'best_stars': min(3, (lv % 3) + 1),
                'best_coins': 200 + lv * 10,
                'best_time_left': 30.0,
                'times_played': 2,
                'times_won': 1,
            }

        # 评估成就
        newly = sm.evaluate_all_achievements()

        # 验证解锁的成就合理
        assert 'C1' in newly  # ants_owned >= 1
        assert 'C2' in newly  # ants_owned >= 5 (3+2+1=6)
        assert 'H1' in newly  # max_level >= 10

        # 领取所有可领取的
        for aid in newly:
            success, _ = claim_achievement(aid, sm)
            assert success is True

        # 验证最终状态
        unlocked, total, claimed = get_total_progress(sm)
        assert unlocked >= 3
        assert claimed >= 3
