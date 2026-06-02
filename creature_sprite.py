"""昆虫精灵类（第一期+第二期）：复用Sweet类的HP+状态机框架

昆虫与甜点共享区域刷新计时器，每次刷新只生成一种。
昆虫在区域内缓慢移动，HP归零后播放缩小+淡出动画消失。
金币直接加到蚂蚁storage，受区域倍率影响。

第二期特殊机制：
- 蟋蟀(cricket): 跳跃闪避 — 被攻击时20%概率闪避，随机位移30像素
- 甲虫(beetle): 护甲 — 使用浮点HP(float)，每次啃食伤害=0.8
- 蜻蜓(dragonfly): 飞行 — 仅树顶(Tree_Top)地形蚂蚁可攻击
- 蜜蜂(bee): 反击 — 10%概率僵直攻击者0.5秒
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
from creatures_data import get_creature_data, get_creature_special
from terrain import TerrainType
import font_helper

# 昆虫刷新闪烁：全局计数器 + 排队队列
_blink_count = 0
_blink_queue = []


def _get_hp_font():
    return font_helper.get_font(16)


class Creature(pygame.sprite.Sprite):
    """昆虫精灵：HP系统 + 区域内移动 + 死亡缩小淡出动画 + 特殊机制"""

    def __init__(self, creature_id, x, y, zone_name, assets=None):
        super().__init__()
        data = get_creature_data(creature_id)
        self.creature_id = creature_id
        self.creature_name = data['name']
        self.x = float(x)
        self.y = float(y)
        self.zone_name = zone_name
        self.special = data.get('special')
        self.base_speed = data['speed']
        self.coin_per = data['coin_per']
        self.alive = True
        self.assets = assets or {}

        # HP：甲虫使用浮点HP，其他昆虫使用整数HP
        if self.special == 'armor':
            self.max_hp = float(data['hp'])
            self.hp = float(data['hp'])
        else:
            self.max_hp = int(data['hp'])
            self.hp = int(data['hp'])

        # 特殊机制参数
        self._dodge_chance = data.get('dodge_chance', 0.0)
        self._dodge_distance = data.get('dodge_distance', 30)
        self._armor_ratio = data.get('armor_ratio', 0.0)
        self._counter_chance = data.get('counter_chance', 0.0)
        self._counter_stun_duration = data.get('counter_stun_duration', 0.0)

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

        # 上一次受到攻击的事件（供main.py读取）
        self.last_event = None        # None | 'dodged' | 'counter_attack'
        self.counter_stun_duration = 0.0  # 蜜蜂反击僵直时长

        # 帧动画状态
        self._frames = []             # 当前方向的帧列表
        self._frame_index = 0         # 当前帧索引
        self._anim_timer = 0.0        # 动画计时器（秒）
        # 动画速度：根据昆虫移速设置，快速昆虫动画快，慢速昆虫动画慢
        # 基准：speed=150 → 0.15秒/帧，线性映射
        self._anim_speed = max(0.08, 0.225 - (self.base_speed / 1000.0))

        self._update_image()
        self.start_spawn_blink()

    def _update_image(self):
        """根据昆虫类型和HP比例选择对应图片或回退绘制"""
        hp_ratio = self.hp / self.max_hp if self.max_hp > 0 else 1.0
        # 尝试从 insect_sprites 嵌套结构加载精灵图
        insect_sprites = self.assets.get('insect_sprites', {})
        sprite_dict = insect_sprites.get(self.creature_id, {})
        frames_n = sprite_dict.get('n', [])
        if frames_n:
            self._frames = frames_n
            # 确保 frame_index 在有效范围内
            if self._frame_index >= len(self._frames):
                self._frame_index = 0
            self.image = self._frames[self._frame_index]
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
            # 蟋蟀：黄褐色 + 触角
            elif self.creature_id == 'cricket':
                # 触角
                pygame.draw.line(self.image, (80, 60, 20),
                                 (c - 5, 2), (c - 12, 0), 2)
                pygame.draw.line(self.image, (80, 60, 20),
                                 (c + 5, 2), (c + 12, 0), 2)
            # 甲虫：深棕色 + 壳纹理
            elif self.creature_id == 'beetle':
                pygame.draw.line(self.image, (40, 30, 10),
                                 (c, 4), (c, self.current_size - 4), 2)
                # 壳两侧弧线
                for side in [-1, 1]:
                    arc_x = c + side * c // 3
                    pygame.draw.arc(self.image, (40, 30, 10),
                                    (arc_x - 6, c - 6, 12, 12), 0, math.pi, 2)
            # 蜻蜓：青色 + 透明翅膀
            elif self.creature_id == 'dragonfly':
                wing_color = (180, 220, 255, 120)
                wing_surf = pygame.Surface((self.current_size, self.current_size), pygame.SRCALPHA)
                pygame.draw.ellipse(wing_surf, wing_color,
                                    (c - 14, c - 4, 12, 8))
                pygame.draw.ellipse(wing_surf, wing_color,
                                    (c + 2, c - 4, 12, 8))
                self.image.blit(wing_surf, (0, 0))
            # 蜜蜂：黄黑条纹
            elif self.creature_id == 'bee':
                for i in range(3):
                    stripe_y = int(self.current_size * (i * 2 + 1) / 7)
                    pygame.draw.line(self.image, (30, 30, 30),
                                     (4, stripe_y), (self.current_size - 4, stripe_y), 3)
        self.current_size = self.image.get_width()
        self.rect = self.image.get_rect(center=(int(self.x), int(self.y)))

    def take_damage(self, attacker=None):
        """受到伤害，处理特殊机制，返回True表示昆虫被消灭。

        特殊机制：
        - 蟋蟀闪避：20%概率闪避，本次攻击无效，蟋蟀随机位移30像素
        - 甲虫护甲：每次伤害=1×(1-armor_ratio)，HP使用float避免int(0.8)=0
        - 蜻蜓飞行：非树顶地形蚂蚁无法攻击（attacker terrain != 'tree_top'时返回False）
        - 蜜蜂反击：10%概率僵直攻击者0.5秒（固定，不受防御影响）

        Args:
            attacker: 攻击者（蚂蚁对象），用于地形判定和反击
        """
        if not self.alive:
            return False

        # 重置上一次事件
        self.last_event = None
        self.counter_stun_duration = 0.0

        # ── 蜻蜓飞行机制：非树顶地形蚂蚁无法攻击 ──
        if self.special == 'flight':
            if attacker is None or getattr(attacker, 'terrain', None) != TerrainType.TREE_TOP:
                self.last_event = 'dodged'  # 用dodged表示攻击无效
                return False

        # ── 蟋蟀跳跃闪避机制 ──
        if self.special == 'dodge' and random.random() < self._dodge_chance:
            self.last_event = 'dodged'
            # 随机位移30像素（简化版避障，不依赖obstacle列表）
            angle = random.uniform(0, math.pi * 2)
            dx = math.cos(angle) * self._dodge_distance
            dy = math.sin(angle) * self._dodge_distance
            new_x = self.x + dx
            new_y = self.y + dy
            # 限制在世界边界内
            self.x = max(30, min(WORLD_WIDTH - 30, new_x))
            self.y = max(60, min(WORLD_HEIGHT - 60, new_y))
            self.rect = self.image.get_rect(center=(int(self.x), int(self.y)))
            return False

        # ── 甲虫护甲机制：浮点伤害 ──
        if self.special == 'armor':
            damage = 1.0 * (1.0 - self._armor_ratio)  # 0.8伤害
            self.hp -= damage
        else:
            self.hp -= 1

        if self.hp <= 0:
            self.alive = False
            self._dying = True
            self._death_timer = 0.0
            return True

        # ── 蜜蜂反击机制：10%概率僵直攻击者0.5秒 ──
        if self.special == 'counter_attack' and attacker is not None:
            if random.random() < self._counter_chance:
                self.last_event = 'counter_attack'
                self.counter_stun_duration = self._counter_stun_duration

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
            if progress >= 1.0:
                # 动画完成：明确重置状态，确保后续不会被误判为"存活"或"死亡动画中"
                self._dying = False
                self.alive = False
                return True
            return False

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

        # 帧动画推进：根据时间切换帧
        if self._frames:
            self._anim_timer += dt
            if self._anim_timer >= self._anim_speed:
                self._anim_timer -= self._anim_speed
                self._frame_index = (self._frame_index + 1) % len(self._frames)
                self.image = self._frames[self._frame_index]

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
