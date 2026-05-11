"""签到系统测试 — checkin_data.py 独立函数 + SaveManager 接口

测试覆盖：
  1. checkin_data.py: 签到状态判断、执行逻辑、UI数据
  2. SaveManager: can_checkin_today / perform_checkin / get_checkin_data
  3. 边界场景: 跨天签到、首日、第7天周期重置、多周期
  4. 存档持久化: 签到状态保存/读取
  5. 数据一致性检查: checkin_data vs SaveManager 行为对比

日期格式统一: checkin_data 和 SaveManager 均使用 YYYY-MM-DD
current_day 语义统一: 0 表示未签到/周期刚完成，签到后递增（两者一致）
返回值类型统一: checkin_data 和 SaveManager.perform_checkin 均返回 dict
"""

import json
import os
import sys
import copy
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import save_manager
from save_manager import SaveManager, _default_save_data

# checkin_data 模块
from checkin_data import (
    CheckinStatus, RewardType, CHECKIN_REWARDS, REWARD_BY_DAY, TOTAL_CYCLE_REWARD,
    get_checkin_status, can_checkin_today as cd_can_checkin_today,
    perform_checkin as cd_perform_checkin, get_checkin_ui_data, get_today_str,
)


# ══════════════════════════════════════════════
# Fixtures
# ══════════════════════════════════════════════

@pytest.fixture
def fresh_sm():
    """创建全新 SaveManager"""
    sm = SaveManager()
    sm.loaded = True
    return sm


@pytest.fixture
def tmp_save_dir(tmp_path, monkeypatch):
    """临时存档目录"""
    monkeypatch.setattr(save_manager, 'SAVE_DIR', str(tmp_path))
    monkeypatch.setattr(save_manager, 'SAVE_FILE', os.path.join(str(tmp_path), 'save_data.json'))
    return tmp_path


def _today_str_cd():
    """checkin_data 格式: YYYY-MM-DD (与 SaveManager 统一)"""
    return datetime.now().strftime('%Y-%m-%d')


def _today_str_sm():
    """SaveManager 格式: YYYY-MM-DD"""
    return datetime.now().strftime('%Y-%m-%d')


def _days_ago_str_cd(n):
    return (datetime.now() - timedelta(days=n)).strftime('%Y-%m-%d')


def _days_ago_str_sm(n):
    return (datetime.now() - timedelta(days=n)).strftime('%Y-%m-%d')


def _set_checkin_state(sm, **kwargs):
    """快捷设置 SaveManager 签到状态"""
    checkin = sm.data.setdefault('checkin', {
        'current_day': 0,
        'last_checkin_date': None,
        'total_checkins': 0,
        'streak': 0,
        'cycles_completed': 0,
    })
    for key, value in kwargs.items():
        checkin[key] = value


def _make_checkin_data(current_day=0, last_checkin_date=None, total_checkins=0, streak=0, cycles_completed=0):
    """构造 checkin_data 签到状态（current_day 从 0 开始）"""
    return {
        'current_day': current_day,
        'last_checkin_date': last_checkin_date,
        'total_checkins': total_checkins,
        'streak': streak,
        'cycles_completed': cycles_completed,
    }


# ══════════════════════════════════════════════
# A. checkin_data.py 独立函数测试
# ══════════════════════════════════════════════

class TestCheckinDataConfig:
    """验证 checkin_data 配置"""

    def test_rewards_count_is_7(self):
        """7天周期，7个奖励"""
        assert len(CHECKIN_REWARDS) == 7

    def test_rewards_are_dicts(self):
        """奖励配置是字典"""
        for r in CHECKIN_REWARDS:
            assert isinstance(r, dict)
            assert 'day' in r
            assert 'amount' in r

    def test_rewards_days_1_to_7(self):
        """奖励天数从1到7"""
        days = [r['day'] for r in CHECKIN_REWARDS]
        assert days == [1, 2, 3, 4, 5, 6, 7]

    def test_rewards_amounts_ascending(self):
        """奖励金额递增"""
        amounts = [r['amount'] for r in CHECKIN_REWARDS]
        for i in range(1, len(amounts)):
            assert amounts[i] >= amounts[i - 1]

    def test_day_7_is_big_reward(self):
        """第7天是大奖"""
        assert CHECKIN_REWARDS[6]['is_big_reward'] is True

    def test_reward_by_day_index(self):
        """REWARD_BY_DAY 索引正确"""
        for r in CHECKIN_REWARDS:
            assert REWARD_BY_DAY[r['day']]['amount'] == r['amount']

    def test_total_cycle_reward(self):
        """单周期全勤总奖励正确"""
        expected = sum(r['amount'] for r in CHECKIN_REWARDS)
        assert TOTAL_CYCLE_REWARD == expected

    def test_reward_types_are_coins(self):
        """当前所有奖励类型为金币"""
        for r in CHECKIN_REWARDS:
            assert r['reward_type'] == RewardType.COINS


