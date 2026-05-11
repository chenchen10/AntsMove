"""签到系统数据模型与奖励配置

7天签到周期：
  - 每天可签到1次，签到后获得当日奖励
  - 连续签到不中断，断签不重置周期（已签到的天数保留）
  - 第7天为大奖日，奖励倍率提升
  - 完成7天周期后自动进入下一个周期，cycles_completed +1

数据结构说明（save_manager.py checkin字段）：
  current_day:       当前周期已签到天数（1-7），周期完成后重置为0
  last_checkin_date: 上次签到日期字符串 YYYY-MM-DD（None表示从未签到）
  total_checkins:    累计签到总次数（跨周期累计）
  streak:            当前连续签到天数（断签归0）
  cycles_completed:  已完成的完整7天周期数

签到状态枚举：
  NOT_CHECKED_IN:    今日未签到
  CHECKED_IN:        今日已签到
  FIRST_TIME:        首次签到（从未签到过）

日期判断逻辑：
  - 本地时间 YYYY-MM-DD 格式比较
  - last_checkin_date 为 None → 首次签到
  - last_checkin_date == 今天 → 已签到，不可重复签
  - last_checkin_date != 今天 → 可签到

断签处理规则：
  - 断签不重置 current_day（已签到的天数保留）
  - 断签将 streak 归 0
  - 断签不影响 cycles_completed
  - 玩家可随时回来继续签到，从当前进度继续

周期循环规则：
  - 当 current_day == 7 且完成签到后，自动触发周期结算
  - cycles_completed += 1，current_day 重置为 0
  - 下一次签到进入新周期的第1天

奖励公式：
  actual_reward = base_reward × (1 + streak_bonus) × cycle_multiplier

  streak_bonus = min(streak - 1, 5) × 0.10，上限 50%
  cycle_multiplier = min(cycles_completed, 4) × 0.20 + 1.0，上限 1.8
"""

from enum import Enum
from datetime import datetime, timedelta


# ── 签到状态枚举 ──

class CheckinStatus(Enum):
    """签到状态"""
    NOT_CHECKED_IN = 'not_checked_in'   # 今日未签到
    CHECKED_IN = 'checked_in'           # 今日已签到
    FIRST_TIME = 'first_time'           # 首次签到（从未签到过）


# ── 奖励类型枚举 ──

class RewardType(Enum):
    """奖励类型"""
    COINS = 'coins'         # 金币
    SPECIAL = 'special'     # 特殊道具（预留）


# ── 签到数值参数配置 ──

# 7天基础奖励（第1周期，无加成）
CHECKIN_BASE_REWARDS = [100, 120, 150, 200, 280, 350, 1000]

# 连续签到加成参数
STREAK_BONUS_PER_DAY = 0.10   # 每天+10%
STREAK_BONUS_CAP = 0.50       # 上限50%（连续5天封顶）

# 周期递增参数
CYCLE_BONUS_PER_CYCLE = 0.20  # 每周期+20%
CYCLE_BONUS_CAP = 0.80        # 上限80%（即最大倍率1.8）

# 7天周期
CYCLE_LENGTH = 7
MAX_CYCLE_MULTIPLIER = 1.8


# ── 奖励计算公式 ──

def calc_actual_reward(base_reward, streak, cycles_completed):
    """计算实际签到奖励

    公式：actual_reward = base_reward × (1 + streak_bonus) × cycle_multiplier

    Args:
        base_reward:      当天基础奖励（1-7天对应不同值）
        streak:           当前连续签到天数
        cycles_completed: 已完成的周期数

    Returns:
        int: 实际发放的金币数量（向下取整）
    """
    streak_bonus = min(streak - 1, 5) * STREAK_BONUS_PER_DAY
    streak_bonus = min(streak_bonus, STREAK_BONUS_CAP)

    cycle_multiplier = min(cycles_completed, 4) * CYCLE_BONUS_PER_CYCLE + 1.0
    cycle_multiplier = min(cycle_multiplier, MAX_CYCLE_MULTIPLIER)

    return int(base_reward * (1 + streak_bonus) * cycle_multiplier)


# ── 7天签到奖励配置表 ──

