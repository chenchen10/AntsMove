"""暂停场景"""

import pygame
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    TEXT_COLOR, CARD_BG, CARD_BORDER,
)
from ui_elements import draw_card, draw_button


class PausedScene:
    def __init__(self, ctx):
        self.ctx = ctx

    def handle_click(self, mx, my):
        ctx = self.ctx
        pw, ph = 300, 200
        px = (SCREEN_WIDTH - pw) // 2
        py = (SCREEN_HEIGHT - ph) // 2
        btn_resume = pygame.Rect(px + 50, py + 80, 200, 45)
        btn_menu = pygame.Rect(px + 50, py + 135, 200, 45)
        if btn_resume.collidepoint(mx, my):
            ctx.state = 'playing'
        elif btn_menu.collidepoint(mx, my):
            if ctx.level_coins > 0:
                ctx.total_coins += ctx.level_coins
                ctx.sm.add_coins(ctx.level_coins)
            ctx.state = 'title'

    def draw(self, screen):
        ctx = self.ctx
        # 先绘制游戏画面底图（复用 playing 场景实例）
        playing_scene = ctx._get_scene('playing')
        playing_scene.draw(screen)

        # 暗色遮罩
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        screen.blit(overlay, (0, 0))

        # Panel
        pw, ph = 300, 200
        px = (SCREEN_WIDTH - pw) // 2
        py = (SCREEN_HEIGHT - ph) // 2
        panel = pygame.Rect(px, py, pw, ph)
        draw_card(screen, panel, bg_color=CARD_BG, border_color=CARD_BORDER, shadow=True, radius=12)

        title = ctx.font_large.render("暂停", True, TEXT_COLOR)
        screen.blit(title, (panel.centerx - title.get_width() // 2, py + 20))

        btn_resume = pygame.Rect(px + 50, py + 80, 200, 45)
        btn_menu = pygame.Rect(px + 50, py + 135, 200, 45)
        draw_button(screen, btn_resume, "继续", ctx.font_medium,
                    hover=btn_resume.collidepoint(*pygame.mouse.get_pos()))
        draw_button(screen, btn_menu, "主菜单", ctx.font_medium,
                    color=(120, 80, 80), hover=btn_menu.collidepoint(*pygame.mouse.get_pos()))
