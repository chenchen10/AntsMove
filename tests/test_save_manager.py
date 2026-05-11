"""save_manager.py 单元测试 — 存档迁移(v1→v5) + 星级记录 + 成就系统接口"""

import json
import os
import sys
import tempfile
import shutil
import pytest

# 确保项目根目录在 path 中
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import save_manager
from save_manager import SaveManager, SAVE_VERSION, _default_save_data


@pytest.fixture
def fresh_sm():
    """创建全新 SaveManager（无存档文件）"""
    sm = SaveManager()
    sm.loaded = True
    return sm


@pytest.fixture
def tmp_save_dir(tmp_path, monkeypatch):
    """临时存档目录，避免污染真实存档"""
    monkeypatch.setattr(save_manager, 'SAVE_DIR', str(tmp_path))
    monkeypatch.setattr(save_manager, 'SAVE_FILE', os.path.join(str(tmp_path), 'save_data.json'))
    return tmp_path


# ══════════════════════════════════════════════
# 1. 默认数据结构测试
# ══════════════════════════════════════════════

class TestDefaultSaveData:
    def test_version_is_5(self):
        data = _default_save_data()
        assert data['version'] == 5

    def test_has_levels_field(self):
        data = _default_save_data()
        assert 'levels' in data
        assert isinstance(data['levels'], dict)

    def test_has_daily_tasks_field(self):
        data = _default_save_data()
        assert 'daily_tasks' in data
        assert data['daily_tasks'] == {'date': '', 'tasks': []}

    def test_has_weekly_tasks_field(self):
        data = _default_save_data()
        assert 'weekly_tasks' in data
        assert data['weekly_tasks'] == {'week': '', 'tasks': []}

    def test_has_achievements_field(self):
        data = _default_save_data()
        assert 'achievements' in data
        assert isinstance(data['achievements'], dict)
        # v5: 每个成就ID都有初始条目
        from achievements_data import ACHIEVEMENTS
        assert len(data['achievements']) == len(ACHIEVEMENTS)
        for ach in ACHIEVEMENTS:
            entry = data['achievements'][ach['id']]
            assert entry == {'progress': 0, 'claimed': False}

    def test_has_checkin_field(self):
        data = _default_save_data()
        assert 'checkin' in data
        checkin = data['checkin']
        assert checkin['current_day'] == 0
        assert checkin['last_checkin_date'] is None
        assert checkin['total_checkins'] == 0
        assert checkin['streak'] == 0
        assert checkin['cycles_completed'] == 0

    def test_has_existing_fields(self):
        data = _default_save_data()
        assert 'total_coins' in data
        assert 'max_level_passed' in data
        assert 'ants' in data
        assert 'settings' in data


# ══════════════════════════════════════════════
# 2. v2→v3 迁移测试
# ══════════════════════════════════════════════