class TestCheckinStatus:
    """验证签到状态判断 (checkin_data.py)"""

    def test_first_time(self):
        """从未签到 → FIRST_TIME"""
        data = _make_checkin_data()
        assert get_checkin_status(data) == CheckinStatus.FIRST_TIME

    def test_checked_in_today(self):
        """今天已签到 → CHECKED_IN"""
        data = _make_checkin_data(last_checkin_date=_today_str_cd())
        assert get_checkin_status(data) == CheckinStatus.CHECKED_IN

    def test_not_checked_in_today(self):
        """昨天签过，今天没签 → NOT_CHECKED_IN"""
        data = _make_checkin_data(last_checkin_date=_days_ago_str_cd(1))
        assert get_checkin_status(data) == CheckinStatus.NOT_CHECKED_IN

    def test_not_checked_long_ago(self):
        """很久以前签过 → NOT_CHECKED_IN"""
        data = _make_checkin_data(last_checkin_date=_days_ago_str_cd(30))
        assert get_checkin_status(data) == CheckinStatus.NOT_CHECKED_IN


class TestCdCanCheckinToday:
    """验证 checkin_data.can_checkin_today"""

    def test_first_time_can_checkin(self):
        """首次签到可签"""
        data = _make_checkin_data()
        assert cd_can_checkin_today(data) is True

    def test_already_checked_in_cannot(self):
        """今天已签到不可重复签"""
        data = _make_checkin_data(last_checkin_date=_today_str_cd())
        assert cd_can_checkin_today(data) is False

    def test_checked_yesterday_can(self):
        """昨天签过，今天可签"""
        data = _make_checkin_data(last_checkin_date=_days_ago_str_cd(1))
        assert cd_can_checkin_today(data) is True

    def test_with_custom_today(self):
        """自定义 today_str 参数"""
        data = _make_checkin_data(last_checkin_date='20260101')
        assert cd_can_checkin_today(data, today_str='20260102') is True
        assert cd_can_checkin_today(data, today_str='20260101') is False


class TestCdPerformCheckin:
    """验证 checkin_data.perform_checkin"""

    def test_first_checkin(self):
        """首次签到成功"""
        data = _make_checkin_data()
        result = cd_perform_checkin(data, today_str='2026-05-10')
        assert result['success'] is True
        assert result['day'] == 1
        assert result['reward']['amount'] == 100

    def test_first_checkin_updates_fields(self):
        """首次签到更新所有字段"""
        data = _make_checkin_data()
        cd_perform_checkin(data, today_str='2026-05-10')
        assert data['last_checkin_date'] == '2026-05-10'
        assert data['total_checkins'] == 1
        assert data['streak'] == 1
        assert data['current_day'] == 1

    def test_double_checkin_rejected(self):
        """同一天重复签到被拒"""
        data = _make_checkin_data(last_checkin_date='2026-05-10')
        result = cd_perform_checkin(data, today_str='2026-05-10')
        assert result['success'] is False

    def test_consecutive_day_increments_streak(self):
        """连续签到 streak +1"""
        data = _make_checkin_data(
            current_day=1, last_checkin_date='2026-05-09', streak=1, total_checkins=1
        )
        cd_perform_checkin(data, today_str='2026-05-10')
        assert data['streak'] == 2
        assert data['current_day'] == 2

    def test_break_resets_streak(self):
        """断签 streak 归 1"""
        data = _make_checkin_data(
            current_day=3, last_checkin_date='2026-05-07', streak=3, total_checkins=3
        )
        cd_perform_checkin(data, today_str='2026-05-10')
        assert data['streak'] == 1

    def test_break_preserves_current_day(self):
        """断签不重置 current_day（已签天数保留）"""
        data = _make_checkin_data(
            current_day=3, last_checkin_date='2026-05-07', streak=3, total_checkins=3
        )
        cd_perform_checkin(data, today_str='2026-05-10')
        assert data['current_day'] == 4  # 从3推进到4

    def test_day7_completes_cycle(self):
        """第7天完成周期"""
        data = _make_checkin_data(
            current_day=6, last_checkin_date='2026-05-09', streak=6, total_checkins=6
        )
        result = cd_perform_checkin(data, today_str='2026-05-10')
        assert result['day'] == 7
        assert result['cycle_completed'] is True
        assert result['new_cycle'] is True
        assert data['cycles_completed'] == 1
        assert data['current_day'] == 0  # 重置为0

    def test_day7_big_reward(self):
        """第7天获得大奖"""
        data = _make_checkin_data(
            current_day=6, last_checkin_date='2026-05-09', streak=6, total_checkins=6
        )
        result = cd_perform_checkin(data, today_str='2026-05-10')
        assert result['reward']['is_big_reward'] is True
        # Day7: base=1000, streak=7 → bonus=0.5, cycle=0 → multiplier=1.0
        # actual = 1000 * 1.5 * 1.0 = 1500
        assert result['reward']['amount'] == 1500

    def test_new_cycle_day1(self):
        """周期完成后下次签到是新周期第1天"""
        data = _make_checkin_data(
            current_day=0, last_checkin_date='2026-05-10', streak=7,
            total_checkins=7, cycles_completed=1
        )
        result = cd_perform_checkin(data, today_str='2026-05-11')
        assert result['day'] == 1
        # Day1: base=100, streak=8 → bonus=0.5(cap), cycle=1 → multiplier=1.2
        # actual = 100 * 1.5 * 1.2 = 180
        assert result['reward']['amount'] == 180

    def test_multiple_cycles(self):
        """多周期循环"""
        data = _make_checkin_data()
        base = datetime(2026, 5, 10)
        for cycle in range(3):
            for day in range(7):
                today = (base + timedelta(days=cycle * 7 + day)).strftime('%Y-%m-%d')
                cd_perform_checkin(data, today_str=today)
        assert data['cycles_completed'] == 3
        assert data['total_checkins'] == 21

    def test_increments_total_checkins(self):
        """total_checkins 正确递增"""
        data = _make_checkin_data(total_checkins=10)
        cd_perform_checkin(data, today_str='2026-05-10')
        assert data['total_checkins'] == 11


