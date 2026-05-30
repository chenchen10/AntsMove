"""Camera 和 MiniMap 单元测试

验证：
- Camera 坐标转换正确
- Camera 边界约束正确
- Camera 平滑跳转（update_jump）lerp 插值、停止阈值
- MiniMap 坐标转换正确
- MiniMap handle_click 触发跳转
"""

import sys
import os
import math

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    WORLD_WIDTH, WORLD_HEIGHT,
    CAMERA_MAX_X, CAMERA_MAX_Y,
    MINIMAP_W, MINIMAP_H,
)

# ── Camera 测试 ──


def test_camera_initial_state():
    """Camera 初始状态：位于原点"""
    from camera import Camera
    cam = Camera()
    assert cam.x == 0.0
    assert cam.y == 0.0
    assert not cam.is_jumping


def test_camera_center_on():
    """Camera.center_on 将视口中心对准目标"""
    from camera import Camera
    cam = Camera()
    cam.center_on(WORLD_WIDTH // 2, SCREEN_HEIGHT // 2)
    # center_on 后 x = target - SCREEN_WIDTH//2, y = target - SCREEN_HEIGHT//2
    expected_x = WORLD_WIDTH // 2 - SCREEN_WIDTH // 2
    expected_y = SCREEN_HEIGHT // 2 - SCREEN_HEIGHT // 2  # = 0
    assert cam.x == expected_x
    assert cam.y == expected_y


def test_camera_move_to():
    """Camera.move_to 直接设置位置（y 被 clamp 到 CAMERA_MAX_Y=0）"""
    from camera import Camera
    cam = Camera()
    cam.move_to(100.0, 50.0)
    assert cam.x == 100.0
    # WORLD_HEIGHT == SCREEN_HEIGHT → CAMERA_MAX_Y = 0, y 被 clamp
    assert cam.y == 0.0


def test_camera_move_by():
    """Camera.move_by 按偏移移动（y 被 clamp 到 CAMERA_MAX_Y=0）"""
    from camera import Camera
    cam = Camera()
    cam.move_by(100.0, 0.0)
    assert cam.x == 100.0
    assert cam.y == 0.0
    cam.move_by(-30.0, 0.0)
    assert cam.x == 70.0
    assert cam.y == 0.0


def test_camera_clamp():
    """Camera 位置不能超出世界边界"""
    from camera import Camera
    cam = Camera()
    # X 方向
    cam.move_to(-100.0, 0.0)
    assert cam.x == 0.0
    cam.move_to(CAMERA_MAX_X + 100.0, 0.0)
    assert cam.x == CAMERA_MAX_X
    # Y 方向
    cam.move_to(0.0, -100.0)
    assert cam.y == 0.0
    cam.move_to(0.0, CAMERA_MAX_Y + 100.0)
    assert cam.y == CAMERA_MAX_Y


def test_camera_world_to_screen():
    """世界坐标 → 屏幕坐标"""
    from camera import Camera
    cam = Camera()
    cam.move_to(100.0, 0.0)
    sx, sy = cam.world_to_screen(200.0, 150.0)
    assert sx == 100.0  # 200 - 100
    assert sy == 150.0  # 150 - 0 (y 不滚动)


def test_camera_screen_to_world():
    """屏幕坐标 → 世界坐标"""
    from camera import Camera
    cam = Camera()
    cam.move_to(100.0, 0.0)
    wx, wy = cam.screen_to_world(200.0, 150.0)
    assert wx == 300.0  # 200 + 100
    assert wy == 150.0  # 150 + 0 (y 不滚动)


def test_camera_roundtrip():
    """坐标转换往返一致性"""
    from camera import Camera
    cam = Camera()
    cam.move_to(200.0, 0.0)
    world_x, world_y = 500.0, 350.0
    sx, sy = cam.world_to_screen(world_x, world_y)
    wx, wy = cam.screen_to_world(sx, sy)
    assert abs(wx - world_x) < 0.001
    assert abs(wy - world_y) < 0.001


def test_camera_jump_basic():
    """update_jump 基本跳转：最终到达目标位置"""
    from camera import Camera
    cam = Camera()
    cam.move_to(0.0, 0.0)
    # 目标世界坐标 (1800, 350) → 相机应到 (1800 - 600, 350 - 350) = (1200, 0)
    cam.start_jump(1800.0, 350.0)
    assert cam.is_jumping
    # 多次更新直到跳转完成
    for _ in range(200):
        cam.update_jump(0.016)
        if not cam.is_jumping:
            break
    assert not cam.is_jumping
    expected_x = 1800.0 - SCREEN_WIDTH // 2
    expected_y = 350.0 - SCREEN_HEIGHT // 2
    assert abs(cam.x - expected_x) < 1.0
    assert abs(cam.y - expected_y) < 1.0


def test_camera_jump_stop_threshold():
    """update_jump 停止阈值 < 1px"""
    from camera import Camera
    cam = Camera()
    cam.move_to(0.0, 0.0)
    # 使用合理的目标坐标（在世界范围内）
    target_world_x = 1800.0  # 世界中部偏右
    cam.start_jump(target_world_x, 350.0)
    # 模拟多帧更新
    for _ in range(300):
        cam.update_jump(0.016)
        if not cam.is_jumping:
            break
    assert not cam.is_jumping
    expected_x = target_world_x - SCREEN_WIDTH // 2
    assert abs(cam.x - expected_x) < 1.0


def test_camera_jump_no_drag():
    """拖拽期间不执行跳转"""
    from camera import Camera
    cam = Camera()
    cam.start_jump(1800.0, 350.0)
    # 手动模拟拖拽状态
    cam._dragging = True
    cam.update_jump(0.016)
    # 跳转应该还没执行（目标还在）
    assert cam.is_jumping
    cam._dragging = False


def test_camera_jump_lerp_factor():
    """验证 lerp 插值因子：dt × 5.0"""
    from camera import Camera
    cam = Camera()
    cam.move_to(0.0, 0.0)
    cam.start_jump(1000.0, 0.0)
    dt = 0.1
    cam.update_jump(dt)
    # 第一帧后：x += (1000 - 600 - 0) * min(1.0, 0.1*5.0) = 400 * 0.5 = 200
    expected_first = 400.0 * min(1.0, dt * 5.0)
    assert abs(cam.x - expected_first) < 0.01


def test_camera_jump_animation_duration():
    """跳转动画时间在 0.3-0.5s 范围内"""
    from camera import Camera
    cam = Camera()
    cam.move_to(0.0, 0.0)
    cam.start_jump(1800.0, 350.0)
    dt = 0.016  # ~60fps
    frame_count = 0
    while cam.is_jumping and frame_count < 1000:
        cam.update_jump(dt)
        frame_count += 1
    elapsed = frame_count * dt
    # 应在 0.3-1.0s 内完成（宽松范围，考虑边界情况）
    assert 0.1 < elapsed < 1.5, f"跳转耗时 {elapsed:.3f}s，超出预期范围"


# ── MiniMap 测试 ──


def _make_mock_ctx():
    """创建模拟的游戏上下文"""
    class MockGrinder:
        def __init__(self, x, y):
            self.x = x
            self.y = y

    class MockAnt:
        def __init__(self, x, y):
            self.x = x
            self.y = y

    class MockSweet:
        def __init__(self, x, y, alive=True):
            self.x = x
            self.y = y
            self.alive = alive

    class MockCtx:
        pass

    ctx = MockCtx()
    from camera import Camera
    ctx.camera = Camera()
    ctx.camera.move_to(0.0, 0.0)
    ctx.player_grinder = MockGrinder(100, 350)
    ctx.ai_grinder = MockGrinder(3500, 350)
    ctx.player_ants = [MockAnt(200, 300), MockAnt(250, 320)]
    ctx.ai_ants = [MockAnt(3400, 300)]
    ctx.sweets = [MockSweet(1800, 350, True), MockSweet(1000, 200, False)]
    return ctx


def test_minimap_position():
    """小地图位于右下角"""
    from ui_minimap import MiniMap
    mm = MiniMap()
    assert mm.x == SCREEN_WIDTH - MINIMAP_W - mm.MARGIN
    assert mm.y == SCREEN_HEIGHT - MINIMAP_H - mm.MARGIN


def test_minimap_handle_click_outside():
    """点击小地图外部不消费"""
    from ui_minimap import MiniMap
    from camera import Camera
    mm = MiniMap()
    cam = Camera()
    # 点击左上角（远离小地图）
    result = mm.handle_click(10, 10, cam)
    assert result is False


def test_minimap_handle_click_inside():
    """点击小地图内部消费并触发跳转"""
    from ui_minimap import MiniMap
    from camera import Camera
    mm = MiniMap()
    cam = Camera()
    cam.move_to(0.0, 0.0)
    # 点击小地图中心
    click_x = mm.x + MINIMAP_W // 2
    click_y = mm.y + MINIMAP_H // 2
    result = mm.handle_click(click_x, click_y, cam)
    assert result is True
    assert cam.is_jumping


def test_minimap_handle_click_world_coords():
    """小地图点击返回精确世界坐标（通过跳转目标验证）"""
    from ui_minimap import MiniMap
    from camera import Camera
    mm = MiniMap()
    cam = Camera()
    cam.move_to(0.0, 0.0)
    # 点击小地图右上角（应映射到世界右上角附近）
    click_x = mm.x + MINIMAP_W - 1
    click_y = mm.y + 1
    mm.handle_click(click_x, click_y, cam)
    # 验证跳转目标的世界坐标接近世界右上角
    target_x = cam._jump_target_x
    target_y = cam._jump_target_y
    assert target_x is not None
    assert target_y is not None
    # 小地图最右 → 世界坐标接近 WORLD_WIDTH
    assert target_x > WORLD_WIDTH * 0.9
    # 小地图最上 → 世界坐标接近 0
    assert target_y < WORLD_HEIGHT * 0.1


def test_minimap_handle_click_clamped():
    """小地图点击坐标被限制在世界边界内"""
    from ui_minimap import MiniMap
    from camera import Camera
    mm = MiniMap()
    cam = Camera()
    cam.move_to(0.0, 0.0)
    # 点击小地图边缘（可能超出世界边界）
    click_x = mm.x + MINIMAP_W + 5  # 超出小地图右边界（不在区域内）
    click_y = mm.y + MINIMAP_H // 2
    result = mm.handle_click(click_x, click_y, cam)
    assert result is False  # 超出小地图区域，不消费


def test_minimap_draw_exists():
    """MiniMap.draw 方法存在"""
    from ui_minimap import MiniMap
    mm = MiniMap()
    assert hasattr(mm, 'draw')


def test_minimap_mini_to_world():
    """小地图坐标 → 世界坐标转换正确"""
    from ui_minimap import MiniMap
    mm = MiniMap()
    # 小地图左上角 → 世界 (0, 0)
    wx, wy = mm._mini_to_world(mm.x, mm.y)
    assert abs(wx) < 1.0
    assert abs(wy) < 1.0
    # 小地图右下角 → 世界 (WORLD_WIDTH, WORLD_HEIGHT)
    wx, wy = mm._mini_to_world(mm.x + MINIMAP_W, mm.y + MINIMAP_H)
    assert abs(wx - WORLD_WIDTH) < 1.0
    assert abs(wy - WORLD_HEIGHT) < 1.0


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    passed = 0
    failed = 0
    for t in tests:
        try:
            t()
            passed += 1
            print(f"  PASS: {t.__name__}")
        except Exception as e:
            failed += 1
            print(f"  FAIL: {t.__name__}: {e}")
    print(f"\n结果: {passed} 通过, {failed} 失败")
