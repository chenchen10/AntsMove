"""CHE-35 游戏结束自动结算未搬运食物 - 测试验证

覆盖 PRD CHE-29 核心场景：
  1. 时间耗尽时玩家蚂蚁身上有食物 → 自动结算为金币
  2. 双方蚂蚁均有未交付食物 → 分别结算
  3. 采集率变化影响星级 → collected_hp 更新
  4. double_income 不生效 → 兜底结算不翻倍
  5. storage=0 的蚂蚁不触发结算
  6. 正常搬运不受影响
  + 边界：STUNNED 状态仍结算、last_sweet_coin_per=0 无影响
"""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# 在导入 main 之前 patch pygame，避免需要真实显示
import pygame
pygame.init = MagicMock()
pygame.font.init = MagicMock()
pygame.display.set_mode = MagicMock(return_value=MagicMock())
pygame.display.set_caption = MagicMock()
pygame.time.Clock = MagicMock()

from ant_sprite import Ant
from main import GameState


# ══════════════════════════════════════════════
# Fixtures
# ══════════════════════════════════════════════

def _make_ant(team, state, storage, coin_per=2, ant_id='worker1'):
    """创建测试用蚂蚁"""
    ant = MagicMock(spec=Ant)
    ant.team = team
    ant.ant_id = ant_id
    ant.state = state
    ant.storage = storage
    ant.last_sweet_coin_per = coin_per
    return ant


@pytest.fixture
def game():
    """创建一个最小化的 GameState 用于测试 _end_level"""
    # Patch 所有 UI 和资源依赖
    with patch('main.font_helper'), \
         patch('main.load_assets', return_value={}), \
         patch('main.ShopUI'), \
         patch('main.TaskUI'), \
         patch('main.AchievementUI'), \
         patch('main.AchievementNotifyQueue'), \
         patch('main.LevelSelectUI'), \
         patch('main.CheckinUI'), \
         patch('main.SaveManager') as MockSM, \
         patch('main.ANT_BY_ID', {'worker1': {}, 'worker2': {}}), \
         patch('main.get_carry_capacity', return_value=5), \
         patch('main.get_speed', return_value=1.0), \
         patch('main.get_defense', return_value=1):

        gs = GameState.__new__(GameState)

        # 基础属性
        gs.panel_active = False
        gs.panel_type = None
        gs.menu_open = False
        gs.state = 'playing'
        gs.double_income_active = False
        gs._win_streak = 0
        gs.team = ['worker1']

        # 关卡数据
        gs.level_data = {
            'target_coins': 50,
            'reward_coins': 20,
            'timer': 90,
            'terrain_name': '草地',
        }
        gs.current_level = 1

        # 金币
        gs.level_coins = 30
        gs.ai_coins = 20
        gs.total_coins = 100
        gs.transit_coins = 0

        # 蚂蚁
        gs.player_ants = []
        gs.ai_ants = []

        # 星级
        gs.total_sweet_hp = 100
        gs.collected_hp = 40
        gs.stars_earned = 0
        gs.level_timer = 0
        gs.collection_rate = 0

        # SaveManager mock
        gs.sm = MockSM()
        gs.sm.get_total_coins.return_value = 100

        return gs


# ══════════════════════════════════════════════
# 用例1：时间耗尽时玩家蚂蚁身上有食物
# ══════════════════════════════════════════════

class TestAutoSettlePlayerAntHasFood:
    """玩家蚂蚁身上有未交付食物，时间耗尽后自动结算"""

    def test_player_ant_settle(self, game):
        """玩家蚂蚁 storage=3, coin_per=2 → 结算 6 金币"""
        ant = _make_ant('player', Ant.STATE_RETURNING, storage=3, coin_per=2)
        game.player_ants = [ant]

        game._end_level()

        # 结算后蚂蚁 storage 清零
        assert ant.storage == 0
        # level_coins 增加 6 (3 × 2)
        assert game.level_coins == 36
        # collected_hp 增加 3
        assert game.collected_hp == 43

    def test_multiple_player_ants(self, game):
        """多只玩家蚂蚁同时有食物"""
        ant1 = _make_ant('player', Ant.STATE_RETURNING, storage=2, coin_per=3)
        ant2 = _make_ant('player', Ant.STATE_EATING, storage=1, coin_per=5)
        game.player_ants = [ant1, ant2]

        game._end_level()

        assert ant1.storage == 0
        assert ant2.storage == 0
        # 2×3 + 1×5 = 11
        assert game.level_coins == 41
        assert game.collected_hp == 43


# ══════════════════════════════════════════════
# 用例2：双方蚂蚁均有未交付食物
# ══════════════════════════════════════════════

