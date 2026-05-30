"""小地图：右下角，蚂蚁/甜点分布 + 视口矩形 + 点击跳转"""

import pygame
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    WORLD_WIDTH, WORLD_HEIGHT,
    MINIMAP_W, MINIMAP_H,
)

# 小地图位置（供 main.py 拦截拖拽点击使用）
_MINIMAP_MARGIN = 12
MINIMAP_X = SCREEN_WIDTH - MINIMAP_W - _MINIMAP_MARGIN
MINIMAP_Y = SCREEN_HEIGHT - MINIMAP_H - _MINIMAP_MARGIN


class MiniMap:
    """右下角小地图，显示全局态势和相机视口"""

    MARGIN = 12
    BG_COLOR = (0, 0, 0, 160)
    BORDER_COLOR = (255, 255, 255, 200)
    PLAYER_COLOR = (70, 130, 220)
    AI_COLOR = (220, 80, 70)
    SWEET_COLOR = (255, 215, 0)
    VIEWPORT_COLOR = (255, 255, 255, 180)

    def __init__(self):
        self.x = SCREEN_WIDTH - MINIMAP_W - self.MARGIN
        self.y = SCREEN_HEIGHT - MINIMAP_H - self.MARGIN
        self.rect = pygame.Rect(self.x, self.y, MINIMAP_W, MINIMAP_H)

    # ── 坐标转换 ──

    def _world_to_mini(self, world_x, world_y):
        """世界坐标 → 小地图像素坐标"""
        mx = self.x + (world_x / WORLD_WIDTH) * MINIMAP_W
        my = self.y + (world_y / WORLD_HEIGHT) * MINIMAP_H
        return int(mx), int(my)

    def _mini_to_world(self, mini_x, mini_y):
        """小地图像素坐标 → 世界坐标"""
        rel_x = (mini_x - self.x) / MINIMAP_W
        rel_y = (mini_y - self.y) / MINIMAP_H
        world_x = rel_x * WORLD_WIDTH
        world_y = rel_y * WORLD_HEIGHT
        return world_x, world_y

    # ── 点击处理 ──

    def handle_click(self, mx, my, camera):
        """处理小地图点击，触发相机跳转。

        Args:
            mx, my: 鼠标屏幕坐标
            camera: Camera 实例

        Returns:
            True 表示点击被消费（在小地图区域内）
        """
        if not self.rect.collidepoint(mx, my):
            return False

        world_x, world_y = self._mini_to_world(mx, my)
        # 限制在世界边界内
        world_x = max(0.0, min(float(WORLD_WIDTH), world_x))
        world_y = max(0.0, min(float(WORLD_HEIGHT), world_y))
        # 发起平滑跳转
        camera.start_jump(world_x, world_y)
        return True

    # ── 绘制 ──

    def draw(self, screen, ctx):
        """绘制小地图，包含全局态势和当前视口矩形"""
        cam = ctx.camera

        # 半透明背景
        bg_surf = pygame.Surface((MINIMAP_W, MINIMAP_H), pygame.SRCALPHA)
        bg_surf.fill(self.BG_COLOR)
        screen.blit(bg_surf, (self.x, self.y))

        # 边框
        pygame.draw.rect(screen, self.BORDER_COLOR, self.rect, 1)

        # 区域分界线（虚线效果）
        for boundary_x in [WORLD_WIDTH // 3, 2 * WORLD_WIDTH // 3]:
            bx, _ = self._world_to_mini(boundary_x, 0)
            pygame.draw.line(screen, (100, 100, 100, 80),
                             (bx, self.y), (bx, self.y + MINIMAP_H), 1)

        # 巢穴（方块标记）
        if ctx.player_grinder:
            px, py = self._world_to_mini(ctx.player_grinder.x, ctx.player_grinder.y)
            pygame.draw.rect(screen, self.PLAYER_COLOR, (px - 2, py - 2, 4, 4))
        if ctx.ai_grinder:
            ax, ay = self._world_to_mini(ctx.ai_grinder.x, ctx.ai_grinder.y)
            pygame.draw.rect(screen, self.AI_COLOR, (ax - 2, ay - 2, 4, 4))

        # 蚂蚁（小圆点）
        for ant in ctx.player_ants:
            ax, ay = self._world_to_mini(ant.x, ant.y)
            if self.rect.collidepoint(ax, ay):
                pygame.draw.circle(screen, self.PLAYER_COLOR, (ax, ay), 2)
        for ant in ctx.ai_ants:
            ax, ay = self._world_to_mini(ant.x, ant.y)
            if self.rect.collidepoint(ax, ay):
                pygame.draw.circle(screen, self.AI_COLOR, (ax, ay), 2)

        # 甜点（黄色圆点）
        for sweet in ctx.sweets:
            if not sweet.alive:
                continue
            sx, sy = self._world_to_mini(sweet.x, sweet.y)
            if self.rect.collidepoint(sx, sy):
                pygame.draw.circle(screen, self.SWEET_COLOR, (sx, sy), 3)

        # 障碍物（可碰撞=灰色方块，纯装饰=绿色小点）
        OBSTACLE_MINI_COLOR = (160, 160, 170)
        DECOR_MINI_COLOR = (100, 170, 80)
        for obs in getattr(ctx, 'obstacles', []):
            ox, oy = self._world_to_mini(obs.x, obs.y)
            if self.rect.collidepoint(ox, oy):
                if obs.collidable:
                    pygame.draw.rect(screen, OBSTACLE_MINI_COLOR, (ox - 2, oy - 2, 4, 4))
                else:
                    pygame.draw.circle(screen, DECOR_MINI_COLOR, (ox, oy), 2)

        # 当前相机视口矩形（白色边框）
        vp_x = self.x + (cam.x / WORLD_WIDTH) * MINIMAP_W
        vp_y = self.y + (cam.y / WORLD_HEIGHT) * MINIMAP_H
        vp_w = (SCREEN_WIDTH / WORLD_WIDTH) * MINIMAP_W
        vp_h = (SCREEN_HEIGHT / WORLD_HEIGHT) * MINIMAP_H
        vp_rect = pygame.Rect(int(vp_x), int(vp_y), int(vp_w), int(vp_h))
        pygame.draw.rect(screen, self.VIEWPORT_COLOR, vp_rect, 1)
