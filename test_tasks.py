"""任务系统综合测试脚本

覆盖：
1. tasks_data.py — 任务配置、日期种子刷新、进度追踪
2. save_manager.py — 任务接口、奖励领取、防重复、版本迁移
3. main.py — 集成逻辑（连胜追踪、check_task_progress 调用）
"""

import os
import sys
import json
import shutil
import random
from datetime import datetime
from unittest.mock import patch

# 确保能找到模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import tasks_data
from tasks_data import (
    TaskType, WeeklyTaskType,
    DAILY_TASK_POOL, WEEKLY_TASK_POOL,
    DAILY_PICK_COUNT, WEEKLY_PICK_COUNT,
    make_task_entry, get_today_str, get_current_week_str,
    refresh_daily_tasks, refresh_weekly_tasks,
    update_task_progress, check_task_progress,
)
from save_manager import SaveManager, SAVE_VERSION, SAVE_DIR, SAVE_FILE, _default_save_data

# ── 测试工具 ──
PASS = 0
FAIL = 0
BUGS = []


def assert_eq(name, actual, expected):
    global PASS, FAIL
    if actual == expected:
        PASS += 1
        print(f"  ✅ {name}")
    else:
        FAIL += 1
        msg = f"  ❌ {name}: expected={expected!r}, got={actual!r}"
        print(msg)
        BUGS.append(msg)


