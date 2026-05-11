"""研磨机精灵"""

import pygame
from config import GRINDER_SIZE, GRINDER_X, GRINDER_Y, GRINDER_COLOR


class Grinder(pygame.sprite.Sprite):
    """研磨机：蚂蚁在此交付甜食换取金币"""

    def __init__(self, x=None, y=None, color=None, label=""):
        super().__init__()
        self.x = x if x is not None else GRINDER_X
        self.y = y if y is not None else GRINDER_Y
        self.label = label
        self.size = GRINDER_SIZE
        self.grinder_color = color or GRINDER_COLOR
        self.image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(self.x, self.y))
        self._draw_grinder()

    def _draw_grinder(self):
        self.image.fill((0, 0, 0, 0))
        center = self.size // 2
        gc = self.grinder_color

        body_rect = pygame.Rect(6, self.size // 3, self.size - 12, self.size * 2 // 3 - 6)
        pygame.draw.rect(self.image, gc, body_rect, border_radius=4)

        funnel_points = [
            (center - self.size // 3, self.size // 3),
            (center + self.size // 3, self.size // 3),
            (center + self.size // 5, 6),
            (center - self.size // 5, 6)
        ]
        lighter = (min(255, gc[0] + 40), min(255, gc[1] + 40), min(255, gc[2] + 40))
        darker = (max(0, gc[0] - 30), max(0, gc[1] - 30), max(0, gc[2] - 30))
        pygame.draw.polygon(self.image, lighter, funnel_points)
        pygame.draw.polygon(self.image, darker, funnel_points, 2)

        pygame.draw.circle(self.image, darker, (center, center + 5), 8)
        pygame.draw.circle(self.image, (200, 200, 210), (center, center + 5), 4)

        pygame.draw.rect(self.image, (218, 165, 32),
                         (center - 6, self.size - 12, 12, 8), border_radius=2)

    def draw(self, screen):
        screen.blit(self.image, self.rect)
