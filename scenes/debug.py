"""调试模式场景：设置金币、解锁关卡、解锁蚂蚁"""

import pygame
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    WHITE, GRAY, BG_COLOR, TEXT_COLOR,
    CARD_BG, CARD_BORDER, ACCENT_BLUE, ACCENT_GOLD, ACCENT_RED, BTN_HOVER,
)
from ants_data import ANTS, MAX_ATTR_LEVEL
from ui_elements import draw_card, draw_button
import font_helper


class DebugScene:
    def __init__(self, ctx):
        self.ctx = ctx
        self.coin_input = ""
        self.ant_level_input = "10"
        self.level_input = "200"
        self.active_input = None  # 'coins' / 'ant_level' / 'level'
        self.message = ""
        self.message_timer = 0.0

    def _show_msg(self, text):
        self.message = text
        self.message_timer = 2.0

    def _layout(self):
        """统一布局计算，确保 draw 和 handle_click 使用完全相同的位置"""
        pw, ph = 700, 520
        px = (SCREEN_WIDTH - pw) // 2
        py = (SCREEN_HEIGHT - ph) // 2
        cx = px + 30  # content x
        cw = pw - 60  # content width

        status_y = py + 50
        row1_y = status_y + 40  # 金币行
        row2_y = row1_y + 50    # 关卡行
        row3_y = row2_y + 50    # 蚂蚁行
        row4_y = row3_y + 50    # 一键满级
        row5_y = row4_y + 42    # 重置存档

        return {
            'px': px, 'py': py, 'pw': pw, 'ph': ph,
            'cx': cx, 'cw': cw,
            'inp_coin': pygame.Rect(cx + 80, row1_y - 4, 150, 28),
            'btn_set':  pygame.Rect(cx + 240, row1_y - 4, 80, 28),
            'inp_level': pygame.Rect(cx + 100, row2_y - 4, 100, 28),
            'btn_unlock': pygame.Rect(cx + 210, row2_y - 4, 120, 28),
            'inp_ant':  pygame.Rect(cx + 100, row3_y - 4, 100, 28),
            'btn_all':  pygame.Rect(cx + 210, row3_y - 4, 120, 28),
            'btn_max':  pygame.Rect(cx, row4_y, cw, 32),
            'btn_reset': pygame.Rect(cx, row5_y, cw, 32),
            'btn_back': pygame.Rect(px + 20, py + ph - 50, 100, 36),
            'close':    pygame.Rect(px + pw - 30, py + 6, 24, 24),
        }

    def handle_click(self, mx, my):
        ctx = self.ctx
        L = self._layout()

        # 关闭 / 返回
        if L['close'].collidepoint(mx, my) or L['btn_back'].collidepoint(mx, my):
            ctx.state = 'title'
            return

        # 金币输入框
        if L['inp_coin'].collidepoint(mx, my):
            self.active_input = 'coins'
            return
        # 金币设置按钮
        if L['btn_set'].collidepoint(mx, my):
            if self.coin_input.isdigit() and self.coin_input:
                amount = int(self.coin_input)
                ctx.sm.data['total_coins'] = amount
                ctx.sm.save()
                ctx.total_coins = amount
                self._show_msg(f"金币已设置为 {amount}")
            else:
                self._show_msg("请先输入数字")
            return

        # 关卡输入框
        if L['inp_level'].collidepoint(mx, my):
            self.active_input = 'level'
            return
        # 关卡解锁按钮
        if L['btn_unlock'].collidepoint(mx, my):
            if self.level_input.isdigit() and self.level_input:
                lv = min(int(self.level_input), 200)
                ctx.sm.data['max_level_passed'] = max(
                    ctx.sm.data.get('max_level_passed', 0), lv)
                ctx.sm.save()
                self._show_msg(f"已解锁到第{lv}关")
            else:
                self._show_msg("请先输入数字")
            return

        # 蚂蚁等级输入框
        if L['inp_ant'].collidepoint(mx, my):
            self.active_input = 'ant_level'
            return
        # 解锁全部蚂蚁
        if L['btn_all'].collidepoint(mx, my):
            if self.ant_level_input.isdigit() and self.ant_level_input:
                lv = min(int(self.ant_level_input), MAX_ATTR_LEVEL)
                for ant in ANTS:
                    aid = str(ant['id'])
                    if aid not in ctx.sm.data['ants']:
                        ctx.sm.data['ants'][aid] = {'count': 1, 'carry': lv, 'speed': lv, 'defense': lv}
                    else:
                        ctx.sm.data['ants'][aid]['count'] = max(
                            ctx.sm.data['ants'][aid].get('count', 0), 1)
                        ctx.sm.data['ants'][aid]['carry'] = max(
                            ctx.sm.data['ants'][aid].get('carry', 0), lv)
                        ctx.sm.data['ants'][aid]['speed'] = max(
                            ctx.sm.data['ants'][aid].get('speed', 0), lv)
                        ctx.sm.data['ants'][aid]['defense'] = max(
                            ctx.sm.data['ants'][aid].get('defense', 0), lv)
                ctx.sm.save()
                self._show_msg(f"全部蚂蚁已解锁 (三属性Lv{lv})")
            else:
                self._show_msg("请先输入等级")
            return

        # 一键满级
        if L['btn_max'].collidepoint(mx, my):
            ctx.sm.data['total_coins'] = 999999
            ctx.sm.data['max_level_passed'] = 200
            for ant in ANTS:
                aid = str(ant['id'])
                ctx.sm.data['ants'][aid] = {'count': 5, 'carry': MAX_ATTR_LEVEL, 'speed': MAX_ATTR_LEVEL, 'defense': MAX_ATTR_LEVEL}
            ctx.sm.save()
            ctx.total_coins = 999999
            self._show_msg("已一键满级：999999G / 200关 / 全蚂蚁三属性Lv200 x5")
            return

        # 重置存档
        if L['btn_reset'].collidepoint(mx, my):
            ctx.sm.reset()
            ctx.sm.ensure_starter_ant()
            ctx.total_coins = 0
            self._show_msg("存档已重置")
            return

        # 点击空白处取消输入焦点
        self.active_input = None

    def handle_key(self, event):
        """处理键盘输入"""
        if self.active_input is None:
            return
        if event.key in (pygame.K_RETURN, pygame.K_TAB):
            self.active_input = None
            return
        if event.key == pygame.K_ESCAPE:
            self.active_input = None
            return
        if event.key == pygame.K_BACKSPACE:
            if self.active_input == 'coins':
                self.coin_input = self.coin_input[:-1]
            elif self.active_input == 'level':
                self.level_input = self.level_input[:-1]
            elif self.active_input == 'ant_level':
                self.ant_level_input = self.ant_level_input[:-1]
            return
        if event.unicode.isdigit():
            target = {
                'coins': (self, 'coin_input', 7),
                'level': (self, 'level_input', 3),
                'ant_level': (self, 'ant_level_input', 3),
            }.get(self.active_input)
            if target:
                obj, attr, maxlen = target
                current = getattr(obj, attr)
                if len(current) < maxlen:
                    setattr(obj, attr, current + event.unicode)

    def update(self, dt):
        if self.message_timer > 0:
            self.message_timer -= dt
            if self.message_timer <= 0:
                self.message = ""
                self.message_timer = 0

    def draw(self, screen):
        ctx = self.ctx
        mx, my = pygame.mouse.get_pos()
        screen.fill(BG_COLOR)

        font_title = font_helper.get_font(22)
        font_md = font_helper.get_font(16)
        font_sm = font_helper.get_font(14)

        L = self._layout()
        px, py, pw, ph = L['px'], L['py'], L['pw'], L['ph']
        cx, cw = L['cx'], L['cw']

        panel = pygame.Rect(px, py, pw, ph)
        draw_card(screen, panel, bg_color=CARD_BG, border_color=CARD_BORDER,
                  shadow=True, radius=14)

        # 标题
        title = font_title.render("调试模式", True, ACCENT_RED)
        screen.blit(title, (panel.centerx - title.get_width() // 2, panel.y + 12))

        # 关闭按钮
        close_color = (255, 100, 100) if L['close'].collidepoint(mx, my) else (200, 80, 80)
        pygame.draw.rect(screen, close_color, L['close'], border_radius=4)
        close_txt = font_md.render("x", True, WHITE)
        screen.blit(close_txt, (L['close'].centerx - close_txt.get_width() // 2,
                                L['close'].centery - close_txt.get_height() // 2))

        # 当前状态
        status_y = py + 50
        status = font_sm.render(
            f"当前: 金币={ctx.sm.get_total_coins()}  "
            f"通关={ctx.sm.get_max_level()}/200  "
            f"蚂蚁={ctx.sm.get_owned_count()}只",
            True, GRAY)
        screen.blit(status, (cx, status_y))

        # ── 金币设置 ──
        row1_y = status_y + 40
        lbl = font_md.render("设置金币:", True, TEXT_COLOR)
        screen.blit(lbl, (cx, row1_y))
        self._draw_input(screen, L['inp_coin'], self.coin_input,
                         self.active_input == 'coins', font_md)
        draw_button(screen, L['btn_set'], "设置", font_sm,
                    color=ACCENT_BLUE, hover=L['btn_set'].collidepoint(mx, my))

        # ── 解锁关卡 ──
        row2_y = row1_y + 50
        lbl2 = font_md.render("解锁关卡:", True, TEXT_COLOR)
        screen.blit(lbl2, (cx, row2_y))
        self._draw_input(screen, L['inp_level'], self.level_input,
                         self.active_input == 'level', font_md)
        draw_button(screen, L['btn_unlock'], "解锁", font_sm,
                    color=ACCENT_GOLD, hover=L['btn_unlock'].collidepoint(mx, my))

        # ── 解锁蚂蚁 ──
        row3_y = row2_y + 50
        lbl3 = font_md.render("蚂蚁等级:", True, TEXT_COLOR)
        screen.blit(lbl3, (cx, row3_y))
        self._draw_input(screen, L['inp_ant'], self.ant_level_input,
                         self.active_input == 'ant_level', font_md)
        draw_button(screen, L['btn_all'], "解锁全部蚂蚁", font_sm,
                    color=(80, 160, 80), hover=L['btn_all'].collidepoint(mx, my))

        # ── 一键满级 ──
        draw_button(screen, L['btn_max'], "一键满级 (999999G / 200关 / 全蚂蚁Lv200x5)", font_sm,
                    color=ACCENT_GOLD, hover=L['btn_max'].collidepoint(mx, my))

        # ── 重置存档 ──
        draw_button(screen, L['btn_reset'], "重置存档", font_sm,
                    color=ACCENT_RED, hover=L['btn_reset'].collidepoint(mx, my))

        # ── 操作提示 ──
        tip_y = row3_y + 50 + 42 + 42 + 10
        tips = [
            "点击输入框后用键盘输入数字，回车/Tab确认",
            "设置金币：直接写入存档，不扣不加",
            "解锁关卡：设置已通关最高关卡数",
            "解锁全部蚂蚁：按设定等级解锁26只蚂蚁",
        ]
        for i, tip in enumerate(tips):
            t = font_sm.render(tip, True, GRAY)
            screen.blit(t, (cx, tip_y + i * 20))

        # ── 提示消息 ──
        if self.message and self.message_timer > 0:
            msg_surf = font_md.render(self.message, True, (100, 255, 100))
            msg_bg = pygame.Surface((msg_surf.get_width() + 20, msg_surf.get_height() + 10),
                                    pygame.SRCALPHA)
            pygame.draw.rect(msg_bg, (40, 40, 60, 220),
                             (0, 0, msg_bg.get_width(), msg_bg.get_height()), border_radius=8)
            screen.blit(msg_bg, (panel.centerx - msg_bg.get_width() // 2, panel.bottom + 10))
            screen.blit(msg_surf,
                        (panel.centerx - msg_surf.get_width() // 2, panel.bottom + 15))

        # 返回按钮
        draw_button(screen, L['btn_back'], "返回", font_md,
                    color=(120, 120, 140), hover=L['btn_back'].collidepoint(mx, my))

    def _draw_input(self, screen, rect, value, focused, font):
        bg = (255, 255, 240) if focused else (240, 238, 230)
        pygame.draw.rect(screen, bg, rect, border_radius=4)
        border_color = ACCENT_BLUE if focused else CARD_BORDER
        pygame.draw.rect(screen, border_color, rect, 1, border_radius=4)
        disp = value if value else "0"
        cursor = "|" if focused else ""
        txt = font.render(disp + cursor, True, TEXT_COLOR)
        screen.blit(txt, (rect.x + 6, rect.centery - txt.get_height() // 2))
