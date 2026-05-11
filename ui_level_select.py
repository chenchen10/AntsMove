"""关卡选择界面：200关分页展示，含星级图标"""

import pygame
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, TEXT_COLOR, WHITE, GRAY,
    ACCENT_BLUE, ACCENT_GOLD, CARD_BG, CARD_BORDER, BG_COLOR,
)
from ui_elements import draw_card, draw_button, draw_text_centered
from levels_data import get_level, get_stage_info, TERRAIN_NAMES
import font_helper
import os

# 星级图标预加载（20×20缩放）
_STAR_ICONS = {}
_ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'images', 'star')


def _load_star_icons():
    global _STAR_ICONS
    if _STAR_ICONS:
        return
    for key, filename in [('full', 'star_full.png'), ('empty', 'star_empty.png')]:
        path = os.path.join(_ASSETS_DIR, filename)
        try:
            img = pygame.image.load(path).convert_alpha()
            _STAR_ICONS[key] = pygame.transform.smoothscale(img, (20, 20))
        except Exception:
            # 代码生成回退
            surf = pygame.Surface((20, 20), pygame.SRCALPHA)
            if key == 'full':
                # 金色实心星
                _draw_star_polygon(surf, 10, 10, 9, (218, 165, 32))
            else:
                # 灰色空心星
                _draw_star_polygon(surf, 10, 10, 9, (120, 120, 120), outline=True)
            _STAR_ICONS[key] = surf


def _draw_star_polygon(surf, cx, cy, r, color, outline=False):
    """绘制五角星"""
    import math
    points = []
    for i in range(10):
        angle = math.radians(-90 + i * 36)
        radius = r if i % 2 == 0 else r * 0.4
        px = cx + radius * math.cos(angle)
        py = cy + radius * math.sin(angle)
        points.append((px, py))
    if outline:
        pygame.draw.polygon(surf, (0, 0, 0, 0), points)  # transparent
        pygame.draw.polygon(surf, color, points, 2)
    else:
        pygame.draw.polygon(surf, color, points)


_load_star_icons()


