"""游戏配置常量"""

# 屏幕设置
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 700
FPS = 60

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
SWEET_SPAWN_BLINK_DURATION = 1.0       # 甜点出现闪烁持续时间（秒）
SWEET_SPAWN_BLINK_LOOPS = 3            # 闪烁循环次数
SWEET_SPAWN_BLINK_MAX_ON_SCREEN = 5    # 同时闪烁的最大甜点数

# 血条
HP_BAR_W = 40
HP_BAR_H = 5
HP_BAR_BG = (50, 50, 50)
HP_BAR_FILL = (80, 200, 80)
HP_BAR_RADIUS = 2
HP_BAR_GAP = 4

# 蚂蚁
ANT_SIZE = 32
STUN_DURATION = 0.5        # 秒（僵直时间）
STUN_SPEED_MULT = 0.0      # 僵直时速度倍率

# 世界地图尺寸（方案C：4200×850）
WORLD_WIDTH = 4200
WORLD_HEIGHT = 850

# 相机边界（世界坐标最大值 = 世界尺寸 - 屏幕尺寸）
CAMERA_MAX_X = max(0, WORLD_WIDTH - SCREEN_WIDTH)   # 3000
CAMERA_MAX_Y = max(0, WORLD_HEIGHT - SCREEN_HEIGHT)  # 150

# 区域配置（左×1.5/中×1.0/右×2.0）
ZONE_CONFIG = {
    'left':   {'x_range': (0, 1399),    'y_range': (0, 850), 'multiplier': 1.5, 'refresh_interval': 8, 'spawn_prob': 0.30},
    'center': {'x_range': (1400, 2799), 'y_range': (0, 850), 'multiplier': 1.0, 'refresh_interval': 5, 'spawn_prob': 0.40},
    'right':  {'x_range': (2800, 4199), 'y_range': (0, 850), 'multiplier': 2.0, 'refresh_interval': 12, 'spawn_prob': 0.30},
}

ZONE_THEME_COLORS = {
    'left':   (255, 200, 220),
    'center': (180, 230, 160),
    'right':  (255, 220, 120),
}

# 发光效果
GLOW_SIZE = 120
GLOW_ALPHA_BASE = 40
GLOW_ALPHA_RANGE = 30
GLOW_FREQ = 0.5
GLOW_COLOR_PLAYER = (70, 130, 220)
GLOW_COLOR_AI = (220, 80, 70)

# 小地图
MINIMAP_W = 250
MINIMAP_H = 80
MINIMAP_DOT_RADIUS_SWEET = 3
MINIMAP_BLINK_FREQ = 1.5
MINIMAP_BLINK_ALPHA_MIN = 100
MINIMAP_BLINK_ALPHA_MAX = 255

# 昆虫系统（第一期：瓢虫+毛毛虫）
CREATURE_SIZE_BASE = 45                # 昆虫基础尺寸
CREATURE_SPAWN_BLINK_DURATION = 0.8   # 昆虫出现闪烁持续时间（秒）
CREATURE_SPAWN_BLINK_LOOPS = 2        # 闪烁循环次数
CREATURE_SPAWN_BLINK_MAX_ON_SCREEN = 4  # 同时闪烁的最大昆虫数
CREATURE_DEATH_ANIM_DURATION = 0.6    # 昆虫死亡动画持续时间（秒）
CREATURE_MAX_PER_ZONE = 3             # 同一区域同时存在的昆虫数量上限
CREATURE_SPEED_VARIATION = 0.2        # 昆虫移动速度随机浮动范围（±20%）

# 昆虫颜色映射（回退绘制用）
CREATURE_COLORS = {
    'ladybug': (220, 50, 50),      # 红色瓢虫
    'caterpillar': (80, 180, 80),   # 绿色毛毛虫
    'cricket': (180, 150, 50),      # 黄褐色蟋蟀
    'beetle': (80, 50, 20),         # 深棕色甲虫
    'dragonfly': (80, 180, 220),    # 青色蜻蜓
    'bee': (220, 180, 40),          # 黄色蜜蜂
}

# 相机滚动速度
SCROLL_SPEED = 10
