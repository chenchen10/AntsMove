"""关卡选择场景"""

import pygame
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    TEXT_COLOR, CARD_BG, CARD_BORDER, BTN_HOVER,
)
from ui_elements import draw_button, draw_card
from levels_data import get_level


class LevelSelectScene:
    def __init__(self, ctx):
        self.ctx = ctx

    def handle_click(self, mx, my):
        ctx = self.ctx
        # 返回按钮
        btn_back = pygame.Rect(20, SCREEN_HEIGHT - 50, 120, 40)
        if btn_back.collidepoint(mx, my):
            ctx.state = 'title'
            return

        # 阵容配置按钮（右上角）
        btn_team = pygame.Rect(SCREEN_WIDTH - 140, 15, 120, 36)
        if btn_team.collidepoint(mx, my):
            ctx.total_coins = ctx.sm.get_total_coins()
            ctx.state = 'team_select'
            return

        # 关卡点击
        level = ctx.level_select_ui.handle_click(mx, my)
        if level:
            ctx.current_level = level
            ctx.level_data = get_level(level)
            ctx.state = 'team_select'

    def draw(self, screen):
        ctx = self.ctx
        ctx.level_select_ui.draw(screen, *pygame.mouse.get_pos())

        # 返回按钮（左下角）
        btn_back = pygame.Rect(20, SCREEN_HEIGHT - 50, 120, 40)
        draw_button(screen, btn_back, "返回", ctx.font_small,
                    color=(120, 120, 140), hover=btn_back.collidepoint(*pygame.mouse.get_pos()))

        # 阵容配置按钮（右上角）
        btn_team = pygame.Rect(SCREEN_WIDTH - 140, 15, 120, 36)
        hover_team = btn_team.collidepoint(*pygame.mouse.get_pos())
        draw_button(screen, btn_team, "阵容配置", ctx.font_small,
                    color=(80, 120, 180), hover=hover_team)