class LevelSelectUI:
    """关卡选择界面"""

    def __init__(self, save_manager):
        self.sm = save_manager
        self.page = 0  # 每页20关
        self.per_page = 20
        self.total_pages = 10  # 200 / 20
        self.scroll_y = 0

    def draw(self, screen, mx, my):
        screen.fill(BG_COLOR)

        # 标题
        draw_text_centered(screen, "关卡选择", font_helper.get_font(36),
                           TEXT_COLOR, SCREEN_WIDTH // 2, 20)

        # 总星数显示
        total_stars = self._get_total_stars()
        max_stars = 600  # 200关 × 3星
        star_font = font_helper.get_font(24)
        star_text = star_font.render(f"★ {total_stars}/{max_stars}", True, ACCENT_GOLD)
        # 放在标题右侧
        screen.blit(star_text, (SCREEN_WIDTH // 2 + 120, 26))

        # 页码导航
        self._draw_pagination(screen, mx, my)

        # 关卡网格（4列5行）
        self._draw_level_grid(screen, mx, my)

        # 返回按钮
        btn_back = pygame.Rect(20, SCREEN_HEIGHT - 50, 120, 40)
        hover_back = btn_back.collidepoint(mx, my)
        draw_button(screen, btn_back, "返回", font_helper.get_font(20),
                    color=(120, 120, 140), hover=hover_back)
        return btn_back

    def _draw_pagination(self, screen, mx, my):
        """页码导航"""
        font = font_helper.get_font(18)
        y = 60

        # 上一页
        if self.page > 0:
            btn_prev = pygame.Rect(SCREEN_WIDTH // 2 - 150, y, 80, 30)
            hover = btn_prev.collidepoint(mx, my)
            draw_button(screen, btn_prev, "< 上一页", font, hover=hover)

        # 页码显示
        draw_text_centered(screen, f"第 {self.page + 1} / {self.total_pages} 页",
                           font, TEXT_COLOR, SCREEN_WIDTH // 2, y + 5)

        # 下一页
        if self.page < self.total_pages - 1:
            btn_next = pygame.Rect(SCREEN_WIDTH // 2 + 70, y, 80, 30)
            hover = btn_next.collidepoint(mx, my)
            draw_button(screen, btn_next, "下一页 >", font, hover=hover)

    def _get_total_stars(self):
        """获取累计总星数"""
        levels = self.sm.data.get('levels', {})
        return sum(lv.get('best_stars', 0) for lv in levels.values())

    def _get_level_stars(self, level_num):
        """获取指定关卡的星级"""
        levels = self.sm.data.get('levels', {})
        return levels.get(str(level_num), {}).get('best_stars', 0)

    def _draw_level_grid(self, screen, mx, my):
        """关卡网格"""
        font_sm = font_helper.get_font(14)
        font_md = font_helper.get_font(16)

        cols = 5
        rows = 4
        cell_w = 100
        cell_h = 95  # 从90增加到95，为星级留空间
        gap = 10
        grid_w = cols * cell_w + (cols - 1) * gap
        start_x = (SCREEN_WIDTH - grid_w) // 2
        start_y = 100

        max_passed = self.sm.get_max_level()
        buttons = []
        hovered_locked = None

        for i in range(self.per_page):
            level_num = self.page * self.per_page + i + 1
            if level_num > 200:
                break

            col = i % cols
            row = i // cols
            x = start_x + col * (cell_w + gap)
            y = start_y + row * (cell_h + gap)

            rect = pygame.Rect(x, y, cell_w, cell_h)
            unlocked = level_num <= max_passed + 1
            passed = level_num <= max_passed
            hover = rect.collidepoint(mx, my)

            # 卡片背景
            if passed:
                bg = (60, 120, 60)
            elif unlocked and hover:
                bg = (200, 220, 240)
            elif unlocked:
                bg = CARD_BG
            else:
                bg = (60, 60, 70)
            draw_card(screen, rect, bg_color=bg, shadow=unlocked)

            # 关卡号
            color = WHITE if unlocked else GRAY
            txt = font_md.render(str(level_num), True, color)
            screen.blit(txt, (rect.centerx - txt.get_width() // 2, y + 6))

            if unlocked:
                info = get_level(level_num)

                # 地形名
                terrain_txt = font_sm.render(info['terrain_name'][:2], True,
                                             (180, 200, 180) if not passed else (200, 255, 200))
                screen.blit(terrain_txt, (rect.centerx - terrain_txt.get_width() // 2, y + 26))

                # 目标金币
                target_txt = font_sm.render(f"目标:{info['target_coins']}", True, ACCENT_GOLD)
                screen.blit(target_txt, (rect.centerx - target_txt.get_width() // 2, y + 44))

                # 限时
                timer_txt = font_sm.render(f"{info['timer']}s", True, (180, 180, 200))
                screen.blit(timer_txt, (rect.centerx - timer_txt.get_width() // 2, y + 58))

                # 星级图标（格子底部，3颗20×20星，间距4px）
                stars = self._get_level_stars(level_num)
                star_total_w = 20 * 3 + 4 * 2  # 68px
                star_start_x = rect.centerx - star_total_w // 2
                star_y = y + cell_h - 26  # 底部留边距
                for s in range(3):
                    icon_key = 'full' if s < stars else 'empty'
                    icon = _STAR_ICONS.get(icon_key)
                    if icon:
                        screen.blit(icon, (star_start_x + s * 24, star_y))
            else:
                lock_txt = font_sm.render("🔒", True, GRAY)
                screen.blit(lock_txt, (rect.centerx - lock_txt.get_width() // 2, y + 38))
                if hover:
                    hovered_locked = level_num

            if unlocked:
                buttons.append((rect, level_num))

        # hover 提示：锁定关卡显示解锁条件
        if hovered_locked:
            req_level = hovered_locked - 1
            tip = f"通过第{req_level}关解锁" if req_level > 0 else "初始关卡"
            tip_surf = font_sm.render(tip, True, WHITE)
            tw, th = tip_surf.get_size()
            pad = 8
            tip_w = tw + pad * 2
            tip_h = th + pad * 2
            tip_x = min(mx + 12, SCREEN_WIDTH - tip_w - 4)
            tip_y = max(my - tip_h - 4, 4)
            tip_rect = pygame.Rect(tip_x, tip_y, tip_w, tip_h)
            draw_card(screen, tip_rect, bg_color=(50, 50, 60), border_color=(80, 80, 90),
                      shadow=True, radius=6)
            screen.blit(tip_surf, (tip_x + pad, tip_y + pad))

        return buttons

    def handle_click(self, mx, my):
        """处理点击，返回关卡号或None"""
        # 页码按钮
        font = font_helper.get_font(18)
        y = 60
        if self.page > 0:
            btn_prev = pygame.Rect(SCREEN_WIDTH // 2 - 150, y, 80, 30)
            if btn_prev.collidepoint(mx, my):
                self.page -= 1
                return None
        if self.page < self.total_pages - 1:
            btn_next = pygame.Rect(SCREEN_WIDTH // 2 + 70, y, 80, 30)
            if btn_next.collidepoint(mx, my):
                self.page += 1
                return None

        # 关卡按钮
        cols = 5
        cell_w = 100
        cell_h = 95
        gap = 10
        grid_w = cols * cell_w + (cols - 1) * gap
        start_x = (SCREEN_WIDTH - grid_w) // 2
        start_y = 100

        max_passed = self.sm.get_max_level()

        for i in range(self.per_page):
            level_num = self.page * self.per_page + i + 1
            if level_num > 200:
                break
            if level_num > max_passed + 1:
                continue

            col = i % cols
            row = i // cols
            x = start_x + col * (cell_w + gap)
            y_pos = start_y + row * (cell_h + gap)
            rect = pygame.Rect(x, y_pos, cell_w, cell_h)
            if rect.collidepoint(mx, my):
                return level_num

        return None
