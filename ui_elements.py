"""共享UI组件：卡片、按钮、进度条等"""

import pygame
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    CARD_BG, CARD_BORDER, TEXT_COLOR, WHITE, BLACK, GRAY,
    ACCENT_BLUE, ACCENT_RED, ACCENT_GOLD, BTN_HOVER, BG_COLOR,
)


def draw_card(surface, rect, bg_color=CARD_BG, border_color=CARD_BORDER,
              radius=8, shadow=True, shadow_offset=3):
    """绘制圆角卡片（带阴影）"""
    if shadow:
        shadow_rect = pygame.Rect(rect.x + shadow_offset, rect.y + shadow_offset,
                                  rect.width, rect.height)
        shadow_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        pygame.draw.rect(shadow_surf, (0, 0, 0, 50),
                         (0, 0, rect.width, rect.height), border_radius=radius)
        surface.blit(shadow_surf, shadow_rect)
    pygame.draw.rect(surface, bg_color, rect, border_radius=radius)
    pygame.draw.rect(surface, border_color, rect, 1, border_radius=radius)


def draw_button(surface, rect, text, font, color=ACCENT_BLUE, text_color=WHITE,
                hover=False, disabled=False, border_radius=8):
    """绘制按钮，返回是否被点击"""
    if disabled:
        bg = (80, 80, 90)
        tc = (140, 140, 150)
    elif hover:
        bg = BTN_HOVER
        tc = WHITE
    else:
        bg = color
        tc = text_color

    pygame.draw.rect(surface, bg, rect, border_radius=border_radius)
    pygame.draw.rect(surface, (60, 80, 120) if not disabled else (60, 60, 70),
                     rect, 1, border_radius=border_radius)

    txt = font.render(text, True, tc)
    surface.blit(txt, (rect.centerx - txt.get_width() // 2,
                       rect.centery - txt.get_height() // 2))


def draw_progress_bar(surface, x, y, w, h, ratio, color=ACCENT_BLUE, bg=(50, 50, 70)):
    """绘制进度条"""
    pygame.draw.rect(surface, bg, (x, y, w, h), border_radius=h // 2)
    if ratio > 0:
        fill_w = max(h, int(w * min(1.0, ratio)))
        pygame.draw.rect(surface, color, (x, y, fill_w, h), border_radius=h // 2)


def draw_text_centered(surface, text, font, color, center_x, y):
    """居中绘制文字"""
    txt = font.render(text, True, color)
    surface.blit(txt, (center_x - txt.get_width() // 2, y))
    return txt.get_height()
