"""
蚂蚁抢甜点 - 主游戏文件
26只蚂蚁 × 200关 × 地形克制 × 双金币体系
"""

import pygame
import sys
import math
import random
import os

from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS,
    SWEET_COLORS, WHITE,
)
from assets import load_assets
from ants_data import (
    ANT_BY_ID, get_carry_capacity, get_speed, get_defense,
)
from ai_data import (
    get_max_team_size, generate_ai_team,
    get_ai_ant_stats, get_ai_late_buffs, is_ai_boss_level,
)
from levels_data import get_level, calc_stars
from save_manager import SaveManager
from ant_sprite import Ant
from sweet_sprite import Sweet
from grinder_sprite import Grinder
from ui_shop import ShopUI
from ui_task import TaskUI
from ui_achievement import AchievementUI
from ui_achievement_notify import AchievementNotifyQueue
from ui_level_select import LevelSelectUI
from ui_checkin import CheckinUI
import font_helper

from scenes import SCENE_MAP


# ── FloatingText ──────────────────────────────────────────


def _get_ft_font(size):
    return font_helper.get_font(size)


class FloatingText:
    def __init__(self, text, x, y, color=(255, 215, 0), duration=1.0, font_size=20):
        self.text = text
        self.x = x
        self.y = y
        self.color = color
        self.duration = duration
        self.timer = 0.0
        self.font_size = font_size
        self.alive = True

    def update(self, dt):
        self.timer += dt
        self.y -= 40 * dt
        if self.timer >= self.duration:
            self.alive = False

    def draw(self, screen, font):
        if not self.alive:
            return
        alpha = max(0, int(255 * (1.0 - self.timer / self.duration)))
        f = _get_ft_font(self.font_size)
        text_surf = f.render(self.text, True, self.color)
        outline_surf = f.render(self.text, True, (0, 0, 0))
        outline_surf.set_alpha(alpha)
        text_surf.set_alpha(alpha)
        rect = text_surf.get_rect(center=(int(self.x), int(self.y)))
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            screen.blit(outline_surf, rect.move(dx, dy))
        screen.blit(text_surf, rect)


# ── Helper ──────────────────────────────────────────

def _get_sweet_edge_pos(sweet, ant_x, ant_y):
    dx = sweet.x - ant_x
    dy = sweet.y - ant_y
    dist = math.sqrt(dx * dx + dy * dy)
    if dist < 1:
        return sweet.x, sweet.y
    radius = sweet.current_size / 2 + 15
    target_x = sweet.x - (dx / dist) * radius
    target_y = sweet.y - (dy / dist) * radius
    return target_x, target_y


# ── Game State ──────────────────────────────────────────

