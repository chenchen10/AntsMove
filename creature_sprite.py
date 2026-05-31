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
        # 尝试加载asset图片（支持嵌套结构 insect_sprites -> creature_id -> direction -> frames）
        insect_sprites = self.assets.get('insect_sprites', {})
        sprite_dict = insect_sprites.get(self.creature_id, {})
        frames_n = sprite_dict.get('n', [])
        if frames_n:
            self.image = frames_n[0]
        elif self.creature_id in self.assets:
            self.image = self.assets[self.creature_id]
        else:
            # 回退：根据HP比例绘制各昆虫的独特形状
            ratio = max(0.4, hp_ratio)
            self.current_size = max(20, int(self.base_size * ratio))
            self.image = self._draw_fallback_insect(self.current_size)
        self.current_size = self.image.get_width()
        self.rect = self.image.get_rect(center=(int(self.x), int(self.y)))
        self.current_size = self.image.get_width()
        self.rect = self.image.get_rect(center=(int(self.x), int(self.y)))

    def _draw_fallback_insect(self, size):
        """程序化绘制各昆虫的独特形状（无PNG素材时的回退）"""
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        cx, cy = size // 2, size // 2
        color = CREATURE_COLORS.get(self.creature_id, (200, 200, 200))

        if self.creature_id == 'ladybug':
            # 瓢虫：椭圆身体 + 黑点
            body_w, body_h = int(size * 0.8), int(size * 0.65)
            pygame.draw.ellipse(surf, color, (cx - body_w // 2, cy - body_h // 2, body_w, body_h))
            pygame.draw.ellipse(surf, (255, 255, 255), (cx - body_w // 2, cy - body_h // 2, body_w, body_h), 2)
            # 中线
            pygame.draw.line(surf, (40, 0, 0), (cx, cy - body_h // 2 + 3), (cx, cy + body_h // 2 - 3), 2)
            # 黑点
            spots = [(-0.22, -0.12), (0.22, -0.12), (-0.15, 0.15), (0.15, 0.15), (0, 0.0)]
            for dx, dy in spots:
                pygame.draw.circle(surf, (20, 20, 20),
                                   (int(cx + dx * size), int(cy + dy * size)),
                                   max(2, size // 10))
            # 头部
            pygame.draw.circle(surf, (40, 20, 20), (cx, cy - body_h // 2 - 2), max(3, size // 8))

        elif self.creature_id == 'caterpillar':
            # 毛毛虫：多个圆球串联 + 蠕动分节
            seg_count = 5
            seg_r = max(3, int(size * 0.18))
            spacing = int(size * 0.28)
            start_x = cx - (seg_count - 1) * spacing // 2
            for i in range(seg_count):
                sx = start_x + i * spacing
                # 颜色渐变：从深绿到浅绿
                g_val = min(255, color[1] + i * 10)
                seg_color = (color[0], g_val, color[2])
                pygame.draw.circle(surf, seg_color, (sx, cy), seg_r)
                pygame.draw.circle(surf, (255, 255, 255), (sx, cy), seg_r, 1)
            # 头部（稍大）+ 触角
            head_x = start_x - seg_r
            pygame.draw.circle(surf, (color[0] - 20, color[1] + 20, color[2] - 10),
                               (head_x, cy), seg_r + 2)
            # 触角
            pygame.draw.line(surf, (60, 120, 60),
                             (head_x - 2, cy - seg_r), (head_x - 6, cy - seg_r - 6), 2)
            pygame.draw.line(surf, (60, 120, 60),
                             (head_x + 2, cy - seg_r), (head_x + 6, cy - seg_r - 6), 2)
            # 眼睛
            pygame.draw.circle(surf, (0, 0, 0), (head_x - 2, cy - 1), 1)
            pygame.draw.circle(surf, (0, 0, 0), (head_x + 2, cy - 1), 1)

        elif self.creature_id == 'cricket':
            # 蟋蟀：扁平身体 + 长触角 + 强壮后腿
            body_w, body_h = int(size * 0.7), int(size * 0.45)
            pygame.draw.ellipse(surf, color, (cx - body_w // 2, cy - body_h // 2, body_w, body_h))
            pygame.draw.ellipse(surf, (255, 255, 255), (cx - body_w // 2, cy - body_h // 2, body_w, body_h), 1)
            # 头部
            head_r = max(3, size // 7)
            pygame.draw.circle(surf, color, (cx - body_w // 2 - head_r + 3, cy), head_r)
            # 长触角
            antenna_start = cx - body_w // 2 - head_r + 2
            pygame.draw.line(surf, (80, 60, 30),
                             (antenna_start, cy - 2), (antenna_start - size // 4, cy - size // 3), 1)
            pygame.draw.line(surf, (80, 60, 30),
                             (antenna_start, cy + 2), (antenna_start - size // 4, cy + size // 3), 1)
            # 后腿（倒V形，体现跳跃能力）
            leg_base_x = cx + body_w // 4
            leg_tip_y = cy + body_h // 2 + size // 5
            pygame.draw.line(surf, (80, 60, 30),
                             (leg_base_x, cy + body_h // 2 - 2), (leg_base_x + size // 6, leg_tip_y), 2)
            pygame.draw.line(surf, (80, 60, 30),
                             (leg_base_x + size // 6, leg_tip_y), (leg_base_x + size // 10, leg_tip_y - size // 8), 2)
            # 翅膀纹理
            wing_y = cy - body_h // 2 + 2
            pygame.draw.line(surf, (color[0] - 20, color[1] - 20, color[2]),
                             (cx - body_w // 4, wing_y), (cx + body_w // 4, wing_y), 1)

        elif self.creature_id == 'beetle':
            # 甲虫：厚实椭圆 + 金属光泽 + 鳌角
            body_w, body_h = int(size * 0.85), int(size * 0.7)
            pygame.draw.ellipse(surf, color, (cx - body_w // 2, cy - body_h // 2, body_w, body_h))
            # 金属光泽（高光椭圆）
            highlight_w, highlight_h = body_w // 3, body_h // 4
            hl_surf = pygame.Surface((highlight_w, highlight_h), pygame.SRCALPHA)
            pygame.draw.ellipse(hl_surf, (255, 255, 255, 80), (0, 0, highlight_w, highlight_h))
            surf.blit(hl_surf, (cx - highlight_w // 2, cy - body_h // 4))
            # 边框
            pygame.draw.ellipse(surf, (255, 255, 255), (cx - body_w // 2, cy - body_h // 2, body_w, body_h), 2)
            # 中线
            pygame.draw.line(surf, (max(0, color[0] - 40), max(0, color[1] - 40), max(0, color[2] - 40)),
                             (cx, cy - body_h // 2 + 4), (cx, cy + body_h // 2 - 4), 2)
            # 头部 + 鳎角
            head_r = max(3, size // 7)
            head_x = cx - body_w // 2 - head_r + 4
            pygame.draw.circle(surf, color, (head_x, cy), head_r)
            pygame.draw.circle(surf, (255, 255, 255), (head_x, cy), head_r, 1)
            # 鳎角（V形）
            horn_len = size // 5
            pygame.draw.line(surf, (60, 40, 20),
                             (head_x - 2, cy - 1), (head_x - horn_len, cy - horn_len // 2), 2)
            pygame.draw.line(surf, (60, 40, 20),
                             (head_x - 2, cy + 1), (head_x - horn_len, cy + horn_len // 2), 2)

        elif self.creature_id == 'dragonfly':
            # 蜻蜓：细长身体 + 透明翅膀
            body_w, body_h = int(size * 0.15), int(size * 0.7)
            # 细长腹部
            pygame.draw.ellipse(surf, color, (cx - body_w // 2, cy - body_h // 2, body_w, body_h))
            pygame.draw.ellipse(surf, (255, 255, 255), (cx - body_w // 2, cy - body_h // 2, body_w, body_h), 1)
            # 头部（大复眼）
            head_r = max(4, size // 6)
            head_y = cy - body_h // 2 - head_r + 3
            pygame.draw.circle(surf, color, (cx, head_y), head_r)
            pygame.draw.circle(surf, (255, 255, 255), (cx, head_y), head_r, 1)
            # 复眼
            pygame.draw.circle(surf, (180, 220, 255), (cx - head_r // 2, head_y - 1), max(2, head_r // 3))
            pygame.draw.circle(surf, (180, 220, 255), (cx + head_r // 2, head_y - 1), max(2, head_r // 3))
            # 翅膀（4片，半透明蓝色）
            wing_color = (150, 200, 255, 100)
            wing_len = int(size * 0.4)
            wing_w = int(size * 0.15)
            # 上翅（左右各一片）
            for side in (-1, 1):
                wing_surf = pygame.Surface((wing_len, wing_w), pygame.SRCALPHA)
                pygame.draw.ellipse(wing_surf, wing_color, (0, 0, wing_len, wing_w))
                wx = cx + side * body_w // 2 - (0 if side > 0 else wing_len)
                wy = cy - body_h // 4 - wing_w // 2
                if side < 0:
                    wing_surf = pygame.transform.flip(wing_surf, True, False)
                surf.blit(wing_surf, (wx, wy))
            # 下翅（稍小）
            for side in (-1, 1):
                wing_w2 = wing_w - 2
                wing_len2 = wing_len - 4
                wing_surf = pygame.Surface((wing_len2, wing_w2), pygame.SRCALPHA)
                pygame.draw.ellipse(wing_surf, wing_color, (0, 0, wing_len2, wing_w2))
                wx = cx + side * body_w // 2 - (0 if side > 0 else wing_len2)
                wy = cy + body_h // 8 - wing_w2 // 2
                if side < 0:
                    wing_surf = pygame.transform.flip(wing_surf, True, False)
                surf.blit(wing_surf, (wx, wy))

        elif self.creature_id == 'bee':
            # 蜜蜂：椭圆身体 + 黄黑条纹 + 翅膀
            body_w, body_h = int(size * 0.65), int(size * 0.55)
            # 身体
            pygame.draw.ellipse(surf, color, (cx - body_w // 2, cy - body_h // 2, body_w, body_h))
            pygame.draw.ellipse(surf, (255, 255, 255), (cx - body_w // 2, cy - body_h // 2, body_w, body_h), 1)
            # 黄黑条纹（3条黑纹）
            stripe_count = 3
            for i in range(stripe_count):
                stripe_x = cx - body_w // 4 + i * (body_w // 4)
                stripe_h = body_h - 4
                pygame.draw.rect(surf, (30, 30, 30),
                                 (stripe_x - 2, cy - stripe_h // 2, 4, stripe_h))
            # 头部
            head_r = max(3, size // 7)
            head_x = cx - body_w // 2 - head_r + 3
            pygame.draw.circle(surf, (40, 30, 10), (head_x, cy), head_r)
            # 眼睛
            pygame.draw.circle(surf, (255, 255, 255), (head_x - 1, cy - 1), max(1, head_r // 3))
            # 翅膀（半透明）
            wing_color = (220, 220, 255, 90)
            wing_len = int(size * 0.3)
            wing_w = int(size * 0.15)
            for side in (-1, 1):
                wing_surf = pygame.Surface((wing_len, wing_w), pygame.SRCALPHA)
                pygame.draw.ellipse(wing_surf, wing_color, (0, 0, wing_len, wing_w))
                wx = cx + side * 2 - (0 if side > 0 else wing_len)
                wy = cy - body_h // 2 - wing_w + 2
                if side < 0:
                    wing_surf = pygame.transform.flip(wing_surf, True, False)
                surf.blit(wing_surf, (wx, wy))
            # 尾针
            tail_x = cx + body_w // 2
            pygame.draw.line(surf, (60, 40, 20), (tail_x, cy), (tail_x + size // 6, cy), 2)

        else:
            # 未知昆虫：简单圆形
            c = size // 2
            pygame.draw.circle(surf, color, (c, c), c)
            pygame.draw.circle(surf, (255, 255, 255), (c, c), c, 2)

        return surf

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
