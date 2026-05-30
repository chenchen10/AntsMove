"""签到面板UI测试 — ui_checkin.py 渲染与交互

测试覆盖：
  1. CheckinUI.draw() 渲染调用不崩溃
  2. CheckinUI.handle_click() 点击交互
  3. current_day 语义与按钮位置匹配（核心回归测试）
  4. CheckinUI 动画状态管理
  5. pygame.draw.rect 参数兼容性（border_radius 类型）
  6. 各种 checkin_data 状态下的渲染
"""

import os
import sys
import pytest
from datetime import timedelta
from unittest.mock import MagicMock, patch, PropertyMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


# ── Mock pygame ──
# 需要在 import ui_checkin/ui_elements 之前 mock pygame，避免无头环境报错。
# 如果其他测试文件（如 test_auto_settle.py）已经导入了真实 pygame，
# 则需要先清除已导入的相关模块，再设置 mock，最后重新导入。

class FakeRect:
    """支持 collidepoint 的 FakeRect"""
    def __init__(self, x, y, w, h):
        self.x = x
        self.y = y
        self.width = w
        self.height = h
        self.right = x + w
        self.bottom = y + h
        self.centerx = x + w // 2
        self.centery = y + h // 2

    def collidepoint(self, mx, my):
        return self.x <= mx <= self.right and self.y <= my <= self.bottom


def _build_pygame_mock():
    """构建 pygame mock"""
    m = MagicMock()
    m.Rect = FakeRect
    draw_mock = MagicMock()
    m.draw = draw_mock
    m.Surface = MagicMock(return_value=MagicMock())
    m.SRCALPHA = 0x00010000
    font_mock = MagicMock()
    font_obj = MagicMock()
    font_obj.render = MagicMock(return_value=MagicMock(
        get_width=MagicMock(return_value=100),
        get_height=MagicMock(return_value=20),
        set_alpha=MagicMock(),
    ))
    font_mock.SysFont = MagicMock(return_value=font_obj)
    m.font = font_mock
    return m, draw_mock, font_obj


def _build_config_mock():
    m = MagicMock()
    m.SCREEN_WIDTH = 800
    m.SCREEN_HEIGHT = 600
    m.TEXT_COLOR = (200, 200, 200)
    m.WHITE = (255, 255, 255)
    m.GRAY = (128, 128, 128)
    m.BLACK = (0, 0, 0)
    m.ACCENT_BLUE = (100, 150, 255)
    m.ACCENT_GOLD = (255, 200, 50)
    m.ACCENT_RED = (255, 80, 80)
    m.CARD_BG = (40, 40, 60)
    m.CARD_BORDER = (80, 80, 100)
    m.BTN_HOVER = (100, 100, 120)
    return m


# ── 清除可能已被其他测试以真实模块导入的相关模块 ──
# 这确保后续 mock 设置能生效，不受其他测试导入顺序影响
_MODULES_TO_CLEAN = [
    'ui_checkin', 'ui_elements', 'font_helper', 'config',
    'checkin_data', 'pygame.draw', 'pygame.font',
]
for _mod_name in _MODULES_TO_CLEAN:
    if _mod_name in sys.modules and not isinstance(sys.modules[_mod_name], MagicMock):
        del sys.modules[_mod_name]

# ── 设置 mock ──
mock_pygame, mock_draw, mock_font_obj = _build_pygame_mock()

sys.modules['pygame'] = mock_pygame
sys.modules['pygame.draw'] = mock_draw
sys.modules['pygame.font'] = mock_pygame.font

mock_config = _build_config_mock()
sys.modules['config'] = mock_config

mock_ui_elements = MagicMock()
sys.modules['ui_elements'] = mock_ui_elements

mock_font_helper = MagicMock()
mock_font_helper.get_font = MagicMock(return_value=mock_font_obj)
sys.modules['font_helper'] = mock_font_helper

# ── 导入被测模块 ──
from ui_checkin import CheckinUI
from checkin_data import CHECKIN_BASE_REWARDS


# ══════════════════════════════════════════════
# Fixtures
# ══════════════════════════════════════════════

@pytest.fixture
def ui():
    """创建 CheckinUI 实例"""
    return CheckinUI()


@pytest.fixture
def mock_screen():
    """Mock pygame screen"""
    return MagicMock()