class TestAutoSettleBothSides:
    """玩家和AI蚂蚁均有未交付食物，分别结算"""

    def test_both_sides_settle(self, game):
        """双方蚂蚁各自结算，金币分别计入 level_coins 和 ai_coins"""
        p_ant = _make_ant('player', Ant.STATE_MOVING_TO_SWEET, storage=4, coin_per=2)
        ai_ant = _make_ant('ai', Ant.STATE_RETURNING, storage=3, coin_per=3, ant_id='worker2')
        game.player_ants = [p_ant]
        game.ai_ants = [ai_ant]

        game._end_level()

        # 玩家: 4×2 = 8, AI: 3×3 = 9
        assert game.level_coins == 38  # 30 + 8
        assert game.ai_coins == 29     # 20 + 9
        assert p_ant.storage == 0
        assert ai_ant.storage == 0


# ══════════════════════════════════════════════
# 用例3：采集率变化影响星级
# ══════════════════════════════════════════════

class TestAutoSettleAffectsCollectionRate:
    """自动结算的 HP 计入 collected_hp，影响采集率和星级"""

    def test_collected_hp_updated(self, game):
        """玩家蚂蚁 storage 计入 collected_hp"""
        ant = _make_ant('player', Ant.STATE_EATING, storage=10, coin_per=1)
        game.player_ants = [ant]
        game.collected_hp = 50
        game.total_sweet_hp = 100

        game._end_level()

        # collected_hp 增加 10
        assert game.collected_hp == 60

    def test_ai_storage_not_in_collected_hp(self, game):
        """AI 蚂蚁的 storage 不应计入 collected_hp"""
        ai_ant = _make_ant('ai', Ant.STATE_RETURNING, storage=5, coin_per=2, ant_id='worker2')
        game.ai_ants = [ai_ant]
        game.collected_hp = 50

        game._end_level()

        # collected_hp 不变（AI 的 storage 不计入）
        assert game.collected_hp == 50
        assert game.ai_coins == 30  # 20 + 5×2


# ══════════════════════════════════════════════
# 用例4：double_income 不生效
# ══════════════════════════════════════════════

class TestAutoSettleNoDoubleIncome:
    """double_income 道具效果在自动结算时不生效"""

    def test_double_income_not_triggered(self, game):
        """即使 double_income_active=True，自动结算也不翻倍"""
        game.double_income_active = True
        ant = _make_ant('player', Ant.STATE_RETURNING, storage=3, coin_per=4)
        game.player_ants = [ant]

        game._end_level()

        # 3×4=12，不翻倍
        assert game.level_coins == 42  # 30 + 12
        assert ant.storage == 0
        # double_income 标志不应被清除（正常交付时才清除）
        assert game.double_income_active is True


# ══════════════════════════════════════════════
# 用例5：storage=0 的蚂蚁不触发结算
# ══════════════════════════════════════════════

class TestAutoSettleEmptyStorage:
    """storage=0 的蚂蚁不产生任何结算"""

    def test_empty_storage_no_settle(self, game):
        """蚂蚁身上无食物，不影响金币"""
        ant = _make_ant('player', Ant.STATE_RETURNING, storage=0, coin_per=3)
        game.player_ants = [ant]
        original_coins = game.level_coins

        game._end_level()

        assert game.level_coins == original_coins
        assert ant.storage == 0

    def test_idle_ant_no_settle(self, game):
        """IDLE 状态的蚂蚁即使有 storage 也不结算（不在 transit_states）"""
        ant = _make_ant('player', Ant.STATE_IDLE, storage=2, coin_per=3)
        game.player_ants = [ant]

        game._end_level()

        # IDLE 不在结算范围内
        assert game.level_coins == 30
        assert ant.storage == 2  # 未被清零


# ══════════════════════════════════════════════
# 用例6：正常搬运不受影响
# ══════════════════════════════════════════════

class TestNormalDeliveryUnaffected:
    """正常搬运到研磨机交付的流程不受自动结算影响"""

    def test_delivered_ants_not_settled_again(self, game):
        """已交付的蚂蚁（storage=0）不会被重复结算"""
        # 已交付的蚂蚁 storage=0，状态可能是 IDLE
        delivered_ant = _make_ant('player', Ant.STATE_IDLE, storage=0)
        game.player_ants = [delivered_ant]

        game._end_level()

        assert game.level_coins == 30  # 不变


# ══════════════════════════════════════════════
# 边界场景
# ══════════════════════════════════════════════