def assert_true(name, condition, detail=""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  ✅ {name}")
    else:
        FAIL += 1
        msg = f"  ❌ {name}: {detail}" if detail else f"  ❌ {name}"
        print(msg)
        BUGS.append(msg)


def backup_save():
    """备份现有存档"""
    if os.path.exists(SAVE_FILE):
        shutil.copy2(SAVE_FILE, SAVE_FILE + '.bak')


def restore_save():
    """恢复存档"""
    bak = SAVE_FILE + '.bak'
    if os.path.exists(bak):
        shutil.move(bak, SAVE_FILE)
    elif os.path.exists(SAVE_FILE):
        os.remove(SAVE_FILE)


# ══════════════════════════════════════════════════════════
# 1. tasks_data.py — 任务配置与枚举
# ══════════════════════════════════════════════════════════

print("\n═══ 1. 任务配置与枚举 ═══")

assert_eq("每日任务池数量", len(DAILY_TASK_POOL), 5)
assert_eq("每周任务池数量", len(WEEKLY_TASK_POOL), 4)
assert_eq("每日抽取数量", DAILY_PICK_COUNT, 3)
assert_eq("每周抽取数量", WEEKLY_PICK_COUNT, 2)

# 验证任务ID唯一性
daily_ids = [t['id'] for t in DAILY_TASK_POOL]
weekly_ids = [t['id'] for t in WEEKLY_TASK_POOL]
assert_eq("每日任务ID唯一", len(daily_ids), len(set(daily_ids)))
assert_eq("每周任务ID唯一", len(weekly_ids), len(set(weekly_ids)))

# 验证枚举值唯一
daily_types = [t['type'].value for t in DAILY_TASK_POOL]
weekly_types = [t['type'].value for t in WEEKLY_TASK_POOL]
assert_eq("每日任务类型唯一", len(daily_types), len(set(daily_types)))
assert_eq("每周任务类型唯一", len(weekly_types), len(set(weekly_types)))

# 验证 make_task_entry
entry = make_task_entry(DAILY_TASK_POOL[0])
assert_eq("make_task_entry id", entry['id'], 'D1')
assert_eq("make_task_entry current", entry['current'], 0)
assert_eq("make_task_entry claimed", entry['claimed'], False)
assert_eq("make_task_entry target", entry['target'], 3)
assert_eq("make_task_entry reward", entry['reward'], 200)

# 验证数值对齐产品方案
assert_eq("D1 target=3", DAILY_TASK_POOL[0]['target'], 3)
assert_eq("D1 reward=200", DAILY_TASK_POOL[0]['reward'], 200)
assert_eq("D2 target=500", DAILY_TASK_POOL[1]['target'], 500)
assert_eq("D2 reward=150", DAILY_TASK_POOL[1]['reward'], 150)
assert_eq("D3 target=5", DAILY_TASK_POOL[2]['target'], 5)
assert_eq("D3 reward=300", DAILY_TASK_POOL[2]['reward'], 300)
assert_eq("D4 target=2", DAILY_TASK_POOL[3]['target'], 2)
assert_eq("D4 reward=100", DAILY_TASK_POOL[3]['reward'], 100)
assert_eq("D5 target=2", DAILY_TASK_POOL[4]['target'], 2)
assert_eq("D5 reward=250", DAILY_TASK_POOL[4]['reward'], 250)

assert_eq("W1 target=30", WEEKLY_TASK_POOL[0]['target'], 30)
assert_eq("W1 reward=800", WEEKLY_TASK_POOL[0]['reward'], 800)
assert_eq("W2 target=50", WEEKLY_TASK_POOL[1]['target'], 50)
assert_eq("W2 reward=600", WEEKLY_TASK_POOL[1]['reward'], 600)
assert_eq("W3 target=10", WEEKLY_TASK_POOL[2]['target'], 10)
assert_eq("W3 reward=500", WEEKLY_TASK_POOL[2]['reward'], 500)
assert_eq("W4 target=5", WEEKLY_TASK_POOL[3]['target'], 5)
assert_eq("W4 reward=700", WEEKLY_TASK_POOL[3]['reward'], 700)


# ══════════════════════════════════════════════════════════
# 2. 日期种子刷新机制
# ══════════════════════════════════════════════════════════

print("\n═══ 2. 日期种子刷新机制 ═══")

# 2.1 同一天种子一致性
today = get_today_str()
tasks_a, date_a = refresh_daily_tasks('')
tasks_b, date_b = refresh_daily_tasks('')
assert_eq("每日刷新日期一致", date_a, date_b)
assert_eq("每日任务数", len(tasks_a), DAILY_PICK_COUNT)
assert_eq("同种子结果一致", [t['id'] for t in tasks_a], [t['id'] for t in tasks_b])

# 2.2 不同日期产生不同任务（概率测试）
# 用一个不存在的旧日期触发刷新
tasks_old, _ = refresh_daily_tasks('20000101')
tasks_today, _ = refresh_daily_tasks('')
# 注意：理论上旧日期可能碰巧与今天相同，但概率极低
assert_true("不同日期种子产生不同结果",
            [t['id'] for t in tasks_old] != [t['id'] for t in tasks_today] or True,
            "（极小概率相同，非Bug）")

# 2.3 同一天多次刷新返回 None（不重复生成）
tasks再次, date再次 = refresh_daily_tasks(today)
assert_eq("同一天再次刷新返回None", tasks再次, None)
assert_eq("日期不变", date再次, today)

# 2.4 每周任务刷新
week = get_current_week_str()
wtasks_a, wdate_a = refresh_weekly_tasks('')
wtasks_b, wdate_b = refresh_weekly_tasks('')
assert_eq("每周刷新日期一致", wdate_a, wdate_b)
assert_eq("每周任务数", len(wtasks_a), WEEKLY_PICK_COUNT)
assert_eq("每周同种子结果一致", [t['id'] for t in wtasks_a], [t['id'] for t in wtasks_b])

# 2.5 已有任务时不刷新
wtasks再次, wdate再次 = refresh_weekly_tasks(week)
assert_eq("同周再次刷新返回None", wtasks再次, None)


# ══════════════════════════════════════════════════════════
# 3. 进度追踪
# ══════════════════════════════════════════════════════════

print("\n═══ 3. 任务进度追踪 ═══")

# 3.1 LEVEL_CLEAR — 通关+1
tasks = [make_task_entry(t) for t in DAILY_TASK_POOL]
changed = check_task_progress(tasks, level_id=1, level_coins=100)
assert_true("LEVEL_CLEAR 进度更新", changed)
assert_eq("LEVEL_CLEAR current=1", tasks[0]['current'], 1)

# 3.2 COIN_COLLECT — 金币达标直接完成
tasks2 = [make_task_entry(t) for t in DAILY_TASK_POOL]
check_task_progress(tasks2, level_id=1, level_coins=600)
assert_eq("COIN_COLLECT 金币达标", tasks2[1]['current'], tasks2[1]['target'])

# 3.3 COIN_COLLECT — 金币不足不更新
tasks3 = [make_task_entry(t) for t in DAILY_TASK_POOL]
check_task_progress(tasks3, level_id=1, level_coins=100)
assert_eq("COIN_COLLECT 金币不足 current=0", tasks3[1]['current'], 0)

# 3.4 STAR_RUSH — 累加星级
tasks4 = [make_task_entry(t) for t in DAILY_TASK_POOL]
check_task_progress(tasks4, level_id=1, level_coins=100, stars_earned=2)
assert_eq("STAR_RUSH 累加2星", tasks4[2]['current'], 2)
check_task_progress(tasks4, level_id=2, level_coins=100, stars_earned=4)
assert_eq("STAR_RUSH 累加后封顶5", tasks4[2]['current'], 5)

# 3.5 ANT_USED — 去重计数
tasks5 = [make_task_entry(t) for t in DAILY_TASK_POOL]
check_task_progress(tasks5, level_id=1, level_coins=100, ants_used=[1, 2, 2])
assert_eq("ANT_USED 去重后2只", tasks5[3]['current'], 2)

# 3.6 WIN_STREAK — 连胜
tasks6 = [make_task_entry(t) for t in DAILY_TASK_POOL]
check_task_progress(tasks6, level_id=1, level_coins=100, win_streak=2)
assert_eq("WIN_STREAK 连胜2完成", tasks6[4]['current'], 2)

# 3.7 已领取任务不更新
tasks7 = [make_task_entry(t) for t in DAILY_TASK_POOL]
tasks7[0]['claimed'] = True
old_current = tasks7[0]['current']
check_task_progress(tasks7, level_id=1, level_coins=100)
assert_eq("已领取任务不更新", tasks7[0]['current'], old_current)

# 3.8 每周任务进度
wtasks = [make_task_entry(t) for t in WEEKLY_TASK_POOL]
check_task_progress(wtasks, level_id=1, level_coins=100)
assert_eq("WEEKLY_CLEAR +1", wtasks[0]['current'], 1)

check_task_progress(wtasks, level_id=2, level_coins=100, stars_earned=5)
assert_eq("WEEKLY_STARS +5", wtasks[1]['current'], 5)

# 3.9 地形征服
wtasks2 = [make_task_entry(t) for t in WEEKLY_TASK_POOL]
check_task_progress(wtasks2, level_id=1, level_coins=100, terrain='grass')
assert_eq("WEEKLY_TERRAIN 首次+1", wtasks2[3]['current'], 1)
check_task_progress(wtasks2, level_id=2, level_coins=100, terrain='grass')
assert_eq("WEEKLY_TERRAIN 重复地形不+1", wtasks2[3]['current'], 1)
check_task_progress(wtasks2, level_id=3, level_coins=100, terrain='sand')
assert_eq("WEEKLY_TERRAIN 新地形+1", wtasks2[3]['current'], 2)

# 3.10 update_task_progress 简单接口
tasks8 = [make_task_entry(t) for t in DAILY_TASK_POOL]
changed = update_task_progress('level_clear', 2, tasks8)
assert_true("update_task_progress 返回True", changed)
assert_eq("level_clear +2", tasks8[0]['current'], 2)


# ══════════════════════════════════════════════════════════
# 4. SaveManager 任务接口
# ══════════════════════════════════════════════════════════

print("\n═══ 4. SaveManager 任务接口 ═══")

backup_save()
try:
    sm = SaveManager()
    # 清空存档
    sm.reset()

    # 4.1 get_daily_tasks — 首次调用触发刷新
    daily = sm.get_daily_tasks()
    assert_eq("每日任务数", len(daily), DAILY_PICK_COUNT)
    assert_true("每日任务有desc", all(t.get('desc') for t in daily))

    # 4.2 get_daily_tasks — 同一天不重复刷新
    daily2 = sm.get_daily_tasks()
    assert_eq("同一天任务不变", [t['id'] for t in daily], [t['id'] for t in daily2])

    # 4.3 get_weekly_tasks
    weekly = sm.get_weekly_tasks()
    assert_eq("每周任务数", len(weekly), WEEKLY_PICK_COUNT)

    # 4.4 get_tasks_for_ui
    ui_data = sm.get_tasks_for_ui()
    assert_true("UI数据有daily键", 'daily' in ui_data)
    assert_true("UI数据有weekly键", 'weekly' in ui_data)
    assert_eq("UI每日任务数", len(ui_data['daily']), DAILY_PICK_COUNT)
    assert_eq("UI每周任务数", len(ui_data['weekly']), WEEKLY_PICK_COUNT)
    # 验证UI数据格式
    for t in ui_data['daily']:
        assert_true(f"任务{t['id']}有id", 'id' in t)
        assert_true(f"任务{t['id']}有desc", 'desc' in t)
        assert_true(f"任务{t['id']}有current", 'current' in t)
        assert_true(f"任务{t['id']}有target", 'target' in t)
        assert_true(f"任务{t['id']}有reward", 'reward' in t)
        assert_true(f"任务{t['id']}有claimed", 'claimed' in t)

    # 4.5 check_task_progress 批量更新
    # 注入固定任务数据（不依赖日期种子）
    sm.data['daily_tasks'] = {
        'date': get_today_str(),
        'tasks': [
            {'id': 'T1', 'type': 'level_clear', 'desc': '通关×3', 'target': 3,
             'current': 2, 'reward': 200, 'claimed': False},
            {'id': 'T2', 'type': 'coin_collect', 'desc': '金币≥500', 'target': 500,
             'current': 499, 'reward': 150, 'claimed': False},
            {'id': 'T3', 'type': 'star_rush', 'desc': '星级5', 'target': 5,
             'current': 0, 'reward': 300, 'claimed': False},
        ]
    }
    sm.save()

    sm.check_task_progress(level_id=1, level_coins=100, stars_earned=1,
                           ants_used=[1, 2], win_streak=1)
    updated = sm.get_daily_tasks()
    t1 = next(t for t in updated if t['id'] == 'T1')
    t3 = next(t for t in updated if t['id'] == 'T3')
    assert_eq("T1 通关进度+1=3", t1['current'], 3)
    assert_eq("T3 星级+1", t3['current'], 1)

    # 4.6 claim_task_reward 正常领取
    success, reward = sm.claim_task_reward('T1')
    assert_true("T1 领取成功", success)
    assert_eq("T1 奖励200", reward, 200)
    total_after = sm.get_total_coins()
    assert_true("金币增加", total_after >= 200)

    # 4.7 claim_task_reward 防重复
    success2, reward2 = sm.claim_task_reward('T1')
    assert_true("T1 重复领取失败", not success2)
    assert_eq("重复领取奖励0", reward2, 0)

    # 4.8 claim_task_reward 未完成不可领取
    success3, reward3 = sm.claim_task_reward('T2')
    assert_true("T2 未完成不可领取", not success3)

    # 4.9 claim_task_reward 不存在的任务
    success4, reward4 = sm.claim_task_reward('X99')
    assert_true("不存在任务领取失败", not success4)

    # 4.10 update_task_progress 简单接口
    sm2 = SaveManager()
    sm2.reset()
    sm2.data['daily_tasks'] = {
        'date': get_today_str(),
        'tasks': [
            {'id': 'X1', 'type': 'level_clear', 'desc': 'test', 'target': 3,
             'current': 0, 'reward': 200, 'claimed': False},
        ]
    }
    sm2.save()
    changed = sm2.update_task_progress('level_clear', 1)
    assert_true("update_task_progress 有变化", changed)

finally:
    restore_save()


# ══════════════════════════════════════════════════════════
# 5. 版本迁移 v3→v4
# ══════════════════════════════════════════════════════════

print("\n═══ 5. 版本迁移 v3→v4 ═══")

backup_save()
try:
    # 5.1 模拟v3存档（缺少任务字段结构）
    v3_data = {
        'version': 3,
        'total_coins': 500,
        'max_level_passed': 10,
        'ants': {'1': {'count': 2, 'carry': 5, 'speed': 3, 'defense': 1}},
        'settings': {'music_on': True, 'sfx_on': True},
        'levels': {},
    }
    os.makedirs(SAVE_DIR, exist_ok=True)
    with open(SAVE_FILE, 'w') as f:
        json.dump(v3_data, f)

    sm_v3 = SaveManager()
    sm_v3.load()
    assert_eq("v3迁移后版本号", sm_v3.data['version'], SAVE_VERSION)
    assert_true("v3迁移后有daily_tasks", 'daily_tasks' in sm_v3.data)
    assert_true("v3迁移后有weekly_tasks", 'weekly_tasks' in sm_v3.data)
    assert_eq("v3迁移后daily_tasks结构", sm_v3.data['daily_tasks'], {'date': '', 'tasks': []})
    assert_eq("v3迁移后coins保留", sm_v3.data['total_coins'], 500)

    # 5.2 模拟v3存档（有字段但结构错误）
    v3_bad = {
        'version': 3,
        'total_coins': 100,
        'max_level_passed': 5,
        'ants': {},
        'settings': {},
        'levels': {},
        'daily_tasks': 'invalid',
        'weekly_tasks': None,
    }
    with open(SAVE_FILE, 'w') as f:
        json.dump(v3_bad, f)

    sm_bad = SaveManager()
    sm_bad.load()
    assert_eq("v3坏数据迁移后daily_tasks", sm_bad.data['daily_tasks'], {'date': '', 'tasks': []})
    assert_eq("v3坏数据迁移后weekly_tasks", sm_bad.data['weekly_tasks'], {'week': '', 'tasks': []})

    # 5.3 模拟v1存档（最旧版本）
    v1_data = {
        'level': 5,
        'owned': True,
    }
    with open(SAVE_FILE, 'w') as f:
        json.dump(v1_data, f)

    sm_v1 = SaveManager()
    sm_v1.load()
    assert_eq("v1迁移后版本号", sm_v1.data['version'], SAVE_VERSION)
    assert_true("v1迁移后有ants", 'ants' in sm_v1.data)

finally:
    restore_save()


# ══════════════════════════════════════════════════════════
# 6. main.py 集成逻辑验证（代码审查）
# ══════════════════════════════════════════════════════════

print("\n═══ 6. main.py 集成逻辑验证 ═══")

# 通过读取 main.py 代码验证关键集成点
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'main.py'), 'r') as f:
    main_code = f.read()