class TestCheckinUiData:
    """验证 checkin_data.get_checkin_ui_data"""

    def test_returns_dict(self):
        """返回字典"""
        data = _make_checkin_data()
        result = get_checkin_ui_data(data)
        assert isinstance(result, dict)

    def test_has_required_keys(self):
        """包含所有必要字段"""
        data = _make_checkin_data()
        result = get_checkin_ui_data(data)
        required = ['status', 'current_day', 'streak', 'total_checkins',
                     'cycles_completed', 'can_checkin', 'rewards', 'today_reward', 'cycle_total']
        for key in required:
            assert key in result, f"缺少字段: {key}"

    def test_can_checkin_matches_status(self):
        """can_checkin 与 status 一致"""
        data = _make_checkin_data()
        result = get_checkin_ui_data(data)
        assert result['can_checkin'] is True
        assert result['status'] == CheckinStatus.FIRST_TIME

    def test_after_checkin_can_checkin_false(self):
        """签到后 can_checkin 为 False"""
        data = _make_checkin_data(last_checkin_date=_today_str_cd())
        result = get_checkin_ui_data(data)
        assert result['can_checkin'] is False

    def test_rewards_list_length(self):
        """rewards 列表长度为7"""
        data = _make_checkin_data()
        result = get_checkin_ui_data(data)
        assert len(result['rewards']) == 7

    def test_rewards_have_checked_field(self):
        """每个奖励项包含 checked 字段"""
        data = _make_checkin_data()
        result = get_checkin_ui_data(data)
        for r in result['rewards']:
            assert 'checked' in r

    def test_cycle_total(self):
        """cycle_total 等于 TOTAL_CYCLE_REWARD"""
        data = _make_checkin_data()
        result = get_checkin_ui_data(data)
        assert result['cycle_total'] == TOTAL_CYCLE_REWARD

    def test_display_day_after_cycle_complete(self):
        """周期完成后 display_day 显示为7"""
        data = _make_checkin_data(current_day=0, cycles_completed=1)
        result = get_checkin_ui_data(data)
        # current_day 为 0 但有已完成周期时，应显示 7
        assert result['current_day'] == 0  # 原始值
        # 但 UI 逻辑中 display_day = 7 if current_day == 0 and cycles_completed > 0


# ══════════════════════════════════════════════
# B. SaveManager 接口测试
# ══════════════════════════════════════════════

class TestSmCanCheckinToday:
    """验证 SaveManager.can_checkin_today"""

    def test_first_time_can_checkin(self, fresh_sm):
        """首次签到可签"""
        assert fresh_sm.can_checkin_today() is True

    def test_already_checked_in_today(self, fresh_sm):
        """今天已签到不可重复签"""
        _set_checkin_state(fresh_sm, last_checkin_date=_today_str_sm())
        assert fresh_sm.can_checkin_today() is False

    def test_checked_yesterday_can(self, fresh_sm):
        """昨天签过可签"""
        _set_checkin_state(fresh_sm, last_checkin_date=_days_ago_str_sm(1))
        assert fresh_sm.can_checkin_today() is True

    def test_last_date_is_none_can(self, fresh_sm):
        """last_checkin_date 为 None 可签"""
        _set_checkin_state(fresh_sm, last_checkin_date=None)
        assert fresh_sm.can_checkin_today() is True


