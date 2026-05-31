"""昆虫精灵类（第一期）：复用Sweet类的HP+状态机框架

昆虫与甜点共享区域刷新计时器，每次刷新只生成一种。
昆虫在区域内缓慢移动，HP归零后播放缩小+淡出动画消失。
金币直接加到蚂蚁storage，受区域倍率影响。
"""

import pygame
import math
import random
from config import (
    CREATURE_SIZE_BASE, CREATURE_COLORS,
    CREATURE_SPAWN_BLINK_DURATION, CREATURE_SPAWN_BLINK_LOOPS,
    CREATURE_SPAWN_BLINK_MAX_ON_SCREEN, CREATURE_DEATH_ANIM_DURATION,
    CREATURE_SPEED_VARIATION, WORLD_WIDTH, WORLD_HEIGHT,
    HP_BAR_W, HP_BAR_H, HP_BAR_BG, HP_BAR_FILL, HP_BAR_RADIUS, HP_BAR_GAP,
)
from creatures_data import get_creature_data
import font_helper

# 昆虫刷新闪烁：全局计数器 + 排队队列
_blink_count = 0
_blink_queue = []


def _get_hp_font():
    return font_helper.get_font(16)


class Creature(pygame.sprite.Sprite):
    """昆虫精灵：HP系统 + 区域内移动 + 死亡缩小淡出动画"""

    def __init__(self, creature_id, x, y, zone_name, assets=None):
        super().__init__()
        data = get_creature_data(creature_id)
        self.creature_id = creature_id
        self.creature_name = data['name']
        self.x = float(x)
        self.y = float(y)
        self.zone_name = zone_name
        self.max_hp = data['hp']
        self.hp = data['hp']
        self.coin_per = data['coin_per']
        self.base_speed = data['speed']
        self.alive = True
        self.assets = assets or {}

        self.base_size = CREATURE_SIZE_BASE
        self.current_size = CREATURE_SIZE_BASE

        # 区域内移动
        self._speed_var = random.uniform(1.0 - CREATURE_SPEED_VARIATION,
                                         1.0 + CREATURE_SPEED_VARIATION)
        self._move_angle = random.uniform(0, math.pi * 2)
        self._move_timer = 0.0
        self._move_change_interval = random.uniform(2.0, 5.0)

        # 刷新闪烁动画状态
        self._blink_active = False
        self._blink_timer = 0.0
        self._blink_alpha = 0

        # 死亡动画状态
        self._dying = False
        self._death_timer = 0.0
        self._death_alpha = 255

        self._update_image()
        self.start_spawn_blink()

    def _update_image(self):
        """根据昆虫类型和HP比例选择对应图片或回退绘制"""
        hp_ratio = self.hp / self.max_hp if self.max_hp > 0 else 1.0
        # 尝试加载asset图片
        key = f'{self.creature_id}'
        if key in self.assets:
            self.image = self.assets[key]
        else:
            # 回退：根据HP比例绘制圆形
            ratio = max(0.4, hp_ratio)
            self.current_size = max(20, int(self.base_size * ratio))
            self.image = pygame.Surface((self.current_size, self.current_size), pygame.SRCALPHA)
            color = CREATURE_COLORS.get(self.creature_id, (200, 200, 200))
            c = self.current_size // 2
            pygame.draw.circle(self.image, color, (c, c), c)
            pygame.draw.circle(self.image, (255, 255, 255), (c, c), c, 2)
            # 瓢虫加黑点装饰
            if self.creature_id == 'ladybug':
                for dx, dy in [(-0.25, -0.2), (0.25, -0.2), (0, 0.2), (-0.2, 0.25), (0.2, 0.25)]:
                    px = int(c + dx * self.current_size)
                    py = int(c + dy * self.current_size)
                    pygame.draw.circle(self.image, (0, 0, 0), (px, py), max(2, c // 6))
            # 毛毛虫加分节线
            elif self.creature_id == 'caterpillar':
                for i in range(1, 4):
                    seg_y = int(self.current_size * i / 4)
                    pygame.draw.line(self.image, (60, 140, 60),
                                     (4, seg_y), (self.current_size - 4, seg_y), 2)
        self.current_size = self.image.get_width()
        self.rect = self.image.get_rect(center=(int(self.x), int(self.y)))

    def take_damage(self):
        """受到伤害，HP归零时启动死亡动画。返回True表示昆虫被消灭。"""
        if not self.alive:
            return False
        self.hp -= 1
        if self.hp <= 0:
            self.alive = False
            self._dying = True
            self._death_timer = 0.0
            return True
        self._update_image()
        return False

    def start_spawn_blink(self):
        """尝试启动刷新闪烁动画，受同屏上限约束（FIFO排队）"""
        global _blink_count, _blink_queue
        if _blink_count < CREATURE_SPAWN_BLINK_MAX_ON_SCREEN:
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
        total = CREATURE_SPAWN_BLINK_DURATION

        if self._blink_timer >= total:
            self._blink_active = False
            self._blink_alpha = 0
            _blink_count -= 1
            if _blink_queue:
                next_creature = _blink_queue.pop(0)
                if next_creature.alive:
                    next_creature._blink_active = True
                    next_creature._blink_timer = 0.0
                    _blink_count += 1
            return 0

        t = self._blink_timer / total
        blink = abs(math.sin(t * math.pi * CREATURE_SPAWN_BLINK_LOOPS))
        self._blink_alpha = int(255 * blink)
        return self._blink_alpha

    def update(self, dt, zone_x_range=None):
        """每帧更新：区域内移动 + 死亡动画"""
        # 死亡动画：缩小+淡出
        if self._dying:
            self._death_timer += dt
            progress = min(1.0, self._death_timer / CREATURE_DEATH_ANIM_DURATION)
            # 缩小到0
            scale = 1.0 - progress
            new_size = max(1, int(self.base_size * scale))
            self.current_size = new_size
            # 淡出
            self._death_alpha = int(255 * (1.0 - progress))
            return progress >= 1.0  # 返回True表示动画完成

        # 区域内缓慢移动
        self._move_timer += dt
        if self._move_timer >= self._move_change_interval:
            self._move_timer = 0.0
            self._move_change_interval = random.uniform(2.0, 5.0)
            self._move_angle = random.uniform(0, math.pi * 2)

        speed = self.base_speed * self._speed_var * 0.3  # 实际移速为定义值的30%
        dx = math.cos(self._move_angle) * speed * dt
        dy = math.sin(self._move_angle) * speed * dt

        new_x = self.x + dx
        new_y = self.y + dy

        # 限制在区域内
        if zone_x_range:
            x_min, x_max = zone_x_range
            if new_x < x_min + 30 or new_x > x_max - 30:
                self._move_angle = math.pi - self._move_angle
                new_x = max(x_min + 30, min(x_max - 30, new_x))
        new_y = max(60, min(WORLD_HEIGHT - 60, new_y))

        self.x = new_x
        self.y = new_y
        self.rect = self.image.get_rect(center=(int(self.x), int(self.y)))
        return False

    def draw_with_hp_effect(self, screen, camera=None):
        """绘制昆虫 + HP条 + 刷新闪烁 + 死亡动画"""
        if not self.alive and not self._dying:
            return

        if camera is not None:
            sx, sy = camera.world_to_screen(self.x, self.y)
            screen_rect = self.image.get_rect(center=(int(sx), int(sy)))
        else:
            screen_rect = self.rect

        # 死亡动画：缩放+淡出
        if self._dying:
            if self.current_size < 2:
                return
            scaled_img = pygame.transform.smoothscale(
                self.image, (max(1, self.current_size), max(1, self.current_size)))
            scaled_img.set_alpha(self._death_alpha)
            screen_rect = scaled_img.get_rect(center=(int(sx) if camera else int(self.x),
                                                       int(sy) if camera else int(self.y)))
            screen.blit(scaled_img, screen_rect)
            return

        # 绘制昆虫本体
        screen.blit(self.image, screen_rect)

        # 刷新闪烁：叠加白色半透明闪烁层
        if self._blink_active and self._blink_alpha > 0:
            blink_surf = pygame.Surface(
                (screen_rect.width, screen_rect.height), pygame.SRCALPHA
            )
            blink_surf.fill((255, 255, 255, self._blink_alpha))
            screen.blit(blink_surf, screen_rect)

        # HP条（位于昆虫上方）
        bar_x = screen_rect.centerx - HP_BAR_W // 2
        bar_y = screen_rect.top - HP_BAR_H - HP_BAR_GAP

        pygame.draw.rect(screen, HP_BAR_BG,
                         (bar_x, bar_y, HP_BAR_W, HP_BAR_H),
                         border_radius=HP_BAR_RADIUS)
        hp_ratio = max(0, self.hp / self.max_hp) if self.max_hp > 0 else 0
        fill_w = int(HP_BAR_W * hp_ratio)
        if fill_w > 0:
            pygame.draw.rect(screen, HP_BAR_FILL,
                             (bar_x, bar_y, fill_w, HP_BAR_H),
                             border_radius=HP_BAR_RADIUS)