CHECKIN_REWARDS = [
    {
        'day': 1,
        'reward_type': RewardType.COINS,
        'amount': CHECKIN_BASE_REWARDS[0],
        'label': f'金币×{CHECKIN_BASE_REWARDS[0]}',
        'is_big_reward': False,
    },
    {
        'day': 2,
        'reward_type': RewardType.COINS,
        'amount': CHECKIN_BASE_REWARDS[1],
        'label': f'金币×{CHECKIN_BASE_REWARDS[1]}',
        'is_big_reward': False,
    },
    {
        'day': 3,
        'reward_type': RewardType.COINS,
        'amount': CHECKIN_BASE_REWARDS[2],
        'label': f'金币×{CHECKIN_BASE_REWARDS[2]}',
        'is_big_reward': False,
    },
    {
        'day': 4,
        'reward_type': RewardType.COINS,
        'amount': CHECKIN_BASE_REWARDS[3],
        'label': f'金币×{CHECKIN_BASE_REWARDS[3]}',
        'is_big_reward': False,
    },
    {
        'day': 5,
        'reward_type': RewardType.COINS,
        'amount': CHECKIN_BASE_REWARDS[4],
        'label': f'金币×{CHECKIN_BASE_REWARDS[4]}',
        'is_big_reward': False,
    },
    {
        'day': 6,
        'reward_type': RewardType.COINS,
        'amount': CHECKIN_BASE_REWARDS[5],
        'label': f'金币×{CHECKIN_BASE_REWARDS[5]}',
        'is_big_reward': False,
    },
    {
        'day': 7,
        'reward_type': RewardType.COINS,
        'amount': CHECKIN_BASE_REWARDS[6],
        'label': f'金币×{CHECKIN_BASE_REWARDS[6]}',
        'is_big_reward': True,
    },
]

# ── 索引表 ──

REWARD_BY_DAY = {r['day']: r for r in CHECKIN_REWARDS}

# 7天周期基础总奖励
TOTAL_CYCLE_REWARD = sum(CHECKIN_BASE_REWARDS)


# ── 签到状态判断 ──

def get_checkin_status(checkin_data, today_str=None):
    """判断当前签到状态

    Args:
        checkin_data: 存档中的 checkin 字段
        today_str:    今天日期字符串 YYYY-MM-DD（默认自动获取）

    Returns:
        CheckinStatus: 当前签到状态
    """
    if today_str is None:
        today_str = get_today_str()

    last_date = checkin_data.get('last_checkin_date')

    if last_date is None:
        return CheckinStatus.FIRST_TIME

    if last_date == today_str:
        return CheckinStatus.CHECKED_IN

    return CheckinStatus.NOT_CHECKED_IN


def can_checkin_today(checkin_data, today_str=None):
    """判断今天是否可以签到

    Returns:
        bool
    """
    status = get_checkin_status(checkin_data, today_str)
    return status in (CheckinStatus.NOT_CHECKED_IN, CheckinStatus.FIRST_TIME)


def get_today_str():
    """返回今天日期字符串 YYYY-MM-DD"""
    return datetime.now().strftime('%Y-%m-%d')


# ── 签到执行逻辑 ──

def perform_checkin(checkin_data, today_str=None):
    """执行签到操作

    逻辑：
    1. 检查是否可以签到
    2. 更新 current_day（+1）
    3. 更新 last_checkin_date
    4. 更新 total_checkins（+1）
    5. 检查连续签到（streak）
    6. 检查是否完成周期（current_day == 7 → 重置）
    7. 计算实际奖励（含连续加成 + 周期倍率）
    7. 返回签到结果（获得的奖励）

    Args:
        checkin_data: 存档中的 checkin 字段（会被原地修改）
        today_str:    今天日期字符串

    Returns:
        dict: {
            'success': bool,
            'reward': dict or None,    # 奖励信息（含实际奖励金额）
            'day': int,                # 签到的天数（1-7）
            'cycle_completed': bool,   # 是否完成了7天周期
            'new_cycle': bool,         # 是否进入了新周期
        }
    """
    if today_str is None:
        today_str = get_today_str()

    # 检查是否可以签到
    if not can_checkin_today(checkin_data, today_str):
        return {
            'success': False,
            'reward': None,
            'day': checkin_data.get('current_day', 0),
            'cycle_completed': False,
            'new_cycle': False,
        }

    # 检查连续签到
    last_date = checkin_data.get('last_checkin_date')
    yesterday_str = (datetime.strptime(today_str, '%Y-%m-%d') - timedelta(days=1)).strftime('%Y-%m-%d')

    if last_date is None:
        # 首次签到，streak 从1开始
        checkin_data['streak'] = 1
    elif last_date == yesterday_str:
        # 昨天签到了，连续 +1
        checkin_data['streak'] = checkin_data.get('streak', 0) + 1
    else:
        # 断签，streak 归1（今天重新开始）
        checkin_data['streak'] = 1

    # 更新 current_day
    current_day = checkin_data.get('current_day', 0)
    if current_day >= 7:
        current_day = 0
    checkin_data['current_day'] = current_day + 1
    day = checkin_data['current_day']

    # 更新基础数据
    checkin_data['last_checkin_date'] = today_str
    checkin_data['total_checkins'] = checkin_data.get('total_checkins', 0) + 1

    # 获取基础奖励
    base_reward = CHECKIN_BASE_REWARDS[(day - 1) % CYCLE_LENGTH]

    # 计算实际奖励（含连续加成 + 周期倍率）
    actual_reward = calc_actual_reward(
        base_reward,
        checkin_data.get('streak', 1),
        checkin_data.get('cycles_completed', 0),
    )

    # 构建奖励信息
    reward = {
        'day': day,
        'base_reward': base_reward,
        'actual_reward': actual_reward,
        'amount': actual_reward,  # 向后兼容：amount = actual_reward
        'reward_type': RewardType.COINS,
        'label': f'金币×{actual_reward}',
        'is_big_reward': (day == CYCLE_LENGTH),
    }

    # 检查周期完成
    cycle_completed = False
    new_cycle = False
    if day == CYCLE_LENGTH:
        checkin_data['cycles_completed'] = checkin_data.get('cycles_completed', 0) + 1
        cycle_completed = True
        # 预重置 current_day（下次签到时生效）
        checkin_data['current_day'] = 0
        new_cycle = True

    return {
        'success': True,
        'reward': reward,
        'day': day,
        'cycle_completed': cycle_completed,
        'new_cycle': new_cycle,
    }