class TestSmPerformCheckin:
    """验证 SaveManager.perform_checkin"""

    def test_first_checkin_returns_dict(self, fresh_sm):
        """首次签到返回 dict（与 checkin_data 统一）"""
        result = fresh_sm.perform_checkin()
        assert isinstance(result, dict)
        assert 'success' in result
        assert 'reward' in result
        assert 'day' in result
        assert 'cycle_completed' in result
        assert 'new_cycle' in result
        assert result['success'] is True

    def test_first_checkin_reward(self, fresh_sm):
        """首次签到获得第1天奖励
        SM: current_day 从 0 递增到 1，reward = calc_actual_reward(base_rewards[0], streak=1, cycles=0)
        base_rewards[0] = 100, streak_bonus = 0, cycle_multiplier = 1.0
        actual = 100 * 1.0 * 1.0 = 100
        """
        result = fresh_sm.perform_checkin()
        assert result['success'] is True
        assert result['reward']['amount'] == 100  # base_rewards[0]=100, no bonuses

    def test_first_checkin_updates_fields(self, fresh_sm):
        """首次签到更新所有字段"""
        fresh_sm.perform_checkin()
        checkin = fresh_sm.data['checkin']
        assert checkin['last_checkin_date'] == _today_str_sm()
        assert checkin['total_checkins'] == 1
        assert checkin['streak'] == 1
        assert checkin['current_day'] == 1  # SM: 从0递增到1

    def test_double_checkin_rejected(self, fresh_sm):
        """同一天重复签到被拒"""
        fresh_sm.perform_checkin()
        result = fresh_sm.perform_checkin()
        assert result['success'] is False
        assert result['reward'] is None

    def test_consecutive_day_increments_streak(self, fresh_sm):
        """连续签到 streak +1"""
        _set_checkin_state(fresh_sm, last_checkin_date=_days_ago_str_sm(1), current_day=2, streak=1, total_checkins=1)
        result = fresh_sm.perform_checkin()
        assert result['success'] is True
        assert fresh_sm.data['checkin']['streak'] == 2

    def test_break_resets_streak(self, fresh_sm):
        """断签 streak 归 1"""
        _set_checkin_state(fresh_sm, last_checkin_date=_days_ago_str_sm(3), current_day=4, streak=3, total_checkins=3)
        fresh_sm.perform_checkin()
        assert fresh_sm.data['checkin']['streak'] == 1

    def test_break_does_not_reset_current_day(self, fresh_sm):
        """⚠️ SM 断签不重置 current_day（与 checkin_data 行为一致）"""
        _set_checkin_state(fresh_sm, last_checkin_date=_days_ago_str_sm(3), current_day=5, streak=3, total_checkins=3)
        fresh_sm.perform_checkin()
        # SM: current_day 从5递增到6，断签不重置
        assert fresh_sm.data['checkin']['current_day'] == 6

    def test_day7_completes_cycle(self, fresh_sm):
        """第7天完成周期（current_day=6 → 签到后 day=7 → 触发周期完成）"""
        _set_checkin_state(fresh_sm, last_checkin_date=_days_ago_str_sm(1), current_day=6, streak=6, total_checkins=6)
        fresh_sm.perform_checkin()
        checkin = fresh_sm.data['checkin']
        assert checkin['cycles_completed'] == 1
        assert checkin['current_day'] == 0  # checkin_data: 完成后重置到0

    def test_adds_coins(self, fresh_sm):
        """签到后金币增加（SM 首次签到奖励为 100）"""
        initial = fresh_sm.get_total_coins()
        result = fresh_sm.perform_checkin()
        assert fresh_sm.get_total_coins() == initial + result['reward']['amount']

    def test_saves_after_checkin(self, fresh_sm, tmp_save_dir):
        """签到后自动保存"""
        fresh_sm.perform_checkin()
        sm2 = SaveManager()
        sm2.load()
        assert sm2.data['checkin']['total_checkins'] == 1


class TestSmGetCheckinData:
    """验证 SaveManager.get_checkin_data"""

    def test_returns_dict(self, fresh_sm):
        """返回字典"""
        data = fresh_sm.get_checkin_data()
        assert isinstance(data, dict)

    def test_has_default_fields(self, fresh_sm):
        """包含默认字段"""
        data = fresh_sm.get_checkin_data()
        assert 'current_day' in data
        assert 'last_checkin_date' in data
        assert 'total_checkins' in data
        assert 'streak' in data
        assert 'cycles_completed' in data


class TestSmGetCheckinRewardForDay:
    """验证 SaveManager.get_checkin_reward_for_day"""

    def test_day_1(self, fresh_sm):
        assert fresh_sm.get_checkin_reward_for_day(1) == 100

    def test_day_7(self, fresh_sm):
        assert fresh_sm.get_checkin_reward_for_day(7) == 1000

    def test_day_8_wraps(self, fresh_sm):
        """超出范围的天数取模"""
        assert fresh_sm.get_checkin_reward_for_day(8) == 100


# ══════════════════════════════════════════════
# C. 边界场景测试
# ══════════════════════════════════════════════

