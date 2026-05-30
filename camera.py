"""相机系统：2D拖拽、平滑跳转（小地图定位）、边界约束"""

import pygame
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    WORLD_WIDTH, WORLD_HEIGHT,
    CAMERA_MAX_X, CAMERA_MAX_Y,
)


class Camera:
    """2D 相机，支持拖拽、惯性、边界约束、小地图跳转"""

    def __init__(self):
        self.x = 0.0
        self.y = 0.0
        # 小地图跳转目标
        self._jump_target_x = None
        self._jump_target_y = None
        # 边界
        self._max_x = float(max(0, CAMERA_MAX_X))
        self._max_y = float(max(0, CAMERA_MAX_Y))

    # ── 坐标转换 ──

    def world_to_screen(self, world_x, world_y):
        """世界坐标 → 屏幕坐标"""
        return world_x - self.x, world_y - self.y

    def screen_to_world(self, screen_x, screen_y):
        """屏幕坐标 → 世界坐标"""
        return screen_x + self.x, screen_y + self.y

    # ── 相机控制 ──

    def center_on(self, x, y):
        """将相机中心对准指定世界坐标"""
        self.x = x - SCREEN_WIDTH // 2
        self.y = y - SCREEN_HEIGHT // 2
        self._clamp()

    def move_to(self, x, y):
        """直接设置相机左上角位置"""
        self.x = float(x)
        self.y = float(y)
        self._clamp()

    def move_by(self, dx, dy):
        """按偏移量移动相机"""
        self.x += dx
        self.y += dy
        self._clamp()

    # ── 小地图跳转 ──

    def start_jump(self, target_x, target_y):
        """发起平滑跳转到目标世界坐标（由小地图点击触发）"""
        self._jump_target_x = target_x
        self._jump_target_y = target_y

    def update_jump(self, dt):
        """平滑跳转插值更新（ease-out 缓动，lerp 插值）

        关键参数：
        - lerp_factor = dt × 5.0
        - 停止阈值 < 1px
        - 跳转动画约 0.3-0.5s
        """
        if self._jump_target_x is None:
            return

        # 目标是让相机中心对准目标世界坐标
        target_cam_x = self._jump_target_x - SCREEN_WIDTH // 2
        target_cam_y = self._jump_target_y - SCREEN_HEIGHT // 2

        diff_x = target_cam_x - self.x
        diff_y = target_cam_y - self.y

        # 检查是否到达目标（停止阈值 < 1px）
        if abs(diff_x) < 1.0 and abs(diff_y) < 1.0:
            self.x = target_cam_x
            self.y = target_cam_y
            self._jump_target_x = None
            self._jump_target_y = None
            self._clamp()
            return

        # lerp 插值，ease-out 缓动
        lerp_factor = dt * 5.0
        self.x += diff_x * min(1.0, lerp_factor)
        self.y += diff_y * min(1.0, lerp_factor)
        self._clamp()

    @property
    def is_jumping(self):
        """是否正在执行跳转动画"""
        return self._jump_target_x is not None

    # ── 通用更新 ──

    def update(self, dt):
        """每帧更新（跳转动画）"""
        self.update_jump(dt)

    # ── 绘制辅助 ──

    def draw_at(self, surface, world_x, world_y, screen):
        """在世界坐标处绘制 surface 到屏幕"""
        sx, sy = self.world_to_screen(world_x, world_y)
        screen.blit(surface, (int(sx), int(sy)))

    # ── 内部方法 ──

    def _clamp(self):
        """将相机位置限制在世界边界内"""
        self.x = max(0.0, min(self._max_x, self.x))
        self.y = max(0.0, min(self._max_y, self.y))