class TestMigrationV2ToV3:
    def _make_v2_save(self, max_level_passed=0, ants=None, total_coins=0):
        """构造一个v2格式的存档数据"""
        return {
            'version': 2,
            'total_coins': total_coins,
            'max_level_passed': max_level_passed,
            'ants': ants or {},
            'settings': {'music_on': True, 'sfx_on': True},
        }

    def test_migration_adds_new_fields(self):
        sm = SaveManager()
        v2_data = self._make_v2_save()
        result = sm._migrate(v2_data)
        assert 'levels' in result
        assert 'daily_tasks' in result
        assert 'weekly_tasks' in result
        assert 'achievements' in result
        assert 'checkin' in result

    def test_migration_version_set_to_5(self):
        sm = SaveManager()
        v2_data = self._make_v2_save()
        result = sm._migrate(v2_data)
        assert result['version'] == 5

    def test_migration_preserves_existing_data(self):
        sm = SaveManager()
        v2_data = self._make_v2_save(total_coins=5000, max_level_passed=10)
        v2_data['ants'] = {'1': {'count': 3, 'carry': 20, 'speed': 10, 'defense': 5}}
        result = sm._migrate(v2_data)
        assert result['total_coins'] == 5000
        assert result['max_level_passed'] == 10
        assert result['ants'] == {'1': {'count': 3, 'carry': 20, 'speed': 10, 'defense': 5}}

    def test_migration_backfills_passed_levels(self):
        sm = SaveManager()
        v2_data = self._make_v2_save(max_level_passed=5)
        result = sm._migrate(v2_data)
        # 应回填第1-5关
        for lv in range(1, 6):
            key = str(lv)
            assert key in result['levels']
            assert result['levels'][key]['best_stars'] == 1
            assert result['levels'][key]['times_won'] == 1
            assert result['levels'][key]['best_coins'] > 0

    def test_migration_does_not_overwrite_existing_levels(self):
        """如果v2存档中已有levels字段（理论上不会），不覆盖"""
        sm = SaveManager()
        v2_data = self._make_v2_save(max_level_passed=3)
        v2_data['levels'] = {
            '1': {'best_stars': 3, 'best_coins': 500, 'best_time_left': 45, 'times_played': 5, 'times_won': 3}
        }
        result = sm._migrate(v2_data)
        # 第1关应保留原有3星数据
        assert result['levels']['1']['best_stars'] == 3
        assert result['levels']['1']['times_won'] == 3

    def test_migration_no_passed_levels(self):
        sm = SaveManager()
        v2_data = self._make_v2_save(max_level_passed=0)
        result = sm._migrate(v2_data)
        assert result['levels'] == {}

    def test_migration_v1_to_v5(self):
        """v1存档直接迁移到v5"""
        sm = SaveManager()
        v1_data = {
            'version': 1,
            'total_coins': 100,
            'max_level_passed': 2,
            'ants': {'1': {'level': 5, 'owned': True}},
            'settings': {'music_on': True, 'sfx_on': True},
        }
        result = sm._migrate(v1_data)
        assert result['version'] == 5
        # v1蚂蚁迁移为v2格式
        assert result['ants']['1']['carry'] == 5
        assert result['ants']['1']['count'] == 1
        # v3字段应存在
        assert 'levels' in result
        assert 'checkin' in result
        # v5成就字段应完整
        from achievements_data import ACHIEVEMENTS
        assert len(result['achievements']) == len(ACHIEVEMENTS)
        for ach in ACHIEVEMENTS:
            entry = result['achievements'][ach['id']]
            assert 'progress' in entry
            assert 'claimed' in entry

    def test_migration_checkin_defaults(self):
        sm = SaveManager()
        v2_data = self._make_v2_save()
        result = sm._migrate(v2_data)
        checkin = result['checkin']
        assert checkin['current_day'] == 0
        assert checkin['last_checkin_date'] is None
        assert checkin['total_checkins'] == 0

    def test_load_creates_default_when_no_file(self, tmp_save_dir):
        """无存档文件时，load创建默认数据"""
        sm = SaveManager()
        data = sm.load()
        assert data['version'] == SAVE_VERSION
        assert data['levels'] == {}
        assert sm.loaded is True

    def test_load_and_save_roundtrip(self, tmp_save_dir):
        """保存后重新加载，数据一致"""
        sm = SaveManager()
        sm.data['total_coins'] = 12345
        sm.data['max_level_passed'] = 42
        sm.save()

        sm2 = SaveManager()
        data = sm2.load()
        assert data['total_coins'] == 12345
        assert data['max_level_passed'] == 42

    def test_load_corrupted_file_falls_back_to_default(self, tmp_save_dir):
        """损坏的JSON文件回退到默认数据"""
        save_path = os.path.join(str(tmp_save_dir), 'save_data.json')
        with open(save_path, 'w') as f:
            f.write('this is not valid json {{{')

        sm = SaveManager()
        data = sm.load()
        assert data['version'] == SAVE_VERSION
        assert data['total_coins'] == 0


# ══════════════════════════════════════════════
# 3. 关卡星级记录测试
# ══════════════════════════════════════════════

