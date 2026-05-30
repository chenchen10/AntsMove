"""蚂蚁精灵类：支持26种独立蚂蚁、地形特性、三属性独立升级"""

import pygame
import math
import random
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, WORLD_WIDTH, WORLD_HEIGHT, ANT_SIZE,
    BLUE_ANT_COLOR, RED_ANT_COLOR,
    STUN_DURATION, STUN_SPEED_MULT,
    SWEET_COLORS,
)
from ants_data import (
    ANTS, ANT_BY_ID, get_carry_capacity, get_speed, get_defense, MAX_ATTR_LEVEL,
    TRAIT_ALL_TERRAIN, TRAIT_DESERT_IMMUNE, TRAIT_DESERT_FULL,
    TRAIT_ICE_IMMUNE, TRAIT_COLD_IMMUNE, TRAIT_DEBUFF_IMMUNE,
    TRAIT_SUPREME, TRAIT_GROUND_SPEED, TRAIT_MOUNTAIN_SPEED,
    TRAIT_CLIMB_SPEED, TRAIT_ALL_CARRY_15, TRAIT_ALL_CARRY_20,
    TRAIT_PLAIN_BONUS, TRAIT_TROPICAL_EAT, TRAIT_FOREST_EAT,
    TRAIT_HEAVY_CARRY, TRAIT_EAT_50, TRAIT_ALL_15,
    TRAIT_KNOCKBACK_10, TRAIT_KNOCKBACK_20, TRAIT_STUN_30,
    TRAIT_STEAL_50, TRAIT_STUN_HALF, TRAIT_STUN_IMMUNE,
    TRAIT_EXP_BONUS, TRAIT_TROPICAL_HALF,
)
from terrain import get_terrain_debuffs, get_speed_multiplier, get_eat_speed_multiplier