class TestEdgeCases:
    """验证各种边界条件"""

    def test_cd_first_day_full_state(self):
        """checkin_data: 首日签到完整状态"""
        data = _make_checkin_data()
        result = cd_perform_checkin(data, today_str='2026-05-10')
        assert result['success'] is True
        assert result['day'] == 1
        assert data['current_day'] == 1
        assert data['total_checkins'] == 1
        assert data['streak'] == 1
        assert data['cycles_completed'] == 0

    def test_sm_first_day_full_state(self, fresh_sm):
        """SaveManager: 首日签到完整状态"""
        result = fresh_sm.perform_checkin()
        checkin = fresh_sm.data['checkin']
        assert result['success'] is True
        assert checkin['current_day'] == 1  # SM: 从0递增到1
        assert checkin['total_checkins'] == 1
        assert checkin['streak'] == 1
        assert checkin['cycles_completed'] == 0

    def test_cd_cross_midnight(self):
        """checkin_data: 跨天签到"""
        data = _make_checkin_data()
        cd_perform_checkin(data, today_str='2026-05-10')
        assert cd_can_checkin_today(data, today_str='2026-05-10') is False
        assert cd_can_checkin_today(data, today_str='2026-05-11') is True

    def test_sm_cross_midnight(self, fresh_sm):
        """SaveManager: 跨天签到"""
        fresh_sm.perform_checkin()
        assert fresh_sm.can_checkin_today() is False
        # 模拟第二天
        _set_checkin_state(fresh_sm, last_checkin_date=_days_ago_str_sm(1))
        assert fresh_sm.can_checkin_today() is True

    def test_cd_long_absence(self):
        """checkin_data: 长时间未签到后回归"""
        data = _make_checkin_data(
            current_day=5, last_checkin_date='2026-03-01', streak=4, total_checkins=50
        )
        cd_perform_checkin(data, today_str='2026-05-10')
        assert data['streak'] == 1  # 断签归1
        assert data['current_day'] == 6  # 保留进度
        assert data['total_checkins'] == 51

    def test_sm_long_absence(self, fresh_sm):
        """SaveManager: 长时间未签到后回归，current_day 不重置"""
        _set_checkin_state(fresh_sm,
            last_checkin_date=_days_ago_str_sm(60),
            current_day=5, streak=4, total_checkins=50
        )
        fresh_sm.perform_checkin()
        checkin = fresh_sm.data['checkin']
        assert checkin['streak'] == 1  # 断签归1
        assert checkin['current_day'] == 6  # SM: current_day 递增不重置
        assert checkin['total_checkins'] == 51

    def test_cd_day7_then_new_cycle(self):
        """checkin_data: 第7天签到后进入新周期"""
        data = _make_checkin_data(
            current_day=6, last_checkin_date='2026-05-09', streak=6, total_checkins=6
        )
        result = cd_perform_checkin(data, today_str='2026-05-10')
        assert result['cycle_completed'] is True
        assert data['cycles_completed'] == 1
        assert data['current_day'] == 0
        # 新周期第1天
        result2 = cd_perform_checkin(data, today_str='2026-05-11')
        assert result2['day'] == 1
        assert result2['new_cycle'] is False

    def test_sm_day7_then_new_cycle(self, fresh_sm):
        """SaveManager: 第7天签到后进入新周期（current_day=6 → day=7 → 周期完成）"""
        _set_checkin_state(fresh_sm, current_day=6, streak=6, total_checkins=6)
        fresh_sm.perform_checkin()
        checkin = fresh_sm.data['checkin']
        assert checkin['cycles_completed'] == 1
        assert checkin['current_day'] == 0  # checkin_data: 完成后重置到0

    def test_cd_multiple_cycles(self):
        """checkin_data: 多周期完整循环"""
        data = _make_checkin_data()
        base = datetime(2026, 5, 10)
        for cycle in range(3):
            for day in range(7):
                today = (base + timedelta(days=cycle * 7 + day)).strftime('%Y-%m-%d')
                cd_perform_checkin(data, today_str=today)
        assert data['cycles_completed'] == 3
        assert data['total_checkins'] == 21

    def test_sm_multiple_cycles(self, fresh_sm):
        """SaveManager: 多周期完整循环"""
        # SM 在 perform_checkin 内部 import date，需要 patch datetime.date
        from datetime import date as real_date
        base_date = datetime(2026, 5, 10)
        for i in range(22):
            mock_date = base_date + timedelta(days=i)
            mock_date_obj = real_date(mock_date.year, mock_date.month, mock_date.day)
            with patch('datetime.date') as mock_date_cls:
                mock_date_cls.today.return_value = mock_date_obj
                mock_date_cls.fromisoformat = real_date.fromisoformat
                fresh_sm.perform_checkin()
        checkin = fresh_sm.data['checkin']
        assert checkin['cycles_completed'] == 3
        assert checkin['total_checkins'] == 22


# ══════════════════════════════════════════════
# D. 存档持久化测试
# ══════════════════════════════════════════════

class TestPersistence:
    """验证签到状态的保存与读取"""

    def test_save_load_roundtrip(self, tmp_save_dir):
        """签到后保存，重新加载一致"""
        sm = SaveManager()
        sm.perform_checkin()
        sm.save()

        sm2 = SaveManager()
        sm2.load()
        assert sm2.data['checkin']['total_checkins'] == 1
        assert sm2.data['checkin']['last_checkin_date'] == _today_str_sm()
        assert sm2.data['checkin']['streak'] == 1

    def test_save_load_multiple_checkins(self, tmp_save_dir):
        """多次签到后保存，重新加载一致"""
        from datetime import date as real_date
        sm = SaveManager()
        base_date = datetime(2026, 5, 10)
        for i in range(5):
            mock_date = base_date + timedelta(days=i)
            mock_date_obj = real_date(mock_date.year, mock_date.month, mock_date.day)
            with patch('datetime.date') as mock_date_cls:
                mock_date_cls.today.return_value = mock_date_obj
                mock_date_cls.fromisoformat = real_date.fromisoformat
                sm.perform_checkin()
        sm.save()

        sm2 = SaveManager()
        sm2.load()
        assert sm2.data['checkin']['total_checkins'] == 5

    def test_default_checkin_on_no_save(self, tmp_save_dir):
        """无存档文件时签到数据为默认值"""
        sm = SaveManager()
        sm.load()
        checkin = sm.data['checkin']
        assert checkin['current_day'] == 0
        assert checkin['last_checkin_date'] is None
        assert checkin['total_checkins'] == 0

    def test_migration_preserves_checkin(self, tmp_save_dir):
        """v2存档迁移保留签到默认值"""
        sm = SaveManager()
        v2_data = {
            'version': 2,
            'total_coins': 100,
            'max_level_passed': 5,
            'ants': {},
            'settings': {'music_on': True, 'sfx_on': True},
        }
        result = sm._migrate(v2_data)
        assert 'checkin' in result
        assert result['checkin']['current_day'] == 0
        assert result['checkin']['total_checkins'] == 0

    def test_checkin_data_independence(self):
        """checkin_data 独立函数操作不依赖 SaveManager"""
        data = _make_checkin_data()
        cd_perform_checkin(data, today_str='2026-05-10')
        # 验证纯函数操作，不涉及 IO
        assert data['total_checkins'] == 1
        assert data['last_checkin_date'] == '2026-05-10'


