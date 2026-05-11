"""任务面板UI：每日/每周任务列表、进度条、领取按钮"""

import pygame
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    TEXT_COLOR, WHITE, GRAY,
    ACCENT_BLUE, ACCENT_GOLD, CARD_BG, CARD_BORDER,
    BTN_HOVER,
)
from ui_elements import draw_card, draw_button, draw_progress_bar, draw_text_centered
import font_helper


class TaskUI:
    """任务面板"""

    def __init__(self):
        self.tab = 0          # 0=每日, 1=每周
        self.scroll_y = 0
        self.tab_names = ['每日', '每周']
        # 缓存遮罩层 surface，避免每帧重建
        self._overlay = None

    def draw(self, screen, mx, my, tasks_data):
        """
        绘制任务面板。
        tasks_data: {'daily': [...], 'weekly': [...]}
        每个任务: {'id', 'desc', 'current', 'target', 'reward', 'claimed'}
        返回: (panel_rect, close_rect, claim_buttons)
        """
        # 遮罩层（缓存复用，避免每帧重建 SRCALPHA surface）
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
        title_text = "每日任务" if self.tab == 0 else "每周任务"
        title = font_title.render(title_text, True, ACCENT_GOLD)
        screen.blit(title, (panel.centerx - title.get_width() // 2, panel.y + 10))

        # Tab 切换
        font_sm = font_helper.get_font(16)
        tab_w = panel.w // 2
        for i, name in enumerate(self.tab_names):
            tab_rect = pygame.Rect(px + i * tab_w, panel.y + 58, tab_w, 30)
            is_active = (self.tab == i)
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

        # 内容区域
        content_y = panel.y + 95
        content_rect = pygame.Rect(px + 10, content_y, pw - 20, ph - 110)
        tasks = tasks_data.get('daily' if self.tab == 0 else 'weekly', [])
        claim_buttons = self._draw_task_list(screen, content_rect, mx, my, tasks)

        return panel, close_rect, claim_buttons

    def _draw_task_list(self, screen, rect, mx, my, tasks):
        """绘制任务列表，返回可点击的领取按钮列表"""
        if not tasks:
            draw_text_centered(screen, "暂无任务", font_helper.get_font(18),
                               GRAY, rect.centerx, rect.y + 20)
            return []

        font_desc = font_helper.get_font(16)
        font_sm = font_helper.get_font(14)

        item_h = 72
        item_gap = 6
        scroll = self.scroll_y
        claim_buttons = []

        for i, task in enumerate(tasks):
            y = rect.y + i * (item_h + item_gap) - scroll
            if y + item_h < rect.y or y > rect.bottom:
                continue

            card_rect = pygame.Rect(rect.x, y, rect.width, item_h)
            current = task.get('current', 0)
            target = task.get('target', 1)
            claimed = task.get('claimed', False)
            reward = task.get('reward', 0)
            desc = task.get('desc', '')
            task_id = task.get('id', '')

            # 卡片背景
            bg = CARD_BG
            pygame.draw.rect(screen, bg, card_rect, border_radius=8)
            pygame.draw.rect(screen, CARD_BORDER, card_rect, 1, border_radius=8)

            # 任务描述（截断加"..."）
            display_desc = desc if len(desc) <= 20 else desc[:19] + '...'
            desc_txt = font_desc.render(display_desc, True, TEXT_COLOR)
            screen.blit(desc_txt, (card_rect.x + 12, card_rect.y + 8))

            # 奖励金币图标 + 数值
            coin_txt = font_sm.render(f"+{reward}", True, ACCENT_GOLD)
            screen.blit(coin_txt, (card_rect.right - 50, card_rect.y + 8))

            # 金币小图标（用文字"G"代替）
            g_txt = font_sm.render("G", True, ACCENT_GOLD)
            screen.blit(g_txt, (card_rect.right - 18, card_rect.y + 8))

            # 进度条
            ratio = min(1.0, current / target) if target > 0 else 0
            if claimed:
                bar_color = (150, 200, 150)  # 浅绿色
            elif current >= target:
                bar_color = ACCENT_GOLD
            else:
                bar_color = ACCENT_BLUE
            draw_progress_bar(screen, card_rect.x + 12, card_rect.y + 42,
                              320, 8, ratio, bar_color)

            # 进度文字
            progress_text = f"{current}/{target}"
            prog_txt = font_sm.render(progress_text, True, TEXT_COLOR)
            screen.blit(prog_txt, (card_rect.x + 340, card_rect.y + 38))

            # 领取按钮
            btn_rect = pygame.Rect(card_rect.right - 70, card_rect.y + 38, 60, 28)
            if claimed:
                draw_button(screen, btn_rect, "✓", font_sm,
                            color=(100, 140, 100), disabled=True)
            elif current >= target:
                hover = btn_rect.collidepoint(mx, my)
                draw_button(screen, btn_rect, "领取", font_sm,
                            color=ACCENT_BLUE, hover=hover)
                claim_buttons.append((btn_rect, task_id))
            else:
                draw_button(screen, btn_rect, "领取", font_sm, disabled=True)

        # 滚动提示
        total_h = len(tasks) * (item_h + item_gap)
        if total_h > rect.height:
            hint = font_sm.render("滚轮翻页", True, GRAY)
            screen.blit(hint, (rect.centerx - hint.get_width() // 2, rect.bottom - 15))

        return claim_buttons

    def handle_click(self, mx, my, tasks_data):
        """处理点击。返回 action 或 None。"""
        pw, ph = 600, 520
        px = (SCREEN_WIDTH - pw) // 2
        py = (SCREEN_HEIGHT - ph) // 2
        panel = pygame.Rect(px, py, pw, ph)

        # Tab 切换
        tab_w = panel.w // 2
        for i in range(2):
            tab_rect = pygame.Rect(px + i * tab_w, panel.y + 58, tab_w, 30)
            if tab_rect.collidepoint(mx, my):
                self.tab = i
                self.scroll_y = 0
                return None

        # 内容区领取按钮点击
        content_rect = pygame.Rect(px + 10, py + 95, pw - 20, ph - 110)
        tasks = tasks_data.get('daily' if self.tab == 0 else 'weekly', [])

        font_desc = font_helper.get_font(16)
        font_sm = font_helper.get_font(14)

        item_h = 72
        item_gap = 6

        for i, task in enumerate(tasks):
            y = content_rect.y + i * (item_h + item_gap) - self.scroll_y
            if y + item_h < content_rect.y or y > content_rect.bottom:
                continue

            card_rect = pygame.Rect(content_rect.x, y, content_rect.width, item_h)
            current = task.get('current', 0)
            target = task.get('target', 1)
            claimed = task.get('claimed', False)
            task_id = task.get('id', '')

            # 领取按钮
            btn_rect = pygame.Rect(card_rect.right - 70, card_rect.y + 38, 60, 28)
            if btn_rect.collidepoint(mx, my):
                if not claimed and current >= target:
                    return ('claim_task', task_id)

        return None

    def scroll(self, dy):
        """滚轮滚动"""
        self.scroll_y = max(0, self.scroll_y - dy * 30)