class GameState:
    def __init__(self):
        pygame.init()
        pygame.font.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("蚂蚁抢甜点")
        self.clock = pygame.time.Clock()

        # Font path
        font_helper.init()
        self.font_xl = font_helper.get_font(48)
        self.font_large = font_helper.get_font(38)
        self.font_medium = font_helper.get_font(24)
        self.font_small = font_helper.get_font(18)
        self.font_tiny = font_helper.get_font(14)

        # Load assets
        try:
            self.assets = load_assets()
        except Exception:
            self.assets = {}

        # Homepage background
        self.homepage_bg = None
        try:
            bg_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'images', 'ant', 'homepage.png')
            bg_img = pygame.image.load(bg_path).convert()
            self.homepage_bg = pygame.transform.smoothscale(bg_img, (SCREEN_WIDTH, SCREEN_HEIGHT))
        except Exception:
            pass

        # Level backgrounds
        self.level_bgs = {}
        try:
            base = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'images', 'ant')
            bg_files = sorted([f for f in os.listdir(base) if 'background' in f.lower() and f.endswith('.png')])
            for idx, name in enumerate(bg_files):
                path = os.path.join(base, name)
                img = pygame.image.load(path).convert()
                self.level_bgs[idx] = pygame.transform.smoothscale(img, (SCREEN_WIDTH, SCREEN_HEIGHT))
        except Exception:
            pass

        # Save manager
        self.sm = SaveManager()
        self.sm.load()
        self.sm.ensure_starter_ant()

        # Game state
        self.state = 'title'
        self.current_level = 1
        self.level_data = None

        # Dual currency
        self.total_coins = self.sm.get_total_coins()
        self.level_coins = 0
        self.ai_coins = 0

        # Team (list of ant_ids)
        self.team = []
        self.team_size_limit = 3
        self._team_btns = {}

        # In-game state
        self.player_ants = []
        self.ai_ants = []
        self.sweets = []
        self.player_grinder = None
        self.ai_grinder = None
        self.floating_texts = []
        self.level_timer = 0
        self.double_income_active = False
        self.speed_boost_timer = 0
        self.item_uses = {}

        # 星级系统：收集率追踪
        self.total_sweet_hp = 0   # 关卡甜点总HP
        self.collected_hp = 0     # 玩家已收集的HP
        self.stars_earned = 0     # 本关获得的星级

        # 自动结算：记录搬运途中未交付食物折算的金币（仅玩家方，用于结算明细展示）
        self.transit_coins = 0

        # 任务系统：连胜追踪
        self._win_streak = 0

        # UI
        self.shop_ui = ShopUI()
        self.task_ui = TaskUI()
        self.achievement_ui = AchievementUI()
        self.checkin_ui = CheckinUI()
        self.level_select_ui = LevelSelectUI(self.sm)
        self.menu_open = False
        self.panel_active = False
        self.panel_type = None
        self.shop_toast = None
        self.shop_toast_timer = 0
        self.shop_active = False  # 标题/关卡选择页的商店浮层
        self._upgrade_cooldown = 0  # 升级防抖计时器（秒）
        self.task_panel_active = False      # 任务面板
        self.achievement_panel_active = False  # 成就面板
        self.checkin_panel_active = False    # 签到面板

        # 成就解锁通知队列
        self.ach_notify_queue = AchievementNotifyQueue()

        # Scenes（按需实例化，首次访问时创建）
        self._scenes = {}

    def _get_scene(self, name):
        """获取或创建场景实例"""
        if name not in self._scenes:
            cls = SCENE_MAP[name]
            self._scenes[name] = cls(self)
        return self._scenes[name]

    def _check_achievements(self):
        """检测新解锁的成就并推送到通知队列。

        在关卡结算、商店购买/升级等关键事件后调用。
        """
        newly_unlocked = self.sm.evaluate_all_achievements()
        if newly_unlocked:
            from achievements_data import ACHIEVEMENT_BY_ID
            for aid in newly_unlocked:
                if aid in ACHIEVEMENT_BY_ID:
                    self.ach_notify_queue.push(ACHIEVEMENT_BY_ID[aid])

    def run(self):
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000.0
            dt = min(dt, 0.05)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if self.state == 'debug':
                        if event.key == pygame.K_ESCAPE:
                            debug_scene = self._get_scene('debug')
                            if debug_scene.active_input:
                                debug_scene.active_input = None
                            else:
                                self.state = 'title'
                        else:
                            self._get_scene('debug').handle_key(event)
                    elif event.key == pygame.K_ESCAPE:
                        if self.shop_active:
                            self.shop_active = False
                            self.shop_ui.close()
                        elif self.task_panel_active:
                            self.task_panel_active = False
                        elif self.achievement_panel_active:
                            self.achievement_panel_active = False
                        elif self.checkin_panel_active:
                            self.checkin_panel_active = False
                        elif self.panel_active:
                            self.panel_active = False
                        elif self.state == 'playing':
                            self.state = 'paused'
                        elif self.state == 'paused':
                            self.state = 'playing'
                        elif self.state in ('level_select', 'team_select'):
                            self.state = 'title'

                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mx, my = event.pos
                    self._handle_click(mx, my)
                if event.type == pygame.MOUSEBUTTONDOWN and event.button in (4, 5):
                    if self.achievement_panel_active:
                        dy = 1 if event.button == 4 else -1
                        self.achievement_ui.scroll(dy)
                    elif self.task_panel_active:
                        dy = 1 if event.button == 4 else -1
                        self.task_ui.scroll(dy)
                    elif self.checkin_panel_active:
                        dy = 1 if event.button == 4 else -1
                        self.checkin_ui.scroll(dy)
                    elif self.shop_active or (self.panel_active and self.panel_type == 'shop'):
                        dy = 1 if event.button == 4 else -1
                        self.shop_ui.scroll(dy)
                    elif self.state == 'level_select':
                        if event.button == 4:
                            self.level_select_ui.page = max(0, self.level_select_ui.page - 1)
                        elif event.button == 5:
                            self.level_select_ui.page = min(
                                self.level_select_ui.total_pages - 1,
                                self.level_select_ui.page + 1)
                if event.type == pygame.MOUSEWHEEL:
                    self._handle_scroll(event.x, event.y)

            self.update(dt)
            self.draw()
            pygame.display.flip()

        pygame.quit()
        sys.exit()

    # ── Scroll routing ──

    def _handle_scroll(self, scroll_x, scroll_y):
        """处理触控板/滚轮滚动事件。

        scroll_x: 水平滚动量（触控板双指左右滑动）
        scroll_y: 垂直滚动量（触控板双指上下滑动 / 物理滚轮）
        """
        if self.achievement_panel_active:
            if scroll_y != 0:
                self.achievement_ui.scroll(scroll_y)
        elif self.task_panel_active:
            if scroll_y != 0:
                self.task_ui.scroll(scroll_y)
        elif self.checkin_panel_active:
            if scroll_y != 0:
                self.checkin_ui.scroll(scroll_y)
        elif self.shop_active or (self.panel_active and self.panel_type == 'shop'):
            if scroll_y != 0:
                self.shop_ui.scroll(scroll_y)
        elif self.state == 'level_select':
            if scroll_x != 0:
                # 触控板水平滑动：左右翻页
                if scroll_x < 0:
                    self.level_select_ui.page = max(0, self.level_select_ui.page - 1)
                else:
                    self.level_select_ui.page = min(
                        self.level_select_ui.total_pages - 1,
                        self.level_select_ui.page + 1)
            elif scroll_y != 0:
                # 垂直滚动也支持翻页
                if scroll_y > 0:
                    self.level_select_ui.page = max(0, self.level_select_ui.page - 1)
                else:
                    self.level_select_ui.page = min(
                        self.level_select_ui.total_pages - 1,
                        self.level_select_ui.page + 1)

    # ── Click routing ──

    def _handle_click(self, mx, my):
        # 成就解锁通知点击（最顶层，优先处理）
        if self.ach_notify_queue.handle_click(mx, my):
            self.ach_notify_queue.clear()
            self.achievement_panel_active = True
            return

        # 成就面板浮层优先处理
        if self.achievement_panel_active:
            consumed = self._click_achievement_overlay(mx, my)
            if consumed:
                return

        # 任务面板浮层优先处理
        if self.task_panel_active:
            consumed = self._click_task_overlay(mx, my)
            if consumed:
                return

        # 签到面板浮层优先处理
        if self.checkin_panel_active:
            consumed = self._click_checkin_overlay(mx, my)
            if consumed:
                return

        # 标题/关卡选择页商店浮层优先处理
        if self.shop_active:
            consumed = self._click_shop_overlay(mx, my)
            if consumed:
                return
            # 点击面板外部 → 面板已关闭，穿透给底层场景

        # 对战内商店面板浮层优先处理
        if self.panel_active:
            consumed = self._click_panel(mx, my)
            if consumed:
                return
            # 点击面板外部 → 面板已关闭，穿透给底层场景

        scene = self._get_scene(self.state)
        scene.handle_click(mx, my)

    def _click_shop_overlay(self, mx, my):
        """标题/关卡选择页的商店浮层点击处理。返回True表示点击被面板消费。"""
        pw, ph = 600, 520
        px = (SCREEN_WIDTH - pw) // 2
        py = (SCREEN_HEIGHT - ph) // 2
        panel = pygame.Rect(px, py, pw, ph)

        # 点击面板外部 → 关闭面板，不消费点击（穿透给底层场景）
        if not panel.collidepoint(mx, my):
            self.shop_active = False
            self.shop_ui.close()
            return False

        # 以下点击都在面板内部，消费掉

        # 关闭按钮
        close_rect = pygame.Rect(panel.right - 30, panel.y + 6, 24, 24)
        if close_rect.collidepoint(mx, my):
            self.shop_active = False
            self.shop_ui.close()
            return True

        # 标签页点击
        tab_w = panel.w // 3
        for i in range(3):
            tab_rect = pygame.Rect(px + i * tab_w, panel.y + 58, tab_w, 30)
            if tab_rect.collidepoint(mx, my):
                self.shop_ui.tab = i
                self.shop_ui.scroll_y = 0
                self.shop_ui.selected_ant = None
                self.shop_ui.upgrade_gear = 1
                return True

        # 内容区点击
        result = self.shop_ui.handle_click(mx, my, self.sm, self.team,
                                            self.total_coins, 0, {})
        if result:
            action, data = result
            if action == 'buy_ant':
                if self.sm.buy_ant(data, ANT_BY_ID[data]['buy_cost']):
                    self.total_coins = self.sm.get_total_coins()
                    name = ANT_BY_ID[data]['name']
                    count = self.sm.get_ant_count(data)
                    self.shop_toast = f"购买成功: {name} x{count}"
                    self.shop_toast_timer = 1.5
                    # 购买蚂蚁可能触发收集类/养成类成就
                    self._check_achievements()
            elif action == 'upgrade_attr':
                ant_id, attr, cost = data
                attr_name = {'carry': '搬运', 'speed': '速度', 'defense': '防御'}.get(attr, attr)
                if self.sm.upgrade_ant_attr(ant_id, attr, cost):
                    self.total_coins = self.sm.get_total_coins()
                    new_lv = self.sm.get_ant_attr(ant_id, attr)
                    self.shop_toast = f"{attr_name}升级成功: Lv{new_lv}"
                    self.shop_toast_timer = 1.5
                    # 属性升级可能触发养成类成就
                    self._check_achievements()
            elif action == 'upgrade_attr_batch':
                # 防抖：0.3s内忽略重复点击
                if self._upgrade_cooldown > 0:
                    return True
                ant_id, attr, target_lv, cost = data
                attr_name = {'carry': '搬运', 'speed': '速度', 'defense': '防御'}.get(attr, attr)
                result = self.sm.batch_upgrade_ant_attr(ant_id, attr, target_lv)
                self._upgrade_cooldown = 0.3
                if result['success']:
                    self.total_coins = self.sm.get_total_coins()
                    new_lv = result['new_level']
                    lv_up = result['levels_up']
                    if new_lv >= target_lv:
                        self.shop_toast = f"{attr_name}升级成功: Lv{new_lv}"
                    else:
                        self.shop_toast = f"{attr_name}升级成功: Lv{new_lv}（金币不足，升了 {lv_up} 级）"
                    self.shop_toast_timer = 1.5
                    self._check_achievements()
        return True

    def _get_task_data(self):
        """获取任务数据，返回 tasks_data 格式"""
        return self.sm.get_tasks_for_ui()

    def _click_task_overlay(self, mx, my):
        """任务面板浮层点击处理。返回True表示点击被面板消费。"""
        pw, ph = 600, 520
        px = (SCREEN_WIDTH - pw) // 2
        py = (SCREEN_HEIGHT - ph) // 2
        panel = pygame.Rect(px, py, pw, ph)

        # 点击面板外部 → 关闭面板（消费点击，防止穿透到底层场景重新打开）
        if not panel.collidepoint(mx, my):
            self.task_panel_active = False
            return True

        # 关闭按钮
        close_rect = pygame.Rect(panel.right - 30, panel.y + 6, 24, 24)
        if close_rect.collidepoint(mx, my):
            self.task_panel_active = False
            return True

        tasks_data = self._get_task_data()
        result = self.task_ui.handle_click(mx, my, tasks_data)
        if result:
            action, data = result
            if action == 'claim_task':
                success, reward = self.sm.claim_task_reward(data)
                if success:
                    self.total_coins = self.sm.get_total_coins()
                    self.shop_toast = f"任务奖励: +{reward}金币"
                    self.shop_toast_timer = 1.5
        return True

    def _click_achievement_overlay(self, mx, my):
        """成就面板浮层点击处理。返回True表示点击被面板消费。"""
        pw, ph = 600, 520
        px = (SCREEN_WIDTH - pw) // 2
        py = (SCREEN_HEIGHT - ph) // 2
        panel = pygame.Rect(px, py, pw, ph)

        # 点击面板外部 → 关闭面板
        if not panel.collidepoint(mx, my):
            self.achievement_panel_active = False
            return True

        # 关闭按钮
        close_rect = pygame.Rect(panel.right - 30, panel.y + 6, 24, 24)
        if close_rect.collidepoint(mx, my):
            self.achievement_panel_active = False
            return True

        from achievements_data import claim_achievement
        result = self.achievement_ui.handle_click(mx, my, self.sm)
        if result:
            action, data = result
            if action == 'claim_achievement':
                success, reward = claim_achievement(data, self.sm)
                if success:
                    self.total_coins = self.sm.get_total_coins()
                    self.shop_toast = f"成就奖励: +{reward}金币"
                    self.shop_toast_timer = 1.5
        return True

    def _click_checkin_overlay(self, mx, my):
        """签到面板浮层点击处理。返回True表示点击被面板消费。"""
        pw, ph = 600, 520
        px = (SCREEN_WIDTH - pw) // 2
        py = (SCREEN_HEIGHT - ph) // 2
        panel = pygame.Rect(px, py, pw, ph)

        # 点击面板外部 → 关闭面板
        if not panel.collidepoint(mx, my):
            self.checkin_panel_active = False
            return True

        # 关闭按钮
        close_rect = pygame.Rect(panel.right - 30, panel.y + 6, 24, 24)
        if close_rect.collidepoint(mx, my):
            self.checkin_panel_active = False
            return True

        checkin_data = self.sm.get_checkin_data()
        can_checkin = self.sm.can_checkin_today()
        result = self.checkin_ui.handle_click(mx, my, checkin_data, can_checkin)
        if result:
            action, *_ = result
            if action == 'checkin':
                result = self.sm.perform_checkin()
                if result['success']:
                    self.total_coins = self.sm.get_total_coins()
                    reward = result['reward']['amount']
                    self.shop_toast = f"签到成功: +{reward}金币"
                    self.shop_toast_timer = 1.5
                    self.checkin_ui.start_reward_animation(reward)
        return True

    def _click_panel(self, mx, my):
        """对战内商店面板点击处理。返回True表示点击被面板消费。"""
        if self.panel_type == 'shop':
            pw, ph = 600, 520
            px = (SCREEN_WIDTH - pw) // 2
            py = (SCREEN_HEIGHT - ph) // 2
            panel = pygame.Rect(px, py, pw, ph)

            # 点击面板外部 → 关闭面板，不消费点击（穿透给底层场景）
            if not panel.collidepoint(mx, my):
                self.panel_active = False
                self.panel_type = None
                return False

            # 以下点击都在面板内部，消费掉

            # 关闭按钮
            close_rect = pygame.Rect(panel.right - 30, panel.y + 6, 24, 24)
            if close_rect.collidepoint(mx, my):
                self.panel_active = False
                self.panel_type = None
                return True

            # 内容区点击（battle_mode=True，仅道具页）
            result = self.shop_ui.handle_click(mx, my, self.sm, self.team,
                                                self.total_coins, self.level_coins, self.item_uses)
            if result:
                action, data = result
                if action == 'buy_item':
                    item_name, cost = data
                    max_uses = {'加速药水': 3, '双倍收益券': 3, '干扰粉尘': 2}
                    used = self.item_uses.get(item_name, 0)
                    if used >= max_uses.get(item_name, 999):
                        self.shop_toast = f"{item_name} 已达使用上限"
                        self.shop_toast_timer = 1.5
                    elif self.level_coins >= cost:
                        self.level_coins -= cost
                        self.item_uses[item_name] = used + 1
                        self._apply_item(item_name)
            return True
        return False

    # ── Level management ──

    def _start_level(self):
        if not self.team:
            return

        self.level_coins = 0
        self.ai_coins = 0
        self.transit_coins = 0
        self.level_timer = self.level_data['timer']
        self.floating_texts = []
        self.double_income_active = False
        self.speed_boost_timer = 0
        self.item_uses = {}

        # 星级系统：初始化收集率追踪
        sweet_info = self.level_data['sweet']
        self.total_sweet_hp = sweet_info['hp'] * sweet_info['quantity']
        self.collected_hp = 0

        # 1:1镜像：上阵上限受关卡限制
        self.team_size_limit = get_max_team_size(self.current_level)

        # Player ants（全部一次性部署，错开位置）
        self.player_ants = []
        for idx, ant_id in enumerate(self.team):
            carry_lv = self.sm.get_ant_attr(ant_id, 'carry')
            speed_lv = self.sm.get_ant_attr(ant_id, 'speed')
            defense_lv = self.sm.get_ant_attr(ant_id, 'defense')
            ant = Ant(ant_id, 'player', 50 + idx * 25, SCREEN_HEIGHT - 80 - idx * 25,
                      carry_level=carry_lv, speed_level=speed_lv, defense_level=defense_lv,
                      assets=self.assets, terrain=self.level_data['terrain'])
            self.player_ants.append(ant)

        # AI ants（独立梯队池 + 独立属性公式，不镜像玩家种类和等级）
        self.ai_ants = []
        ai_count = len(self.team)  # 1:1数量镜像
        ai_team_ids = generate_ai_team(self.current_level, ai_count)
        ai_buffs = get_ai_late_buffs(self.current_level)
        for idx, aid in enumerate(ai_team_ids):
            ai_carry, ai_speed, ai_defense = get_ai_ant_stats(aid, self.current_level)
            ant = Ant(aid, 'ai', SCREEN_WIDTH - 60 - idx * 25, 80 + idx * 25,
                      carry_level=0, speed_level=0, defense_level=0,
                      assets=self.assets, terrain=self.level_data['terrain'])
            # 用AI独立属性覆盖基础值
            ant.max_storage = ai_carry
            ant.storage = 0
            ant.speed = ai_speed
            ant.defense = ai_defense
            # 151关后全体敌方额外Buff
            if ai_buffs:
                ant._ai_terrain_debuff_reduction = ai_buffs.get('terrain_debuff_reduction', 0)
                ant._ai_stun_reduction = ai_buffs.get('stun_reduction', 0)
            self.ai_ants.append(ant)

        # Sweets
        self.sweets = []
        sweet_info = self.level_data['sweet']
        sweet = Sweet(
            sweet_type=sweet_info['type'],
            x=SCREEN_WIDTH // 2,
            y=300,
            max_hp=sweet_info['hp'],
            coin_per=sweet_info['coin_per'],
            assets=self.assets,
            quantity=sweet_info['quantity']
        )
        self.sweets.append(sweet)

        # Grinders
        self.player_grinder = Grinder(x=80, y=SCREEN_HEIGHT - 110, color=(80, 130, 80), label="我方")
        self.ai_grinder = Grinder(x=SCREEN_WIDTH - 80, y=80, color=(130, 80, 80), label="敌方")

        # 场景缓存失效（关卡切换后需要重建）
        self._scenes.pop('paused', None)

        self.state = 'playing'

    def _end_level(self):
        self.panel_active = False
        self.panel_type = None
        self.menu_open = False
        target = self.level_data.get('target_coins', 0)
        reward = self.level_data.get('reward_coins', 0)

        # ── 自动结算未搬运食物（PRD CHE-29）──
        # 游戏结束时，搬运途中（EATING / MOVING_TO_SWEET / RETURNING / STUNNED）且身上有食物的蚂蚁，
        # 按 storage × last_sweet_coin_per 兜底结算为金币，不触发 double_income 效果。
        transit_states = {Ant.STATE_EATING, Ant.STATE_MOVING_TO_SWEET, Ant.STATE_RETURNING, Ant.STATE_STUNNED}
        for ant in self.player_ants:
            if ant.state in transit_states and ant.storage > 0:
                coins_earned = ant.storage * ant.last_sweet_coin_per
                self.level_coins += coins_earned
                self.transit_coins += coins_earned
                self.collected_hp += ant.storage
                ant.storage = 0
        for ant in self.ai_ants:
            if ant.state in transit_states and ant.storage > 0:
                coins_earned = ant.storage * ant.last_sweet_coin_per
                self.ai_coins += coins_earned
                ant.storage = 0

        if self.level_coins >= target and self.level_coins > self.ai_coins:
            # 胜利：对战金币 + 通关奖励
            total_earned = self.level_coins + reward
            self.total_coins += total_earned
            self.sm.add_coins(total_earned)
            self.sm.set_max_level(self.current_level)

            # 星级系统：计算并记录星级
            total_time = self.level_data.get('timer', 90)
            collection_rate = (self.collected_hp / self.total_sweet_hp
                               if self.total_sweet_hp > 0 else 0)
            self.collection_rate = collection_rate
            self.stars_earned = calc_stars(
                self.current_level,
                self.level_coins,
                target,
                self.level_timer,
                total_time,
                collection_rate,
            )
            self.sm.update_level_record(
                self.current_level,
                self.stars_earned,
                self.level_coins,
                self.level_timer,
            )

            # 任务系统：更新进度
            self._win_streak += 1
            terrain_name = self.level_data.get('terrain_name', '')
            ants_used = [ant.ant_id for ant in self.player_ants]
            self.sm.check_task_progress(
                level_data=self.level_data,
                sm=self.sm,
                team=self.team,
                level_coins=self.level_coins,
                stars_earned=self.stars_earned,
                level_id=self.current_level,
                win_streak=self._win_streak,
                terrain=terrain_name,
                ants_used=ants_used,
            )

            # 成就系统：检测新解锁的成就
            self._check_achievements()

            self.state = 'level_complete'
        else:
            # 失败：仅保存对战金币（无通关奖励）
            self.stars_earned = 0
            self._win_streak = 0  # 连胜中断
            if self.level_coins > 0:
                self.total_coins += self.level_coins
                self.sm.add_coins(self.level_coins)
            # 失败也记录挑战次数
            self.sm.update_level_record(
                self.current_level, 0, 0, 0,
            )

            # 成就系统：检测新解锁的成就（失败也可能触发累积类成就）
            self._check_achievements()

            self.state = 'game_over'

    # ── Update ──

    def update(self, dt):
        # 商店提示倒计时（任何状态下都更新）
        if self.shop_toast_timer > 0:
            self.shop_toast_timer -= dt
            if self.shop_toast_timer <= 0:
                self.shop_toast = None
                self.shop_toast_timer = 0

        # 升级防抖计时器
        if self._upgrade_cooldown > 0:
            self._upgrade_cooldown = max(0, self._upgrade_cooldown - dt)

        # 成就解锁通知队列（任何状态下都更新）
        self.ach_notify_queue.update(dt)

        # 签到面板动画更新
        self.checkin_ui.update(dt)

        # 场景级 update（如调试面板的消息倒计时）
        scene = self._get_scene(self.state)
        if hasattr(scene, 'update'):
            scene.update(dt)

        if self.state != 'playing':
            return

        # Timer
        self.level_timer -= dt
        if self.level_timer <= 0:
            self.level_timer = 0
            self._end_level()
            return

        # Speed boost timer
        if self.speed_boost_timer > 0:
            self.speed_boost_timer -= dt
            if self.speed_boost_timer <= 0:
                self.speed_boost_timer = 0
                for ant in self.player_ants:
                    ant.speed /= 2.0

        # Update player ants
        for ant in self.player_ants:
            self._update_ant(ant, dt, is_player=True)

        # Update AI ants
        for ant in self.ai_ants:
            self._update_ant(ant, dt, is_player=False)

        # Combat: check collisions between player and AI ants
        self._check_combat()

        # Update floating texts
        for ft in self.floating_texts:
            ft.update(dt)
        self.floating_texts = [ft for ft in self.floating_texts if ft.alive]

    def _update_ant(self, ant, dt, is_player):
        if ant.state == Ant.STATE_STUNNED:
            ant.stun_timer -= dt
            if ant.stun_timer <= 0:
                ant.state = Ant.STATE_IDLE
            return

        if ant.state == Ant.STATE_IDLE:
            alive_sweets = [s for s in self.sweets if s.alive]
            if alive_sweets:
                ant.target_sweet = min(alive_sweets, key=lambda s: math.hypot(s.x - ant.x, s.y - ant.y))
                ant.state = Ant.STATE_MOVING_TO_SWEET
            return

        if ant.state == Ant.STATE_MOVING_TO_SWEET:
            if ant.target_sweet is None or not ant.target_sweet.alive:
                ant.state = Ant.STATE_IDLE
                return

            tx, ty = _get_sweet_edge_pos(ant.target_sweet, ant.x, ant.y)
            eat_mult = ant.get_eat_speed_mult(self.level_data['terrain'])
            arrived = ant.move_toward(tx, ty, dt, speed_mult=1.0)

            if arrived:
                ant.state = Ant.STATE_EATING
                ant.eat_timer = 0.0
            return

        if ant.state == Ant.STATE_EATING:
            if ant.target_sweet is None or not ant.target_sweet.alive:
                ant.state = Ant.STATE_IDLE
                return

            if ant.is_storage_full():
                grinder = self.player_grinder if is_player else self.ai_grinder
                ant.state = Ant.STATE_RETURNING
                ant.target_sweet = None
                return

            ant.eat_timer += dt
            eat_mult = ant.get_eat_speed_mult(self.level_data['terrain'])
            # 采集速度随搬运等级提升：每级+1.5%，保证装满时间不随搬运量膨胀
            lv = ant.carry_level
            carry_speed_boost = 1.0 + lv * 0.015 + (lv * lv) * 0.00005
            interval = 1.0 / (eat_mult * carry_speed_boost)

            if ant.eat_timer >= interval:
                ant.eat_timer = 0.0
                destroyed = ant.target_sweet.take_damage()
                ant.storage += 1
                ant.last_sweet_coin_per = ant.target_sweet.coin_per

                # 星级系统：玩家收集的HP计入统计
                if is_player:
                    self.collected_hp += 1

                sweet_color = SWEET_COLORS.get(ant.target_sweet.sweet_type, (100, 255, 100))
                self.floating_texts.append(
                    FloatingText("+1", ant.x + random.randint(-5, 5), ant.y - 18,
                                 sweet_color, 0.7, 16))
            return

        if ant.state == Ant.STATE_RETURNING:
            grinder = self.player_grinder if is_player else self.ai_grinder
            arrived = ant.move_toward(grinder.x, grinder.y, dt, speed_mult=1.0)

            if arrived:
                coin_per = ant.last_sweet_coin_per
                coins_earned = ant.storage * coin_per
                if self.double_income_active and is_player:
                    coins_earned *= 2
                    self.double_income_active = False

                if is_player:
                    self.level_coins += coins_earned
                    self.floating_texts.append(
                        FloatingText(f"+{coins_earned}金币", grinder.x, grinder.y - 35,
                                     (255, 230, 50), 1.5, 28))
                else:
                    self.ai_coins += coins_earned
                    self.floating_texts.append(
                        FloatingText(f"+{coins_earned}", grinder.x, grinder.y + 15,
                                     (255, 120, 120), 1.0, 18))
                ant.storage = 0
                ant.state = Ant.STATE_IDLE

    def _check_combat(self):
        """检测敌我蚂蚁碰撞，触发击退/僵直/抢夺（PRD v2.0 分级冷却机制）"""
        COMBAT_RANGE = 30
        # 分级冷却时间（秒）
        KNOCKBACK_COOLDOWN = 0.5
        STUN_COOLDOWN = 1.0
        STEAL_COOLDOWN = 0.8
        STUN_IMMUNE_PERIOD = 0.5  # 被僵直后的免疫期

        current_time = pygame.time.get_ticks() / 1000.0

        for p_ant in self.player_ants:
            if p_ant.state == Ant.STATE_STUNNED:
                continue
            for a_ant in self.ai_ants:
                if a_ant.state == Ant.STATE_STUNNED:
                    continue
                dist = math.hypot(p_ant.x - a_ant.x, p_ant.y - a_ant.y)
                if dist > COMBAT_RANGE:
                    continue

                p_id = p_ant.ant_id
                a_id = a_ant.ant_id

                # ── 玩家 → AI 方向 ──

                # 击退（冷却0.5秒）
                kb = p_ant.has_knockback()
                if kb > 0 and random.random() < kb:
                    last_kb = p_ant._last_knockback_time.get(a_id, 0)
                    if current_time - last_kb >= KNOCKBACK_COOLDOWN:
                        p_ant._last_knockback_time[a_id] = current_time
                        dx = a_ant.x - p_ant.x
                        dy = a_ant.y - p_ant.y
                        d = max(1, math.hypot(dx, dy))
                        push = 60
                        a_ant.x += dx / d * push
                        a_ant.y += dy / d * push
                        a_ant.x = max(10, min(SCREEN_WIDTH - 10, a_ant.x))
                        a_ant.y = max(10, min(SCREEN_HEIGHT - 10, a_ant.y))
                        self.floating_texts.append(
                            FloatingText("击退!", a_ant.x, a_ant.y - 20,
                                         (255, 180, 50), 0.6, 14))

                # 僵直（冷却1.0秒 + 被动方0.5秒免疫期）
                sc = p_ant.has_stun_chance()
                if sc > 0 and random.random() < sc:
                    last_stun = p_ant._last_stun_time.get(a_id, 0)
                    if (current_time - last_stun >= STUN_COOLDOWN
                            and current_time < a_ant._stun_immune_until):
                        pass  # 冰直免疫期内，跳过
                    elif current_time - last_stun >= STUN_COOLDOWN:
                        p_ant._last_stun_time[a_id] = current_time
                        a_ant.stun()
                        a_ant._stun_immune_until = current_time + STUN_IMMUNE_PERIOD

                # 抢夺（冷却0.8秒）
                steal = p_ant.has_steal()
                if steal > 0 and a_ant.storage > 0 and random.random() < steal:
                    last_steal = p_ant._last_steal_time.get(a_id, 0)
                    if current_time - last_steal >= STEAL_COOLDOWN:
                        p_ant._last_steal_time[a_id] = current_time
                        stolen = min(a_ant.storage, max(1, a_ant.storage // 3))
                        a_ant.storage -= stolen
                        p_ant.storage = min(p_ant.max_storage, p_ant.storage + stolen)
                        self.floating_texts.append(
                            FloatingText(f"抢夺x{stolen}", a_ant.x, a_ant.y - 25,
                                         (255, 100, 200), 0.8, 14))

                # ── AI → 玩家 方向 ──

                # 击退（冷却0.5秒）
                kb2 = a_ant.has_knockback()
                if kb2 > 0 and random.random() < kb2:
                    last_kb2 = a_ant._last_knockback_time.get(p_id, 0)
                    if current_time - last_kb2 >= KNOCKBACK_COOLDOWN:
                        a_ant._last_knockback_time[p_id] = current_time
                        dx = p_ant.x - a_ant.x
                        dy = p_ant.y - a_ant.y
                        d = max(1, math.hypot(dx, dy))
                        push = 60
                        p_ant.x += dx / d * push
                        p_ant.y += dy / d * push
                        p_ant.x = max(10, min(SCREEN_WIDTH - 10, p_ant.x))
                        p_ant.y = max(10, min(SCREEN_HEIGHT - 10, p_ant.y))

                # 僵直（冷却1.0秒 + 被动方0.5秒免疫期）
                sc2 = a_ant.has_stun_chance()
                if sc2 > 0 and random.random() < sc2:
                    last_stun2 = a_ant._last_stun_time.get(p_id, 0)
                    if (current_time - last_stun2 >= STUN_COOLDOWN
                            and current_time < p_ant._stun_immune_until):
                        pass
                    elif current_time - last_stun2 >= STUN_COOLDOWN:
                        a_ant._last_stun_time[p_id] = current_time
                        p_ant.stun()
                        p_ant._stun_immune_until = current_time + STUN_IMMUNE_PERIOD

    def _apply_item(self, item_name):
        """使用道具"""
        if item_name == '加速药水':
            if self.speed_boost_timer > 0:
                # 已在加速中，仅刷新持续时间，不叠加倍率
                self.speed_boost_timer = 10.0
                self.floating_texts.append(
                    FloatingText("加速效果已刷新! (10秒)", SCREEN_WIDTH // 2, 100,
                                 (100, 200, 255), 2.0, 22))
            else:
                for ant in self.player_ants:
                    ant.speed *= 2.0
                self.speed_boost_timer = 10.0
                self.floating_texts.append(
                    FloatingText("加速药水生效! (10秒)", SCREEN_WIDTH // 2, 100,
                                 (100, 200, 255), 2.0, 22))
        elif item_name == '双倍收益券':
            self.double_income_active = True
            self.floating_texts.append(
                FloatingText("下次交付双倍!", SCREEN_WIDTH // 2, 100,
                             (255, 200, 50), 2.0, 22))
        elif item_name == '干扰粉尘':
            for ant in self.ai_ants:
                ant.stun()
                ant.stun_timer = 2.0
            self.floating_texts.append(
                FloatingText("干扰粉尘生效!", SCREEN_WIDTH // 2, 100,
                             (255, 100, 100), 2.0, 22))

    # ── Drawing ──

    def draw(self):
        scene = self._get_scene(self.state)
        scene.draw(self.screen)

        # 标题/关卡选择页商店浮层
        if self.shop_active:
            self.shop_ui.battle_mode = False
            self.shop_ui.draw(self.screen, *pygame.mouse.get_pos(),
                              self.sm, self.team, self.total_coins, 0, {})

        # 任务面板浮层
        if self.task_panel_active:
            tasks_data = self._get_task_data()
            self.task_ui.draw(self.screen, *pygame.mouse.get_pos(), tasks_data)

        # 成就面板浮层
        if self.achievement_panel_active:
            self.achievement_ui.draw(self.screen, *pygame.mouse.get_pos(), self.sm)

        # 签到面板浮层
        if self.checkin_panel_active:
            checkin_data = self.sm.get_checkin_data()
            can_checkin = self.sm.can_checkin_today()
            self.checkin_ui.draw(self.screen, *pygame.mouse.get_pos(),
                                 checkin_data, can_checkin)

        # 商店提示（任何状态）
        if self.shop_toast and self.shop_toast_timer > 0:
            self._draw_shop_toast()

        # 成就解锁通知（任何状态，绘制在最顶层）
        self.ach_notify_queue.draw(self.screen)

    def _draw_shop_toast(self):
        """商店购买/升级成功提示（半透明胶囊）"""
        if not self.shop_toast or self.shop_toast_timer <= 0:
            return
        font = font_helper.get_font(18)
        txt = font.render(self.shop_toast, True, WHITE)
        tw, th = txt.get_size()
        pad = 10
        toast_w = tw + pad * 2
        toast_h = th + pad * 2
        toast_x = (SCREEN_WIDTH - toast_w) // 2
        toast_y = (SCREEN_HEIGHT - 520) // 2 - toast_h - 10
        alpha = min(255, int(self.shop_toast_timer / 1.5 * 255))
        toast_surf = pygame.Surface((toast_w, toast_h), pygame.SRCALPHA)
        pygame.draw.rect(toast_surf, (50, 140, 60, alpha), (0, 0, toast_w, toast_h), border_radius=toast_h // 2)
        txt_a = min(255, alpha + 60)
        txt_surf = font.render(self.shop_toast, True, (255, 255, 255))
        txt_surf.set_alpha(txt_a)
        toast_surf.blit(txt_surf, (pad, pad))
        self.screen.blit(toast_surf, (toast_x, toast_y))


# ── Main ──

if __name__ == '__main__':
    game = GameState()
    game.run()