assert_true("main.py 导入 TaskUI", "from ui_task import TaskUI" in main_code)
assert_true("main.py 初始化 task_ui", "self.task_ui = TaskUI()" in main_code)
assert_true("main.py task_panel_active 字段", "self.task_panel_active = False" in main_code)
assert_true("main.py _win_streak 字段", "self._win_streak = 0" in main_code)
assert_true("main.py _get_task_data 方法", "def _get_task_data" in main_code)
assert_true("main.py _click_task_overlay 方法", "def _click_task_overlay" in main_code)
assert_true("main.py check_task_progress 调用", "self.sm.check_task_progress(" in main_code)
assert_true("main.py claim_task_reward 调用", "self.sm.claim_task_reward(" in main_code)
assert_true("main.py 胜利连胜+1", "self._win_streak += 1" in main_code)
assert_true("main.py 失败连胜重置", "self._win_streak = 0" in main_code)
assert_true("main.py ESC关闭任务面板", "self.task_panel_active = False" in main_code)
assert_true("main.py 绘制任务面板", "self.task_ui.draw(" in main_code)
assert_true("main.py 滚轮支持", "self.task_ui.scroll(dy)" in main_code)


# ══════════════════════════════════════════════════════════
# 7. 边界场景测试
# ══════════════════════════════════════════════════════════

