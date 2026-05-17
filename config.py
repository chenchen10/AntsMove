"""游戏配置常量"""

# 屏幕设置
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 700
FPS = 60

# 世界尺寸（大于屏幕尺寸，支持相机滚动）
WORLD_WIDTH = 2400
WORLD_HEIGHT = 1400

# 颜色
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (180, 180, 180)
BLUE_ANT_COLOR = (70, 130, 220)
RED_ANT_COLOR = (220, 80, 70)
GRINDER_COLOR = (100, 100, 120)

# 统一UI配色
BG_COLOR = (255, 249, 230)           # #FFF9E6
TEXT_COLOR = (74, 56, 43)            # #4A382B
CARD_BG = (255, 252, 240)           # 卡片背景
CARD_BORDER = (210, 195, 170)       # 卡片边框
ACCENT_BLUE = (70, 130, 220)        # 强调蓝（我方）
ACCENT_RED = (220, 80, 70)          # 强调红（敌方）
ACCENT_GOLD = (218, 165, 32)        # 金色强调
BTN_HOVER = (90, 160, 210)          # 按钮悬停

# 甜点颜色映射
SWEET_COLORS = {
    'candy': (255, 150, 200),
    'cookie': (210, 160, 80),
    'cake': (255, 180, 220),
    'donut': (200, 120, 60),
    'cream_cup': (255, 200, 200),
    'chocolate': (100, 60, 30),
}

# 研磨机
GRINDER_SIZE = 60
GRINDER_X = SCREEN_WIDTH // 2
GRINDER_Y = SCREEN_HEIGHT - 50

# 甜点
SWEET_SIZE_BASE = 50

# 蚂蚁
ANT_SIZE = 40
STUN_DURATION = 0.5        # 秒（僵直时间）
STUN_SPEED_MULT = 0.0      # 僵直时速度倍率