class Ant(pygame.sprite.Sprite):
    """蚂蚁精灵：支持三属性独立升级"""

    STATE_IDLE = 'idle'
    STATE_MOVING_TO_SWEET = 'moving_to_sweet'
    STATE_EATING = 'eating'
    STATE_RETURNING = 'returning'
    STATE_STUNNED = 'stunned'

    def __init__(self, ant_id, team, x, y, carry_level=0, speed_level=0, defense_level=0,
                 assets=None, terrain=None, level=None):
        """
        三属性独立升级版本。
        兼容旧调用：如果传入 level 参数，视为 carry_level。
        """
        super().__init__()
        self.ant_id = ant_id
        self.team = team
        self.ant_data = ANT_BY_ID[ant_id]
        self.terrain = terrain

        # 属性等级
        if level is not None:
            carry_level = level  # 兼容旧代码
        self.carry_level = carry_level
        self.speed_level = speed_level
        self.defense_level = defense_level

        # 计算实际属性
        self.max_storage = get_carry_capacity(ant_id, carry_level)
        self.speed = get_speed(ant_id, speed_level)
        self.defense = get_defense(ant_id, defense_level)
        self.storage = 0
        self.coin_per = 1

        # 位置
        self.x = float(x)
        self.y = float(y)

        # 状态机
        self.state = self.STATE_IDLE
        self.target_sweet = None
        self.eat_timer = 0.0
        self.stun_timer = 0.0
        self.last_sweet_coin_per = 1
        self.last_sweet_zone_multiplier = 1.0

        # 差异化参数
        self.speed_var = random.uniform(0.92, 1.08)
        self.wobble_amp = random.uniform(10, 25)
        self.wobble_freq = random.uniform(1.5, 2.5)
        self.wobble_offset = random.uniform(0, math.pi * 2)

        # AI后期Buff（151关后由main.py设置）
        self._ai_terrain_debuff_reduction = 0.0
        self._ai_stun_reduction = 0.0

        # 障碍物列表引用（由main.py设置，用于碰撞绕行）
        self.obstacles = []

        # 战斗冷却（per-enemy，PRD v2.0 BUG-03）
        self._last_knockback_time = {}  # {enemy_ant_id: timestamp}
        self._last_stun_time = {}       # {enemy_ant_id: timestamp}
        self._last_steal_time = {}      # {enemy_ant_id: timestamp}
        self._stun_immune_until = 0.0   # 被僵直后的免疫期

        # 颜色
        if team == 'player':
            self.color = BLUE_ANT_COLOR
        else:
            self.color = RED_ANT_COLOR

        # 加载精灵
        self.size = ANT_SIZE
        self.assets = assets or {}

        # 优先使用每只蚂蚁的独立原型图
        ant_images = self.assets.get('ant_images', {})
        if ant_id in ant_images and ant_images[ant_id] is not None:
            self.base_image = ant_images[ant_id].copy()
            # 敌方蚂蚁加红色色调区分（只改RGB，不碰Alpha）
            if team == 'ai':
                tint = pygame.Surface(self.base_image.get_size(), pygame.SRCALPHA)
                tint.fill((220, 160, 160, 255))
                self.base_image.blit(tint, (0, 0), special_flags=pygame.BLEND_RGB_MULT)
            self.up_frames = []
            self.down_frames = []
        elif team == 'player':
            self.up_frames = self.assets.get('blue_ant_up_frames', [])
            self.down_frames = self.assets.get('blue_ant_down_frames', [])
            self.base_image = self.up_frames[0] if self.up_frames else pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        else:
            self.up_frames = []
            self.down_frames = []
            self.base_image = self.assets.get('red_ant', pygame.Surface((self.size, self.size), pygame.SRCALPHA))
        self.image = self.base_image.copy()
        self.rect = self.image.get_rect(center=(int(self.x), int(self.y)))

        # 动画
        self.move_anim = 0.0
        self.anim_frame_idx = 0
        self.anim_frame_timer = 0.0
        self.prev_x = self.x
        self.prev_y = self.y

        # 应用特性加成
        self._apply_trait_bonuses()

    def _apply_trait_bonuses(self):
        """应用蚂蚁特性的被动加成"""
        trait = self.ant_data['trait']

        if trait == TRAIT_EXP_BONUS:
            self.max_storage = int(self.max_storage * 1.20)

        if trait == TRAIT_ALL_15:
            self.speed *= 1.15
            self.max_storage = int(self.max_storage * 1.15)

        if trait == TRAIT_SUPREME:
            self.max_storage = int(self.max_storage * 1.3)

        if trait == TRAIT_ALL_CARRY_15:
            self.max_storage = int(self.max_storage * 1.15)
        if trait == TRAIT_ALL_CARRY_20:
            self.max_storage = int(self.max_storage * 1.20)

        if trait == TRAIT_PLAIN_BONUS:
            self.max_storage = int(self.max_storage * 1.10)

        if trait == TRAIT_MOUNTAIN_SPEED:
            self.speed *= 1.20

        if trait == TRAIT_CLIMB_SPEED:
            self.speed *= 1.30

    def _reduce_debuff(self, mult):
        """AI后期Buff：缩减地形负面效果强度"""
        if self._ai_terrain_debuff_reduction > 0 and mult < 1.0:
            mult = mult + (1.0 - mult) * self._ai_terrain_debuff_reduction
        return mult

    def get_effective_speed(self, terrain=None):
        effective = self.speed * self.speed_var
        if terrain and self.terrain:
            debuffs = get_terrain_debuffs(terrain, self.ant_data.get('terrain'), self.ant_data['trait'])
            speed_mult = get_speed_multiplier(debuffs, terrain_type=terrain)
            speed_mult = self._reduce_debuff(speed_mult)
            effective *= speed_mult
        return effective

    def get_eat_speed_mult(self, terrain=None):
        mult = 1.0
        if terrain and self.terrain:
            debuffs = get_terrain_debuffs(terrain, self.ant_data.get('terrain'), self.ant_data['trait'])
            mult = get_eat_speed_multiplier(debuffs)
            mult = self._reduce_debuff(mult)
        trait = self.ant_data['trait']
        if trait == TRAIT_FOREST_EAT and terrain:
            from terrain import TerrainType
            if terrain == TerrainType.FOREST:
                mult *= 1.2
        if trait == TRAIT_TROPICAL_EAT and terrain:
            from terrain import TerrainType
            if terrain == TerrainType.TROPICAL:
                mult *= 1.3
        if trait == TRAIT_EAT_50:
            mult *= 1.5
        if trait == TRAIT_HEAVY_CARRY:
            mult *= 1.2
        if trait == TRAIT_SUPREME:
            mult *= 1.5
        return mult

    def get_carry_mult(self, terrain=None):
        mult = 1.0
        if terrain and self.terrain:
            debuffs = get_terrain_debuffs(terrain, self.ant_data.get('terrain'), self.ant_data['trait'])
            from terrain import get_carry_multiplier
            mult = get_carry_multiplier(debuffs)
            mult = self._reduce_debuff(mult)
        return mult

    def is_debuff_immune(self):
        return self.ant_data['trait'] in (TRAIT_DEBUFF_IMMUNE, TRAIT_SUPREME, TRAIT_ALL_TERRAIN)

    def has_knockback(self):
        trait = self.ant_data['trait']
        if trait == TRAIT_KNOCKBACK_10:
            return 0.10
        if trait == TRAIT_KNOCKBACK_20:
            return 0.20
        return 0.0

    def has_stun_chance(self):
        trait = self.ant_data['trait']
        if trait == TRAIT_STUN_30:
            return 0.30
        return 0.0

    def has_steal(self):
        trait = self.ant_data['trait']
        if trait == TRAIT_STEAL_50:
            return 0.50
        return 0.0

    def has_exp_bonus(self):
        return self.ant_data['trait'] == TRAIT_EXP_BONUS

    def is_stun_half(self):
        return self.ant_data['trait'] == TRAIT_STUN_HALF

    def move_toward(self, tx, ty, dt, speed_mult=1.0):
        dx = tx - self.x
        dy = ty - self.y
        dist = math.sqrt(dx * dx + dy * dy)
        if dist < 2:
            self.x = tx
            self.y = ty
            self._update_animation(dt, moving=False)
            self.rect.center = (int(self.x), int(self.y))
            return True

        effective_speed = self.get_effective_speed(self.terrain) * speed_mult
        if self.state == self.STATE_STUNNED:
            effective_speed *= STUN_SPEED_MULT

        dir_x = dx / dist
        dir_y = dy / dist

        self.wobble_offset += dt * self.wobble_freq
        wobble = math.sin(self.wobble_offset) * self.wobble_amp
        perp_x = -dir_y
        perp_y = dir_x

        move_dist = effective_speed * dt
        if move_dist >= dist:
            new_x, new_y = tx, ty
        else:
            new_x = self.x + dir_x * move_dist + perp_x * wobble * dt
            new_y = self.y + dir_y * move_dist + perp_y * wobble * dt

        # 障碍物碰撞绕行
        if self.obstacles:
            new_x, new_y = self._avoid_obstacles(new_x, new_y, dir_x, dir_y, move_dist)

        self.x = max(10, min(WORLD_WIDTH - 10, new_x))
        self.y = max(10, min(WORLD_HEIGHT - 10, new_y))

        self._update_animation(dt, moving=True)
        self.rect.center = (int(self.x), int(self.y))
        return False

    def _avoid_obstacles(self, new_x, new_y, dir_x, dir_y, move_dist):
        """碰撞绕行：沿路径逐段检测，碰撞时尝试绕行、滑动或沿原方向最大安全距离前进"""
        ant_radius = self.size // 2
        total_dist = math.sqrt((new_x - self.x) ** 2 + (new_y - self.y) ** 2)
        min_step = 2  # 最小采样步长

        def _point_clear(x, y):
            """检查单个点是否无障碍"""
            for obs in self.obstacles:
                if obs.check_collision(x, y, ant_radius):
                    return False
            return True

        def _max_safe_dist(sx, sy, dx, dy, max_d):
            """沿(dx,dy)方向从(sx,sy)出发，找到最大安全前进距离（二分法）"""
            # 逐步从最小步长开始探测
            for start in [min_step, ant_radius // 2, ant_radius]:
                if start <= max_d and _point_clear(sx + dx * start, sy + dy * start):
                    lo, hi = start, max_d
                    for _ in range(10):
                        mid = (lo + hi) / 2
                        if _point_clear(sx + dx * mid, sy + dy * mid):
                            lo = mid
                        else:
                            hi = mid
                    return lo
            return 0

        # 检查原路径是否碰撞
        if _point_clear(new_x, new_y):
            d = total_dist
            if d < 1:
                return new_x, new_y
            n = max(1, int(d / min_step))
            path_ok = True
            for i in range(1, n):
                t = i / n
                cx = self.x + (new_x - self.x) * t
                cy = self.y + (new_y - self.y) * t
                if not _point_clear(cx, cy):
                    path_ok = False
                    break
            if path_ok:
                return new_x, new_y

        # 阶段1：沿原方向找到最大安全前进距离
        safe_dist = _max_safe_dist(self.x, self.y, dir_x, dir_y, total_dist)
        if safe_dist > min_step:
            return self.x + dir_x * safe_dist, self.y + dir_y * safe_dist

        # 阶段2：尝试多个角度绕行
        best_x, best_y = None, None
        best_angle = float('inf')
        short_dist = min(total_dist, ant_radius * 4)

        for angle_offset in [0.3, -0.3, 0.6, -0.6, 0.9, -0.9, 1.2, -1.2, 1.5, -1.5]:
            cos_a = math.cos(angle_offset)
            sin_a = math.sin(angle_offset)
            test_dir_x = dir_x * cos_a - dir_y * sin_a
            test_dir_y = dir_x * sin_a + dir_y * cos_a
            sd = _max_safe_dist(self.x, self.y, test_dir_x, test_dir_y, short_dist)
            if sd > min_step:
                test_x = self.x + test_dir_x * sd
                test_y = self.y + test_dir_y * sd
                d = abs(angle_offset)
                if d < best_angle:
                    best_angle = d
                    best_x, best_y = test_x, test_y

        if best_x is not None:
            return best_x, best_y

        # 阶段3：沿最近障碍物推开方向滑动
        nearest_obs = None
        nearest_dist = float('inf')
        for obs in self.obstacles:
            if not obs.collidable:
                continue
            cx = max(obs.rect.left, min(self.x, obs.rect.right))
            cy = max(obs.rect.top, min(self.y, obs.rect.bottom))
            d = math.hypot(self.x - cx, self.y - cy)
            if d < nearest_dist:
                nearest_dist = d
                nearest_obs = obs

        if nearest_obs is not None:
            cx = max(nearest_obs.rect.left, min(self.x, nearest_obs.rect.right))
            cy = max(nearest_obs.rect.top, min(self.y, nearest_obs.rect.bottom))
            push_dx = self.x - cx
            push_dy = self.y - cy
            push_len = math.hypot(push_dx, push_dy)
            if push_len > 1:
                push_dx /= push_len
                push_dy /= push_len
            else:
                push_dx = dir_x if abs(dir_x) > 0.01 else 1.0
                push_dy = dir_y if abs(dir_y) > 0.01 else 0.0
                pl = math.hypot(push_dx, push_dy)
                push_dx /= pl
                push_dy /= pl

            # 沿推开方向前进
            push_dist = _max_safe_dist(self.x, self.y, push_dx, push_dy, ant_radius * 3)
            if push_dist > min_step:
                return self.x + push_dx * push_dist, self.y + push_dy * push_dist

            # 沿推开方向的垂直方向（沿障碍物表面）滑动
            for perp_sign in [1, -1]:
                slide_x = -push_dy * perp_sign
                slide_y = push_dx * perp_sign
                sd = _max_safe_dist(self.x, self.y, slide_x, slide_y, ant_radius * 3)
                if sd > min_step:
                    return self.x + slide_x * sd, self.y + slide_y * sd

        # 阶段4：最后尝试任意方向短距离移动
        for angle in [0, 0.5, -0.5, 1.0, -1.0, 1.5, -1.5, 2.0, -2.0, math.pi]:
            dx = math.cos(angle)
            dy = math.sin(angle)
            sd = _max_safe_dist(self.x, self.y, dx, dy, ant_radius * 2)
            if sd > min_step:
                return self.x + dx * sd, self.y + dy * sd

        return self.x, self.y

    def _update_animation(self, dt, moving=True):
        dx = self.x - self.prev_x
        dy = self.y - self.prev_y
        self.prev_x = self.x
        self.prev_y = self.y

        bob = 0
        tilt = 0
        if moving:
            self.move_anim += dt * 8
            bob = math.sin(self.move_anim) * 1.5

            if dy < -0.1:
                frames = self.up_frames
            elif dy > 0.1:
                frames = self.down_frames
            else:
                frames = self.up_frames or self.down_frames

            if abs(dx) > 0.5 and abs(dy) > 0.5:
                if dx > 0 and dy < 0:
                    tilt = -45
                elif dx < 0 and dy < 0:
                    tilt = 45
                elif dx > 0 and dy > 0:
                    tilt = 45
                else:
                    tilt = -45

            if frames:
                self.anim_frame_timer += dt
                if self.anim_frame_timer >= 0.15:
                    self.anim_frame_timer -= 0.15
                    self.anim_frame_idx = (self.anim_frame_idx + 1) % len(frames)
                frame = frames[self.anim_frame_idx]
            else:
                frame = self.base_image
        else:
            self.anim_frame_timer = 0.0
            frame = (self.up_frames or [self.base_image])[0]

        if tilt != 0:
            frame = pygame.transform.rotate(frame, tilt)
        self.image = frame
        self.rect = self.image.get_rect(center=(int(self.x), int(self.y + bob)))

    def is_storage_full(self):
        return self.storage >= self.max_storage

    def stun(self, immune=False):
        if immune or self.is_debuff_immune():
            return
        if self.state != self.STATE_STUNNED:
            self.state = self.STATE_STUNNED
            duration = STUN_DURATION
            # 防御减少僵直时间
            duration *= (1.0 - self.defense * 0.005)  # 每点防御减少0.5%僵直
            # 151关后AI僵直再减15%
            if self._ai_stun_reduction > 0:
                duration *= (1.0 - self._ai_stun_reduction)
            duration = max(0.1, duration)
            if self.is_stun_half():
                duration *= 0.5
            self.stun_timer = duration
            self.target_sweet = None
            self.eat_timer = 0.0

    def draw_storage_bar(self, screen):
        if self.storage <= 0:
            return
        icon_count = (self.storage + 1) // 2
        icon_size = 12
        spacing = 2
        total_height = icon_count * (icon_size + spacing) - spacing
        start_x = int(self.x) - icon_size // 2
        start_y = int(self.y) - self.size // 2 - 5 - total_height
        icon_key = f'{self.ant_data["name"]}_icon'
        icon_image = self.assets.get(icon_key)
        for i in range(icon_count):
            x = start_x
            y = start_y + i * (icon_size + spacing)
            if icon_image:
                screen.blit(icon_image, (x, y))
            else:
                color = SWEET_COLORS.get('candy', (200, 200, 200))
                pygame.draw.circle(screen, color, (x + icon_size // 2, y + icon_size // 2), icon_size // 2)

    def draw_stun_indicator(self, screen, font):
        if self.state == self.STATE_STUNNED:
            txt = font.render("晕", True, (255, 0, 0))
            screen.blit(txt, (int(self.x) - txt.get_width() // 2,
                              int(self.y) - self.size // 2 - 22))

    def draw_level_badge(self, screen, font):
        """绘制等级标签（显示搬运等级）"""
        if self.team == 'player' and self.carry_level > 0:
            txt = font.render(f"C{self.carry_level}", True, (200, 220, 255))
            screen.blit(txt, (int(self.x) - txt.get_width() // 2,
                              int(self.y) + self.size // 2 + 2))

    def draw_storage_bar_at(self, screen, camera):
        """绘制搬运量条（使用摄像机偏移）"""
        if self.storage <= 0:
            return
        icon_count = (self.storage + 1) // 2
        icon_size = 12
        spacing = 2
        total_height = icon_count * (icon_size + spacing) - spacing
        sx, sy = camera.world_to_screen(self.x, self.y)
        start_x = int(sx) - icon_size // 2
        start_y = int(sy) - self.size // 2 - 5 - total_height
        icon_key = f'{self.ant_data["name"]}_icon'
        icon_image = self.assets.get(icon_key)
        for i in range(icon_count):
            x = start_x
            y = start_y + i * (icon_size + spacing)
            if icon_image:
                screen.blit(icon_image, (x, y))
            else:
                color = SWEET_COLORS.get('candy', (200, 200, 200))
                pygame.draw.circle(screen, color, (x + icon_size // 2, y + icon_size // 2), icon_size // 2)

    def draw_stun_indicator_at(self, screen, font, camera):
        """绘制僵直指示器（使用摄像机偏移）"""
        if self.state == self.STATE_STUNNED:
            sx, sy = camera.world_to_screen(self.x, self.y)
            txt = font.render("晕", True, (255, 0, 0))
            screen.blit(txt, (int(sx) - txt.get_width() // 2,
                              int(sy) - self.size // 2 - 22))

    def draw_level_badge_at(self, screen, font, camera):
        """绘制等级标签（使用摄像机偏移）"""
        if self.team == 'player' and self.carry_level > 0:
            sx, sy = camera.world_to_screen(self.x, self.y)
            txt = font.render(f"C{self.carry_level}", True, (200, 220, 255))
            screen.blit(txt, (int(sx) - txt.get_width() // 2,
                              int(sy) + self.size // 2 + 2))