class TestLevelRecord:
    def test_update_level_record_first_win(self, fresh_sm):
        sm = fresh_sm
        sm.update_level_record(1, stars=2, coins=500, time_left=30.0)
        record = sm.get_level_record(1)
        assert record['best_stars'] == 2
        assert record['best_coins'] == 500
        assert record['best_time_left'] == 30.0
        assert record['times_played'] == 1
        assert record['times_won'] == 1

    def test_update_level_record_star_only_goes_up(self, fresh_sm):
        sm = fresh_sm
        sm.update_level_record(1, stars=2, coins=500, time_left=30.0)
        # 第二次1星，不应覆盖2星
        sm.update_level_record(1, stars=1, coins=400, time_left=20.0)
        record = sm.get_level_record(1)
        assert record['best_stars'] == 2
        assert record['best_coins'] == 500
        assert record['best_time_left'] == 30.0

    def test_update_level_record_star_upgrade(self, fresh_sm):
        sm = fresh_sm
        sm.update_level_record(1, stars=1, coins=300, time_left=10.0)
        sm.update_level_record(1, stars=3, coins=600, time_left=45.0)
        record = sm.get_level_record(1)
        assert record['best_stars'] == 3
        assert record['best_coins'] == 600
        assert record['best_time_left'] == 45.0

    def test_update_level_record_failure(self, fresh_sm):
        sm = fresh_sm
        sm.update_level_record(1, stars=0, coins=0, time_left=0)
        record = sm.get_level_record(1)
        assert record['best_stars'] == 0
        assert record['times_played'] == 1
        assert record['times_won'] == 0

    def test_update_level_record_multiple_plays(self, fresh_sm):
        sm = fresh_sm
        sm.update_level_record(1, stars=1, coins=300, time_left=10.0)
        sm.update_level_record(1, stars=0, coins=0, time_left=0)
        sm.update_level_record(1, stars=2, coins=500, time_left=30.0)
        record = sm.get_level_record(1)
        assert record['times_played'] == 3
        assert record['times_won'] == 2
        assert record['best_stars'] == 2

    def test_get_level_stars_no_record(self, fresh_sm):
        sm = fresh_sm
        assert sm.get_level_stars(99) == 0

    def test_get_level_stars_with_record(self, fresh_sm):
        sm = fresh_sm
        sm.update_level_record(5, stars=3, coins=800, time_left=50.0)
        assert sm.get_level_stars(5) == 3

    def test_get_total_stars(self, fresh_sm):
        sm = fresh_sm
        sm.update_level_record(1, stars=1, coins=300, time_left=10)
        sm.update_level_record(2, stars=3, coins=600, time_left=40)
        sm.update_level_record(3, stars=2, coins=500, time_left=25)
        assert sm.get_total_stars() == 6

    def test_get_total_stars_empty(self, fresh_sm):
        sm = fresh_sm
        assert sm.get_total_stars() == 0

    def test_get_total_levels_won(self, fresh_sm):
        sm = fresh_sm
        sm.update_level_record(1, stars=1, coins=300, time_left=10)
        sm.update_level_record(2, stars=0, coins=0, time_left=0)
        sm.update_level_record(3, stars=2, coins=500, time_left=25)
        assert sm.get_total_levels_won() == 2

    def test_get_total_levels_won_empty(self, fresh_sm):
        sm = fresh_sm
        assert sm.get_total_levels_won() == 0


# ══════════════════════════════════════════════
# 4. 边界条件测试
# ══════════════════════════════════════════════

