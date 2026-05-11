"""成就解锁通知系统：顶部弹窗 + 光效粒子 + 队列播放 + 音效

通知从屏幕顶部滑入，显示成就图标、名称、描述，伴随金色粒子特效，
停留约2.5秒后滑出。多个成就同时解锁时依次播放，间隔0.3秒。
点击通知可跳转到成就面板。
"""

import pygame
import math
import random
import array
import struct

from config import SCREEN_WIDTH, SCREEN_HEIGHT, ACCENT_GOLD, WHITE, TEXT_COLOR
import font_helper


# ── 音效合成 ──

def _generate_unlock_sound():
    """生成成就解锁音效：短促的上行三音和弦 + 淡出"""
    try:
        sample_rate = 22050
        duration = 0.6
        n_samples = int(sample_rate * duration)
        buf = array.array('h')  # signed short

        # 三个音符的频率 (C5, E5, G5)
        freqs = [523, 659, 784]
        for i in range(n_samples):
            t = i / sample_rate
            # 每个音符依次响起，间隔0.12秒
            val = 0.0
            for j, freq in enumerate(freqs):
                note_start = j * 0.12
                if t < note_start:
                    continue
                note_t = t - note_start
                note_env = max(0, 1.0 - note_t / (duration - note_start))
                val += math.sin(2 * math.pi * freq * note_t) * note_env * 0.3

            # 整体淡出
            global_env = max(0, 1.0 - t / duration)
            val *= global_env

            sample = int(max(-32767, min(32767, val * 32767)))
            buf.append(sample)

        sound = pygame.mixer.Sound(buffer=buf)
        sound.set_volume(0.5)
        return sound
    except Exception:
        return None


# ── 粒子系统 ──

class _Sparkle:
    """单个金色光点粒子"""

    __slots__ = ('x', 'y', 'vx', 'vy', 'life', 'max_life', 'size', 'color')

    def __init__(self, x, y):
        self.x = x
        self.y = y
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(20, 80)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed - 30  # 轻微向上偏移
        self.life = random.uniform(0.4, 1.0)
        self.max_life = self.life
        self.size = random.uniform(2, 5)
        # 金色系随机色
        self.color = (
            random.randint(218, 255),
            random.randint(165, 220),
            random.randint(32, 100),
        )

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += 20 * dt  # 轻微重力
        self.life -= dt

    def draw(self, screen):
        if self.life <= 0:
            return
        alpha = max(0, min(255, int(255 * (self.life / self.max_life))))
        size = max(1, int(self.size * (self.life / self.max_life)))
        surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
        pygame.draw.circle(surf, (*self.color, alpha), (size, size), size)
        screen.blit(surf, (int(self.x) - size, int(self.y) - size))


# ── 单条通知 ──

