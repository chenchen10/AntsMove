"""统一中文字体模块：所有 UI 文字使用 PingFang，彻底消除乱码"""

import os
import pygame

_font_path = None
_font_cache = {}   # {(size, bold): Font}


def init():
    """初始化字体路径（游戏启动时调用一次）"""
    global _font_path
    # STHeiti 排在最前：PingFang.ttc 对个别汉字（如"敌"）渲染为空白
    candidates = [
        '/System/Library/Fonts/STHeiti Medium.ttc',
        '/System/Library/Fonts/PingFang.ttc',
        '/System/Library/Fonts/Hiragino Sans GB.ttc',
        '/System/Library/Fonts/Supplemental/Songti.ttc',
    ]
    for fp in candidates:
        if os.path.exists(fp):
            _font_path = fp
            break


def get_font(size, bold=False):
    """获取指定大小的 PingFang 字体（带缓存）"""
    key = (size, bold)
    if key not in _font_cache:
        if _font_path:
            _font_cache[key] = pygame.font.Font(_font_path, size)
        else:
            _font_cache[key] = pygame.font.SysFont(None, size, bold=bold)
    return _font_cache[key]