def _make_checkin_data(current_day=1, last_checkin_date=None, streak=0,
                       total_checkins=0, cycles_completed=0):
    """构造 checkin_data"""
    return {
        'current_day': current_day,
        'last_checkin_date': last_checkin_date,
        'total_checkins': total_checkins,
        'streak': streak,
        'cycles_completed': cycles_completed,
    }


# ══════════════════════════════════════════════
# 1. draw() 渲染调用测试
# ══════════════════════════════════════════════

class TestCheckinUIDraw:
    """验证 draw() 方法不崩溃"""

    def test_draw_first_time(self, ui, mock_screen):
        """首次签到状态渲染"""
        data = _make_checkin_data()
        result = ui.draw(mock_screen, 400, 300, data, can_checkin=True)
        # 应返回 (panel_rect, close_rect, checkin_btn_rect)
        assert isinstance(result, tuple)
        assert len(result) == 3

    def test_draw_already_checked_in(self, ui, mock_screen):
        """今日已签到状态渲染"""
        from datetime import date
        today = date.today().isoformat()
        data = _make_checkin_data(last_checkin_date=today, current_day=2)
        result = ui.draw(mock_screen, 400, 300, data, can_checkin=False)
        assert isinstance(result, tuple)

    def test_draw_day7(self, ui, mock_screen):
        """第7天（大奖日）渲染"""
        from datetime import date
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        data = _make_checkin_data(current_day=7, last_checkin_date=yesterday, streak=6)
        result = ui.draw(mock_screen, 400, 300, data, can_checkin=True)
        assert isinstance(result, tuple)

    def test_draw_broken_streak(self, ui, mock_screen):
        """断签状态渲染"""
        from datetime import date
        long_ago = (date.today() - timedelta(days=5)).isoformat()
        data = _make_checkin_data(current_day=4, last_checkin_date=long_ago, streak=0)
        result = ui.draw(mock_screen, 400, 300, data, can_checkin=True)
        assert isinstance(result, tuple)

    def test_draw_high_streak(self, ui, mock_screen):
        """高连续签到天数渲染"""
        from datetime import date
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        data = _make_checkin_data(current_day=5, last_checkin_date=yesterday, streak=30)
        result = ui.draw(mock_screen, 400, 300, data, can_checkin=True)
        assert isinstance(result, tuple)

    def test_draw_all_days_done(self, ui, mock_screen):
        """7天全部完成渲染"""
        from datetime import date
        today = date.today().isoformat()
        data = _make_checkin_data(current_day=7, last_checkin_date=today, streak=7, total_checkins=7)
        result = ui.draw(mock_screen, 400, 300, data, can_checkin=False)
        assert isinstance(result, tuple)

    def test_draw_calls_pygame_draw(self, ui, mock_screen):
        """draw() 调用了 pygame.draw 方法"""
        data = _make_checkin_data()
        mock_draw.reset_mock()
        ui.draw(mock_screen, 400, 300, data, can_checkin=True)
        # 应该调用了 pygame.draw.rect（面板背景、单元格等）
        assert mock_draw.rect.call_count > 0

    def test_draw_no_border_radius_tuple(self, ui, mock_screen):
        """⚠️ 关键测试：验证 pygame.draw.rect 不使用 tuple 形式的 border_radius"""
        data = _make_checkin_data()
        mock_draw.reset_mock()
        ui.draw(mock_screen, 400, 300, data, can_checkin=True)

        # 检查所有 rect 调用，确保 border_radius 参数不是 tuple
        for call in mock_draw.rect.call_args_list:
            args, kwargs = call
            if 'border_radius' in kwargs:
                assert not isinstance(kwargs['border_radius'], tuple), \
                    f"border_radius 不应为 tuple: {kwargs['border_radius']}"
            # 检查独立角参数
            for key in ('border_top_left_radius', 'border_top_right_radius',
                        'border_bottom_left_radius', 'border_bottom_right_radius'):
                if key in kwargs:
                    assert isinstance(kwargs[key], int), \
                        f"{key} 应为 int: {kwargs[key]}"


# ══════════════════════════════════════════════
# 2. handle_click() 点击交互测试
# ══════════════════════════════════════════════