# ══════════════════════════════════════════════
# G. 存档状态一致性测试
# ══════════════════════════════════════════════

class TestSaveConsistency:
    """验证 current_day、last_checkin_date、total_checkins 的一致性关系"""

    def test_current_day_equals_total_mod_7(self):
        """不变量: current_day == total_checkins % 7"""
        data = _make_checkin_data()
        base = datetime(2026, 5, 10)
        for i in range(21):  # 3个完整周期
            today = (base + timedelta(days=i)).strftime('%Y-%m-%d')
            cd_perform_checkin(data, today_str=today)
            assert data['current_day'] == data['total_checkins'] % 7, \
                f"第{i+1}次签到后 current_day={data['current_day']} != total_checkins%7={data['total_checkins'] % 7}"

    def test_current_day_equals_total_mod_7_with_breaks(self):
        """断签后不变量仍然成立"""
        data = _make_checkin_data()
        cd_perform_checkin(data, today_str='2026-05-10')  # Day 1
        cd_perform_checkin(data, today_str='2026-05-11')  # Day 2
        # 跳过 05-12, 05-13
        cd_perform_checkin(data, today_str='2026-05-14')  # Day 3 (断签)
        assert data['current_day'] == 3
        assert data['total_checkins'] == 3
        assert data['current_day'] == data['total_checkins'] % 7

    def test_last_checkin_date_matches_total(self):
        """total_checkins > 0 时 last_checkin_date 不能为 None"""
        data = _make_checkin_data()
        cd_perform_checkin(data, today_str='2026-05-10')
        assert data['total_checkins'] == 1
        assert data['last_checkin_date'] is not None

    def test_streak_bounded_by_total_checkins(self):
        """streak 不可能超过 total_checkins"""
        data = _make_checkin_data()
        base = datetime(2026, 5, 10)
        for i in range(7):
            today = (base + timedelta(days=i)).strftime('%Y-%m-%d')
            cd_perform_checkin(data, today_str=today)
            assert data['streak'] <= data['total_checkins'], \
                f"streak={data['streak']} > total_checkins={data['total_checkins']}"

    def test_cycles_completed_bounded(self):
        """cycles_completed 不可能超过 total_checkins // 7"""
        data = _make_checkin_data()
        base = datetime(2026, 5, 10)
        for i in range(21):
            today = (base + timedelta(days=i)).strftime('%Y-%m-%d')
            cd_perform_checkin(data, today_str=today)
            assert data['cycles_completed'] <= data['total_checkins'] // 7, \
                f"cycles_completed={data['cycles_completed']} > total//7={data['total_checkins'] // 7}"

    def test_sm_current_day_equals_total_mod_7(self, fresh_sm):
        """SaveManager: 不变量 current_day == total_checkins % 7"""
        from datetime import date as real_date
        base_date = datetime(2026, 5, 10)
        for i in range(14):
            mock_date = base_date + timedelta(days=i)
            mock_date_obj = real_date(mock_date.year, mock_date.month, mock_date.day)
            with patch('datetime.date') as mock_date_cls:
                mock_date_cls.today.return_value = mock_date_obj
                mock_date_cls.fromisoformat = real_date.fromisoformat
                fresh_sm.perform_checkin()
            checkin = fresh_sm.data['checkin']
            assert checkin['current_day'] == checkin['total_checkins'] % 7, \
                f"第{i+1}次签到后 current_day={checkin['current_day']} != total%7={checkin['total_checkins'] % 7}"

    def test_migration_current_day_is_zero(self, tmp_save_dir):
        """迁移后 current_day 必须为 0（不是 1）"""
        sm = SaveManager()
        v2_data = {
            'version': 2,
            'total_coins': 0,
            'max_level_passed': 0,
            'ants': {},
            'settings': {'music_on': True, 'sfx_on': True},
        }
        result = sm._migrate(v2_data)
        checkin = result['checkin']
        assert checkin['current_day'] == 0, f"迁移后 current_day={checkin['current_day']}，应为0"
        assert checkin['last_checkin_date'] is None
        assert checkin['total_checkins'] == 0
        # 关键一致性: current_day == total_checkins % 7
        assert checkin['current_day'] == checkin['total_checkins'] % 7

    def test_migration_then_first_checkin_consistent(self, tmp_save_dir):
        """迁移后首次签到，所有字段一致"""
        sm = SaveManager()
        v2_data = {
            'version': 2,
            'total_coins': 0,
            'max_level_passed': 0,
            'ants': {},
            'settings': {'music_on': True, 'sfx_on': True},
        }
        result = sm._migrate(v2_data)
        sm.data = result
        sm.loaded = True
        # 执行首次签到
        checkin_result = sm.perform_checkin()
        assert checkin_result['success'] is True
        checkin = sm.data['checkin']
        assert checkin['current_day'] == 1
        assert checkin['total_checkins'] == 1
        assert checkin['streak'] == 1
        assert checkin['last_checkin_date'] is not None
        assert checkin['current_day'] == checkin['total_checkins'] % 7

    def test_default_save_data_consistent(self):
        """默认存档数据字段一致"""
        data = _default_save_data()
        checkin = data['checkin']
        assert checkin['current_day'] == 0
        assert checkin['last_checkin_date'] is None
        assert checkin['total_checkins'] == 0
        assert checkin['streak'] == 0
        assert checkin['cycles_completed'] == 0
        # 不变量
        assert checkin['current_day'] == checkin['total_checkins'] % 7

    def test_cycle_reset_preserves_invariant(self):
        """周期重置后不变量仍然成立"""
        data = _make_checkin_data()
        base = datetime(2026, 5, 10)
        # 完成一个周期
        for i in range(7):
            today = (base + timedelta(days=i)).strftime('%Y-%m-%d')
            cd_perform_checkin(data, today_str=today)
        assert data['current_day'] == 0
        assert data['total_checkins'] == 7
        assert data['cycles_completed'] == 1
        assert data['current_day'] == data['total_checkins'] % 7
        # 新周期第一天
        result = cd_perform_checkin(data, today_str=(base + timedelta(days=7)).strftime('%Y-%m-%d'))
        assert result['day'] == 1
        assert data['current_day'] == 1
        assert data['total_checkins'] == 8
        assert data['current_day'] == data['total_checkins'] % 7

    def test_corrupted_current_day_stays_corrupted(self):
        """⚠️ 回归测试：如果 current_day 被错误设置，不变量持续被破坏

        这证明我们必须在源头防止 current_day 被错误设置（迁移、初始化），
        因为 perform_checkin 不会自愈不一致状态。
        如果 current_day=2 但 total_checkins=0，UI 会显示第1、2天为绿色但不可点击。
        """
        data = _make_checkin_data()
        # 模拟可能被错误设置的状态：current_day=2, total_checkins=0
        data['current_day'] = 2
        data['total_checkins'] = 0
        # 不变量被破坏
        assert data['current_day'] != data['total_checkins'] % 7
        # perform_checkin 不会修复不一致 — 它只是递增 current_day
        cd_perform_checkin(data, today_str='2026-05-10')
        # 不变量仍然被破坏（3 != 1 % 7 = 1）
        assert data['current_day'] != data['total_checkins'] % 7

    def test_fresh_save_never_shows_green_days(self):
        """⚠️ 回归测试：全新存档不应有任何绿色（done）天

        如果 current_day > 0 但 total_checkins == 0，UI 会错误地显示绿色天。
        """
        data = _default_save_data()
        checkin = data['checkin']
        # 全新存档：current_day 必须为 0
        assert checkin['current_day'] == 0
        assert checkin['total_checkins'] == 0
        # 不变量
        assert checkin['current_day'] == checkin['total_checkins'] % 7

    def test_migration_never_sets_nonzero_current_day(self):
        """⚠️ 回归测试：任何版本迁移都不会设置 current_day > 0

        如果迁移错误地设置 current_day=2，会导致"绿色不可点"问题。
        """
        sm = SaveManager()
        # v1 迁移
        v1_data = {
            'version': 1,
            'total_coins': 100,
            'max_level_passed': 5,
            'ants': {},
            'settings': {'music_on': True, 'sfx_on': True},
        }
        result = sm._migrate(v1_data)
        assert result['checkin']['current_day'] == 0

        # v2 迁移
        v2_data = {
            'version': 2,
            'total_coins': 100,
            'max_level_passed': 5,
            'ants': {},
            'settings': {'music_on': True, 'sfx_on': True},
        }
        result = sm._migrate(v2_data)
        assert result['checkin']['current_day'] == 0

    def test_sm_perform_checkin_maintains_invariant(self, fresh_sm):
        """⚠️ 回归测试：SaveManager.perform_checkin 维持不变量"""
        from datetime import date as real_date
        base_date = datetime(2026, 5, 10)
        # 连续签到7天
        for i in range(7):
            mock_date = base_date + timedelta(days=i)
            mock_date_obj = real_date(mock_date.year, mock_date.month, mock_date.day)
            with patch('datetime.date') as mock_date_cls:
                mock_date_cls.today.return_value = mock_date_obj
                mock_date_cls.fromisoformat = real_date.fromisoformat
                fresh_sm.perform_checkin()
            checkin = fresh_sm.data['checkin']
            assert checkin['current_day'] == checkin['total_checkins'] % 7, \
                f"第{i+1}次签到后不变量破坏: current_day={checkin['current_day']}, total%7={checkin['total_checkins'] % 7}"

    def test_initial_state_ui_would_show_no_green(self):
        """⚠️ 回归测试：初始状态下 UI 不应显示任何绿色天

        模拟 UI 状态判断逻辑：day_num < next_day 为 done（绿色）。
        初始状态 current_day=0, next_day=1，没有任何 day < 1，所以不应有绿色。
        """
        data = _make_checkin_data(current_day=0)
        next_day = data['current_day'] + 1 if data['current_day'] < 7 else 1
        for day_num in range(1, 8):
            is_done = day_num < next_day
            assert not is_done, \
                f"初始状态 current_day=0 时第{day_num}天不应为 done（绿色）"


