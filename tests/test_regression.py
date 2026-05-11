"""回归测试：验证 BUG-1 和 BUG-2 修复"""

import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import save_manager
from save_manager import SaveManager, SAVE_VERSION
from levels_data import get_star3_time_threshold, calc_stars


# ══════════════════════════════════════════════
# BUG-1 回归：星级条件显示使用分阶段阈值
# ══════════════════════════════════════════════

class TestBUG1StarConditionDisplay:
    """验证 level_complete.py 中星级条件判断使用 get_star3_time_threshold 而非固定 0.30"""

    def test_stage1_threshold_display_uses_50_percent(self):
        """第1关应使用50%阈值，而非固定30%"""
        threshold = get_star3_time_threshold(1)
        assert threshold == 0.50, f"Stage 1 阈值应为 0.50，实际为 {threshold}"

    def test_stage2_threshold_display_uses_40_percent(self):
        """第60关应使用40%阈值"""
        threshold = get_star3_time_threshold(60)
        assert threshold == 0.40

    def test_stage3_threshold_display_uses_35_percent(self):
        """第120关应使用35%阈值"""
        threshold = get_star3_time_threshold(120)
        assert threshold == 0.35

    def test_stage4_threshold_display_uses_30_percent(self):
        """第180关应使用30%阈值"""
        threshold = get_star3_time_threshold(180)
        assert threshold == 0.30

    def test_early_level_30_percent_not_3_star(self):
        """BUG核心：第1关30%剩余时间不应获得3星（旧bug会显示30%但实际需要50%）"""
        result = calc_stars(1, level_coins=100, target_coins=100,
                           remaining_time=27, total_time=90, collection_rate=0.85)
        # 30% = 27/90，Stage 1需要50%才能3星，所以应该是2星
        assert result == 2, f"第1关30%剩余应为2星，实际为{result}星"

    def test_early_level_50_percent_is_3_star(self):
        """第1关50%剩余应获得3星"""
        result = calc_stars(1, level_coins=100, target_coins=100,
                           remaining_time=45, total_time=90, collection_rate=0.85)
        assert result == 3

    def test_import_in_level_complete(self):
        """验证 level_complete.py 导入了 get_star3_time_threshold"""
        import importlib
        spec = importlib.util.find_spec('scenes.level_complete')
        assert spec is not None
        # 读取源码确认导入
        source_path = os.path.join(os.path.dirname(__file__), '..', 'scenes', 'level_complete.py')
        with open(source_path) as f:
            source = f.read()
        assert 'get_star3_time_threshold' in source, "level_complete.py 应导入 get_star3_time_threshold"

    def test_no_fixed_030_in_star_conditions(self):
        """验证 level_complete.py 中不再使用固定的 0.30 阈值"""
        source_path = os.path.join(os.path.dirname(__file__), '..', 'scenes', 'level_complete.py')
        with open(source_path) as f:
            source = f.read()
        # 检查 _draw_star_conditions 方法中没有硬编码 0.30
        # （允许注释和文档字符串中出现）
        lines = source.split('\n')
        in_method = False
        for line in lines:
            if 'def _draw_star_conditions' in line:
                in_method = True
            elif in_method and line.strip().startswith('def '):
                break
            elif in_method and '0.30' in line and not line.strip().startswith('#'):
                assert False, f"发现硬编码的 0.30: {line.strip()}"


# ══════════════════════════════════════════════
# BUG-2 回归：ensure_starter_ant 防止软锁定
# ══════════════════════════════════════════════

@pytest.fixture
def tmp_save_dir(tmp_path, monkeypatch):
    """临时存档目录"""
    monkeypatch.setattr(save_manager, 'SAVE_DIR', str(tmp_path))
    monkeypatch.setattr(save_manager, 'SAVE_FILE', os.path.join(str(tmp_path), 'save_data.json'))
    return tmp_path


