"""任务系统数据模型与配置定义

每日任务：5选3，00:00（本地时间）刷新，未完成不保留
每周任务：4选2，每周一00:00刷新
"""

import random
from datetime import datetime, timedelta
from enum import Enum


# ── 任务类型枚举 ──

class TaskType(Enum):
    LEVEL_CLEAR = 'level_clear'      # 通关挑战：通关任意关卡×N
    COIN_COLLECT = 'coin_collect'    # 金币收集：单局收集金币≥X
    STAR_RUSH = 'star_rush'          # 星级冲刺：累计获得X颗星
    ANT_USED = 'ant_used'            # 蚂蚁出击：使用≥N只不同蚂蚁出战
    WIN_STREAK = 'win_streak'        # 连胜挑战：连续通关X关


class WeeklyTaskType(Enum):
    WEEKLY_CLEAR = 'weekly_clear'    # 周常通关：累计通关X关
    WEEKLY_STARS = 'weekly_stars'    # 星级收集：累计获得X颗星
    WEEKLY_ANTS = 'weekly_ants'      # 全蚂蚁出击：使用≥X种不同蚂蚁
    WEEKLY_TERRAIN = 'weekly_terrain'  # 地形征服：通关≥X种不同地形关卡


# ── 每日任务池（5选3）──

DAILY_TASK_POOL = [
    {
        'id': 'D1',
        'type': TaskType.LEVEL_CLEAR,
        'desc': '通关任意关卡×3',
        'target': 3,
        'reward': 200,
    },
    {
        'id': 'D2',
        'type': TaskType.COIN_COLLECT,
        'desc': '单局收集金币≥500',
        'target': 500,
        'reward': 150,
    },
    {
        'id': 'D3',
        'type': TaskType.STAR_RUSH,
        'desc': '累计获得5颗星',
        'target': 5,
        'reward': 300,
    },
    {
        'id': 'D4',
        'type': TaskType.ANT_USED,
        'desc': '使用≥2只不同蚂蚁出战',
        'target': 2,
        'reward': 100,
    },
    {
        'id': 'D5',
        'type': TaskType.WIN_STREAK,
        'desc': '连续通关2关',
        'target': 2,
        'reward': 250,
    },
]

# ── 每周任务池（4选2）──

WEEKLY_TASK_POOL = [
    {
        'id': 'W1',
        'type': WeeklyTaskType.WEEKLY_CLEAR,
        'desc': '累计通关30关',
        'target': 30,
        'reward': 800,
    },
    {
        'id': 'W2',
        'type': WeeklyTaskType.WEEKLY_STARS,
        'desc': '累计获得50颗星',
        'target': 50,
        'reward': 600,
    },
    {
        'id': 'W3',
        'type': WeeklyTaskType.WEEKLY_ANTS,
        'desc': '使用≥10种不同蚂蚁',
        'target': 10,
        'reward': 500,
    },
    {
        'id': 'W4',
        'type': WeeklyTaskType.WEEKLY_TERRAIN,
        'desc': '通关≥5种不同地形关卡',
        'target': 5,
        'reward': 700,
    },
]

DAILY_PICK_COUNT = 3
WEEKLY_PICK_COUNT = 2


def make_task_entry(task_def):
    """从任务定义创建运行时任务条目"""
    return {
        'id': task_def['id'],
        'type': task_def['type'].value,
        'desc': task_def['desc'],
        'target': task_def['target'],
        'current': 0,
        'reward': task_def['reward'],
        'claimed': False,
    }


# ── CHE-11: 日期种子刷新机制 ──

def get_today_str():
    """返回今天日期字符串 YYYYMMDD"""
    return datetime.now().strftime('%Y%m%d')


def get_current_week_str():
    """返回当前周字符串 YYYY-Www（ISO周）"""
    now = datetime.now()
    year, week, _ = now.isocalendar()
    return f'{year}-W{week:02d}'