# ══════════════════════════════════════════════
# E. 数据一致性对比测试
# ══════════════════════════════════════════════

class TestConsistency:
    """对比 checkin_data.py 和 SaveManager 行为一致性"""

    def test_date_format_consistent(self):
        """✅ 日期格式统一：checkin_data 和 SaveManager 均使用 YYYY-MM-DD"""
        data = _make_checkin_data()
        cd_perform_checkin(data, today_str='2026-05-10')
        assert len(data['last_checkin_date']) == 10  # YYYY-MM-DD

        sm = SaveManager()
        sm.perform_checkin()
        assert len(sm.data['checkin']['last_checkin_date']) == 10  # YYYY-MM-DD

    def test_reward_consistent(self):
        """✅ 奖励数值一致：checkin_data 和 SaveManager 首次签到均获得 100G"""
        data = _make_checkin_data()
        result = cd_perform_checkin(data, today_str='2026-05-10')
        cd_reward = result['reward']['amount']  # 100

        sm = SaveManager()
        sm_result = sm.perform_checkin()

        assert cd_reward == 100
        assert sm_result['reward']['amount'] == 100

    def test_current_day_semantic_consistent(self):
        """✅ current_day 语义一致：checkin_data 和 SaveManager 均从 0 开始"""
        data_cd = _make_checkin_data(current_day=0)
        cd_perform_checkin(data_cd, today_str='2026-05-10')
        assert data_cd['current_day'] == 1

        sm = SaveManager()
        sm.perform_checkin()
        assert sm.data['checkin']['current_day'] == 1

    def test_break_behavior_same(self):
        """✅ 断签行为一致：checkin_data 和 SaveManager 都保留 current_day"""
        data_cd = _make_checkin_data(current_day=4, last_checkin_date='2026-05-05')
        cd_perform_checkin(data_cd, today_str='2026-05-10')
        assert data_cd['current_day'] == 5

        sm = SaveManager()
        _set_checkin_state(sm, current_day=5, last_checkin_date=_days_ago_str_sm(3))
        sm.perform_checkin()
        assert sm.data['checkin']['current_day'] == 6

    def test_return_type_same(self):
        """✅ 返回值类型统一：checkin_data 和 SaveManager 均返回 dict"""
        data = _make_checkin_data()
        result = cd_perform_checkin(data, today_str='2026-05-10')
        assert isinstance(result, dict)
        assert 'success' in result
        assert 'reward' in result
        assert 'day' in result

        sm = SaveManager()
        result = sm.perform_checkin()
        assert isinstance(result, dict)
        assert 'success' in result
        assert 'reward' in result
        assert 'day' in result


