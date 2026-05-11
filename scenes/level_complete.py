"""关卡通过场景 — 含星级动画"""

import pygame
import math
from levels_data import get_level, get_star3_time_threshold
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    TEXT_COLOR, BG_COLOR, ACCENT_GOLD, WHITE, GRAY,
)
from ui_elements import draw_button, draw_text_centered
import font_helper
import os

# 星级图标加载（48×48，结算动画用）
_STAR_FULL = None
_STAR_EMPTY = None
_STAR_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                         'images', 'star')


def _ensure_star_icons():
    global _STAR_FULL, _STAR_EMPTY
    if _STAR_FULL is not None:
        return
    for attr, filename in [('_STAR_FULL', 'star_full.png'), ('_STAR_EMPTY', 'star_empty.png')]:
        path = os.path.join(_STAR_DIR, filename)
        try:
            img = pygame.image.load(path).convert_alpha()
            icon = pygame.transform.smoothscale(img, (48, 48))
        except Exception:
            # 代码生成回退
            icon = pygame.Surface((48, 48), pygame.SRCALPHA)
            if 'full' in filename:
                _draw_star_fallback(icon, 24, 24, 20, (218, 165, 32))
            else:
                _draw_star_fallback(icon, 24, 24, 20, (120, 120, 120), outline=True)
        if attr == '_STAR_FULL':
            _STAR_FULL = icon
        else:
            _STAR_EMPTY = icon


def _draw_star_fallback(surf, cx, cy, r, color, outline=False):
    points = []
    for i in range(10):
        angle = math.radians(-90 + i * 36)
        radius = r if i % 2 == 0 else r * 0.4
        px = cx + radius * math.cos(angle)
        py = cy + radius * math.sin(angle)
        points.append((px, py))
    if outline:
        pygame.draw.polygon(surf, color, points, 2)
    else:
        pygame.draw.polygon(surf, color, points)


class StarAnimation:
    """星级逐个点亮动画"""

    def __init__(self, stars, center_x, y):
        """
        stars: 0-3，获得的星数
        center_x: 星星区域水平中心
        y: 星星区域顶部y坐标
        """
        self.stars = stars
        self.center_x = center_x
        self.y = y
        self.timer = 0.0
        self.duration = 1.2  # 总动画时长
        self.star_delay = 0.3  # 每颗星间隔
        self.scale = 1.0
        self.glow_alpha = 0
        self.current_lit = 0  # 当前已点亮的星数
        self.done = False

    def update(self, dt):
        if self.done:
            return
        self.timer += dt

        # 计算当前应点亮几颗星
        target_lit = 0
        for s in range(self.stars):
            if self.timer >= s * self.star_delay:
                target_lit = s + 1

        # 缩放动画：新星点亮时 1.0→1.3→1.0
        if target_lit > self.current_lit:
            # 新星点亮，重置缩放
            self.current_lit = target_lit
            self.scale = 1.3
            self.glow_alpha = 80
        elif self.scale > 1.0:
            self.scale = max(1.0, self.scale - dt * 3.0)
        if self.glow_alpha > 0:
            self.glow_alpha = max(0, self.glow_alpha - dt * 200)

        if self.timer >= self.duration:
            self.done = True
            self.scale = 1.0
            self.glow_alpha = 0
            self.current_lit = self.stars

    def draw(self, screen):
        _ensure_star_icons()
        star_w = 48
        gap = 16
        total_w = star_w * 3 + gap * 2
        start_x = self.center_x - total_w // 2

        for s in range(3):
            sx = start_x + s * (star_w + gap)
            sy = self.y

            if s < self.current_lit:
                # 已点亮的星：金色 + 缩放
                icon = _STAR_FULL
                if self.scale > 1.0 and s == self.current_lit - 1:
                    # 当前正在动画的星
                    scaled_size = int(48 * self.scale)
                    icon = pygame.transform.smoothscale(_STAR_FULL, (scaled_size, scaled_size))
                    offset = (scaled_size - 48) // 2
                    screen.blit(icon, (sx - offset, sy - offset))
                    # 金色光晕
                    if self.glow_alpha > 0:
                        glow_surf = pygame.Surface((80, 80), pygame.SRCALPHA)
                        pygame.draw.circle(glow_surf, (218, 165, 32, int(self.glow_alpha)),
                                           (40, 40), 40)
                        screen.blit(glow_surf, (sx - 16, sy - 16))
                else:
                    screen.blit(icon, (sx, sy))
            else:
                # 未点亮：灰色空心星
                screen.blit(_STAR_EMPTY, (sx, sy))