class TestBUG2EnsureStarterAnt:
    """验证 ensure_starter_ant 防止蚂蚁数据为空时的软锁定"""

    def test_empty_ants_gets_starter(self):
        """蚂蚁字典为空时，应自动给予 ant_id=1"""
        sm = SaveManager()
        sm.loaded = True
        sm.data['ants'] = {}
        sm.ensure_starter_ant()
        assert '1' in sm.data['ants']
        assert sm.data['ants']['1']['count'] == 1
        assert sm.data['ants']['1']['carry'] == 0
        assert sm.data['ants']['1']['speed'] == 0
        assert sm.data['ants']['1']['defense'] == 0

    def test_existing_ants_not_overwritten(self):
        """已有蚂蚁时，不应覆盖"""
        sm = SaveManager()
        sm.loaded = True
        sm.data['ants'] = {'3': {'count': 2, 'carry': 10, 'speed': 5, 'defense': 3}}
        sm.ensure_starter_ant()
        assert '3' in sm.data['ants']
        assert sm.data['ants']['3']['count'] == 2
        # 不应添加 ant_id=1
        assert '1' not in sm.data['ants']

    def test_zero_count_ants_gets_starter(self):
        """蚂蚁count全为0时，应给予初始蚂蚁"""
        sm = SaveManager()
        sm.loaded = True
        sm.data['ants'] = {'1': {'count': 0, 'carry': 0, 'speed': 0, 'defense': 0}}
        sm.ensure_starter_ant()
        assert sm.data['ants']['1']['count'] == 1

    def test_starter_ant_id_is_string_1(self):
        """初始蚂蚁的key应为字符串'1'"""
        sm = SaveManager()
        sm.loaded = True
        sm.data['ants'] = {}
        sm.ensure_starter_ant()
        assert '1' in sm.data['ants']
        assert isinstance(list(sm.data['ants'].keys())[0], str)

    def test_starter_ant_has_required_fields(self):
        """初始蚂蚁应包含所有必要字段"""
        sm = SaveManager()
        sm.loaded = True
        sm.data['ants'] = {}
        sm.ensure_starter_ant()
        ant = sm.data['ants']['1']
        assert 'count' in ant
        assert 'carry' in ant
        assert 'speed' in ant
        assert 'defense' in ant

    def test_ensure_starter_ant_saves(self, tmp_save_dir):
        """ensure_starter_ant 应持久化保存"""
        sm = SaveManager()
        sm.loaded = True
        sm.data['ants'] = {}
        sm.ensure_starter_ant()
        # 重新加载验证
        sm2 = SaveManager()
        sm2.load()
        assert '1' in sm2.data['ants']
        assert sm2.data['ants']['1']['count'] == 1

    def test_reset_then_ensure_starter(self, tmp_save_dir):
        """重置存档后调用 ensure_starter_ant 应给予初始蚂蚁"""
        sm = SaveManager()
        sm.loaded = True
        sm.reset()
        sm.ensure_starter_ant()
        assert '1' in sm.data['ants']
        assert sm.data['ants']['1']['count'] == 1

    def test_get_owned_count_empty(self):
        """空蚂蚁字典的 owned_count 应为 0"""
        sm = SaveManager()
        sm.loaded = True
        sm.data['ants'] = {}
        assert sm.get_owned_count() == 0

    def test_get_owned_count_with_ants(self):
        """有蚂蚁时 owned_count 应正确计算"""
        sm = SaveManager()
        sm.loaded = True
        sm.data['ants'] = {
            '1': {'count': 3, 'carry': 0, 'speed': 0, 'defense': 0},
            '2': {'count': 2, 'carry': 0, 'speed': 0, 'defense': 0},
        }
        assert sm.get_owned_count() == 5

    def test_multiple_ensure_calls_idempotent(self):
        """多次调用 ensure_starter_ant 不会产生重复"""
        sm = SaveManager()
        sm.loaded = True
        sm.data['ants'] = {}
        sm.ensure_starter_ant()
        sm.ensure_starter_ant()
        assert sm.get_owned_count() == 1
        assert sm.data['ants']['1']['count'] == 1

    def test_import_in_main(self):
        """验证 main.py 调用了 ensure_starter_ant"""
        source_path = os.path.join(os.path.dirname(__file__), '..', 'main.py')
        with open(source_path) as f:
            source = f.read()
        assert 'ensure_starter_ant' in source, "main.py 应调用 ensure_starter_ant"

    def test_import_in_debug(self):
        """验证 debug.py 在重置后调用了 ensure_starter_ant"""
        source_path = os.path.join(os.path.dirname(__file__), '..', 'scenes', 'debug.py')
        with open(source_path) as f:
            source = f.read()
        assert 'ensure_starter_ant' in source, "debug.py 应调用 ensure_starter_ant"

    def test_method_exists_in_save_manager(self):
        """验证 SaveManager 类有 ensure_starter_ant 方法"""
        assert hasattr(SaveManager, 'ensure_starter_ant'), \
            "SaveManager 应有 ensure_starter_ant 方法"
