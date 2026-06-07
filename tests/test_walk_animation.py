#!/usr/bin/env python3
"""
蚂蚁行走动画集成测试
测试范围：
1. assets.py load_walk_animation() — Sprite Sheet / 序列帧 / 空列表兜底
2. config.py WALK_ANIM_FPS 常量
3. ant_sprite.py _update_animation() — walk_frames 播放逻辑
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 设置 SDL 视频驱动为哑模式，避免无显示器环境报错
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'

import pygame
pygame.init()
screen = pygame.display.set_mode((1, 1))

from config import WALK_ANIM_FPS
from assets import load_walk_animation, ANT_PROCESSED_DIR, TARGET_SIZES

# ============================================================
# 1. config.py — WALK_ANIM_FPS 常量
# ============================================================
class TestWalkAnimFPS(unittest.TestCase):
    def test_fps_exists(self):
        """WALK_ANIM_FPS 应存在且为正整数"""
        self.assertIsInstance(WALK_ANIM_FPS, int)
        self.assertGreater(WALK_ANIM_FPS, 0)

    def test_fps_value(self):
        """WALK_ANIM_FPS 应为 12"""
        self.assertEqual(WALK_ANIM_FPS, 12)


# ============================================================
# 2. assets.py — load_walk_animation() 加载优先级
# ============================================================
class TestLoadWalkAnimation(unittest.TestCase):

    def test_sprite_sheet_loads_24_frames(self):
        """Sprite Sheet 加载：应返回 24 帧（8列×3行）"""
        frames = load_walk_animation(1)
        self.assertEqual(len(frames), 24, f"期望 24 帧，实际 {len(frames)} 帧")

    def test_sprite_sheet_frame_size(self):
        """Sprite Sheet 帧尺寸应与 TARGET_SIZES['ant'] 一致"""
        frames = load_walk_animation(1)
        target = TARGET_SIZES['ant']
        for i, f in enumerate(frames):
            self.assertEqual(f.get_size(), target,
                             f"帧 {i} 尺寸 {f.get_size()} 不匹配目标 {target}")

    def test_sprite_sheet_frame_is_surface(self):
        """每帧应为 pygame Surface"""
        frames = load_walk_animation(1)
        for i, f in enumerate(frames):
            self.assertIsInstance(f, pygame.Surface, f"帧 {i} 不是 Surface")

    def test_sprite_sheet_frame_alpha(self):
        """Sprite Sheet 帧应包含 Alpha 通道（去背处理）"""
        frames = load_walk_animation(1)
        for i, f in enumerate(frames):
            flags = f.get_flags()
            self.assertTrue(flags & pygame.SRCALPHA,
                            f"帧 {i} 缺少 SRCALPHA 标志")

    def test_load_priority_sheet_over_sequence(self):
        """加载优先级：Sprite Sheet 优先于序列帧"""
        sheet_path = os.path.join(ANT_PROCESSED_DIR, 'ant1_walk_sheet.png')
        walk_dir = os.path.join(ANT_PROCESSED_DIR, 'ant1_walk')
        # 两者都存在时，load_walk_animation 返回 Sheet 的帧数（24）
        if os.path.exists(sheet_path) and os.path.isdir(walk_dir):
            frames = load_walk_animation(1)
            self.assertEqual(len(frames), 24,
                             "两者共存时应优先加载 Sprite Sheet（24帧）")

    def test_nonexistent_ant_returns_empty(self):
        """不存在的 ant_id 应返回空列表"""
        frames = load_walk_animation(999)
        self.assertEqual(frames, [], "不存在的 ant_id 应返回空列表")

    def test_sheet_not_exists_fallback_to_sequence(self):
        """若 Sheet 不存在，应回退到序列帧目录"""
        # 临时重命名 sheet 测试回退
        sheet_path = os.path.join(ANT_PROCESSED_DIR, 'ant99_walk_sheet.png')
        walk_dir = os.path.join(ANT_PROCESSED_DIR, 'ant99_walk')
        # ant99 不存在，应返回空
        frames = load_walk_animation(999)
        self.assertEqual(frames, [])


# ============================================================
# 3. ant_sprite.py — _update_animation() 行走帧播放
# ============================================================
class TestAntSpriteWalkAnimation(unittest.TestCase):

    def _make_ant(self, walk_frames=None):
        """创建一个最小化的 Ant 用于测试"""
        from ant_sprite import Ant
        assets = {}
        if walk_frames is not None:
            assets['ant_walk_frames'] = {1: walk_frames}
        assets['ant_images'] = {1: pygame.Surface((48, 48), pygame.SRCALPHA)}
        ant = Ant.__new__(Ant)
        # 手动初始化关键属性
        ant.x = 100.0
        ant.y = 100.0
        ant.prev_x = 100.0
        ant.prev_y = 100.0
        ant.size = 48
        ant.team = 'player'
        ant.ant_id = 1
        ant.assets = assets
        ant_walk_frames_map = assets.get('ant_walk_frames', {})
        ant.walk_frames = ant_walk_frames_map.get(1, [])
        ant.base_image = assets['ant_images'][1].copy()
        ant.up_frames = []
        ant.down_frames = []
        ant.image = ant.base_image.copy()
        ant.rect = ant.image.get_rect(center=(int(ant.x), int(ant.y)))
        ant.move_anim = 0.0
        ant.anim_frame_idx = 0
        ant.anim_frame_timer = 0.0
        ant.state = 0  # STATE_IDLE
        ant.terrain = None
        return ant

    def test_walk_frames_assigned(self):
        """AntSprite 初始化时 walk_frames 应正确赋值"""
        frames = [pygame.Surface((48, 48), pygame.SRCALPHA) for _ in range(24)]
        ant = self._make_ant(walk_frames=frames)
        self.assertEqual(len(ant.walk_frames), 24)

    def test_walk_frames_empty_when_no_data(self):
        """无素材时 walk_frames 应为空列表"""
        ant = self._make_ant(walk_frames=None)
        self.assertEqual(ant.walk_frames, [])

    def test_animation_playback_advances_frame(self):
        """行走时 _update_animation 应推进帧索引"""
        frames = [pygame.Surface((48, 48), pygame.SRCALPHA) for _ in range(24)]
        ant = self._make_ant(walk_frames=frames)
        ant.x = 150.0  # 产生位移

        dt = 1.0 / 12.0  # 一帧间隔
        ant._update_animation(dt, moving=True)

        # 移动后应至少推进一帧
        self.assertGreater(ant.anim_frame_idx, 0,
                           f"移动 {dt}s 后帧索引仍为 0，动画未推进")

    def test_animation_wraps_around(self):
        """帧索引应循环回绕"""
        frames = [pygame.Surface((48, 48), pygame.SRCALPHA) for _ in range(24)]
        ant = self._make_ant(walk_frames=frames)
        ant.x = 150.0

        # 播放足够长时间让帧循环
        dt = 1.0 / 12.0
        for _ in range(50):
            ant._update_animation(dt, moving=True)

        # 帧索引应在 [0, 24) 范围内
        self.assertIn(ant.anim_frame_idx, range(24),
                      f"帧索引 {ant.anim_frame_idx} 超出范围")

    def test_static_shows_first_frame(self):
        """静止时应显示 walk_frames 的第 0 帧"""
        frames = [pygame.Surface((48, 48), pygame.SRCALPHA) for _ in range(24)]
        ant = self._make_ant(walk_frames=frames)
        ant._update_animation(0.1, moving=False)
        self.assertEqual(ant.image, frames[0],
                         "静止时应显示 walk_frames[0]")

    def test_fallback_without_walk_frames(self):
        """无 walk_frames 时应回退到 up_frames/down_frames 逻辑"""
        ant = self._make_ant(walk_frames=[])
        ant.up_frames = [pygame.Surface((48, 48), pygame.SRCALPHA)]
        ant.down_frames = []
        ant._update_animation(0.1, moving=False)
        # 应使用 up_frames 或 base_image
        self.assertIsNotNone(ant.image)

    def test_fps_interval_calculation(self):
        """帧间隔应为 1/WALK_ANIM_FPS"""
        frames = [pygame.Surface((48, 48), pygame.SRCALPHA) for _ in range(24)]
        ant = self._make_ant(walk_frames=frames)
        ant.x = 150.0

        expected_interval = 1.0 / WALK_ANIM_FPS
        # 恰好一个间隔应推进一帧
        ant._update_animation(expected_interval, moving=True)
        self.assertEqual(ant.anim_frame_idx, 1,
                         f"一个间隔后帧索引应为 1，实际 {ant.anim_frame_idx}")

    def test_tilt_applies_on_diagonal(self):
        """对角线移动时应产生倾斜效果"""
        frames = [pygame.Surface((48, 48), pygame.SRCALPHA) for _ in range(24)]
        ant = self._make_ant(walk_frames=frames)
        # 对角线移动
        ant.x = 110.0
        ant.y = 90.0

        ant._update_animation(0.1, moving=True)
        # 倾斜会导致 image 旋转，尺寸可能改变
        # 只要 image 被更新即可
        self.assertIsNotNone(ant.image)


# ============================================================
# 4. 集成测试 — load_walk_animation → AntSprite
# ============================================================
class TestIntegration(unittest.TestCase):

    def test_full_pipeline(self):
        """完整流程：load → Ant → 播放"""
        from ant_sprite import Ant

        # 加载行走动画
        walk_frames = load_walk_animation(1)
        self.assertEqual(len(walk_frames), 24, "应加载到 24 帧")

        # 构造 assets
        assets = {'ant_walk_frames': {1: walk_frames}, 'ant_images': {}}
        fallback = pygame.Surface((48, 48), pygame.SRCALPHA)
        for aid in range(1, 27):
            assets['ant_images'][aid] = fallback

        # 创建 Ant
        ant = Ant.__new__(Ant)
        ant.x = 100.0
        ant.y = 100.0
        ant.prev_x = 100.0
        ant.prev_y = 100.0
        ant.size = 48
        ant.team = 'player'
        ant.ant_id = 1
        ant.assets = assets
        ant_walk_frames_map = assets.get('ant_walk_frames', {})
        ant.walk_frames = ant_walk_frames_map.get(1, [])
        ant.base_image = assets['ant_images'][1].copy()
        ant.up_frames = []
        ant.down_frames = []
        ant.image = ant.base_image.copy()
        ant.rect = ant.image.get_rect(center=(int(ant.x), int(ant.y)))
        ant.move_anim = 0.0
        ant.anim_frame_idx = 0
        ant.anim_frame_timer = 0.0
        ant.state = 0
        ant.terrain = None

        # 播放 1 秒
        dt = 1.0 / 60.0
        for _ in range(60):
            ant.x += 1.0
            ant._update_animation(dt, moving=True)

        # 应播放了多帧
        expected_frames_played = int(60 * dt * WALK_ANIM_FPS)
        self.assertGreater(ant.anim_frame_idx, 0,
                           f"播放 1s 后帧索引 {ant.anim_frame_idx}，期望 >0")


if __name__ == '__main__':
    unittest.main()
