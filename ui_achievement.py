"""成就面板UI：5大维度Tab切换、成就列表、进度条、领取按钮"""

import pygame
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    TEXT_COLOR, WHITE, GRAY,
    ACCENT_BLUE, ACCENT_GOLD, CARD_BG, CARD_BORDER,
    BTN_HOVER,
)
from ui_elements import draw_card, draw_button, draw_progress_bar, draw_text_centered
from achievements_data import (
    ACHIEVE_CATEGORIES, ACHIEVEMENTS_BY_CATEGORY,
    evaluate_achievements, get_total_progress,
)
import font_helper


# 成就状态颜色
COLOR_LOCKED = (140, 140, 150)       # 未解锁：灰色
COLOR_UNLOCKED = ACCENT_GOLD         # 已解锁：金色
COLOR_CLAIMED = (100, 170, 100)      # 已领取：绿色
COLOR_REWARD = ACCENT_GOLD           # 奖励金币色


class AchievementUI:
    """成就面板"""

    def __init__(self):
        self.tab = 0  # 0-4 对应 5大维度
        self.scroll_y = 0
        self._overlay = None

    def draw(self, screen, mx, my, sm):
        """
        绘制成就面板。
        sm: SaveManager 实例
        返回: (panel_rect, close_rect, claim_buttons)
        """
        # 遮罩层
        if self._overlay is None:
            self._overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            self._overlay.fill((0, 0, 0, 140))
        screen.blit(self._overlay, (0, 0))

        # 面板
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

        # 标题
        font_title = font_helper.get_font(24)
        title = font_title.render("成就", True, ACCENT_GOLD)
        screen.blit(title, (panel.centerx - title.get_width() // 2, panel.y + 10))

        # 总进度
        unlocked, total, claimed = get_total_progress(sm)
        font_sm = font_helper.get_font(14)
        progress_text = f"总进度: {unlocked}/{total}  已领取: {claimed}"
        prog_txt = font_sm.render(progress_text, True, TEXT_COLOR)
        screen.blit(prog_txt, (panel.centerx - prog_txt.get_width() // 2, panel.y + 38))

        # Tab 切换（5个维度，均匀分布）
        font_tab = font_helper.get_font(14)
        tab_w = panel.w // len(ACHIEVE_CATEGORIES)
        for i, cat_name in enumerate(ACHIEVE_CATEGORIES):
            tab_rect = pygame.Rect(px + i * tab_w, panel.y + 58, tab_w, 28)
            is_active = (self.tab == i)
            hover_tab = tab_rect.collidepoint(mx, my)
            if is_active:
                tab_color = ACCENT_BLUE
            elif hover_tab:
                tab_color = BTN_HOVER
            else:
                tab_color = CARD_BORDER
            pygame.draw.rect(screen, tab_color, tab_rect, border_radius=5)
            tab_txt = font_tab.render(cat_name, True, WHITE if is_active else TEXT_COLOR)
            screen.blit(tab_txt, (tab_rect.centerx - tab_txt.get_width() // 2,
                                  tab_rect.centery - tab_txt.get_height() // 2))

        # 内容区域
        content_y = panel.y + 92
        content_rect = pygame.Rect(px + 10, content_y, pw - 20, ph - 108)

        cat_name = ACHIEVE_CATEGORIES[self.tab]
        achievements = ACHIEVEMENTS_BY_CATEGORY.get(cat_name, [])
        stats = evaluate_achievements(sm)
        claim_buttons = self._draw_achievement_list(screen, content_rect, mx, my,
                                                     achievements, stats)

        return panel, close_rect, claim_buttons

    def _draw_achievement_list(self, screen, rect, mx, my, achievements, stats):
        """绘制成就列表，返回可点击的领取按钮列表"""
        if not achievements:
            draw_text_centered(screen, "暂无成就", font_helper.get_font(18),
                               GRAY, rect.centerx, rect.y + 20)
            return []

        font_name = font_helper.get_font(16)
        font_desc = font_helper.get_font(13)
        font_sm = font_helper.get_font(12)
        font_icon = font_helper.get_font(22)

        item_h = 72
        item_gap = 6
        scroll = self.scroll_y
        claim_buttons = []

        for i, ach in enumerate(achievements):
            y = rect.y + i * (item_h + item_gap) - scroll
            if y + item_h < rect.y or y > rect.bottom:
                continue

            aid = ach['id']
            st = stats.get(aid, {'current': 0, 'unlocked': False, 'claimed': False})
            current = st['current']
            unlocked = st['unlocked']
            claimed = st['claimed']
            target = ach['threshold']

            card_rect = pygame.Rect(rect.x, y, rect.width, item_h)

            # 卡片背景 — 根据状态区分
            if claimed:
                bg = (230, 245, 230)  # 浅绿底
            elif unlocked:
                bg = (255, 248, 220)  # 浅金底
            else:
                bg = CARD_BG
            pygame.draw.rect(screen, bg, card_rect, border_radius=8)
            pygame.draw.rect(screen, CARD_BORDER, card_rect, 1, border_radius=8)

            # 图标区（左侧40x40）
            icon_rect = pygame.Rect(card_rect.x + 8, card_rect.y + 16, 40, 40)
            if claimed:
                icon_bg = COLOR_CLAIMED
            elif unlocked:
                icon_bg = (218, 165, 32, 60)
            else:
                icon_bg = (180, 180, 190)
            pygame.draw.rect(screen, icon_bg, icon_rect, border_radius=8)
            icon_txt = font_icon.render(ach['icon_text'], True, WHITE)
            screen.blit(icon_txt, (icon_rect.centerx - icon_txt.get_width() // 2,
                                   icon_rect.centery - icon_txt.get_height() // 2))

            # 名称
            name_color = COLOR_CLAIMED if claimed else (TEXT_COLOR if unlocked else COLOR_LOCKED)
            name_txt = font_name.render(ach['name'], True, name_color)
            screen.blit(name_txt, (card_rect.x + 56, card_rect.y + 6))

            # 描述
            desc_color = (120, 120, 140) if unlocked else COLOR_LOCKED
            desc_txt = font_desc.render(ach['desc'], True, desc_color)
            screen.blit(desc_txt, (card_rect.x + 56, card_rect.y + 26))

            # 进度条
            ratio = min(1.0, current / target) if target > 0 else 0
            bar_x = card_rect.x + 56
            bar_w = 200
            if claimed:
                bar_color = COLOR_CLAIMED
            elif unlocked:
                bar_color = ACCENT_GOLD
            else:
                bar_color = ACCENT_BLUE
            draw_progress_bar(screen, bar_x, card_rect.y + 50, bar_w, 8, ratio, bar_color)

            # 进度文字
            progress_str = f"{min(current, target)}/{target}"
            prog_txt = font_sm.render(progress_str, True, TEXT_COLOR if not claimed else COLOR_CLAIMED)
            screen.blit(prog_txt, (bar_x + bar_w + 6, card_rect.y + 47))

            # 奖励 + 领取按钮
            reward_text = f"+{ach['rewards']['coins']}G"
            reward_txt = font_sm.render(reward_text, True, COLOR_REWARD if not claimed else COLOR_CLAIMED)
            screen.blit(reward_txt, (card_rect.right - 100, card_rect.y + 6))

            btn_rect = pygame.Rect(card_rect.right - 68, card_rect.y + 40, 58, 26)
            if claimed:
                draw_button(screen, btn_rect, "✓", font_sm,
                            color=(100, 140, 100), disabled=True)
            elif unlocked:
                hover = btn_rect.collidepoint(mx, my)
                draw_button(screen, btn_rect, "领取", font_sm,
                            color=ACCENT_BLUE, hover=hover)
                claim_buttons.append((btn_rect, aid))
            else:
                draw_button(screen, btn_rect, "领取", font_sm, disabled=True)

        # 滚动提示
        total_h = len(achievements) * (item_h + item_gap)
        if total_h > rect.height:
            hint = font_sm.render("滚轮翻页", True, GRAY)
            screen.blit(hint, (rect.centerx - hint.get_width() // 2, rect.bottom - 15))

        return claim_buttons

    def handle_click(self, mx, my, sm):
        """处理点击。返回 action 或 None。"""
        pw, ph = 600, 520
        px = (SCREEN_WIDTH - pw) // 2
        py = (SCREEN_HEIGHT - ph) // 2
        panel = pygame.Rect(px, py, pw, ph)

        # Tab 切换
        tab_w = panel.w // len(ACHIEVE_CATEGORIES)
        for i in range(len(ACHIEVE_CATEGORIES)):
            tab_rect = pygame.Rect(px + i * tab_w, panel.y + 58, tab_w, 28)
            if tab_rect.collidepoint(mx, my):
                self.tab = i
                self.scroll_y = 0
                return None

        # 内容区领取按钮点击
        content_rect = pygame.Rect(px + 10, py + 92, pw - 20, ph - 108)
        cat_name = ACHIEVE_CATEGORIES[self.tab]
        achievements = ACHIEVEMENTS_BY_CATEGORY.get(cat_name, [])
        stats = evaluate_achievements(sm)

        item_h = 72
        item_gap = 6

        for i, ach in enumerate(achievements):
            y = content_rect.y + i * (item_h + item_gap) - self.scroll_y
            if y + item_h < content_rect.y or y > content_rect.bottom:
                continue

            aid = ach['id']
            st = stats.get(aid, {})
            if not st.get('unlocked', False) or st.get('claimed', False):
                continue

            card_rect = pygame.Rect(content_rect.x, y, content_rect.width, item_h)
            btn_rect = pygame.Rect(card_rect.right - 68, card_rect.y + 40, 58, 26)
            if btn_rect.collidepoint(mx, my):
                return ('claim_achievement', aid)

        return None

    def scroll(self, dy):
        """滚轮滚动"""
        self.scroll_y = max(0, self.scroll_y - dy * 30)