# ── UI消费格式 ──

def get_checkin_ui_data(checkin_data, today_str=None):
    """获取签到面板UI需要的数据

    Returns:
        dict: {
            'status': CheckinStatus,
            'current_day': int,        # 当前周期已签到天数（0-7）
            'streak': int,             # 连续签到天数
            'total_checkins': int,     # 累计签到次数
            'cycles_completed': int,   # 完成周期数
            'can_checkin': bool,       # 今天是否可签到
            'rewards': list,           # 7天奖励配置（含已签到状态和实际奖励）
            'today_reward': dict,      # 今日可获得的奖励
            'cycle_total': int,        # 单周期基础总奖励
        }
    """
    if today_str is None:
        today_str = get_today_str()

    status = get_checkin_status(checkin_data, today_str)
    current_day = checkin_data.get('current_day', 0)
    streak = checkin_data.get('streak', 0)
    cycles_completed = checkin_data.get('cycles_completed', 0)

    # 如果周期刚完成（current_day 被重置为0），显示为7
    display_day = CYCLE_LENGTH if current_day == 0 and cycles_completed > 0 else current_day

    # 构建7天奖励列表，标注已签到状态和实际奖励金额
    rewards_with_status = []
    for day_num, base_reward in enumerate(CHECKIN_BASE_REWARDS, start=1):
        actual = calc_actual_reward(base_reward, streak, cycles_completed)
        rewards_with_status.append({
            'day': day_num,
            'reward_type': RewardType.COINS,
            'amount': actual,
            'base_reward': base_reward,
            'label': f'金币×{actual}',
            'is_big_reward': (day_num == CYCLE_LENGTH),
            'checked': day_num <= current_day if current_day > 0 else False,
        })

    # 今日奖励（下一天的基础奖励 + 当前加成）
    next_day = current_day + 1 if current_day < CYCLE_LENGTH else 1
    next_base = CHECKIN_BASE_REWARDS[(next_day - 1) % CYCLE_LENGTH]
    today_actual = calc_actual_reward(next_base, streak, cycles_completed)
    today_reward = {
        'day': next_day,
        'base_reward': next_base,
        'actual_reward': today_actual,
        'reward_type': RewardType.COINS,
        'label': f'金币×{today_actual}',
        'is_big_reward': (next_day == CYCLE_LENGTH),
    }

    return {
        'status': status,
        'current_day': current_day,
        'streak': streak,
        'total_checkins': checkin_data.get('total_checkins', 0),
        'cycles_completed': cycles_completed,
        'can_checkin': can_checkin_today(checkin_data, today_str),
        'rewards': rewards_with_status,
        'today_reward': today_reward,
        'cycle_total': TOTAL_CYCLE_REWARD,
    }


# ── 数值推导说明（供数值策划参考）──

# 签到奖励梯度设计逻辑：
#
# 1. 基础梯度：100 → 120 → 150 → 200 → 280 → 350 → 1000
#    - 前6天缓→急递增（+20%~+40%），第7天质变（×3.6倍）
#    - 第7天大奖是Day1的10倍，激励玩家坚持签满7天
#
# 2. 单周期全勤收益：2200金币（基础）
#    - 日均314G，约为每日任务均值（600G）的52%
#    - 签到定位为被动收入来源，不喧宾夺主
#
# 3. 连续签到加成：streak_bonus = min(streak-1, 5) × 10%，上限50%
#    - 全勤7天实际总奖励：3089G（较基础值+40.4%）
#    - 断签代价：失去连续加成（约40%收益差），但不重置周期
#
# 4. 周期递增：每完成一个周期，下一周期基础奖励 ×(1 + cycles_completed × 20%)，上限100%
#    - 第5周期起倍率封顶 ×1.8
#    - 第5周期Day7最高奖励 = 1000 × 1.8 × 1.5 = 2700G
#
# 5. 多周期收益曲线（全勤）：
#    - 第1周期：3,089G
#    - 第2周期：3,708G
#    - 第3周期：4,326G
#    - 第4周期：4,945G
#    - 第5周期：5,562G（封顶）
#
# 6. 经济平衡验证：
#    - 签到日均 vs 每日任务日均：314G vs 600G（52%）✅
#    - 全勤5周期累计 vs 全蚂蚁成本：21,632G vs 103,800G（20.8%）✅
#    - Day7最高奖励(满倍率)：2,700G ≈ 高级成就奖励级别 ✅