class TestEdgeCases:
    def test_update_level_record_all_200_levels(self, fresh_sm):
        """测试200关全部记录"""
        sm = fresh_sm
        for lv in range(1, 201):
            sm.update_level_record(lv, stars=1, coins=100, time_left=5)
        assert sm.get_total_stars() == 200
        assert sm.get_total_levels_won() == 200

    def test_update_level_record_level_0(self, fresh_sm):
        """关卡号0不应崩溃"""
        sm = fresh_sm
        sm.update_level_record(0, stars=1, coins=100, time_left=5)
        record = sm.get_level_record(0)
        assert record['best_stars'] == 1

    def test_update_level_record_negative_coins(self, fresh_sm):
        """负数金币不会覆盖默认的0值（coins > best_coins 判断拒绝负数）"""
        sm = fresh_sm
        sm.update_level_record(1, stars=1, coins=-100, time_left=5)
        record = sm.get_level_record(1)
        assert record['best_coins'] == 0  # -100 > 0 为False，不更新

    def test_update_level_record_zero_time(self, fresh_sm):
        """剩余时间为0"""
        sm = fresh_sm
        sm.update_level_record(1, stars=1, coins=100, time_left=0)
        record = sm.get_level_record(1)
        assert record['best_time_left'] == 0

    def test_coins_tie_does_not_upgrade(self, fresh_sm):
        """金币相同时不应覆盖"""
        sm = fresh_sm
        sm.update_level_record(1, stars=2, coins=500, time_left=30)
        sm.update_level_record(1, stars=2, coins=500, time_left=30)
        record = sm.get_level_record(1)
        assert record['times_played'] == 2
        assert record['best_coins'] == 500


# ══════════════════════════════════════════════
# 5. v4→v5 迁移测试
# ══════════════════════════════════════════════

class TestMigrationV4ToV5:
    def _make_v4_save(self, achievements=None, **kwargs):
        """构造v4格式存档数据"""
        data = {
            'version': 4,
            'total_coins': kwargs.get('total_coins', 0),
            'max_level_passed': kwargs.get('max_level_passed', 0),
            'ants': kwargs.get('ants', {}),
            'settings': {'music_on': True, 'sfx_on': True},
            'levels': {},
            'daily_tasks': {'date': '', 'tasks': []},
            'weekly_tasks': {'week': '', 'tasks': []},
            'achievements': achievements or {},
            'checkin': {
                'current_day': 1,
                'last_checkin_date': None,
                'total_checkins': 0,
                'streak': 0,
                'cycles_completed': 0,
            },
        }
        return data

    def test_migration_empty_achievements(self):
        """v4空成就 → v5补全所有成就ID"""
        sm = SaveManager()
        v4_data = self._make_v4_save()
        result = sm._migrate(v4_data)
        assert result['version'] == 5
        from achievements_data import ACHIEVEMENTS
        assert len(result['achievements']) == len(ACHIEVEMENTS)
        for ach in ACHIEVEMENTS:
            entry = result['achievements'][ach['id']]
            assert entry == {'progress': 0, 'claimed': False}

    def test_migration_old_current_field_renamed(self):
        """v4旧'current'字段 → v5重命名为'progress'"""
        sm = SaveManager()
        v4_data = self._make_v4_save(achievements={
            'C1': {'current': 3, 'claimed': False},
            'H2': {'current': 50, 'claimed': True},
        })
        result = sm._migrate(v4_data)
        # C1: current=3 → progress=3
        assert result['achievements']['C1']['progress'] == 3
        assert result['achievements']['C1']['claimed'] is False
        # H2: current=50, claimed=True
        assert result['achievements']['H2']['progress'] == 50
        assert result['achievements']['H2']['claimed'] is True

    def test_migration_preserves_progress_field(self):
        """v4已有'progress'字段 → v5保留"""
        sm = SaveManager()
        v4_data = self._make_v4_save(achievements={
            'C1': {'progress': 5, 'claimed': True},
        })
        result = sm._migrate(v4_data)
        assert result['achievements']['C1']['progress'] == 5
        assert result['achievements']['C1']['claimed'] is True

    def test_migration_all_achievements_present(self):
        """v5迁移后所有成就ID都存在"""
        sm = SaveManager()
        v4_data = self._make_v4_save(achievements={'C1': {'current': 1, 'claimed': True}})
        result = sm._migrate(v4_data)
        from achievements_data import ACHIEVEMENTS
        for ach in ACHIEVEMENTS:
            assert ach['id'] in result['achievements']


