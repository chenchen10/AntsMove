"""商店系统：蚂蚁购买页、蚂蚁多属性升级页、本局道具页"""

import pygame
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, TEXT_COLOR, WHITE, GRAY,
    ACCENT_BLUE, ACCENT_RED, ACCENT_GOLD, CARD_BG, CARD_BORDER, BG_COLOR,
    BTN_HOVER,
)
from ants_data import (
    ANTS, ANT_BY_ID, get_upgrade_cost, get_carry_capacity, get_speed, get_defense,
    MAX_ATTR_LEVEL,
)
from items_data import ITEMS, ITEM_BY_NAME
from ui_elements import draw_card, draw_button, draw_progress_bar, draw_text_centered
import font_helper


class ShopUI:
    """商店面板"""

    def __init__(self):
        self.tab = 0  # 0=蚂蚁购买, 1=蚂蚁升级, 2=本局道具
        self.scroll_y = 0
        self.selected_ant = None
        self.tab_names = ['蚂蚁购买', '蚂蚁升级', '本局道具']
        self.battle_mode = False
        self.upgrade_gear = 1  # 升级档位: 1, 10, -1(升满)

    def draw(self, screen, mx, my, save_manager, team, total_coins, level_coins, item_uses=None):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        screen.blit(overlay, (0, 0))

        pw, ph = 600, 520
        px = (SCREEN_WIDTH - pw) // 2
        py = (SCREEN_HEIGHT - ph) // 2
        panel = pygame.Rect(px, py, pw, ph)
        draw_card(screen, panel, bg_color=CARD_BG, border_color=CARD_BORDER,
                  shadow=True, radius=14)

        # 关闭按钮
        close_rect = pygame.Rect(panel.right - 30, panel.y + 6, 24, 24)
        hover_close = close_rect.collidepoint(mx, my)
        close_color = (255, 100, 100) if hover_close else (200, 80, 80)
        pygame.draw.rect(screen, close_color, close_rect, border_radius=4)
        close_txt = font_helper.get_font(18).render("x", True, WHITE)
        screen.blit(close_txt, (close_rect.centerx - close_txt.get_width() // 2,
                                close_rect.centery - close_txt.get_height() // 2))

        font_title = font_helper.get_font(24)
        font_sm = font_helper.get_font(16)
        title = font_title.render("商店", True, (255, 200, 100))
        screen.blit(title, (panel.centerx - title.get_width() // 2, panel.y + 10))

        coins_txt = font_sm.render(f"累计金币: {total_coins}  |  关卡金币: {level_coins}", True, ACCENT_GOLD)
        screen.blit(coins_txt, (panel.centerx - coins_txt.get_width() // 2, panel.y + 38))

        # 标签页
        tab_w = panel.w // 3
        for i, name in enumerate(self.tab_names):
            if self.battle_mode and i < 2:
                continue
            tab_rect = pygame.Rect(px + i * tab_w, panel.y + 58, tab_w, 30)
            is_active = (self.tab == i) if not self.battle_mode else (i == 2)
            hover_tab = tab_rect.collidepoint(mx, my)
            if is_active:
                tab_color = ACCENT_BLUE
            elif hover_tab:
                tab_color = BTN_HOVER
            else:
                tab_color = CARD_BORDER
            pygame.draw.rect(screen, tab_color, tab_rect, border_radius=6)
            tab_txt = font_sm.render(name, True, WHITE if is_active else TEXT_COLOR)
            screen.blit(tab_txt, (tab_rect.centerx - tab_txt.get_width() // 2,
                                  tab_rect.centery - tab_txt.get_height() // 2))

        content_y = panel.y + 95
        content_rect = pygame.Rect(px + 10, content_y, pw - 20, ph - 110)

        active_tab = 2 if self.battle_mode else self.tab
        if active_tab == 0:
            self._draw_purchase_tab(screen, content_rect, mx, my, save_manager, total_coins)
        elif active_tab == 1:
            self._draw_upgrade_tab(screen, content_rect, mx, my, save_manager, total_coins)
        else:
            self._draw_items_tab(screen, content_rect, mx, my, level_coins, item_uses)

        return panel, close_rect

    def _draw_purchase_tab(self, screen, rect, mx, my, sm, total_coins):
        """蚂蚁购买页：按种类显示拥有数量和单价"""
        font_sm = font_helper.get_font(14)
        font_md = font_helper.get_font(16)

        item_h = 55
        scroll = self.scroll_y

        for i, ant in enumerate(ANTS):
            y = rect.y + i * (item_h + 3) - scroll
            if y + item_h < rect.y or y > rect.bottom:
                continue

            item_rect = pygame.Rect(rect.x, y, rect.width, item_h)
            count = sm.get_ant_count(ant['id'])
            unlocked = ant['unlock_level'] <= sm.get_max_level() + 1
            can_buy = unlocked and total_coins >= ant['buy_cost']
            hover = item_rect.collidepoint(mx, my) and unlocked

            if not unlocked:
                bg = (230, 230, 230)
            elif hover:
                bg = (210, 230, 255)
            else:
                bg = CARD_BG
            pygame.draw.rect(screen, bg, item_rect, border_radius=6)
            pygame.draw.rect(screen, CARD_BORDER, item_rect, 1, border_radius=6)

            # 名称 + 拥有数量
            name_color = TEXT_COLOR if unlocked else GRAY
            name_str = f"#{ant['id']} {ant['name'][:8]}"
            txt = font_md.render(name_str, True, name_color)
            screen.blit(txt, (item_rect.x + 8, item_rect.y + 5))

            # 拥有数量
            count_color = ACCENT_BLUE if count > 0 else GRAY
            count_txt = font_sm.render(f"x{count}", True, count_color)
            screen.blit(count_txt, (item_rect.x + 8, item_rect.y + 28))

            # 搬运 / 特性
            carry = get_carry_capacity(ant['id'], 0)
            info_txt = font_sm.render(f"搬运:{carry} | {ant['trait_desc'][:10]}", True, (120, 120, 140))
            screen.blit(info_txt, (item_rect.x + 60, item_rect.y + 28))

            # 右侧：价格 + [购买] 按钮
            if not unlocked:
                lock = font_sm.render(f"第{ant['unlock_level']}关解锁", True, GRAY)
                screen.blit(lock, (item_rect.right - 85, item_rect.y + 18))
            else:
                # 价格
                cost_color = ACCENT_GOLD if can_buy else ACCENT_RED
                cost_txt = font_md.render(f"{ant['buy_cost']}G", True, cost_color)
                screen.blit(cost_txt, (item_rect.right - 120, item_rect.y + 5))

                # [购买] 按钮
                btn_buy = pygame.Rect(item_rect.right - 55, item_rect.y + 8, 45, 24)
                draw_button(screen, btn_buy, "+1", font_sm,
                            color=ACCENT_BLUE if can_buy else (80, 80, 90),
                            hover=btn_buy.collidepoint(mx, my), disabled=not can_buy)

        # 滚动提示
        total_h = len(ANTS) * (item_h + 3)
        if total_h > rect.height:
            hint = font_sm.render("滚轮翻页", True, GRAY)
            screen.blit(hint, (rect.centerx - hint.get_width() // 2, rect.bottom - 15))

    def _draw_upgrade_tab(self, screen, rect, mx, my, sm, total_coins):
        """蚂蚁升级页：搬运/速度/防御三个独立属性"""
        font_sm = font_helper.get_font(14)
        font_md = font_helper.get_font(16)

        owned = sm.get_unique_owned_ants()
        if not owned:
            draw_text_centered(screen, "还没有蚂蚁，先去购买吧!", font_sm, GRAY, rect.centerx, rect.y + 20)
            return

        # 左侧列表
        list_w = 160
        list_rect = pygame.Rect(rect.x, rect.y, list_w, rect.height)
        item_h = 36

        for i, ant_id in enumerate(owned):
            ant = ANT_BY_ID[ant_id]
            y = rect.y + i * (item_h + 2) - self.scroll_y
            if y + item_h < rect.y or y > rect.bottom:
                continue

            item_rect = pygame.Rect(rect.x, y, list_w, item_h)
            is_selected = (self.selected_ant == ant_id)
            hover = item_rect.collidepoint(mx, my)

            if is_selected:
                bg = (210, 230, 255)
            elif hover:
                bg = (230, 240, 250)
            else:
                bg = CARD_BG
            pygame.draw.rect(screen, bg, item_rect, border_radius=4)
            pygame.draw.rect(screen, ACCENT_BLUE if is_selected else CARD_BORDER,
                             item_rect, 1, border_radius=4)

            carry_lv = sm.get_ant_attr(ant_id, 'carry')
            txt = font_sm.render(f"#{ant['id']} {ant['name'][:6]} C{carry_lv}", True, TEXT_COLOR)
            screen.blit(txt, (item_rect.x + 4, item_rect.centery - txt.get_height() // 2))

        # 右侧详情
        detail_x = rect.x + list_w + 10
        detail_w = rect.width - list_w - 10

        if self.selected_ant and self.selected_ant in owned:
            ant = ANT_BY_ID[self.selected_ant]
            carry_lv = sm.get_ant_attr(self.selected_ant, 'carry')
            speed_lv = sm.get_ant_attr(self.selected_ant, 'speed')
            defense_lv = sm.get_ant_attr(self.selected_ant, 'defense')

            # 名称
            name_txt = font_md.render(f"#{ant['id']} {ant['name']}", True, TEXT_COLOR)
            screen.blit(name_txt, (detail_x, rect.y + 5))

            # 当前属性
            carry_val = get_carry_capacity(self.selected_ant, carry_lv)
            speed_val = get_speed(self.selected_ant, speed_lv)
            defense_val = get_defense(self.selected_ant, defense_lv)
            stats_lines = [
                f"搬运: {carry_val} (Lv{carry_lv}/{MAX_ATTR_LEVEL})",
                f"速度: {speed_val} (Lv{speed_lv}/{MAX_ATTR_LEVEL})",
                f"防御: {defense_val} (Lv{defense_lv}/{MAX_ATTR_LEVEL})",
            ]
            for j, s in enumerate(stats_lines):
                stxt = font_sm.render(s, True, TEXT_COLOR)
                screen.blit(stxt, (detail_x, rect.y + 30 + j * 20))

            # ── 档位选择器 ──
            gear_y = rect.y + 95
            gear_labels = ['+1', '+10', '升满']
            gear_values = [1, 10, -1]
            gear_btn_w = 52
            gear_btn_h = 26
            gear_gap = 6
            gear_total_w = len(gear_labels) * gear_btn_w + (len(gear_labels) - 1) * gear_gap
            gear_start_x = detail_x + (detail_w - gear_total_w) // 2

            # 判断是否有任何属性已满200级
            all_maxed = (carry_lv >= MAX_ATTR_LEVEL and speed_lv >= MAX_ATTR_LEVEL
                         and defense_lv >= MAX_ATTR_LEVEL)

            self._gear_btn_rects = []
            for gi, (gl, gv) in enumerate(zip(gear_labels, gear_values)):
                gx = gear_start_x + gi * (gear_btn_w + gear_gap)
                gear_rect = pygame.Rect(gx, gear_y, gear_btn_w, gear_btn_h)
                self._gear_btn_rects.append(gear_rect)
                is_active = (self.upgrade_gear == gv)
                hov = gear_rect.collidepoint(mx, my) and not all_maxed
                if all_maxed:
                    g_color = (80, 80, 90)
                elif is_active:
                    g_color = ACCENT_GOLD
                elif hov:
                    g_color = BTN_HOVER
                else:
                    g_color = CARD_BORDER
                draw_button(screen, gear_rect, gl, font_sm,
                            color=g_color, hover=hov,
                            disabled=all_maxed, border_radius=6)

            # ── 三个属性升级按钮 ──
            attrs = [
                ('carry', '搬运', carry_lv, carry_val),
                ('speed', '速度', speed_lv, speed_val),
                ('defense', '防御', defense_lv, defense_val),
            ]
            for j, (attr_key, attr_name, attr_lv, attr_val) in enumerate(attrs):
                btn_y = rect.y + 132 + j * 48

                if attr_lv >= MAX_ATTR_LEVEL:
                    max_txt = font_md.render(f"{attr_name}: 已满级", True, ACCENT_GOLD)
                    screen.blit(max_txt, (detail_x, btn_y + 8))
                    continue

                # 根据档位计算目标等级和总费用
                if self.upgrade_gear == -1:
                    target_lv = MAX_ATTR_LEVEL
                else:
                    target_lv = min(attr_lv + self.upgrade_gear, MAX_ATTR_LEVEL)

                from ants_data import get_total_upgrade_cost
                cost = get_total_upgrade_cost(self.selected_ant, attr_key, attr_lv, target_lv)
                lv_diff = target_lv - attr_lv

                if cost:
                    btn_rect = pygame.Rect(detail_x, btn_y, detail_w, 38)
                    can_upgrade = total_coins >= cost
                    hover = btn_rect.collidepoint(mx, my)
                    if self.upgrade_gear == -1:
                        btn_text = f"{attr_name}升满 ({cost}G)"
                    else:
                        btn_text = f"{attr_name}+{lv_diff} ({cost}G)"
                    draw_button(screen, btn_rect,
                                btn_text, font_md,
                                color=ACCENT_BLUE if can_upgrade else (80, 80, 90),
                                hover=hover, disabled=not can_upgrade)

                    # 进度条
                    bar_y = btn_y + 38
                    draw_progress_bar(screen, detail_x, bar_y, detail_w, 6,
                                      attr_lv / MAX_ATTR_LEVEL, ACCENT_BLUE)
                else:
                    max_txt = font_md.render(f"{attr_name}: 已满级", True, ACCENT_GOLD)
                    screen.blit(max_txt, (detail_x, btn_y + 8))
        else:
            draw_text_centered(screen, "选择一只蚂蚁查看详情", font_sm, GRAY,
                               detail_x + detail_w // 2, rect.y + 20)

    def _draw_items_tab(self, screen, rect, mx, my, level_coins, item_uses=None):
        font_sm = font_helper.get_font(14)
        font_md = font_helper.get_font(16)
        font_lg = font_helper.get_font(18)
        item_uses = item_uses or {}

        draw_text_centered(screen, f"关卡金币: {level_coins}", font_md, ACCENT_GOLD,
                           rect.centerx, rect.y + 5)

        card_h = 80  # 每张卡片高度（含间距）
        for i, item in enumerate(ITEMS):
            name = item["name"]
            cost = item["cost"]
            desc = item["description"]
            tip = item["tip"]
            max_use = item["max_uses"]

            y = rect.y + 35 + i * card_h - self.scroll_y
            # 裁剪：不在可见区域内的跳过
            if y + card_h < rect.y or y > rect.bottom:
                continue

            item_rect = pygame.Rect(rect.x, y, rect.width, 70)
            used = item_uses.get(name, 0)
            remain = max_use - used
            no_uses = remain <= 0
            no_coins = level_coins < cost
            can_buy = not no_uses and not no_coins
            hover = item_rect.collidepoint(mx, my)

            # 背景色：正常/不可用
            if no_uses:
                bg = (220, 220, 220)
            elif no_coins:
                bg = (240, 235, 230)
            elif hover:
                bg = (210, 230, 255)
            else:
                bg = CARD_BG
            pygame.draw.rect(screen, bg, item_rect, border_radius=8)
            pygame.draw.rect(screen, CARD_BORDER, item_rect, 1, border_radius=8)

            # 名称 + 价格
            name_color = TEXT_COLOR if can_buy else GRAY
            name_txt = font_md.render(f"{name}", True, name_color)
            screen.blit(name_txt, (item_rect.x + 12, item_rect.y + 6))

            cost_color = ACCENT_RED if no_coins else ACCENT_GOLD
            cost_txt = font_md.render(f"{cost}G", True, cost_color if can_buy else GRAY)
            screen.blit(cost_txt, (item_rect.x + 12 + name_txt.get_width() + 8, item_rect.y + 6))

            # 描述
            desc_txt = font_sm.render(desc, True, (120, 120, 140))
            screen.blit(desc_txt, (item_rect.x + 12, item_rect.y + 26))

            # 使用时机提示（12pt浅灰色小字）
            font_tip = font_helper.get_font(12)
            tip_txt = font_tip.render(tip, True, (160, 160, 160))
            screen.blit(tip_txt, (item_rect.x + 12, item_rect.y + 44))

            # 剩余次数（放大至18pt白色加粗）
            remain_str = f"剩余{remain}/{max_use}"
            if no_uses:
                remain_color = ACCENT_RED
                remain_txt = font_lg.render(remain_str, True, remain_color)
                # 次数耗尽：显示「次数已用完」
                hint_txt = font_sm.render("次数已用完", True, ACCENT_RED)
                screen.blit(remain_txt, (item_rect.right - remain_txt.get_width() - 12, item_rect.y + 6))
                screen.blit(hint_txt, (item_rect.right - hint_txt.get_width() - 12, item_rect.y + 30))
            else:
                remain_color = WHITE if can_buy else ACCENT_RED
                remain_txt = font_lg.render(remain_str, True, remain_color)
                screen.blit(remain_txt, (item_rect.right - remain_txt.get_width() - 12, item_rect.y + 6))
                if no_coins:
                    # 金币不足提示
                    hint_txt = font_sm.render("金币不足", True, ACCENT_RED)
                    screen.blit(hint_txt, (item_rect.right - hint_txt.get_width() - 12, item_rect.y + 30))

        # 滚动提示（道具数 > 可视区域时）
        total_h = len(ITEMS) * card_h
        visible_h = rect.height - 35
        if total_h > visible_h:
            hint = font_sm.render("滚轮翻页", True, GRAY)
            screen.blit(hint, (rect.centerx - hint.get_width() // 2, rect.bottom - 15))

    def handle_click(self, mx, my, save_manager, team, total_coins, level_coins, item_uses=None):
        pw, ph = 600, 520
        px = (SCREEN_WIDTH - pw) // 2
        py = (SCREEN_HEIGHT - ph) // 2
        panel = pygame.Rect(px, py, pw, ph)

        # 标签页切换
        tab_w = panel.w // 3
        for i in range(3):
            if self.battle_mode and i < 2:
                continue
            tab_rect = pygame.Rect(px + i * tab_w, panel.y + 58, tab_w, 30)
            if tab_rect.collidepoint(mx, my):
                self.tab = i
                self.scroll_y = 0
                self.selected_ant = None
                self.upgrade_gear = 1
                return None

        if self.battle_mode:
            return self._click_items(mx, my, level_coins, item_uses)

        if self.tab == 0:
            return self._click_purchase(mx, my, save_manager, total_coins)
        elif self.tab == 1:
            return self._click_upgrade(mx, my, save_manager, total_coins)
        elif self.tab == 2:
            return self._click_items(mx, my, level_coins, item_uses)
        return None

    def _click_purchase(self, mx, my, sm, total_coins):
        rect = self._get_content_rect()
        item_h = 55
        for i, ant in enumerate(ANTS):
            y = rect.y + i * (item_h + 3) - self.scroll_y
            if y + item_h < rect.y or y > rect.bottom:
                continue
            item_rect = pygame.Rect(rect.x, y, rect.width, item_h)
            if not item_rect.collidepoint(mx, my):
                continue
            if ant['unlock_level'] > sm.get_max_level() + 1:
                return None
            if total_coins < ant['buy_cost']:
                return None
            # 检查是否点击了 [购买] 按钮区域（右侧55px范围内）
            if mx >= item_rect.right - 55:
                return ('buy_ant', ant['id'])
            # 点击整行也可购买
            return ('buy_ant', ant['id'])
        return None

    def _click_upgrade(self, mx, my, sm, total_coins):
        rect = self._get_content_rect()
        list_w = 160
        item_h = 36
        owned = sm.get_unique_owned_ants()

        # 左侧列表选择
        for i, ant_id in enumerate(owned):
            y = rect.y + i * (item_h + 2) - self.scroll_y
            if y + item_h < rect.y or y > rect.bottom:
                continue
            item_rect = pygame.Rect(rect.x, y, list_w, item_h)
            if item_rect.collidepoint(mx, my):
                self.selected_ant = ant_id
                self.scroll_y = 0
                return None

        # 档位选择器点击
        if hasattr(self, '_gear_btn_rects'):
            gear_values = [1, 10, -1]
            for gi, gear_rect in enumerate(self._gear_btn_rects):
                if gear_rect.collidepoint(mx, my):
                    self.upgrade_gear = gear_values[gi]
                    return None

        # 右侧升级按钮（支持批量）
        if self.selected_ant and self.selected_ant in owned:
            detail_x = rect.x + list_w + 10
            detail_w = rect.width - list_w - 10

            attrs = ['carry', 'speed', 'defense']
            for j, attr_key in enumerate(attrs):
                btn_y = rect.y + 132 + j * 48
                btn_rect = pygame.Rect(detail_x, btn_y, detail_w, 38)
                if btn_rect.collidepoint(mx, my):
                    attr_lv = sm.get_ant_attr(self.selected_ant, attr_key)
                    if attr_lv >= MAX_ATTR_LEVEL:
                        return None
                    # 根据档位计算目标等级
                    if self.upgrade_gear == -1:
                        target_lv = MAX_ATTR_LEVEL
                    else:
                        target_lv = min(attr_lv + self.upgrade_gear, MAX_ATTR_LEVEL)
                    from ants_data import get_total_upgrade_cost
                    cost = get_total_upgrade_cost(self.selected_ant, attr_key, attr_lv, target_lv)
                    if cost and total_coins >= cost:
                        return ('upgrade_attr_batch', (self.selected_ant, attr_key, target_lv, cost))
        return None

    def _click_items(self, mx, my, level_coins, item_uses=None):
        rect = self._get_content_rect()
        item_uses = item_uses or {}
        card_h = 80
        for i, item in enumerate(ITEMS):
            name = item["name"]
            cost = item["cost"]
            max_use = item["max_uses"]
            y = rect.y + 35 + i * card_h - self.scroll_y
            item_rect = pygame.Rect(rect.x, y, rect.width, 70)
            if item_rect.collidepoint(mx, my):
                used = item_uses.get(name, 0)
                if used < max_use and level_coins >= cost:
                    return ('buy_item', (name, cost))
        return None

    def _get_content_rect(self):
        pw, ph = 600, 520
        px = (SCREEN_WIDTH - pw) // 2
        py = (SCREEN_HEIGHT - ph) // 2
        return pygame.Rect(px + 10, py + 95, pw - 20, ph - 110)

    def scroll(self, dy):
        self.scroll_y = max(0, self.scroll_y - dy * 30)

    def close(self):
        """关闭商店时重置档位"""
        self.upgrade_gear = 1
