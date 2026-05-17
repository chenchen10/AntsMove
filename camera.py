"""相机/视口系统：管理世界坐标的屏幕映射"""

import pygame
from config import SCREEN_WIDTH, SCREEN_HEIGHT, WORLD_WIDTH, WORLD_HEIGHT


class Camera:
    """管理世界坐标到屏幕坐标的映射，支持平滑跟随和平移"""

    def __init__(self):
        # 相机左上角在世界中的坐标
        self.x = 0.0
        self.y = 0.0
        # 平滑跟随目标（None = 不跟随）
        self._follow_target = None
        self._follow_speed = 5.0
        # 小地图绘制区域（屏幕坐标）
        self.minimap_rect = pygame.Rect(
            SCREEN_WIDTH - 170, SCREEN_HEIGHT - 170, 160, 160
        )

    def update(self, dt):
        """更新相机位置（平滑跟随）"""
        if self._follow_target is not None:
            tx, ty = self._follow_target
            # 目标：让目标位于屏幕中央
            target_cam_x = tx - SCREEN_WIDTH / 2
            target_cam_y = ty - SCREEN_HEIGHT / 2
            # 平滑插值
            self.x += (target_cam_x - self.x) * self._follow_speed * dt
            self.y += (target_cam_y - self.y) * self._follow_speed * dt
            self._clamp()

    def set_follow(self, target_x, target_y):
        """设置跟随目标坐标"""
        self._follow_target = (target_x, target_y)

    def clear_follow(self):
        """取消跟随"""
        self._follow_target = None

    def move(self, dx, dy):
        """直接平移相机"""
        self.x += dx
        self.y += dy
        self._clamp()

    def center_on(self, x, y):
        """将相机中心对准世界坐标"""
        self.x = x - SCREEN_WIDTH / 2
        self.y = y - SCREEN_HEIGHT / 2
        self._clamp()

    def world_to_screen(self, wx, wy):
        """世界坐标 → 屏幕坐标"""
        return (wx - self.x, wy - self.y)

    def screen_to_world(self, sx, sy):
        """屏幕坐标 → 世界坐标"""
        return (sx + self.x, sy + self.y)

    def world_to_minimap(self, wx, wy):
        """世界坐标 → 小地图坐标"""
        scale_x = self.minimap_rect.width / WORLD_WIDTH
        scale_y = self.minimap_rect.height / WORLD_HEIGHT
        mx = self.minimap_rect.x + wx * scale_x
        my = self.minimap_rect.y + wy * scale_y
        return (mx, my)

    def minimap_to_world(self, mx, my):
        """小地图坐标 → 世界坐标"""
        scale_x = WORLD_WIDTH / self.minimap_rect.width
        scale_y = WORLD_HEIGHT / self.minimap_rect.height
        wx = (mx - self.minimap_rect.x) * scale_x
        wy = (my - self.minimap_rect.y) * scale_y
        return (wx, wy)

    def _clamp(self):
        """限制相机不超出世界边界"""
        self.x = max(0, min(WORLD_WIDTH - SCREEN_WIDTH, self.x))
        self.y = max(0, min(WORLD_HEIGHT - SCREEN_HEIGHT, self.y))

    def get_view_rect(self):
        """获取当前视口在世界中的矩形"""
        return pygame.Rect(self.x, self.y, SCREEN_WIDTH, SCREEN_HEIGHT)

    def is_visible(self, wx, wy, margin=50):
        """判断世界坐标是否在当前视口内（带边距）"""
        vr = self.get_view_rect()
        vr.inflate_ip(margin * 2, margin * 2)
        return vr.collidepoint(wx, wy)

    def draw_minimap(self, screen, ctx):
        """绘制小地图"""
        rect = self.minimap_rect
        # 背景
        bg = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        bg.fill((20, 30, 20, 160))
        pygame.draw.rect(bg, (100, 180, 100, 200), (0, 0, rect.width, rect.height), 2, border_radius=4)
        screen.blit(bg, rect.topleft)

        scale_x = rect.width / WORLD_WIDTH
        scale_y = rect.height / WORLD_HEIGHT

        # 绘制甜点
        for sweet in ctx.sweets:
            if sweet.alive:
                mx = rect.x + int(sweet.x * scale_x)
                my = rect.y + int(sweet.y * scale_y)
                pygame.draw.circle(screen, (255, 200, 50), (mx, my), 3)

        # 绘制研磨机
        pg = ctx.player_grinder
        mx = rect.x + int(pg.x * scale_x)
        my = rect.y + int(pg.y * scale_y)
        pygame.draw.circle(screen, (80, 200, 80), (mx, my), 4)

        ag = ctx.ai_grinder
        mx = rect.x + int(ag.x * scale_x)
        my = rect.y + int(ag.y * scale_y)
        pygame.draw.circle(screen, (200, 80, 80), (mx, my), 4)

        # 绘制玩家蚂蚁（蓝点）
        for ant in ctx.player_ants:
            mx = rect.x + int(ant.x * scale_x)
            my = rect.y + int(ant.y * scale_y)
            pygame.draw.circle(screen, (70, 130, 220), (mx, my), 2)

        # 绘制AI蚂蚁（红点）
        for ant in ctx.ai_ants:
            mx = rect.x + int(ant.x * scale_x)
            my = rect.y + int(ant.y * scale_y)
            pygame.draw.circle(screen, (220, 80, 70), (mx, my), 2)

        # 绘制当前视口矩形
        vp_x = rect.x + int(self.x * scale_x)
        vp_y = rect.y + int(self.y * scale_y)
        vp_w = int(SCREEN_WIDTH * scale_x)
        vp_h = int(SCREEN_HEIGHT * scale_y)
        pygame.draw.rect(screen, (255, 255, 255), (vp_x, vp_y, vp_w, vp_h), 1)