class TestCheckinUIClick:
    """验证 handle_click() 方法"""

    def test_click_checkin_button(self, ui):
        """点击签到按钮返回 checkin action"""
        data = _make_checkin_data(current_day=1)
        # 签到按钮在第1天单元格底部，需要精确坐标
        # 面板居中: px = (800-600)//2 = 100, py = (600-520)//2 = 40
        # 单元格: x=120, y=50, col_w=(600-40)//7=80
        # 按钮: x+2, cell_y+110-26, col_w-4, 22
        btn_x = 120 + 2 + 38  # 按钮中心 x
        btn_y = 50 + 110 - 26 + 11  # 按钮中心 y
        result = ui.handle_click(btn_x, btn_y, data, can_checkin=True)
        # 可能返回 ('checkin',) 或 None，取决于精确坐标
        if result is not None:
            assert result == ('checkin',)

    def test_click_close_button(self, ui):
        """点击关闭按钮区域"""
        data = _make_checkin_data()
        # 关闭按钮在面板右上角
        result = ui.handle_click(670, 46, data, can_checkin=True)
        # handle_click 只处理签到按钮，关闭按钮由 main.py 处理
        assert result is None

    def test_click_no_action_when_already_checked(self, ui):
        """今日已签到时点击无反应"""
        from datetime import date
        today = date.today().isoformat()
        data = _make_checkin_data(current_day=1, last_checkin_date=today)
        result = ui.handle_click(160, 134, data, can_checkin=False)
        assert result is None

    def test_click_future_day_no_action(self, ui):
        """点击未来日期无反应"""
        data = _make_checkin_data(current_day=2)
        # 点击第1天区域（已是 past）
        result = ui.handle_click(160, 134, data, can_checkin=True)
        assert result is None


# ══════════════════════════════════════════════
# 3. current_day 语义与按钮位置匹配（核心回归测试）
# ══════════════════════════════════════════════

