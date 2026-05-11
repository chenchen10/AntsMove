"""编队选择场景：分种类独立管理出战数量，上限30只"""

import pygame
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    WHITE, GRAY, BG_COLOR, TEXT_COLOR,
    ACCENT_BLUE, CARD_BG, CARD_BORDER,
)
from ants_data import ANT_BY_ID, get_carry_capacity, MAX_TEAM_SIZE
from ai_data import get_max_team_size
from ui_elements import draw_button, draw_text_centered
import font_helper


class TeamSelectScene:
    def __init__(self, ctx):
        self.ctx = ctx

    def handle_click(self, mx, my):
        ctx = self.ctx
        has_level = ctx.level_data is not None

        # 确认/开始按钮
        btn_confirm = pygame.Rect(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT - 70, 200, 45)
        if btn_confirm.collidepoint(mx, my):
            if len(ctx.team) > 0:
                if has_level:
                    ctx._start_level()
                else:
                    ctx.state = 'level_select'
            return

        # 返回按钮
        btn_back = pygame.Rect(20, SCREEN_HEIGHT - 70, 100, 40)
        if btn_back.collidepoint(mx, my):
            ctx.state = 'level_select'
            return

        # [-] [+] 按钮点击
        team_limit = self._get_team_limit()
        for ant_id, (minus_rect, plus_rect) in ctx._team_btns.items():
            if minus_rect.collidepoint(mx, my):
                if ant_id in ctx.team:
                    ctx.team.remove(ant_id)
                return
            if plus_rect.collidepoint(mx, my):
                deployed = ctx.team.count(ant_id)
                owned = ctx.sm.get_ant_count(ant_id)
                if deployed < owned and len(ctx.team) < team_limit:
                    ctx.team.append(ant_id)
                return

    def _get_team_limit(self):
        ctx = self.ctx
        if ctx.level_data is not None:
            return get_max_team_size(ctx.current_level)
        return MAX_TEAM_SIZE

    def draw(self, screen):
        ctx = self.ctx
        mx, my = pygame.mouse.get_pos()
        has_level = ctx.level_data is not None

        screen.fill(BG_COLOR)
        # 注意：不在这里重置 _team_btns，因为 handle_click 在 draw 之前执行，
        # 需要保留上一帧的按钮位置供点击检测使用
        ctx._team_btns = getattr(ctx, '_team_btns', {})

        draw_text_centered(screen, "配置出战蚂蚁", ctx.font_large, TEXT_COLOR,
                           SCREEN_WIDTH // 2, 15)

        # 关卡信息
        if has_level:
            info_txt = ctx.font_small.render(
                f"第{ctx.current_level}关 | {ctx.level_data['terrain_name']} | "
                f"目标:{ctx.level_data['target_coins']}金币 | {ctx.level_data['timer']}秒",
                True, GRAY)
            screen.blit(info_txt, (SCREEN_WIDTH // 2 - info_txt.get_width() // 2, 55))

        # 上阵数量
        team_limit = self._get_team_limit()
        team_count = len(ctx.team)
        team_color = ACCENT_BLUE if team_count <= team_limit else (220, 80, 70)
        team_txt = ctx.font_medium.render(f"上阵: {team_count}/{team_limit}只", True, team_color)
        screen.blit(team_txt, (SCREEN_WIDTH // 2 - team_txt.get_width() // 2, 78))

        # 总搬运量统计
        total_carry = 0
        for ant_id in ctx.team:
            ant = ANT_BY_ID[ant_id]
            carry_lv = ctx.sm.get_ant_attr(ant_id, 'carry')
            total_carry += get_carry_capacity(ant_id, carry_lv)
        carry_txt = ctx.font_small.render(f"总搬运量: {total_carry}", True, GRAY)
        screen.blit(carry_txt, (SCREEN_WIDTH // 2 - carry_txt.get_width() // 2, 102))

        # 蚂蚁列表（按种类显示）
        owned = ctx.sm.get_unique_owned_ants()
        font_sm = font_helper.get_font(14)
        font_md = font_helper.get_font(16)

        item_h = 55
        start_y = 125
        cols = 2
        col_w = (SCREEN_WIDTH - 80) // cols

        for i, ant_id in enumerate(owned):
            col = i % cols
            row = i // cols
            x = 40 + col * col_w
            y = start_y + row * (item_h + 4)
            if y + item_h > SCREEN_HEIGHT - 90:
                break

            ant = ANT_BY_ID[ant_id]
            carry_lv = ctx.sm.get_ant_attr(ant_id, 'carry')
            speed_lv = ctx.sm.get_ant_attr(ant_id, 'speed')
            defense_lv = ctx.sm.get_ant_attr(ant_id, 'defense')
            carry = get_carry_capacity(ant_id, carry_lv)
            deployed = ctx.team.count(ant_id)
            owned_count = ctx.sm.get_ant_count(ant_id)

            item_rect = pygame.Rect(x, y, col_w - 10, item_h)
            hover = item_rect.collidepoint(mx, my)

            if deployed > 0:
                bg = (40, 100, 60)
            elif hover:
                bg = (60, 80, 120)
            else:
                bg = (40, 50, 70)
            pygame.draw.rect(screen, bg, item_rect, border_radius=6)
            pygame.draw.rect(screen, ACCENT_BLUE if deployed > 0 else (60, 80, 110),
                             item_rect, 1, border_radius=6)

            # 名称 + 搬运
            name_txt = font_md.render(f"#{ant['id']} {ant['name'][:6]}", True, WHITE)
            screen.blit(name_txt, (x + 8, y + 4))

            # 属性信息
            prop_txt = font_sm.render(
                f"搬运:{carry} 速:{get_speed_text(ant_id, speed_lv)} 防:{get_defense_text(ant_id, defense_lv)}",
                True, (180, 200, 220))
            screen.blit(prop_txt, (x + 8, y + 22))

            # 拥有/出战数量
            count_txt = font_sm.render(f"拥有:{owned_count} 出战:{deployed}", True, (150, 180, 200))
            screen.blit(count_txt, (x + 8, y + 38))

            # [-] [+] 按钮组
            btn_size = 26
            btn_gap = 4
            num_txt = font_md.render(str(deployed), True, WHITE)
            num_w = num_txt.get_width()
            group_w = btn_size + btn_gap + num_w + btn_gap + btn_size
            group_x = item_rect.right - group_w - 8
            group_y = y + (item_h - btn_size) // 2

            # [-] 按钮
            minus_rect = pygame.Rect(group_x, group_y, btn_size, btn_size)
            m_hover = minus_rect.collidepoint(mx, my)
            m_color = (180, 80, 80) if m_hover else (100, 60, 60)
            pygame.draw.rect(screen, m_color, minus_rect, border_radius=4)
            m_txt = font_md.render("-", True, WHITE)
            screen.blit(m_txt, (minus_rect.centerx - m_txt.get_width() // 2,
                                 minus_rect.centery - m_txt.get_height() // 2))

            # 数量
            screen.blit(num_txt, (group_x + btn_size + btn_gap,
                                   group_y + (btn_size - num_txt.get_height()) // 2))

            # [+] 按钮
            plus_rect = pygame.Rect(group_x + btn_size + btn_gap + num_w + btn_gap,
                                    group_y, btn_size, btn_size)
            p_hover = plus_rect.collidepoint(mx, my)
            can_add = deployed < owned_count and len(ctx.team) < team_limit
            p_color = (80, 160, 80) if p_hover and can_add else (60, 100, 60) if can_add else (50, 50, 55)
            pygame.draw.rect(screen, p_color, plus_rect, border_radius=4)
            p_txt = font_md.render("+", True, WHITE)
            screen.blit(p_txt, (plus_rect.centerx - p_txt.get_width() // 2,
                                 plus_rect.centery - p_txt.get_height() // 2))

            ctx._team_btns[ant_id] = (minus_rect, plus_rect)

        # 确认/开始按钮
        btn_confirm = pygame.Rect(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT - 70, 200, 45)
        can_start = len(ctx.team) > 0
        confirm_text = "开始关卡" if has_level else "确认阵容"
        hover = btn_confirm.collidepoint(mx, my)
        draw_button(screen, btn_confirm, confirm_text, ctx.font_medium,
                    color=ACCENT_BLUE if can_start else (80, 80, 90),
                    hover=hover, disabled=not can_start)

        # 返回按钮
        btn_back = pygame.Rect(20, SCREEN_HEIGHT - 70, 100, 40)
        draw_button(screen, btn_back, "返回", ctx.font_small,
                    color=(120, 120, 140), hover=btn_back.collidepoint(mx, my))


def get_speed_text(ant_id, speed_lv):
    from ants_data import get_speed
    return str(get_speed(ant_id, speed_lv))


def get_defense_text(ant_id, defense_lv):
    from ants_data import get_defense
    return str(get_defense(ant_id, defense_lv))
