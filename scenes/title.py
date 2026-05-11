"""标题画面场景 — 2+3分层布局"""

import pygame
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    GRAY, BG_COLOR, TEXT_COLOR, CARD_BG, CARD_BORDER, ACCENT_GOLD, ACCENT_BLUE,
)
from ui_elements import draw_button, draw_card
import font_helper


class TitleScene:
    def __init__(self, ctx):
        self.ctx = ctx
        # 第二行功能按钮定义（名称, 状态字段）
        self._func_buttons = [
            ("任务", "task_panel_active"),
            ("成就", "achievement_panel_active"),
            ("签到", "checkin_panel_active"),
        ]

    def _get_func_btn_rect(self, index):
        """获取第二行功能按钮的矩形区域"""
        btn_w, btn_h, gap = 120, 44, 16
        total_w = btn_w * 3 + gap * 2
        start_x = (SCREEN_WIDTH - total_w) // 2
        x = start_x + index * (btn_w + gap)
        return pygame.Rect(x, 420, btn_w, btn_h)

    def handle_click(self, mx, my):
        ctx = self.ctx
        # 商店按钮（左）
        btn_shop = pygame.Rect(SCREEN_WIDTH // 2 - 210, 340, 190, 60)
        if btn_shop.collidepoint(mx, my):
            ctx.shop_active = True
            ctx.shop_ui.battle_mode = False
            ctx.shop_ui.tab = 0
            return

        # 开始游戏按钮（右）
        btn_start = pygame.Rect(SCREEN_WIDTH // 2 + 20, 340, 190, 60)
        if btn_start.collidepoint(mx, my):
            ctx.total_coins = ctx.sm.get_total_coins()
            ctx.state = 'level_select'
            return

        # 第二行功能按钮
        for i, (label, attr) in enumerate(self._func_buttons):
            btn = self._get_func_btn_rect(i)
            if btn.collidepoint(mx, my):
                setattr(ctx, attr, True)
                return

        # 调试按钮（右下角小字）
        btn_debug = pygame.Rect(SCREEN_WIDTH - 80, SCREEN_HEIGHT - 36, 70, 28)
        if btn_debug.collidepoint(mx, my):
            ctx.state = 'debug'

    def draw(self, screen):
        ctx = self.ctx
        if ctx.homepage_bg:
            screen.blit(ctx.homepage_bg, (0, 0))
        else:
            for y in range(SCREEN_HEIGHT):
                t = y / SCREEN_HEIGHT
                r = int(255 - t * 30)
                g = int(249 - t * 40)
                b = int(230 - t * 50)
                pygame.draw.line(screen, (r, g, b), (0, y), (SCREEN_WIDTH, y))

        title = ctx.font_xl.render("蚂蚁抢甜点", True, TEXT_COLOR)
        shadow = ctx.font_xl.render("蚂蚁抢甜点", True, (150, 130, 110))
        screen.blit(shadow, (SCREEN_WIDTH // 2 - shadow.get_width() // 2 + 2, 152))
        screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 150))

        sub = ctx.font_medium.render("26只蚂蚁 | 200关挑战 | 地形克制", True, TEXT_COLOR)
        screen.blit(sub, (SCREEN_WIDTH // 2 - sub.get_width() // 2, 230))

        # Stats
        owned = ctx.sm.get_owned_count()
        maxed = ctx.sm.get_maxed_count()
        max_lv = ctx.sm.get_max_level()
        stats = ctx.font_small.render(
            f"已拥有: {owned}/26  满级: {maxed}  通关: {max_lv}/200  金币: {ctx.sm.get_total_coins()}",
            True, GRAY)
        screen.blit(stats, (SCREEN_WIDTH // 2 - stats.get_width() // 2, 275))

        # ── 第一行：核心按钮 ──
        # 商店按钮（左）
        btn_shop = pygame.Rect(SCREEN_WIDTH // 2 - 210, 340, 190, 60)
        hover_shop = btn_shop.collidepoint(*pygame.mouse.get_pos())
        draw_button(screen, btn_shop, "商店", ctx.font_large,
                    color=ACCENT_GOLD, hover=hover_shop)

        # 开始游戏按钮（右）
        btn_start = pygame.Rect(SCREEN_WIDTH // 2 + 20, 340, 190, 60)
        hover_start = btn_start.collidepoint(*pygame.mouse.get_pos())
        draw_button(screen, btn_start, "开始游戏", ctx.font_large, hover=hover_start)

        # ── 第二行：功能按钮（任务/成就/签到）──
        mx, my = pygame.mouse.get_pos()
        font_func = font_helper.get_font(20)
        for i, (label, _) in enumerate(self._func_buttons):
            btn = self._get_func_btn_rect(i)
            hover = btn.collidepoint(mx, my)
            if hover:
                # hover态：ACCENT_BLUE底+白色文字
                draw_button(screen, btn, label, font_func, color=ACCENT_BLUE, hover=True)
            else:
                # 常态：卡片风格（CARD_BG底+CARD_BORDER边框）
                draw_card(screen, btn, bg_color=CARD_BG, border_color=CARD_BORDER,
                          shadow=False, radius=8)
                txt = font_func.render(label, True, TEXT_COLOR)
                screen.blit(txt, (btn.centerx - txt.get_width() // 2,
                                  btn.centery - txt.get_height() // 2))

        # 调试按钮（右下角小字）
        btn_debug = pygame.Rect(SCREEN_WIDTH - 80, SCREEN_HEIGHT - 36, 70, 28)
        hover_debug = btn_debug.collidepoint(*pygame.mouse.get_pos())
        font_sm = font_helper.get_font(14)
        debug_color = (180, 120, 120) if hover_debug else (150, 140, 130)
        pygame.draw.rect(screen, debug_color, btn_debug, border_radius=6)
        dtxt = font_sm.render("调试", True, (255, 255, 255))
        screen.blit(dtxt, (btn_debug.centerx - dtxt.get_width() // 2,
                           btn_debug.centery - dtxt.get_height() // 2))