class LevelCompleteScene:
    def __init__(self, ctx):
        self.ctx = ctx
        self.star_anim = None

    def _init_star_anim(self):
        """初始化星级动画（仅首次通关时触发）"""
        ctx = self.ctx
        # 使用GameState中已计算的星级
        stars = getattr(ctx, 'stars_earned', 0)

        center_x = SCREEN_WIDTH // 2
        star_y = 170
        self.star_anim = StarAnimation(stars, center_x, star_y)
        self._shown_stars = stars

    def handle_click(self, mx, my):
        ctx = self.ctx
        # 星级动画未完成时，点击跳过动画
        if self.star_anim and not self.star_anim.done:
            self.star_anim.done = True
            self.star_anim.current_lit = self.star_anim.stars
            return

        btn_next = pygame.Rect(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 80, 200, 50)
        btn_back = pygame.Rect(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 140, 200, 50)
        if btn_next.collidepoint(mx, my):
            self.star_anim = None  # 重置动画
            ctx.current_level = min(ctx.current_level + 1, 200)
            ctx.level_data = get_level(ctx.current_level)
            ctx.state = 'team_select'
        elif btn_back.collidepoint(mx, my):
            self.star_anim = None
            ctx.state = 'level_select'

    def draw(self, screen):
        ctx = self.ctx
        screen.fill(BG_COLOR)

        # "关卡通过!" 标题
        draw_text_centered(screen, "关卡通过!", ctx.font_xl, (100, 255, 100),
                           SCREEN_WIDTH // 2, 120)

        # 初始化星级动画（每次进入结算画面时初始化一次）
        if self.star_anim is None:
            self._init_star_anim()

        # 更新并绘制星级动画
        if self.star_anim:
            self.star_anim.update(1.0 / 60.0)  # 假设60fps
            self.star_anim.draw(screen)

            # 星级达成条件文字（动画完成后显示）
            if self.star_anim.done:
                self._draw_star_conditions(screen)

        # 奖励信息
        reward = ctx.level_data.get('reward_coins', 0)
        info_y = 280 if self.star_anim and self.star_anim.stars > 0 else 200
        info = ctx.font_medium.render(
            f"对战金币: {ctx.level_coins}  奖励: {reward}  共: {ctx.level_coins + reward}G",
            True, ACCENT_GOLD)
        screen.blit(info, (SCREEN_WIDTH // 2 - info.get_width() // 2, info_y))

        score = ctx.font_small.render(
            f"我方: {ctx.level_coins}G  敌方: {ctx.ai_coins}G  累计: {ctx.total_coins}G",
            True, TEXT_COLOR)
        screen.blit(score, (SCREEN_WIDTH // 2 - score.get_width() // 2, info_y + 40))

        # 搬运结算明细（如有自动结算金额）
        transit = getattr(ctx, 'transit_coins', 0)
        if transit > 0:
            transit_text = ctx.font_small.render(
                f"搬运结算 +{transit}G", True, (100, 200, 255))
            screen.blit(transit_text, (SCREEN_WIDTH // 2 - transit_text.get_width() // 2, info_y + 62))

        # 按钮（下移80px为星级动画腾出空间）
        btn_next = pygame.Rect(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 80, 200, 50)
        btn_back = pygame.Rect(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 140, 200, 50)
        draw_button(screen, btn_next, "下一关", ctx.font_medium,
                    hover=btn_next.collidepoint(*pygame.mouse.get_pos()))
        draw_button(screen, btn_back, "关卡选择", ctx.font_medium,
                    color=(120, 120, 140), hover=btn_back.collidepoint(*pygame.mouse.get_pos()))

    def _draw_star_conditions(self, screen):
        """绘制星级达成条件 ✓/✗"""
        ctx = self.ctx
        font = font_helper.get_font(16)
        center_x = SCREEN_WIDTH // 2
        y = 228  # 星星下方

        target = ctx.level_data.get('target_coins', 0)
        timer_total = ctx.level_data.get('timer', 90)
        remaining_pct = (ctx.level_timer / timer_total) if timer_total > 0 else 0

        time_threshold = get_star3_time_threshold(ctx.current_level)
        conditions = [
            (f"通关: {ctx.level_coins}G ≥ {target}G", ctx.level_coins >= target),
            (f"剩余时间: {remaining_pct * 100:.0f}%(需≥{time_threshold * 100:.0f}%)",
             remaining_pct >= time_threshold),
            (f"收集率: {getattr(ctx, 'collection_rate', 0) * 100:.0f}%",
             getattr(ctx, 'collection_rate', 0) >= 0.80),
        ]

        for i, (text, met) in enumerate(conditions):
            icon = "✓" if met else "✗"
            color = (100, 255, 100) if met else (255, 100, 100)
            line = f"{icon} {text}"
            surf = font.render(line, True, color)
            screen.blit(surf, (center_x - surf.get_width() // 2, y + i * 22))
