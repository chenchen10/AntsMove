"""游戏进行中场景：战场绘制、点击交互、部署面板、排行榜"""

import pygame
import math
import time as _time
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    GRAY, BG_COLOR, TEXT_COLOR,
    CARD_BG, CARD_BORDER, ACCENT_BLUE, ACCENT_RED, ACCENT_GOLD, BTN_HOVER,
)
from ants_data import ANT_BY_ID
from ant_sprite import Ant
from ui_elements import draw_card, draw_button
import font_helper


class PlayingScene:
    def __init__(self, ctx):
        self.ctx = ctx

    # ── Click ──

    def handle_click(self, mx, my):
        ctx = self.ctx

        # Hamburger menu
        btn_menu = pygame.Rect(SCREEN_WIDTH - 44, 8, 36, 36)
        if btn_menu.collidepoint(mx, my):
            ctx.menu_open = not ctx.menu_open
            return

        if ctx.menu_open:
            menu_items = ['商店', '暂停', '主菜单']
            menu_w = 130
            menu_x = SCREEN_WIDTH - menu_w - 10
            menu_y = 52
            item_h = 38
            for i, item_name in enumerate(menu_items):
                item_rect = pygame.Rect(menu_x, menu_y + i * item_h, menu_w, item_h)
                if item_rect.collidepoint(mx, my):
                    ctx.menu_open = False
                    if item_name == '商店':
                        ctx.panel_active = True
                        ctx.panel_type = 'shop'
                    elif item_name == '暂停':
                        ctx.state = 'paused'
                    elif item_name == '主菜单':
                        if ctx.level_coins > 0:
                            ctx.total_coins += ctx.level_coins
                            ctx.sm.add_coins(ctx.level_coins)
                        ctx.state = 'title'
                    return
            ctx.menu_open = False
            return

        # Click on sweet → direct player ants
        for sweet in ctx.sweets:
            if not sweet.alive:
                continue
            dist = math.sqrt((mx - sweet.x) ** 2 + (my - sweet.y) ** 2)
            if dist < sweet.current_size // 2 + 10:
                for ant in ctx.player_ants:
                    if ant.state == Ant.STATE_STUNNED or ant.state == Ant.STATE_RETURNING:
                        continue
                    ant.target_sweet = sweet
                    ant.state = Ant.STATE_MOVING_TO_SWEET
                    ant.eat_timer = 0.0
                return

    # ── Drawing ──

    def draw(self, screen):
        ctx = self.ctx
        self._draw_playing(screen)
        if ctx.panel_active:
            self._draw_panel(screen)

    def _draw_playing(self, screen):
        ctx = self.ctx

        # Background（按关卡轮训背景图）
        if ctx.level_bgs:
            bg_count = len(ctx.level_bgs)
            bg_idx = (ctx.current_level - 1) % bg_count
            screen.blit(ctx.level_bgs[bg_idx], (0, 0))
        else:
            screen.fill(BG_COLOR)

        # Terrain color overlay (skip if level has its own background image)
        if not ctx.level_bgs:
            terrain = ctx.level_data['terrain']
            from terrain import TERRAIN_COLORS
            terrain_color = TERRAIN_COLORS.get(terrain, (120, 180, 80))
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((*terrain_color, 30))
            screen.blit(overlay, (0, 0))

        # ── 顶部信息栏 ──
        minutes = int(ctx.level_timer) // 60
        seconds = int(ctx.level_timer) % 60
        timer_color = ACCENT_RED if ctx.level_timer < 30 else TEXT_COLOR
        target = ctx.level_data.get('target_coins', 0)
        hud_text = f"第{ctx.current_level}关 | {ctx.level_data['terrain_name']} | {minutes:02d}:{seconds:02d} | 目标:{target}G"
        hud_surf = ctx.font_small.render(hud_text, True, timer_color)
        hud_w = hud_surf.get_width() + 30
        hud_rect = pygame.Rect(SCREEN_WIDTH // 2 - hud_w // 2, 6, hud_w, 32)
        draw_card(screen, hud_rect, bg_color=CARD_BG, border_color=CARD_BORDER, shadow=True, radius=10)
        screen.blit(hud_surf, (hud_rect.centerx - hud_surf.get_width() // 2,
                                hud_rect.centery - hud_surf.get_height() // 2))

        # ── 左下状态栏 ──
        self._draw_status_bar(screen)

        # Draw grinders with glow
        glow_alpha = int(30 + 20 * math.sin(_time.time() * 2))

        glow_surf = pygame.Surface((60 + 20, 60 + 20), pygame.SRCALPHA)
        glow_center = (40, 40)
        pygame.draw.circle(glow_surf, (80, 180, 80, glow_alpha), glow_center, 38)
        glow_rect = glow_surf.get_rect(center=(ctx.player_grinder.x, ctx.player_grinder.y))
        screen.blit(glow_surf, glow_rect)
        ctx.player_grinder.draw(screen)
        label_font = font_helper.get_font(22)
        label_p = label_font.render("我方", True, ACCENT_BLUE)
        screen.blit(label_p, (ctx.player_grinder.x - label_p.get_width() // 2,
                               ctx.player_grinder.y - 35))

        glow_surf2 = pygame.Surface((60 + 20, 60 + 20), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf2, (180, 80, 80, glow_alpha), glow_center, 38)
        glow_rect2 = glow_surf2.get_rect(center=(ctx.ai_grinder.x, ctx.ai_grinder.y))
        screen.blit(glow_surf2, glow_rect2)
        ctx.ai_grinder.draw(screen)
        label_a = label_font.render("敌方", True, ACCENT_RED)
        screen.blit(label_a, (ctx.ai_grinder.x - label_a.get_width() // 2,
                               ctx.ai_grinder.y + 38))

        # ── 右侧排行榜 ──
        self._draw_leaderboard(screen)

        # ── 右上菜单按钮 ──
        btn_menu = pygame.Rect(SCREEN_WIDTH - 44, 8, 36, 36)
        hover_menu = btn_menu.collidepoint(*pygame.mouse.get_pos())
        draw_card(screen, btn_menu,
                  bg_color=CARD_BG if not hover_menu else BTN_HOVER,
                  border_color=CARD_BORDER, shadow=False, radius=8)
        menu_txt = ctx.font_medium.render("≡", True, TEXT_COLOR)
        screen.blit(menu_txt, (btn_menu.centerx - menu_txt.get_width() // 2,
                                btn_menu.centery - menu_txt.get_height() // 2))

        # ── 下拉菜单 ──
        if ctx.menu_open:
            menu_items = ['商店', '暂停', '主菜单']
            menu_w = 130
            menu_x = SCREEN_WIDTH - menu_w - 10
            menu_y = 52
            item_h = 38
            menu_rect = pygame.Rect(menu_x, menu_y, menu_w, item_h * len(menu_items))
            draw_card(screen, menu_rect, bg_color=CARD_BG, border_color=CARD_BORDER, shadow=True)
            for i, item_name in enumerate(menu_items):
                item_rect = pygame.Rect(menu_x, menu_y + i * item_h, menu_w, item_h)
                hover = item_rect.collidepoint(*pygame.mouse.get_pos())
                if hover:
                    pygame.draw.rect(screen, BTN_HOVER, item_rect, border_radius=6)
                txt = ctx.font_small.render(item_name, True, TEXT_COLOR)
                screen.blit(txt, (item_rect.centerx - txt.get_width() // 2,
                                   item_rect.centery - txt.get_height() // 2))

        # Draw sweets
        for sweet in ctx.sweets:
            if sweet.alive:
                sweet.draw_with_hp_effect(screen)

        # Draw player ants
        mx, my = pygame.mouse.get_pos()
        hover_ant = None
        for ant in ctx.player_ants:
            screen.blit(ant.image, ant.rect)
            ant.draw_storage_bar(screen)
            ant.draw_stun_indicator(screen, ctx.font_tiny)
            ant.draw_level_badge(screen, ctx.font_tiny)
            if ant.rect.collidepoint(mx, my):
                hover_ant = ant

        # Draw AI ants
        for ant in ctx.ai_ants:
            screen.blit(ant.image, ant.rect)
            ant.draw_storage_bar(screen)
            ant.draw_stun_indicator(screen, ctx.font_tiny)
            if ant.rect.collidepoint(mx, my):
                hover_ant = ant

        # Hover tooltip
        if hover_ant:
            name = hover_ant.ant_data['name']
            role = hover_ant.ant_data['role']
            tip = f"#{hover_ant.ant_id} {name} 搬:{int(hover_ant.max_storage)} 速:{int(hover_ant.speed)} 防:{hover_ant.defense} [{role}]"
            tip_surf = font_helper.get_font(14).render(tip, True, (255, 255, 220))
            tip_w = tip_surf.get_width() + 12
            tip_h = tip_surf.get_height() + 8
            tip_x = min(mx + 12, SCREEN_WIDTH - tip_w - 4)
            tip_y = max(my - tip_h - 4, 0)
            tip_rect = pygame.Rect(tip_x, tip_y, tip_w, tip_h)
            tip_bg = pygame.Surface((tip_w, tip_h), pygame.SRCALPHA)
            pygame.draw.rect(tip_bg, (30, 30, 50, 200), (0, 0, tip_w, tip_h), border_radius=6)
            screen.blit(tip_bg, (tip_x, tip_y))
            screen.blit(tip_surf, (tip_x + 6, tip_y + 4))

        # Draw floating texts
        for ft in ctx.floating_texts:
            ft.draw(screen, ctx.font_small)

    def _draw_status_bar(self, screen):
        """左下角状态栏：上阵总数、总搬运量、平均速度"""
        ctx = self.ctx
        bar_w, bar_h = 280, 56
        bar_x = 10
        bar_y = SCREEN_HEIGHT - bar_h - 12
        bar_rect = pygame.Rect(bar_x, bar_y, bar_w, bar_h)
        draw_card(screen, bar_rect, bg_color=CARD_BG, border_color=CARD_BORDER, shadow=True, radius=8)

        # 计算上阵蚂蚁综合属性
        from ants_data import get_carry_capacity, get_speed
        total_carry = 0
        total_speed = 0
        count = len(ctx.player_ants)
        for ant in ctx.player_ants:
            total_carry += ant.max_storage
            total_speed += ant.speed
        avg_speed = int(total_speed / count) if count > 0 else 0

        line1 = f"上阵: {count}只  |  总搬运: {total_carry}  |  均速: {avg_speed}"
        txt1 = ctx.font_tiny.render(line1, True, TEXT_COLOR)
        screen.blit(txt1, (bar_x + 12, bar_y + 8))

        line2 = f"累计金币: {ctx.total_coins}  |  关卡金币: {ctx.level_coins}"
        txt2 = ctx.font_tiny.render(line2, True, ACCENT_GOLD)
        screen.blit(txt2, (bar_x + 12, bar_y + 30))

    def _draw_leaderboard(self, screen):
        """右侧排行榜"""
        ctx = self.ctx
        lb_w, lb_h = 170, 110
        lb_x = SCREEN_WIDTH - lb_w - 12
        lb_y = (SCREEN_HEIGHT - lb_h) // 2

        pygame.draw.rect(screen, CARD_BG, (lb_x, lb_y, lb_w, lb_h), border_radius=10)
        pygame.draw.rect(screen, CARD_BORDER, (lb_x, lb_y, lb_w, lb_h), 1, border_radius=10)

        title = ctx.font_tiny.render("排行榜", True, TEXT_COLOR)
        screen.blit(title, (lb_x + lb_w // 2 - title.get_width() // 2, lb_y + 12))

        line_y = lb_y + 34
        pygame.draw.line(screen, CARD_BORDER, (lb_x + 14, line_y), (lb_x + lb_w - 14, line_y), 1)

        dot_r = 4
        dot_x = lb_x + 14
        dot_y = lb_y + 50
        pygame.draw.circle(screen, ACCENT_BLUE, (dot_x, dot_y), dot_r)
        p_txt = ctx.font_tiny.render(f"我方金币: {ctx.level_coins}", True, TEXT_COLOR)
        screen.blit(p_txt, (dot_x + dot_r + 6, dot_y - p_txt.get_height() // 2))

        dot_y2 = lb_y + 74
        pygame.draw.circle(screen, ACCENT_RED, (dot_x, dot_y2), dot_r)
        a_txt = ctx.font_tiny.render(f"对方金币: {ctx.ai_coins}", True, TEXT_COLOR)
        screen.blit(a_txt, (dot_x + dot_r + 6, dot_y2 - a_txt.get_height() // 2))

    def _draw_panel(self, screen):
        ctx = self.ctx
        if ctx.panel_type == 'shop':
            ctx.shop_ui.battle_mode = True
            ctx.shop_ui.draw(screen, *pygame.mouse.get_pos(),
                              ctx.sm, ctx.team, ctx.total_coins, ctx.level_coins, ctx.item_uses)

