"""甜点精灵类：支持数量系统、形态随数量变化"""

import pygame
import math
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, SWEET_SIZE_BASE,
    SWEET_COLORS,
)
import font_helper


def _get_qty_font():
    return font_helper.get_font(20)


class Sweet(pygame.sprite.Sprite):
    """甜点精灵：数量系统 + 形态随剩余数量变化"""

    def __init__(self, sweet_type, x, y, max_hp, coin_per, assets=None, quantity=20):
        super().__init__()
        self.sweet_type = sweet_type
        self.x = float(x)
        self.y = float(y)
        self.max_hp = max_hp
        self.hp = max_hp
        self.coin_per = coin_per
        self.alive = True
        self.assets = assets or {}
        self.remaining = quantity

        self.base_size = SWEET_SIZE_BASE
        self.current_size = SWEET_SIZE_BASE
        self._update_image()

        # 刷新闪烁效果（新生成时触发）
        self.flicker_timer = 0.0
        self.flicker_duration = 1.0  # 总时长1s
        self.flicker_active = False

    def _update_image(self):
        """根据剩余数量选择对应形态的PNG图片"""
        total = self.remaining
        if total > 13:
            state = 'full'
        elif total > 6:
            state = '60'
        else:
            state = '30'
        key = f'{self.sweet_type}_{state}'
        if key in self.assets:
            self.image = self.assets[key]
        else:
            ratio = max(0.4, total / 20)
            self.current_size = max(12, int(self.base_size * ratio))
            self.image = pygame.Surface((self.current_size, self.current_size), pygame.SRCALPHA)
            color = SWEET_COLORS.get(self.sweet_type, (200, 200, 200))
            c = self.current_size // 2
            pygame.draw.circle(self.image, color, (c, c), c)
            pygame.draw.circle(self.image, (255, 255, 255), (c, c), c, 2)
        self.current_size = self.image.get_width()
        self.rect = self.image.get_rect(center=(int(self.x), int(self.y)))

    def take_damage(self):
        """受到伤害，HP归零时remaining-1并回满血。remaining归零时消失。"""
        if not self.alive:
            return False
        self.hp -= 1
        if self.hp <= 0:
            self.remaining -= 1
            if self.remaining <= 0:
                self.alive = False
                return True
            self.hp = self.max_hp
        self._update_image()
        return False

    def start_flicker(self):
        """启动刷新闪烁效果"""
        self.flicker_active = True
        self.flicker_timer = 0.0

    def update_flicker(self, dt):
        """更新闪烁计时器"""
        if self.flicker_active:
            self.flicker_timer += dt
            if self.flicker_timer >= self.flicker_duration:
                self.flicker_active = False
                self.flicker_timer = 0.0

    def draw_with_hp_effect(self, screen):
        """绘制甜点 + 卡通化高光/阴影 + 数量标签"""
        if not self.alive:
            return

        screen.blit(self.image, self.rect)

        size = self.current_size
        cx, cy = self.rect.centerx, self.rect.centery

        # 刷新闪烁效果（2次循环，正弦波渐入渐出）
        if self.flicker_active:
            import math
            progress = self.flicker_timer / self.flicker_duration
            # 2个循环 = sin(4π * progress)
            alpha = int(abs(math.sin(4 * math.pi * progress)) * 120)
            glow_r = size // 2 + 8
            glow_surf = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
            sweet_color = SWEET_COLORS.get(self.sweet_type, (200, 200, 200))
            pygame.draw.circle(glow_surf, (*sweet_color, alpha), (glow_r, glow_r), glow_r)
            screen.blit(glow_surf, (cx - glow_r, cy - glow_r))

        # 底部阴影（深色半椭圆）
        shadow_w = int(size * 0.7)
        shadow_h = int(size * 0.15)
        shadow_surf = pygame.Surface((shadow_w, shadow_h * 2), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow_surf, (0, 0, 0, 50),
                            (0, 0, shadow_w, shadow_h * 2))
        shadow_rect = shadow_surf.get_rect(center=(cx, cy + size // 2 - 2))
        screen.blit(shadow_surf, shadow_rect)

        # 高光点（左上角白色小圆）
        hl_r = max(2, int(size * 0.08))
        hl_x = cx - int(size * 0.2)
        hl_y = cy - int(size * 0.2)
        hl_surf = pygame.Surface((hl_r * 2, hl_r * 2), pygame.SRCALPHA)
        pygame.draw.circle(hl_surf, (255, 255, 255, 180), (hl_r, hl_r), hl_r)
        screen.blit(hl_surf, (hl_x - hl_r, hl_y - hl_r))

        # 数量标签（半透明胶囊 + 手绘× + 数字）
        font = _get_qty_font()
        num_surf = font.render(str(self.remaining), True, (255, 255, 255))
        nw, nh = num_surf.get_size()
        icon_size = 10
        gap = 4
        pad_x, pad_y = 6, 3
        badge_w = icon_size + gap + nw + pad_x * 2
        badge_h = max(icon_size, nh) + pad_y * 2
        badge_x = self.rect.centerx - badge_w // 2
        badge_y = self.rect.top - badge_h - 4
        badge_rect = pygame.Rect(badge_x, badge_y, badge_w, badge_h)

        badge_surf = pygame.Surface((badge_w, badge_h), pygame.SRCALPHA)
        pygame.draw.rect(badge_surf, (0, 0, 0, 140), (0, 0, badge_w, badge_h), border_radius=badge_h // 2)
        screen.blit(badge_surf, badge_rect)

        cx_icon = badge_x + pad_x + icon_size // 2
        cy_icon = badge_y + badge_h // 2
        half = icon_size // 2 - 1
        pygame.draw.line(screen, (255, 80, 80),
                         (cx_icon - half, cy_icon - half),
                         (cx_icon + half, cy_icon + half), 2)
        pygame.draw.line(screen, (255, 80, 80),
                         (cx_icon + half, cy_icon - half),
                         (cx_icon - half, cy_icon + half), 2)
        screen.blit(num_surf, (badge_x + pad_x + icon_size + gap, badge_y + pad_y))