class AchievementNotification:
    """单条成就解锁通知，含滑入/停留/滑出动画 + 粒子特效"""

    # 动画时间参数（秒）
    SLIDE_IN_DURATION = 0.4
    DISPLAY_DURATION = 2.5
    SLIDE_OUT_DURATION = 0.3

    # 通知尺寸
    BANNER_W = 360
    BANNER_H = 72

    def __init__(self, achievement, unlock_time=None):
        """
        achievement: {'id', 'name', 'desc', 'icon_text', 'rewards'}
        unlock_time: 解锁时刻的 unix timestamp（用于标题显示）
        """
        self.achievement = achievement
        self.unlock_time = unlock_time

        # 动画状态
        self.timer = 0.0
        self.phase = 'slide_in'  # slide_in -> display -> slide_out -> done
        self.alive = True

        # 目标位置（屏幕顶部居中）
        self.target_x = (SCREEN_WIDTH - self.BANNER_W) // 2
        self.target_y = 16
        self.current_y = self.target_y - self.BANNER_H - 20  # 起始位置在屏幕外

        # 粒子
        self._particles = []
        self._particle_timer = 0.0

    @property
    def total_duration(self):
        return self.SLIDE_IN_DURATION + self.DISPLAY_DURATION + self.SLIDE_OUT_DURATION

    @property
    def rect(self):
        """通知的可点击区域"""
        return pygame.Rect(self.target_x, int(self.current_y), self.BANNER_W, self.BANNER_H)

    def update(self, dt):
        self.timer += dt

        if self.phase == 'slide_in':
            progress = min(1.0, self.timer / self.SLIDE_IN_DURATION)
            # ease-out cubic
            eased = 1 - (1 - progress) ** 3
            self.current_y = (self.target_y - self.BANNER_H - 20) + \
                             (self.target_y - (self.target_y - self.BANNER_H - 20)) * eased
            if progress >= 1.0:
                self.phase = 'display'
                self.timer = 0.0
                self.current_y = self.target_y

        elif self.phase == 'display':
            progress = self.timer / self.DISPLAY_DURATION
            if progress >= 1.0:
                self.phase = 'slide_out'
                self.timer = 0.0

            # 持续生成粒子
            self._particle_timer += dt
            if self._particle_timer >= 0.08:
                self._particle_timer = 0.0
                cx = self.target_x + self.BANNER_W // 2
                cy = int(self.current_y) + self.BANNER_H // 2
                for _ in range(3):
                    self._particles.append(_Sparkle(cx, cy))

        elif self.phase == 'slide_out':
            progress = min(1.0, self.timer / self.SLIDE_OUT_DURATION)
            # ease-in cubic
            eased = progress ** 3
            self.current_y = self.target_y + (-self.BANNER_H - 20 - self.target_y) * eased
            if progress >= 1.0:
                self.alive = False

        # 更新粒子
        for p in self._particles:
            p.update(dt)
        self._particles = [p for p in self._particles if p.life > 0]

    def draw(self, screen):
        if not self.alive:
            return

        y = int(self.current_y)
        x = self.target_x

        # 通知卡片背景
        banner_rect = pygame.Rect(x, y, self.BANNER_W, self.BANNER_H)
        self._draw_banner(screen, banner_rect)

        # 粒子（在卡片上方绘制）
        for p in self._particles:
            p.draw(screen)

    def _draw_banner(self, screen, rect):
        """绘制通知卡片"""
        # 半透明背景
        bg_surf = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
        # 主背景：深色半透明
        pygame.draw.rect(bg_surf, (30, 30, 50, 220), (0, 0, rect.w, rect.h), border_radius=12)
        # 金色顶部高光线
        pygame.draw.line(bg_surf, (*ACCENT_GOLD, 180), (12, 2), (rect.w - 12, 2), 2)
        # 金色边框
        pygame.draw.rect(bg_surf, (*ACCENT_GOLD, 120), (0, 0, rect.w, rect.h), 2, border_radius=12)
        screen.blit(bg_surf, rect)

        # 左侧图标区
        icon_size = 44
        icon_rect = pygame.Rect(rect.x + 12, rect.y + (rect.h - icon_size) // 2, icon_size, icon_size)
        icon_bg = pygame.Surface((icon_size, icon_size), pygame.SRCALPHA)
        pygame.draw.rect(icon_bg, (*ACCENT_GOLD, 60), (0, 0, icon_size, icon_size), border_radius=10)
        screen.blit(icon_bg, icon_rect)
        # 图标文字（emoji）
        icon_font = font_helper.get_font(24)
        icon_txt = icon_font.render(self.achievement.get('icon_text', '⭐'), True, WHITE)
        screen.blit(icon_txt, (icon_rect.centerx - icon_txt.get_width() // 2,
                               icon_rect.centery - icon_txt.get_height() // 2))

        # 右侧文字区
        text_x = rect.x + 66
        text_w = rect.w - 78

        # 成就名称
        name_font = font_helper.get_font(16)
        name_txt = name_font.render(self.achievement.get('name', '成就'), True, ACCENT_GOLD)
        screen.blit(name_txt, (text_x, rect.y + 10))

        # "成就解锁" 标签
        tag_font = font_helper.get_font(11)
        tag_txt = tag_font.render("成就解锁", True, (180, 180, 190))
        screen.blit(tag_txt, (text_x + name_txt.get_width() + 8, rect.y + 13))

        # 成就描述
        desc_font = font_helper.get_font(13)
        desc = self.achievement.get('desc', '')
        desc_txt = desc_font.render(desc, True, (200, 200, 210))
        # 截断过长描述
        if desc_txt.get_width() > text_w:
            while len(desc) > 0 and desc_txt.get_width() > text_w - 10:
                desc = desc[:-1]
                desc_txt = desc_font.render(desc + "...", True, (200, 200, 210))
        screen.blit(desc_txt, (text_x, rect.y + 34))

        # 奖励金币数
        reward = self.achievement.get('rewards', {}).get('coins', 0)
        if reward > 0:
            reward_font = font_helper.get_font(13)
            reward_txt = reward_font.render(f"+{reward}G", True, ACCENT_GOLD)
            screen.blit(reward_txt, (text_x, rect.y + 52))

    def handle_click(self, mx, my):
        """点击通知 → 返回 True 表示应跳转到成就面板"""
        return self.rect.collidepoint(mx, my)


# ── 通知队列 ──

class AchievementNotifyQueue:
    """成就解锁通知队列：依次播放多条通知"""

    GAP_DURATION = 0.3  # 两条通知之间的间隔

    def __init__(self):
        self._queue = []       # 等待播放的成就列表
        self._current = None   # 当前正在显示的通知
        self._gap_timer = 0.0  # 间隔倒计时
        self._in_gap = False   # 是否处于间隔期
        self._sound = None     # 解锁音效（懒加载）
        self._sound_loaded = False

    def _ensure_sound(self):
        """懒加载音效"""
        if not self._sound_loaded:
            self._sound_loaded = True
            self._sound = _generate_unlock_sound()

    def push(self, achievement):
        """入队一条成就通知

        achievement: {'id', 'name', 'desc', 'icon_text', 'rewards'}
        """
        self._queue.append(achievement)

    def push_many(self, achievements):
        """批量入队"""
        for ach in achievements:
            self._queue.append(ach)

    @property
    def is_active(self):
        """是否有通知正在显示或等待显示"""
        return self._current is not None or len(self._queue) > 0

    @property
    def current_notification(self):
        """当前正在显示的通知（用于点击检测）"""
        return self._current

    def update(self, dt):
        # 更新当前通知
        if self._current is not None:
            self._current.update(dt)
            if not self._current.alive:
                self._current = None
                self._in_gap = True
                self._gap_timer = self.GAP_DURATION
            return

        # 间隔期
        if self._in_gap:
            self._gap_timer -= dt
            if self._gap_timer <= 0:
                self._in_gap = False

        # 从队列取下一条
        if not self._in_gap and self._current is None and self._queue:
            ach = self._queue.pop(0)
            self._current = AchievementNotification(ach)
            # 播放音效
            self._ensure_sound()
            if self._sound:
                try:
                    self._sound.play()
                except Exception:
                    pass

    def draw(self, screen):
        if self._current is not None:
            self._current.draw(screen)

    def handle_click(self, mx, my):
        """点击检测。返回 True 表示应跳转到成就面板"""
        if self._current is not None:
            return self._current.handle_click(mx, my)
        return False

    def clear(self):
        """清空队列"""
        self._queue.clear()
        self._current = None
        self._in_gap = False
        self._gap_timer = 0.0