# ══════════════════════════════════════════════
# 6. 成就系统便捷接口测试
# ══════════════════════════════════════════════

class TestAchievementInterfaces:
    def test_get_achievements(self, fresh_sm):
        sm = fresh_sm
        achs = sm.get_achievements()
        from achievements_data import ACHIEVEMENTS
        assert len(achs) == len(ACHIEVEMENTS)

    def test_get_achievement_single(self, fresh_sm):
        sm = fresh_sm
        entry = sm.get_achievement('C1')
        assert entry == {'progress': 0, 'claimed': False}

    def test_get_achievement_nonexistent(self, fresh_sm):
        sm = fresh_sm
        entry = sm.get_achievement('NONEXISTENT')
        assert entry == {'progress': 0, 'claimed': False}

    def test_get_achievement_progress(self, fresh_sm):
        sm = fresh_sm
        assert sm.get_achievement_progress('C1') == 0

    def test_is_achievement_claimed(self, fresh_sm):
        sm = fresh_sm
        assert sm.is_achievement_claimed('C1') is False

    def test_update_achievement_progress(self, fresh_sm):
        sm = fresh_sm
        changed = sm.update_achievement_progress('C1', 5)
        assert changed is True
        assert sm.get_achievement_progress('C1') == 5

    def test_update_achievement_progress_no_downgrade(self, fresh_sm):
        """进度只升不降"""
        sm = fresh_sm
        sm.update_achievement_progress('C1', 10)
        changed = sm.update_achievement_progress('C1', 5)
        assert changed is False
        assert sm.get_achievement_progress('C1') == 10

    def test_claim_achievement_reward_success(self, fresh_sm):
        """领取成就奖励"""
        sm = fresh_sm
        # 设置进度满足条件
        sm.update_achievement_progress('C1', 1)  # C1 需要 1
        success, reward = sm.claim_achievement_reward('C1')
        assert success is True
        from achievements_data import ACHIEVEMENT_BY_ID
        assert reward == ACHIEVEMENT_BY_ID['C1']['rewards']['coins']
        assert sm.is_achievement_claimed('C1') is True

    def test_claim_achievement_reward_insufficient_progress(self, fresh_sm):
        """进度不足时拒绝领取"""
        sm = fresh_sm
        success, reward = sm.claim_achievement_reward('C1')
        assert success is False
        assert reward == 0

    def test_claim_achievement_reward_duplicate(self, fresh_sm):
        """重复领取拒绝"""
        sm = fresh_sm
        sm.update_achievement_progress('C1', 1)
        sm.claim_achievement_reward('C1')
        success, reward = sm.claim_achievement_reward('C1')
        assert success is False
        assert reward == 0

    def test_claim_achievement_reward_nonexistent(self, fresh_sm):
        """不存在的成就ID"""
        sm = fresh_sm
        success, reward = sm.claim_achievement_reward('NONEXISTENT')
        assert success is False
        assert reward == 0

    def test_claim_achievement_reward_adds_coins(self, fresh_sm):
        """领取奖励后金币增加"""
        sm = fresh_sm
        sm.update_achievement_progress('C1', 1)
        initial_coins = sm.get_total_coins()
        sm.claim_achievement_reward('C1')
        from achievements_data import ACHIEVEMENT_BY_ID
        expected = initial_coins + ACHIEVEMENT_BY_ID['C1']['rewards']['coins']
        assert sm.get_total_coins() == expected

    def test_save_and_load_achievements_roundtrip(self, tmp_save_dir):
        """成就数据保存后重新加载一致"""
        sm = SaveManager()
        sm.update_achievement_progress('C1', 5)
        sm.claim_achievement_reward('C1')
        sm.save()

        sm2 = SaveManager()
        sm2.load()
        assert sm2.get_achievement_progress('C1') == 5
        assert sm2.is_achievement_claimed('C1') is True
