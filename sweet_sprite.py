"""甜点精灵类（V1.4）：单甜点，HP归零后消失"""

import pygame
import math
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, SWEET_SIZE_BASE,
    SWEET_COLORS,
    SWEET_SPAWN_BLINK_DURATION, SWEET_SPAWN_BLINK_LOOPS,
    SWEET_SPAWN_BLINK_MAX_ON_SCREEN,
    HP_BAR_W, HP_BAR_H, HP_BAR_BG, HP_BAR_FILL, HP_BAR_RADIUS, HP_BAR_GAP,
)
import font_helper

# 甜点刷新闪烁：全局计数器 + 排队队列
_blink_count = 0          # 当前正在闪烁的甜点数量
_blink_queue = []         # 排队等待闪烁的甜点列表（FIFO）


def _get_hp_font():
    return font_helper.get_font(16)


class Sweet(pygame.sprite.Sprite):
    """甜点精灵：单HP系统，HP归零时消失"""

    def __init__(self, sweet_type, x, y, max_hp, coin_per, assets=None):
        super().__init__()
        self.sweet_type = sweet_type
        self.x = float(x)
        self.y = float(y)
        self.max_hp = max_hp
        self.hp = max_hp
        self.coin_per = coin_per
        self.alive = True
        self.assets = assets or {}

        self.base_size = SWEET_SIZE_BASE
        self.current_size = SWEET_SIZE_BASE

        # 刷新闪烁动画状态
        self._blink_active = False
        self._blink_timer = 0.0
        self._blink_alpha = 0  # 当前闪烁alpha偏移

        self._update_image()
        self.start_spawn_blink()

    def _update_image(self):
        """根据甜点类型和HP比例选择对应形态的PNG图片"""
        hp_ratio = self.hp / self.max_hp if self.max_hp > 0 else 1.0
        if hp_ratio > 0.5:
            state = 'full'
        elif hp_ratio > 0.25:
            state = '60'
        else:
            state = '30'
        key = f'{self.sweet_type}_{state}'
        if key in self.assets:
            self.image = self.assets[key]
        else:
            # 回退：根据HP比例绘制圆形
            ratio = max(0.5, self.hp / self.max_hp) if self.max_hp > 0 else 1.0
            self.current_size = max(20, int(self.base_size * ratio))
            self.image = pygame.Surface((self.current_size, self.current_size), pygame.SRCALPHA)
            color = SWEET_COLORS.get(self.sweet_type, (200, 200, 200))
            c = self.current_size // 2
            pygame.draw.circle(self.image, color, (c, c), c)
            pygame.draw.circle(self.image, (255, 255, 255), (c, c), c, 2)
        self.current_size = self.image.get_width()
        self.rect = self.image.get_rect(center=(int(self.x), int(self.y)))

    def take_damage(self, attacker=None):
        """受到伤害，HP归零时甜点消失。返回True表示甜点被消灭。
        attacker参数保留以兼容Creature接口，甜点不需要攻击者信息。"""
        if not self.alive:
            return False
        self.hp -= 1
        if self.hp <= 0:
            self.alive = False
            return True
        self._update_image()
        return False

    def start_spawn_blink(self):
        """尝试启动刷新闪烁动画，受同屏上限约束（FIFO排队）"""
        global _blink_count, _blink_queue
        if _blink_count < SWEET_SPAWN_BLINK_MAX_ON_SCREEN:
            _blink_count += 1
            self._blink_active = True
            self._blink_timer = 0.0
        else:
            _blink_queue.append(self)

    def update_blink(self, dt):
        """更新闪烁动画，返回当前alpha偏移（0-255）"""
        global _blink_count, _blink_queue
        if not self._blink_active:
            return 0

        self._blink_timer += dt
        total = SWEET_SPAWN_BLINK_DURATION

        if self._blink_timer >= total:
            # 闪烁结束
            self._blink_active = False
            self._blink_alpha = 0
            _blink_count -= 1
            # 从排队队列中取下一个开始闪烁
            if _blink_queue:
                next_sweet = _blink_queue.pop(0)
                if next_sweet.alive:
                    next_sweet._blink_active = True
                    next_sweet._blink_timer = 0.0
                    _blink_count += 1
            return 0

        # sine缓动: (sin(t * π) + 1) / 2 → 0~1
        t = self._blink_timer / total
        # 2次循环 = 4段渐变，用 sin(t * 2π * loops) 取绝对值实现
        blink = abs(math.sin(t * math.pi * SWEET_SPAWN_BLINK_LOOPS))
        self._blink_alpha = int(255 * blink)
        return self._blink_alpha

    def draw_with_hp_effect(self, screen, camera=None):
        """绘制甜点 + HP条 + 刷新闪烁。camera 用于世界坐标到屏幕坐标的转换。"""
        if not self.alive:
            return

        if camera is not None:
            sx, sy = camera.world_to_screen(self.x, self.y)
            screen_rect = self.image.get_rect(center=(int(sx), int(sy)))
        else:
            screen_rect = self.rect

        # 绘制甜点本体
        screen.blit(self.image, screen_rect)

        # 刷新闪烁：在甜点上方叠加白色半透明闪烁层
        if self._blink_active and self._blink_alpha > 0:
            blink_surf = pygame.Surface(
                (screen_rect.width, screen_rect.height), pygame.SRCALPHA
            )
            blink_surf.fill((255, 255, 255, self._blink_alpha))
            screen.blit(blink_surf, screen_rect)

        # HP条（位于甜点上方）
        bar_x = screen_rect.centerx - HP_BAR_W // 2
        bar_y = screen_rect.top - HP_BAR_H - HP_BAR_GAP

        # 背景
        pygame.draw.rect(screen, HP_BAR_BG,
                         (bar_x, bar_y, HP_BAR_W, HP_BAR_H),
                         border_radius=HP_BAR_RADIUS)
        # HP填充
        hp_ratio = max(0, self.hp / self.max_hp) if self.max_hp > 0 else 0
        fill_w = int(HP_BAR_W * hp_ratio)
        if fill_w > 0:
            pygame.draw.rect(screen, HP_BAR_FILL,
                             (bar_x, bar_y, fill_w, HP_BAR_H),
                             border_radius=HP_BAR_RADIUS)
