"""游戏进行中场景：战场绘制、点击交互、部署面板、排行榜"""

import pygame
import math
import time as _time
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    GRAY, BG_COLOR, TEXT_COLOR,
    CARD_BG, CARD_BORDER, ACCENT_BLUE, ACCENT_RED, ACCENT_GOLD, BTN_HOVER,
    GRINDER_SIZE,
    ZONE_CONFIG, ZONE_THEME_COLORS,
    GLOW_SIZE, GLOW_ALPHA_BASE, GLOW_ALPHA_RANGE, GLOW_FREQ,
    GLOW_COLOR_PLAYER, GLOW_COLOR_AI,
)
from ants_data import ANT_BY_ID
from ant_sprite import Ant
from obstacle import generate_obstacles
from ui_elements import draw_card, draw_button
from ui_minimap import MiniMap
import font_helper


class PlayingScene:
    def __init__(self, ctx):
        self.ctx = ctx
        self.minimap = MiniMap()

    # ── Click ──

    def handle_click(self, mx, my):
        ctx = self.ctx
        cam = ctx.camera

        # ── 小地图点击跳转 ──
        if self.minimap.handle_click(mx, my, cam):
            return

        # ── 巢穴快捷道具菜单 toggle ──
        nest_r = GRINDER_SIZE // 2 + 15  # 45px
        nest_dist = math.sqrt((mx - ctx.player_grinder.x + cam.x) ** 2 + (my - ctx.player_grinder.y + cam.y) ** 2)
        if nest_dist <= nest_r:
            ctx.nest_menu_open = not ctx.nest_menu_open
            # 打开菜单时关闭商店面板
            if ctx.nest_menu_open:
                ctx.panel_active = False
                ctx.panel_type = None
            return

        # ── 巢穴菜单内部点击 ──
        if ctx.nest_menu_open:
            consumed = ctx._click_nest_menu(mx, my)
            if consumed:
                return
            # 点击菜单外部 → 关闭菜单，穿透给底层
            ctx.nest_menu_open = False

        # Hamburger menu
        btn_menu = pygame.Rect(SCREEN_WIDTH - 44, 8, 36, 36)
        if btn_menu.collidepoint(mx, my):
            ctx.menu_open = not ctx.menu_open
            ctx.nest_menu_open = False  # 打开汉堡菜单时关闭巢穴菜单
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
            dist = math.sqrt((mx - sweet.x + cam.x) ** 2 + (my - sweet.y + cam.y) ** 2)
            if dist < sweet.current_size // 2 + 10:
                for ant in ctx.player_ants:
                    if ant.state == Ant.STATE_STUNNED or ant.state == Ant.STATE_RETURNING:
                        continue
                    ant.target_sweet = sweet
                    ant.state = Ant.STATE_MOVING_TO_SWEET
                    ant.eat_timer = 0.0
                return

        # Click on creature → direct player ants
        for creature in ctx.creatures:
            if not creature.alive:
                continue
            dist = math.sqrt((mx - creature.x + cam.x) ** 2 + (my - creature.y + cam.y) ** 2)
            if dist < creature.current_size // 2 + 10:
                for ant in ctx.player_ants:
                    if ant.state == Ant.STATE_STUNNED or ant.state == Ant.STATE_RETURNING:
                        continue
                    ant.target_sweet = creature
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
        cam = ctx.camera

        # Background（三区域统一背景，一张图覆盖三区域，跟随摄像机偏移）
        if getattr(ctx, 'zone_bg_full', None):
            self._draw_zone_backgrounds(screen, cam)
        else:
            screen.fill(BG_COLOR)
            terrain = ctx.level_data['terrain']
            from terrain import TERRAIN_COLORS
            terrain_color = TERRAIN_COLORS.get(terrain, (120, 180, 80))
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((*terrain_color, 30))
            screen.blit(overlay, (0, 0))

        # ── 绘制三区域地面标识 ──
        self._draw_zone_ground(screen, cam)

        # ── 绘制障碍物（地面层之上，游戏实体之下） ──
        for obs in getattr(ctx, 'obstacles', []):
            obs.draw(screen, cam)

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

        # Draw grinders with glow (using camera offset)
        glow_alpha = int(GLOW_ALPHA_BASE + GLOW_ALPHA_RANGE * math.sin(_time.time() * GLOW_FREQ * 2 * math.pi))

        # 玩家巢穴
        px, py = cam.world_to_screen(ctx.player_grinder.x, ctx.player_grinder.y)
        glow_surf = pygame.Surface((GLOW_SIZE, GLOW_SIZE), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (*GLOW_COLOR_PLAYER, glow_alpha), (GLOW_SIZE // 2, GLOW_SIZE // 2), GLOW_SIZE // 2)
        screen.blit(glow_surf, (int(px - GLOW_SIZE // 2), int(py - GLOW_SIZE // 2)))
        cam.draw_at(ctx.player_grinder.image, ctx.player_grinder.x, ctx.player_grinder.y, screen)
        label_font = font_helper.get_font(22)
        label_p = label_font.render("我方", True, ACCENT_BLUE)
        screen.blit(label_p, (int(px - label_p.get_width() // 2), int(py - 35)))

        # 敌方巢穴
        ax, ay = cam.world_to_screen(ctx.ai_grinder.x, ctx.ai_grinder.y)
        glow_surf2 = pygame.Surface((GLOW_SIZE, GLOW_SIZE), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf2, (*GLOW_COLOR_AI, glow_alpha), (GLOW_SIZE // 2, GLOW_SIZE // 2), GLOW_SIZE // 2)
        screen.blit(glow_surf2, (int(ax - GLOW_SIZE // 2), int(ay - GLOW_SIZE // 2)))
        cam.draw_at(ctx.ai_grinder.image, ctx.ai_grinder.x, ctx.ai_grinder.y, screen)
        label_a = label_font.render("敌方", True, ACCENT_RED)
        screen.blit(label_a, (int(ax - label_a.get_width() // 2), int(ay + 38)))

        # ── 右侧排行榜 ──
        self._draw_leaderboard(screen)

        # ── 迷你小地图（右下角） ──
        self.minimap.draw(screen, ctx)

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

        # ── 巢穴快捷道具菜单 ──
        if ctx.nest_menu_open:
            self._draw_nest_menu(screen, cam)

        # Draw sweets (with camera offset)
        for sweet in ctx.sweets:
            if sweet.alive:
                sweet.draw_with_hp_effect(screen, camera=cam)

        # Draw creatures (with camera offset)
        for creature in ctx.creatures:
            creature.draw_with_hp_effect(screen, camera=cam)

        # Draw player ants (with camera offset)
        mx, my = pygame.mouse.get_pos()
        hover_ant = None
        for ant in ctx.player_ants:
            ant_sx, ant_sy = cam.world_to_screen(ant.x, ant.y)
            screen.blit(ant.image, ant.image.get_rect(center=(int(ant_sx), int(ant_sy))))
            ant.draw_storage_bar_at(screen, cam)
            ant.draw_stun_indicator_at(screen, ctx.font_tiny, cam)
            ant.draw_level_badge_at(screen, ctx.font_tiny, cam)
            if ant.image.get_rect(center=(int(ant_sx), int(ant_sy))).collidepoint(mx, my):
                hover_ant = ant

        # Draw AI ants (with camera offset)
        for ant in ctx.ai_ants:
            ant_sx, ant_sy = cam.world_to_screen(ant.x, ant.y)
            screen.blit(ant.image, ant.image.get_rect(center=(int(ant_sx), int(ant_sy))))
            ant.draw_storage_bar_at(screen, cam)
            ant.draw_stun_indicator_at(screen, ctx.font_tiny, cam)
            if ant.image.get_rect(center=(int(ant_sx), int(ant_sy))).collidepoint(mx, my):
                hover_ant = ant

        # Hover tooltip (screen coordinates, no camera offset needed)
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

        # Draw floating texts (with camera offset)
        for ft in ctx.floating_texts:
            ft.draw_at_screen(screen, ctx.font_small, cam)

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

    # ── 巢穴快捷道具菜单 ──

    def _get_nest_menu_items(self):
        """获取巢穴菜单中可显示的道具列表（有剩余次数的）"""
        from items_data import ITEMS
        ctx = self.ctx
        items = []
        for item_def in ITEMS:
            name = item_def["name"]
            used = ctx.item_uses.get(name, 0)
            if used < item_def["max_uses"]:
                items.append(item_def)
        return items

    def _draw_nest_menu(self, screen, cam=None):
        """绘制巢穴上方的快捷道具菜单"""
        from items_data import ITEMS
        ctx = self.ctx

        nest_items = self._get_nest_menu_items()
        if not nest_items:
            ctx.nest_menu_open = False
            return

        menu_w = 180
        item_h = 42
        menu_h = len(nest_items) * item_h + 10
        # 菜单固定在巢穴正上方（世界坐标 → 屏幕坐标）
        if cam:
            gx, gy = cam.world_to_screen(ctx.player_grinder.x, ctx.player_grinder.y)
        else:
            gx, gy = ctx.player_grinder.x, ctx.player_grinder.y
        menu_x = gx - menu_w // 2
        menu_y = gy - GRINDER_SIZE // 2 - 15 - menu_h

        # 菜单背景
        menu_rect = pygame.Rect(menu_x, menu_y, menu_w, menu_h)
        draw_card(screen, menu_rect, bg_color=CARD_BG, border_color=CARD_BORDER,
                  shadow=True, radius=10)

        mx, my = pygame.mouse.get_pos()

        for i, item_def in enumerate(nest_items):
            row_rect = pygame.Rect(menu_x, menu_y + 5 + i * item_h, menu_w, item_h)
            hover = row_rect.collidepoint(mx, my)

            if hover:
                pygame.draw.rect(screen, BTN_HOVER, row_rect, border_radius=6)

            name = item_def["name"]
            cost = item_def["cost"]
            used = ctx.item_uses.get(name, 0)
            max_uses = item_def["max_uses"]
            affordable = ctx.level_coins >= cost

            name_font = font_helper.get_font(14)
            name_surf = name_font.render(name, True, TEXT_COLOR if affordable else GRAY)
            screen.blit(name_surf, (row_rect.x + 10, row_rect.centery - name_surf.get_height() // 2))

            price_font = font_helper.get_font(14)
            price_color = ACCENT_GOLD if affordable else ACCENT_RED
            price_surf = price_font.render(f"{cost}G", True, price_color)
            screen.blit(price_surf, (row_rect.right - 60, row_rect.centery - price_surf.get_height() // 2))

            uses_font = font_helper.get_font(12)
            uses_surf = uses_font.render(f"剩余{max_uses - used}/{max_uses}", True, GRAY)
            screen.blit(uses_surf, (row_rect.right - 60, row_rect.centery + 4))

    def _draw_zone_backgrounds(self, screen, cam):
        """绘制三区域统一背景（一张图覆盖三区域），跟随Camera水平滚动"""
        bg = getattr(self.ctx, 'zone_bg_full', None)
        if not bg:
            return
        # 世界坐标 → 屏幕坐标（背景从世界原点开始）
        sx, sy = cam.world_to_screen(0, 0)
        screen.blit(bg, (int(sx), int(sy)))

    def _draw_zone_ground(self, screen, cam):
        """绘制三区域标注标签：半透明胶囊样式"""
        ctx = self.ctx
        zones = [
            ('left',   '稀有区 ×1.5', ZONE_THEME_COLORS.get('left', (255, 200, 220))),
            ('center', '普通区 ×1.0', ZONE_THEME_COLORS.get('center', (180, 230, 160))),
            ('right',  '高阶区 ×2.0', ZONE_THEME_COLORS.get('right', (255, 220, 120))),
        ]
        label_font = font_helper.get_font(14)
        padding_x, padding_y = 12, 5
        capsule_h = 24

        for zone_name, label_text, theme_color in zones:
            cfg = ZONE_CONFIG[zone_name]
            x_min, x_max = cfg['x_range']

            # 区域标签（半透明胶囊）
            cx = (x_min + x_max) // 2
            lbl = label_font.render(label_text, True, (255, 255, 255))
            lbl_w = lbl.get_width()
            lbl_h = lbl.get_height()
            capsule_w = lbl_w + padding_x * 2
            capsule_h_actual = lbl_h + padding_y * 2

            lx, ly = cam.world_to_screen(cx - capsule_w // 2, SCREEN_HEIGHT * 0.85)

            # 仅绘制在屏幕内的标签
            if -capsule_w - 50 < lx < SCREEN_WIDTH + 50:
                # 半透明胶囊背景
                capsule_surf = pygame.Surface((capsule_w, capsule_h_actual), pygame.SRCALPHA)
                # 主体颜色（半透明）
                bg_alpha = 140
                capsule_color = (theme_color[0], theme_color[1], theme_color[2], bg_alpha)
                pygame.draw.rect(capsule_surf, capsule_color, (0, 0, capsule_w, capsule_h_actual),
                                 border_radius=capsule_h_actual // 2)
                # 边框
                border_color = (255, 255, 255, 100)
                pygame.draw.rect(capsule_surf, border_color, (0, 0, capsule_w, capsule_h_actual),
                                 width=1, border_radius=capsule_h_actual // 2)
                screen.blit(capsule_surf, (int(lx), int(ly)))
                # 文字
                text_x = lx + padding_x
                text_y = ly + padding_y
                screen.blit(lbl, (int(text_x), int(text_y)))

    def _draw_panel(self, screen):
        ctx = self.ctx
        if ctx.panel_type == 'shop':
            ctx.shop_ui.battle_mode = True
            ctx.shop_ui.draw(screen, *pygame.mouse.get_pos(),
                              ctx.sm, ctx.team, ctx.total_coins, ctx.level_coins, ctx.item_uses)

