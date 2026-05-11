"""挑战失败场景"""

import pygame
from levels_data import get_level
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    TEXT_COLOR, GRAY, BG_COLOR, ACCENT_RED, ACCENT_GOLD,
)
from ui_elements import draw_button, draw_text_centered


class GameOverScene:
    def __init__(self, ctx):
        self.ctx = ctx

    def handle_click(self, mx, my):
        ctx = self.ctx
        btn_retry = pygame.Rect(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 40, 200, 50)
        btn_back = pygame.Rect(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 100, 200, 50)
        if btn_retry.collidepoint(mx, my):
            ctx.level_data = get_level(ctx.current_level)
            ctx.state = 'team_select'
        elif btn_back.collidepoint(mx, my):
            ctx.state = 'level_select'

    def draw(self, screen):
        ctx = self.ctx
        screen.fill(BG_COLOR)
        draw_text_centered(screen, "挑战失败", ctx.font_xl, ACCENT_RED,
                           SCREEN_WIDTH // 2, 120)

        info = ctx.font_medium.render(
            f"我方: {ctx.level_coins}G  敌方: {ctx.ai_coins}G  累计: {ctx.total_coins}G", True, ACCENT_GOLD)
        screen.blit(info, (SCREEN_WIDTH // 2 - info.get_width() // 2, 200))

        # 搬运结算明细（如有自动结算金额）
        transit = getattr(ctx, 'transit_coins', 0)
        if transit > 0:
            transit_text = ctx.font_small.render(
                f"搬运结算 +{transit}G", True, (100, 200, 255))
            screen.blit(transit_text, (SCREEN_WIDTH // 2 - transit_text.get_width() // 2, 235))

        target = ctx.level_data.get('target_coins', 0)
        hint = ctx.font_small.render(f"需要 {target}G 才能通过", True, GRAY)
        screen.blit(hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2, 250))

        btn_retry = pygame.Rect(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 40, 200, 50)
        btn_back = pygame.Rect(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 100, 200, 50)
        draw_button(screen, btn_retry, "重试", ctx.font_medium,
                    hover=btn_retry.collidepoint(*pygame.mouse.get_pos()))
        draw_button(screen, btn_back, "关卡选择", ctx.font_medium,
                    color=(120, 120, 140), hover=btn_back.collidepoint(*pygame.mouse.get_pos()))
