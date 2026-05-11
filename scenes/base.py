"""场景基类"""

import pygame


class Scene:
    """所有场景的基类。子类按需覆写 handle_click / draw。"""

    def __init__(self, ctx):
        self.ctx = ctx

    def handle_click(self, mx, my):
        """处理鼠标左键点击，子类覆写。"""
        pass

    def draw(self, screen):
        """绘制场景，子类覆写。"""
        pass