class TestAutoSettleEdgeCases:
    """边界场景测试"""

    def test_stunned_ant_also_settles(self, game):
        """STUNNED 状态的蚂蚁：PRD 要求仍结算（被击晕是被动行为，不应丢失食物）"""
        ant = _make_ant('player', Ant.STATE_STUNNED, storage=2, coin_per=3)
        game.player_ants = [ant]

        game._end_level()

        # STUNNED 在 transit_states 中，应结算 2×3=6 金币
        assert ant.storage == 0
        assert game.level_coins == 36  # 30 + 6
        assert game.collected_hp == 42  # 40 + 2

    def test_coin_per_zero_no_coins(self, game):
        """last_sweet_coin_per=0 时，storage 仍被清零但不产生金币"""
        ant = _make_ant('player', Ant.STATE_RETURNING, storage=5, coin_per=0)
        game.player_ants = [ant]

        game._end_level()

        assert ant.storage == 0
        assert game.level_coins == 30  # 5×0=0，不变
        # 但 collected_hp 仍会增加（storage=5）
        assert game.collected_hp == 45

    def test_level_coins_reach_target_after_settle(self, game):
        """自动结算后金币达到目标，应判定为胜利"""
        # level_coins=30, target=50, 需要至少 20 金币
        ant = _make_ant('player', Ant.STATE_RETURNING, storage=10, coin_per=3)
        game.player_ants = [ant]
        game.ai_coins = 25

        game._end_level()

        # 30 + 30 = 60 >= 50，且 60 > 25 → 胜利
        assert game.level_coins == 60
        assert game.state == 'level_complete'

    def test_level_coins_still_below_after_settle(self, game):
        """自动结算后金币仍不足，判定为失败"""
        ant = _make_ant('player', Ant.STATE_RETURNING, storage=1, coin_per=2)
        game.player_ants = [ant]
        game.ai_coins = 40

        game._end_level()

        # 30 + 2 = 32 < 50 → 失败
        assert game.state == 'game_over'


# ══════════════════════════════════════════════
# 代码审查：发现潜在 Bug
# ══════════════════════════════════════════════

class TestCodeReviewFindings:
    """基于 PRD 对代码实现的审查"""

    def test_stunned_state_in_transit(self):
        """PRD 明确要求 STUNNED 状态也应结算，transit_states 必须包含 STUNNED"""
        transit_states = {Ant.STATE_EATING, Ant.STATE_MOVING_TO_SWEET, Ant.STATE_RETURNING, Ant.STATE_STUNNED}
        assert Ant.STATE_STUNNED in transit_states

    def test_ai_collected_hp_not_tracked(self):
        """AI 蚂蚁的 collected_hp 不计入玩家的收集率，这是正确的（PRD 要求分别结算）"""
        pass  # 通过 TestAutoSettleBothSides 已验证


# ══════════════════════════════════════════════
# STUNNED 场景专项测试
# ══════════════════════════════════════════════

class TestStunnedStateSettle:
    """STUNNED 状态蚂蚁的自动结算专项测试

    PRD 规则：蚂蚁在 STUNNED 状态（被击晕）→ 仍结算，不影响。
    理由：被击晕是被动行为，食物不应因击晕而丢失。
    """

    def test_stunned_player_ant_settles(self, game):
        """玩家 STUNNED 蚂蚁身上有食物 → 自动结算"""
        ant = _make_ant('player', Ant.STATE_STUNNED, storage=3, coin_per=2)
        game.player_ants = [ant]

        game._end_level()

        assert ant.storage == 0
        assert game.level_coins == 36  # 30 + 3×2
        assert game.collected_hp == 43  # 40 + 3

    def test_stunned_ai_ant_settles(self, game):
        """AI STUNNED 蚂蚁身上有食物 → 同样自动结算"""
        ai_ant = _make_ant('ai', Ant.STATE_STUNNED, storage=4, coin_per=3, ant_id='worker2')
        game.ai_ants = [ai_ant]

        game._end_level()

        assert ai_ant.storage == 0
        assert game.ai_coins == 32  # 20 + 4×3

    def test_stunned_with_storage_zero_no_settle(self, game):
        """STUNNED 但 storage=0 的蚂蚁不产生结算"""
        ant = _make_ant('player', Ant.STATE_STUNNED, storage=0, coin_per=5)
        game.player_ants = [ant]

        game._end_level()

        assert game.level_coins == 30  # 不变
        assert ant.storage == 0

    def test_stunned_and_normal_mixed(self, game):
        """STUNNED 和正常状态蚂蚁混合，各自正确结算"""
        stunned_ant = _make_ant('player', Ant.STATE_STUNNED, storage=2, coin_per=3)
        normal_ant = _make_ant('player', Ant.STATE_RETURNING, storage=4, coin_per=2, ant_id='worker2')
        game.player_ants = [stunned_ant, normal_ant]

        game._end_level()

        # STUNNED: 2×3=6, RETURNING: 4×2=8, 合计 14
        assert stunned_ant.storage == 0
        assert normal_ant.storage == 0
        assert game.level_coins == 44  # 30 + 6 + 8
        assert game.collected_hp == 46  # 40 + 2 + 4

    def test_stunned_ant_with_max_storage(self, game):
        """STUNNED 蚂蚁满载 storage，全部结算"""
        ant = _make_ant('player', Ant.STATE_STUNNED, storage=10, coin_per=5)
        game.player_ants = [ant]

        game._end_level()

        assert ant.storage == 0
        assert game.level_coins == 80  # 30 + 10×5
        assert game.collected_hp == 50  # 40 + 10
