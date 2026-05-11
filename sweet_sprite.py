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

    def draw_with_hp_effect(self, screen):
        """绘制甜点 + 数量标签"""
        if not self.alive:
            return

        screen.blit(self.image, self.rect)

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