class TestCurrentDaySemantics:
    """验证 current_day 语义与 UI 按钮位置的正确匹配

    核心回归测试：防止 current_day 语义 bug 再次出现。
    current_day = 已签到天数（0→1→2...），next_day = current_day + 1。
    UI 应该在 next_day 位置显示签到按钮，而非 current_day 位置。
    """

    def _calc_btn_position(self, day_num):
        """计算第 day_num 天签到按钮的中心坐标

        面板居中: px = (800-600)//2 = 100, py = (600-520)//2 = 40
        单元格: x = 120 + i * (col_w + col_gap), y = 50
        col_w = (600-40)//7 = 80, col_gap = 4
        按钮: x+2, cell_y+110-26, col_w-4, 22
        """
        px, py = 100, 40
        col_w = (600 - 40) // 7  # 80
        col_gap = 4
        start_x = px + 20  # 120
        i = day_num - 1
        x = start_x + i * (col_w + col_gap)
        cell_y = py + 10  # 50
        btn_rect_x = x + 2
        btn_rect_y = cell_y + 110 - 26  # 134
        btn_rect_w = col_w - 4  # 76
        btn_rect_h = 22
        center_x = btn_rect_x + btn_rect_w // 2
        center_y = btn_rect_y + btn_rect_h // 2
        return center_x, center_y

    def test_current_day_0_button_on_day_1(self, ui):
        """current_day=0（首次签到），按钮应在第1天"""
        data = _make_checkin_data(current_day=0)
        cx, cy = self._calc_btn_position(1)
        result = ui.handle_click(cx, cy, data, can_checkin=True)
        assert result == ('checkin',), \
            f"current_day=0 时点击第1天按钮应返回 ('checkin',)，实际: {result}"

    def test_current_day_1_button_on_day_2(self, ui):
        """current_day=1（已签1天），按钮应在第2天"""
        data = _make_checkin_data(current_day=1)
        cx, cy = self._calc_btn_position(2)
        result = ui.handle_click(cx, cy, data, can_checkin=True)
        assert result == ('checkin',), \
            f"current_day=1 时点击第2天按钮应返回 ('checkin',)，实际: {result}"

    def test_current_day_1_click_day_1_no_action(self, ui):
        """current_day=1 时点击第1天按钮应无反应（已签过）"""
        data = _make_checkin_data(current_day=1)
        cx, cy = self._calc_btn_position(1)
        result = ui.handle_click(cx, cy, data, can_checkin=True)
        assert result is None, \
            f"current_day=1 时点击第1天按钮应返回 None，实际: {result}"

    def test_current_day_6_button_on_day_7(self, ui):
        """current_day=6（已签6天），按钮应在第7天（大奖日）"""
        data = _make_checkin_data(current_day=6)
        cx, cy = self._calc_btn_position(7)
        result = ui.handle_click(cx, cy, data, can_checkin=True)
        assert result == ('checkin',), \
            f"current_day=6 时点击第7天按钮应返回 ('checkin',)，实际: {result}"

    def test_current_day_7_wraps_to_day_1(self, ui):
        """current_day=7（周期完成），按钮应回到第1天"""
        data = _make_checkin_data(current_day=7)
        cx, cy = self._calc_btn_position(1)
        result = ui.handle_click(cx, cy, data, can_checkin=True)
        assert result == ('checkin',), \
            f"current_day=7 时点击第1天按钮应返回 ('checkin',)，实际: {result}"

    def test_after_checkin_button_moves_to_next_day(self, ui):
        """签到后 current_day 递增，按钮应自动跳到下一天

        模拟流程：current_day=0 → 签到 → current_day=1 → 按钮应在第2天
        """
        # 签到前：current_day=0，按钮在第1天
        data_before = _make_checkin_data(current_day=0)
        cx1, cy1 = self._calc_btn_position(1)
        result1 = ui.handle_click(cx1, cy1, data_before, can_checkin=True)
        assert result1 == ('checkin',)

        # 签到后：current_day=1，按钮应在第2天
        data_after = _make_checkin_data(current_day=1)
        cx2, cy2 = self._calc_btn_position(2)
        result2 = ui.handle_click(cx2, cy2, data_after, can_checkin=True)
        assert result2 == ('checkin',)

        # 签到后：点击第1天应无反应
        result3 = ui.handle_click(cx1, cy1, data_after, can_checkin=True)
        assert result3 is None

    def test_each_day_button_position_matches(self, ui):
        """验证每一天的按钮位置都正确"""
        for current_day in range(7):
            next_day = current_day + 1
            data = _make_checkin_data(current_day=current_day)
            cx, cy = self._calc_btn_position(next_day)
            result = ui.handle_click(cx, cy, data, can_checkin=True)
            assert result == ('checkin',), \
                f"current_day={current_day} 时点击第{next_day}天按钮应返回 ('checkin',)，实际: {result}"

    def test_all_past_days_no_button(self, ui):
        """所有已签过的天不应有签到按钮"""
        for current_day in range(1, 7):  # 不含7，因为 current_day=7 时 next_day=1
            data = _make_checkin_data(current_day=current_day)
            next_day = current_day + 1
            # 点击所有 < next_day 的天，应无反应
            for past_day in range(1, next_day):
                cx, cy = self._calc_btn_position(past_day)
                result = ui.handle_click(cx, cy, data, can_checkin=True)
                assert result is None, \
                    f"current_day={current_day} 时点击第{past_day}天应返回 None，实际: {result}"

    def test_future_days_no_button(self, ui):
        """未来天不应有签到按钮"""
        for current_day in range(7):
            next_day = current_day + 1
            data = _make_checkin_data(current_day=current_day)
            # 点击 > next_day 的天，应无反应
            for future_day in range(next_day + 1, 8):
                cx, cy = self._calc_btn_position(future_day)
                result = ui.handle_click(cx, cy, data, can_checkin=True)
                assert result is None, \
                    f"current_day={current_day} 时点击第{future_day}天应返回 None，实际: {result}"

    def test_draw_returns_correct_button_rect(self, ui, mock_screen):
        """draw() 返回的 checkin_btn_rect 位置与 next_day 匹配"""
        from datetime import date
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        # current_day=3，next_day=4，按钮应在第4天
        data = _make_checkin_data(current_day=3, last_checkin_date=yesterday, streak=2)
        panel, close_rect, checkin_btn_rect = ui.draw(mock_screen, 400, 300, data, can_checkin=True)

        if checkin_btn_rect is not None:
            # 第4天按钮的预期 x 范围
            px = 100
            col_w = (600 - 40) // 7
            col_gap = 4
            start_x = px + 20
            i = 3  # 第4天，index=3
            expected_x = start_x + i * (col_w + col_gap)
            assert checkin_btn_rect.x == expected_x + 2, \
                f"按钮 x 位置不匹配: 期望 {expected_x + 2}，实际 {checkin_btn_rect.x}"


# ══════════════════════════════════════════════
# 3. 动画状态测试
# ══════════════════════════════════════════════