def refresh_daily_tasks(saved_date):
    """检查并刷新每日任务。返回 (tasks_list, date_str)。

    如果 saved_date 与今天不同，从任务池随机抽取 DAILY_PICK_COUNT 个任务。
    """
    today = get_today_str()
    if saved_date == today:
        return None, today

    rng = random.Random(int(today))
    indices = rng.sample(range(len(DAILY_TASK_POOL)), DAILY_PICK_COUNT)
    tasks = [make_task_entry(DAILY_TASK_POOL[i]) for i in indices]
    return tasks, today


def refresh_weekly_tasks(saved_week):
    """检查并刷新每周任务。返回 (tasks_list, week_str)。

    如果 saved_week 与当前周不同，从任务池随机抽取 WEEKLY_PICK_COUNT 个任务。
    """
    current_week = get_current_week_str()
    if saved_week == current_week:
        return None, current_week

    rng = random.Random(int(current_week.replace('-', '').replace('W', '')))
    indices = rng.sample(range(len(WEEKLY_TASK_POOL)), WEEKLY_PICK_COUNT)
    tasks = [make_task_entry(WEEKLY_TASK_POOL[i]) for i in indices]
    return tasks, current_week


# ── CHE-12: 任务进度追踪 ──

def update_task_progress(task_type_value, amount, tasks):
    """更新指定类型任务的进度。

    Args:
        task_type_value: TaskType/WeeklyTaskType 的 .value 字符串
        amount: 本次增量
        tasks: 当前任务列表

    Returns:
        是否有任务进度发生变化
    """
    changed = False
    for task in tasks:
        if task['type'] == task_type_value and not task['claimed']:
            task['current'] = min(task['target'], task['current'] + amount)
            changed = True
    return changed


def check_task_progress(tasks, level_data=None, sm=None, team=None,
                        level_coins=0, stars_earned=0, level_id=None,
                        win_streak=0, terrain=None, ants_used=None):
    """根据游戏结算数据检查并更新所有任务进度。

    由关卡结算时调用，批量更新，不在每帧追踪。
    """
    changed = False

    for task in tasks:
        if task['claimed']:
            continue

        t = task['type']

        if t == TaskType.LEVEL_CLEAR.value:
            if level_id is not None and level_coins > 0:
                # 通关即 +1
                task['current'] = min(task['target'], task['current'] + 1)
                changed = True

        elif t == TaskType.COIN_COLLECT.value:
            if level_coins > 0:
                # 单局金币累加（取最高）
                if level_coins >= task['target']:
                    task['current'] = task['target']
                    changed = True

        elif t == TaskType.STAR_RUSH.value:
            if stars_earned > 0:
                task['current'] = min(task['target'], task['current'] + stars_earned)
                changed = True

        elif t == TaskType.ANT_USED.value:
            if ants_used is not None:
                unique_count = len(set(ants_used))
                task['current'] = min(task['target'], unique_count)
                changed = True

        elif t == TaskType.WIN_STREAK.value:
            if win_streak > 0:
                task['current'] = min(task['target'], win_streak)
                changed = True

        elif t == WeeklyTaskType.WEEKLY_CLEAR.value:
            if level_id is not None and level_coins > 0:
                task['current'] = min(task['target'], task['current'] + 1)
                changed = True

        elif t == WeeklyTaskType.WEEKLY_STARS.value:
            if stars_earned > 0:
                task['current'] = min(task['target'], task['current'] + stars_earned)
                changed = True

        elif t == WeeklyTaskType.WEEKLY_ANTS.value:
            if ants_used is not None:
                unique_count = len(set(ants_used))
                task['current'] = min(task['target'], unique_count)
                changed = True

        elif t == WeeklyTaskType.WEEKLY_TERRAIN.value:
            if terrain is not None and level_coins > 0:
                # 通关才计入地形（用列表存储，保证 JSON 可序列化）
                terrains_seen = set(task.get('_terrains_seen', []))
                if terrain not in terrains_seen:
                    terrains_seen.add(terrain)
                    task['_terrains_seen'] = list(terrains_seen)
                    task['current'] = min(task['target'], task['current'] + 1)
                    changed = True

    return changed