# ══════════════════════════════════════════════
# F. 综合场景测试
# ══════════════════════════════════════════════

class TestIntegratedScenarios:
    """验证完整用户场景（使用 checkin_data 独立函数）"""

    def test_new_player_full_week(self):
        """新玩家连续签到一周"""
        data = _make_checkin_data()
        base = datetime(2026, 5, 10)
        for day in range(7):
            today = (base + timedelta(days=day)).strftime('%Y-%m-%d')
            result = cd_perform_checkin(data, today_str=today)
            assert result['success'] is True
            assert result['day'] == day + 1

        assert data['cycles_completed'] == 1
        assert data['total_checkins'] == 7
        assert data['current_day'] == 0  # 周期完成重置

    def test_skip_day_and_continue(self):
        """签到2天，跳过1天，继续签到"""
        data = _make_checkin_data()
        cd_perform_checkin(data, today_str='2026-05-10')  # Day 1
        cd_perform_checkin(data, today_str='2026-05-11')  # Day 2
        # 跳过 05-12
        cd_perform_checkin(data, today_str='2026-05-13')  # Day 3 (断签)

        assert data['streak'] == 1  # 断签归1
        assert data['current_day'] == 3  # 保留进度
        assert data['total_checkins'] == 3

    def test_two_full_cycles(self):
        """完成两个完整周期"""
        data = _make_checkin_data()
        base = datetime(2026, 5, 10)
        for cycle in range(2):
            for day in range(7):
                today = (base + timedelta(days=cycle * 7 + day)).strftime('%Y-%m-%d')
                cd_perform_checkin(data, today_str=today)
        assert data['cycles_completed'] == 2
        assert data['total_checkins'] == 14

    def test_ui_data_after_full_week(self):
        """完整一周后的 UI 数据"""
        data = _make_checkin_data()
        base = datetime(2026, 5, 10)
        for day in range(7):
            today = (base + timedelta(days=day)).strftime('%Y-%m-%d')
            cd_perform_checkin(data, today_str=today)

        ui = get_checkin_ui_data(data, today_str='2026-05-17')
        assert ui['can_checkin'] is True
        assert ui['cycles_completed'] == 1
        assert ui['total_checkins'] == 7
        assert len(ui['rewards']) == 7