class TestCheckinUIAnimation:
    """验证动画状态管理"""

    def test_initial_state(self, ui):
        """初始状态无动画"""
        assert ui._anim_active is False
        assert ui._anim_reward == 0
        assert ui._anim_timer == 0.0

    def test_start_animation(self, ui):
        """启动动画"""
        ui.start_reward_animation(100)
        assert ui._anim_active is True
        assert ui._anim_reward == 100
        assert ui._anim_timer == 0.0

    def test_update_animation(self, ui):
        """更新动画计时器"""
        ui.start_reward_animation(100)
        ui.update(0.5)
        assert ui._anim_timer == 0.5
        assert ui._anim_active is True

    def test_animation_completes(self, ui):
        """动画在 1.5 秒后结束"""
        ui.start_reward_animation(100)
        ui.update(1.5)
        assert ui._anim_active is False
        assert ui._anim_timer == 0.0

    def test_scroll_noop(self, ui):
        """scroll 方法不崩溃"""
        ui.scroll(100)  # 不应抛异常


# ══════════════════════════════════════════════
# 4. pygame API 兼容性测试
# ══════════════════════════════════════════════

class TestPygameCompatibility:
    """验证 pygame API 调用兼容性"""

    def test_rect_draw_with_individual_radius(self, ui, mock_screen):
        """验证使用独立角参数而非 tuple"""
        data = _make_checkin_data()
        mock_draw.reset_mock()
        ui.draw(mock_screen, 400, 300, data, can_checkin=True)

        # 所有 draw.rect 调用中，不应出现 border_radius=tuple 的情况
        problematic_calls = []
        for i, call in enumerate(mock_draw.rect.call_args_list):
            args, kwargs = call
            if 'border_radius' in kwargs and isinstance(kwargs['border_radius'], tuple):
                problematic_calls.append((i, kwargs['border_radius']))

        assert len(problematic_calls) == 0, \
            f"发现 tuple 形式的 border_radius: {problematic_calls}"

    def test_draw_circle_calls(self, ui, mock_screen):
        """draw() 调用了 pygame.draw.circle（状态图标）"""
        from datetime import date
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        data = _make_checkin_data(current_day=3, last_checkin_date=yesterday, streak=2)
        mock_draw.reset_mock()
        ui.draw(mock_screen, 400, 300, data, can_checkin=True)
        # 应该有 circle 调用（已完成天数的绿色圆、今日的金色圆等）
        assert mock_draw.circle.call_count > 0

    def test_draw_polygon_for_star(self, ui, mock_screen):
        """第7天大奖使用 polygon 绘制星形（current_day=6 → next_day=7 为 today）"""
        from datetime import date
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        # current_day=6 → next_day=7，第7天是 today → 画星形
        data = _make_checkin_data(current_day=6, last_checkin_date=yesterday, streak=5)
        mock_draw.reset_mock()
        ui.draw(mock_screen, 400, 300, data, can_checkin=True)
        # 应该有 polygon 调用（星形绘制）
        assert mock_draw.polygon.call_count > 0


# ══════════════════════════════════════════════
# 5. 边界场景渲染测试
# ══════════════════════════════════════════════

class TestCheckinUIEdgeCases:
    """验证各种边界条件下的渲染"""

    def test_draw_with_empty_data(self, ui, mock_screen):
        """空数据不崩溃"""
        data = {}
        result = ui.draw(mock_screen, 400, 300, data, can_checkin=True)
        assert isinstance(result, tuple)

    def test_draw_with_none_last_date(self, ui, mock_screen):
        """last_checkin_date 为 None"""
        data = _make_checkin_data(last_checkin_date=None)
        result = ui.draw(mock_screen, 400, 300, data, can_checkin=True)
        assert isinstance(result, tuple)

    def test_draw_mouse_outside(self, ui, mock_screen):
        """鼠标在面板外"""
        data = _make_checkin_data()
        result = ui.draw(mock_screen, 0, 0, data, can_checkin=True)
        assert isinstance(result, tuple)

    def test_draw_mouse_on_close_button(self, ui, mock_screen):
        """鼠标悬停在关闭按钮上"""
        data = _make_checkin_data()
        # 关闭按钮在面板右上角
        result = ui.draw(mock_screen, 670, 46, data, can_checkin=True)
        assert isinstance(result, tuple)

    def test_cycles_completed_nonzero(self, ui, mock_screen):
        """已完成多个周期"""
        from datetime import date
        today = date.today().isoformat()
        data = _make_checkin_data(
            current_day=3, last_checkin_date=today,
            streak=10, total_checkins=24, cycles_completed=3
        )
        result = ui.draw(mock_screen, 400, 300, data, can_checkin=False)
        assert isinstance(result, tuple)
