"""签到面板UI：7日签到日历、连续签到、周期进度、签到动效"""

import math
import pygame
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    TEXT_COLOR, WHITE, GRAY, BLACK,
    ACCENT_BLUE, ACCENT_GOLD, CARD_BG, CARD_BORDER,
    BTN_HOVER,
)
from ui_elements import draw_card, draw_button, draw_text_centered
import font_helper
from checkin_data import CHECKIN_BASE_REWARDS


class CheckinUI:
    """签到面板"""

    def __init__(self):
        self._overlay = None
        # 签到成功动画状态
        self._anim_active = False
        self._anim_reward = 0
        self._anim_timer = 0.0

    def draw(self, screen, mx, my, checkin_data, can_checkin):
        """
        绘制签到面板。

        checkin_data: SaveManager.get_checkin_data() 返回的签到数据
        can_checkin: bool, 今天是否可签到

        返回: (panel_rect, close_rect, checkin_btn_rect)
        """
        pw, ph = 600, 520
        px = (SCREEN_WIDTH - pw) // 2
        py = (SCREEN_HEIGHT - ph) // 2
        panel = pygame.Rect(px, py, pw, ph)

        # 遮罩层（缓存复用）
        if self._overlay is None:
            self._overlay = pygame.Surface(
                (SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            self._overlay.fill((0, 0, 0, 140))
        screen.blit(self._overlay, (0, 0))

        # 面板背景
        draw_card(screen, panel, bg_color=CARD_BG, border_color=CARD_BORDER,
                  shadow=True, radius=14)

        # 关闭按钮
        close_rect = pygame.Rect(panel.right - 30, panel.y + 6, 24, 24)
        hover_close = close_rect.collidepoint(mx, my)
        close_color = (255, 100, 100) if hover_close else (200, 80, 80)
        pygame.draw.rect(screen, close_color, close_rect, border_radius=4)
        close_txt = font_helper.get_font(18).render("x", True, WHITE)
        screen.blit(close_txt, (
            close_rect.centerx - close_txt.get_width() // 2,
            close_rect.centery - close_txt.get_height() // 2))

        # 标题
        font_title = font_helper.get_font(24)
        title = font_title.render("每日签到", True, ACCENT_GOLD)
        screen.blit(title, (panel.centerx - title.get_width() // 2,
                            panel.y + 14))

        # 连续签到 / 累计签到 统计
        font_info = font_helper.get_font(15)
        streak = checkin_data.get('streak', 0)
        total = checkin_data.get('total_checkins', 0)
        stat_text = f"连续签到 {streak} 天  |  累计签到 {total} 天"
        stat_color = ACCENT_GOLD if streak >= 3 else TEXT_COLOR
        stat_txt = font_info.render(stat_text, True, stat_color)
        screen.blit(stat_txt, (panel.centerx - stat_txt.get_width() // 2,
                               panel.y + 46))

        # ── 7日签到日历 ──
        current_day = checkin_data.get('current_day', 0)
        last_date = checkin_data.get('last_checkin_date')
        calendar_y = panel.y + 76
        checkin_btn_rect = self._draw_calendar(
            screen, px, calendar_y, pw, mx, my,
            current_day, last_date, can_checkin)

        # ── 底部：周期进度条 ──
        from datetime import date
        today = date.today().isoformat()
        already_checked_today = (last_date == today)
        completed = current_day

        bar_y = panel.bottom - 60
        bar_x = px + 30
        bar_w = pw - 60
        bar_h = 10

        pygame.draw.rect(screen, (50, 50, 70),
                         (bar_x, bar_y, bar_w, bar_h),
                         border_radius=bar_h // 2)
        ratio = completed / 7.0
        if ratio > 0:
            fill_w = max(bar_h, int(bar_w * ratio))
            color = (100, 180, 100) if completed >= 7 else ACCENT_GOLD
            pygame.draw.rect(screen, color,
                             (bar_x, bar_y, fill_w, bar_h),
                             border_radius=bar_h // 2)

        font_bar = font_helper.get_font(13)
        progress_label = f"周期进度 {completed}/7"
        label_txt = font_bar.render(progress_label, True, TEXT_COLOR)
        screen.blit(label_txt, (bar_x, bar_y + bar_h + 4))

        # 底部提示
        hint = font_bar.render("每天签到获得金币，连续7天完成周期获得额外奖励",
                               True, GRAY)
        screen.blit(hint, (panel.centerx - hint.get_width() // 2,
                           panel.bottom - 24))

        # ── 签到成功浮动动画 ──
        if self._anim_active:
            self._draw_reward_float(screen, panel)

        return panel, close_rect, checkin_btn_rect

    def _draw_calendar(self, screen, px, py, pw, mx, my,
                       current_day, last_date, can_checkin):
        """绘制7日签到日历，返回签到按钮Rect"""
        font_day = font_helper.get_font(14)
        font_reward = font_helper.get_font(13)
        font_big = font_helper.get_font(22)
        font_tag = font_helper.get_font(11)

        col_w = (pw - 40) // 7
        col_gap = 4
        start_x = px + 20

        checkin_btn_rect = None

        # next_day: 下一个要签到的天数（current_day 是已签到天数，+1 得到下一个）
        next_day = current_day + 1 if current_day < 7 else 1

        for i in range(7):
            day_num = i + 1
            x = start_x + i * (col_w + col_gap)
            y = py + 10
            cell_h = 110
            is_day7 = (day_num == 7)

            # 判断状态
            if day_num < next_day:
                status = 'done'
            elif day_num == next_day and can_checkin:
                status = 'today'
            else:
                status = 'future'

            # ── 单元格背景 ──
            cell_rect = pygame.Rect(x, y, col_w, cell_h)
            border_w = 1
            if status == 'today':
                if is_day7:
                    bg_color = (255, 240, 190)
                    border_color = ACCENT_GOLD
                    border_w = 3
                else:
                    bg_color = (255, 245, 200)
                    border_color = ACCENT_GOLD
                    border_w = 2
            elif status == 'done':
                bg_color = (220, 240, 220)
                border_color = (150, 200, 150)
            else:
                bg_color = (240, 238, 230)
                border_color = CARD_BORDER

            # Day7 特殊边框
            if is_day7 and status != 'future':
                border_color = ACCENT_GOLD
                if status != 'done':
                    border_w = max(border_w, 2)

            pygame.draw.rect(screen, bg_color, cell_rect, border_radius=10)
            pygame.draw.rect(screen, border_color, cell_rect,
                             border_w, border_radius=10)

            # ── 顶部：天数标签 ──
            tag_h = 22
            tag_rect = pygame.Rect(x, y, col_w, tag_h)
            if status == 'today':
                tag_bg = ACCENT_GOLD
                tag_tc = WHITE
            elif is_day7 and status != 'future':
                tag_bg = ACCENT_GOLD
                tag_tc = WHITE
            else:
                tag_bg = border_color if status == 'done' else CARD_BORDER
                tag_tc = WHITE if status == 'done' else TEXT_COLOR
            pygame.draw.rect(screen, tag_bg, tag_rect,
                             border_top_left_radius=10, border_top_right_radius=10,
                             border_bottom_left_radius=0, border_bottom_right_radius=0)
            tag_text = f"第{day_num}天"
            tag_txt = font_tag.render(tag_text, True, tag_tc)
            screen.blit(tag_txt, (
                cell_rect.centerx - tag_txt.get_width() // 2,
                y + (tag_h - tag_txt.get_height()) // 2))

            # ── 中部：状态图标 ──
            icon_y = y + tag_h + 6
            icon_size = min(col_w - 10, 38)

            if status == 'done':
                # 已签到：绿色圆形 + ✓
                icon_color = (100, 180, 100)
                pygame.draw.circle(screen, icon_color,
                                   (cell_rect.centerx,
                                    icon_y + icon_size // 2),
                                   icon_size // 2)
                check_txt = font_big.render("✓", True, WHITE)
                screen.blit(check_txt, (
                    cell_rect.centerx - check_txt.get_width() // 2,
                    icon_y + (icon_size - check_txt.get_height()) // 2))
            elif status == 'today':
                if is_day7:
                    # 第7天大奖：金色星形
                    star_cx = cell_rect.centerx
                    star_cy = icon_y + icon_size // 2
                    self._draw_star(screen, star_cx, star_cy,
                                    icon_size // 2, ACCENT_GOLD)
                    crown_txt = font_tag.render("大", True, WHITE)
                    screen.blit(crown_txt, (
                        star_cx - crown_txt.get_width() // 2,
                        star_cy - crown_txt.get_height() // 2))
                else:
                    # 今日可签：金色圆形 + ★
                    pygame.draw.circle(screen, ACCENT_GOLD,
                                       (cell_rect.centerx,
                                        icon_y + icon_size // 2),
                                       icon_size // 2)
                    today_txt = font_big.render("★", True, WHITE)
                    screen.blit(today_txt, (
                        cell_rect.centerx - today_txt.get_width() // 2,
                        icon_y + (icon_size - today_txt.get_height()) // 2))
            else:
                # 未签到：金币图标（金色圆形 + "G"）
                coin_cx = cell_rect.centerx
                coin_cy = icon_y + icon_size // 2
                pygame.draw.circle(screen, ACCENT_GOLD,
                                   (coin_cx, coin_cy),
                                   icon_size // 2)
                g_font_big = font_helper.get_font(16)
                g_txt_big = g_font_big.render("G", True, WHITE)
                screen.blit(g_txt_big, (
                    coin_cx - g_txt_big.get_width() // 2,
                    coin_cy - g_txt_big.get_height() // 2))

            # ── 底部：奖励数量 ──
            reward = CHECKIN_BASE_REWARDS[i]
            reward_y = icon_y + icon_size + 5

            if is_day7 and status != 'future':
                reward_text = f"+{reward}"
                reward_txt = font_big.render(reward_text, True, ACCENT_GOLD)
            else:
                reward_text = f"+{reward}"
                reward_txt = font_reward.render(reward_text, True, ACCENT_GOLD)
            screen.blit(reward_txt, (
                cell_rect.centerx - reward_txt.get_width() // 2, reward_y))

            # 币图标
            g_font = font_helper.get_font(10)
            g_txt = g_font.render("G", True, ACCENT_GOLD)
            screen.blit(g_txt, (
                cell_rect.centerx + reward_txt.get_width() // 2 + 2,
                reward_y + 2))

            # ── 今日待签到：底部签到按钮 ──
            if status == 'today':
                btn_rect = pygame.Rect(x + 2, cell_rect.bottom - 26,
                                       col_w - 4, 22)
                hover = btn_rect.collidepoint(mx, my)
                draw_button(screen, btn_rect, "签到", font_tag,
                            color=ACCENT_GOLD, hover=hover, border_radius=6)
                checkin_btn_rect = btn_rect

        return checkin_btn_rect

    def _draw_star(self, screen, cx, cy, radius, color):
        """绘制五角星"""
        points = []
        for i in range(5):
            angle = math.radians(-90 + i * 72)
            px_ = cx + radius * math.cos(angle)
            py_ = cy + radius * math.sin(angle)
            points.append((px_, py_))
            angle2 = math.radians(-90 + i * 72 + 36)
            px2 = cx + radius * 0.4 * math.cos(angle2)
            py2 = cy + radius * 0.4 * math.sin(angle2)
            points.append((px2, py2))
        pygame.draw.polygon(screen, color, points)
        pygame.draw.polygon(screen, (180, 130, 20), points, 2)

    def _draw_reward_float(self, screen, panel):
        """绘制签到成功浮动奖励文字"""
        if self._anim_reward <= 0:
            return
        t = self._anim_timer
        alpha = max(0, int(255 * (1.0 - t / 1.5)))
        y_offset = int(40 * t)

        font_ft = font_helper.get_font(22)
        text = f"+{self._anim_reward} 金币"
        txt_surf = font_ft.render(text, True, ACCENT_GOLD)
        txt_surf.set_alpha(alpha)
        ft_x = panel.centerx
        ft_y = panel.centery - 40 - y_offset
        screen.blit(txt_surf, (ft_x - txt_surf.get_width() // 2, ft_y))

    def handle_click(self, mx, my, checkin_data, can_checkin):
        """处理点击。返回 action 或 None。"""
        pw, ph = 600, 520
        px = (SCREEN_WIDTH - pw) // 2
        py = (SCREEN_HEIGHT - ph) // 2

        from datetime import date
        current_day = checkin_data.get('current_day', 0)
        last_date = checkin_data.get('last_checkin_date')
        today = date.today().isoformat()
        already_checked_today = (last_date == today)

        # next_day: 下一个要签到的天数
        next_day = current_day + 1 if current_day < 7 else 1

        col_w = (pw - 40) // 7
        col_gap = 4
        start_x = px + 20
        calendar_y = py + 76  # 与 draw() 中 calendar_y 保持一致

        for i in range(7):
            day_num = i + 1
            if day_num != next_day:
                continue
            if already_checked_today or not can_checkin:
                continue

            x = start_x + i * (col_w + col_gap)
            cell_y = calendar_y + 10
            # 整个单元格都可点击签到
            cell_rect = pygame.Rect(x, cell_y, col_w, 110)
            if cell_rect.collidepoint(mx, my):
                return ('checkin',)

        return None

    def start_reward_animation(self, reward):
        """启动签到成功动画"""
        self._anim_active = True
        self._anim_reward = reward
        self._anim_timer = 0.0

    def update(self, dt):
        """更新动画计时器"""
        if self._anim_active:
            self._anim_timer += dt
            if self._anim_timer >= 1.5:
                self._anim_active = False
                self._anim_timer = 0.0

    def scroll(self, dy):
        """签到面板无滚动内容，但保持接口一致"""
        pass