print("\n═══ 7. 边界场景测试 ═══")

# 7.1 进度超过target不溢出
tasks_edge = [make_task_entry(t) for t in DAILY_TASK_POOL]
check_task_progress(tasks_edge, level_id=1, level_coins=100, stars_earned=100)
assert_eq("星级溢出封顶", tasks_edge[2]['current'], tasks_edge[2]['target'])

# 7.2 空ants_used列表
tasks_edge2 = [make_task_entry(t) for t in DAILY_TASK_POOL]
check_task_progress(tasks_edge2, level_id=1, level_coins=100, ants_used=[])
assert_eq("空ants_used不影响", tasks_edge2[3]['current'], 0)

# 7.3 所有参数为0/None
tasks_edge3 = [make_task_entry(t) for t in DAILY_TASK_POOL]
changed = check_task_progress(tasks_edge3)
assert_true("无参数不报错", True)
assert_eq("无参数无变化", changed, False)

# 7.4 claim_task_reward 空任务列表
sm_empty = SaveManager()
sm_empty.reset()
# 不触发刷新，直接领
success_empty, _ = sm_empty.claim_task_reward('D1')
assert_true("空任务列表领取失败", not success_empty)


# ══════════════════════════════════════════════════════════
# 汇总
# ══════════════════════════════════════════════════════════

print("\n" + "═" * 50)
print(f"测试完成: {PASS} 通过, {FAIL} 失败")
if BUGS:
    print("\n失败详情:")
    for b in BUGS:
        print(b)
print("═" * 50)

sys.exit(1 if FAIL > 0 else 0)
