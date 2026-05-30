"""本地存档系统：JSON持久化，支持版本迁移

蚂蚁数据结构（v2）：
  ants: {ant_id_str: {'count': int, 'carry': int, 'speed': int, 'defense': int}}
  - count: 拥有数量（分种类独立管理）
  - carry: 搬运属性等级（0-200）
  - speed: 速度属性等级（0-200）
  - defense: 防御属性等级（0-200）

关卡星级数据结构（v3新增）：
  levels: {level_id_str: {
      'best_stars': int,      # 最高星级（0-3）
      'best_coins': int,      # 最高金币记录
      'best_time_left': float, # 最佳剩余时间
      'times_played': int,    # 累计挑战次数
      'times_won': int,       # 累计通关次数
  }}

任务系统数据结构（v4新增）：
  daily_tasks: {date: str, tasks: [{id, type, desc, target, current, reward, claimed}]}
  weekly_tasks: {week: str, tasks: [{id, type, desc, target, current, reward, claimed}]}

成就系统数据结构（v5新增）：
  achievements: {achievement_id: {
      'progress': int,        # 当前进度
      'claimed': bool,        # 是否已领取奖励
  }}
"""

import json
import logging
import os
import shutil

logger = logging.getLogger(__name__)

SAVE_VERSION = 5
SAVE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'saves')
SAVE_FILE = os.path.join(SAVE_DIR, 'save_data.json')
BACKUP_FILE = SAVE_FILE + '.bak'


def _default_save_data():
    """返回初始存档数据结构"""
    from achievements_data import ACHIEVEMENTS
    achievements = {}
    for ach in ACHIEVEMENTS:
        achievements[ach['id']] = {'progress': 0, 'claimed': False}
    return {
        'version': SAVE_VERSION,
        'total_coins': 0,
        'max_level_passed': 0,
        'ants': {},
        'settings': {
            'music_on': True,
            'sfx_on': True,
        },
        'levels': {},
        'daily_tasks': {'date': '', 'tasks': []},
        'weekly_tasks': {'week': '', 'tasks': []},
        'achievements': achievements,
        'checkin': {
            'current_day': 0,
            'last_checkin_date': None,
            'total_checkins': 0,
            'streak': 0,
            'cycles_completed': 0,
        },
    }


class SaveManager:
    """管理本地存档的读写"""

    def __init__(self):
        self.data = _default_save_data()
        self.loaded = False
        self.load_failed = False

    def load(self):
        if not os.path.exists(SAVE_FILE):
            self.data = _default_save_data()
            self.loaded = True
            self.load_failed = False
            return self.data

        try:
            with open(SAVE_FILE, 'r', encoding='utf-8') as f:
                saved = json.load(f)
            self.data = self._migrate(saved)
            self.loaded = True
            self.load_failed = False
        except Exception:
            logger.exception('Failed to load save file, falling back to defaults. '
                             'This will OVERWRITE the save on next save()!')
            self.data = _default_save_data()
            self.loaded = True
            self.load_failed = True
            # 尝试从备份恢复
            restored = self._try_restore_backup()
            if restored:
                self.load_failed = False

        return self.data

    def save(self):
        os.makedirs(SAVE_DIR, exist_ok=True)
        tmp_path = SAVE_FILE + '.tmp'
        try:
            with open(tmp_path, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
            # 原子替换前，备份当前存档
            if os.path.exists(SAVE_FILE):
                try:
                    shutil.copy2(SAVE_FILE, BACKUP_FILE)
                except OSError:
                    pass
            # 原子替换：先写临时文件再 rename，防止写入中途崩溃导致存档损坏
            os.replace(tmp_path, SAVE_FILE)
        except Exception:
            logger.exception('Failed to save file')
            # 清理临时文件
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass

    def _try_restore_backup(self):
        """尝试从备份文件恢复存档"""
        if not os.path.exists(BACKUP_FILE):
            logger.warning('No backup file found at %s', BACKUP_FILE)
            return False
        try:
            with open(BACKUP_FILE, 'r', encoding='utf-8') as f:
                saved = json.load(f)
            self.data = self._migrate(saved)
            logger.info('Successfully restored save from backup')
            return True
        except Exception:
            logger.exception('Failed to restore from backup')
            return False

    def _migrate(self, saved):
        """版本迁移：v1 → v2 → v3 → v4 → v5"""
        data = _default_save_data()
        for key in data:
            if key in saved:
                data[key] = saved[key]

        old_version = saved.get('version', 1)
        if old_version < 2:
            try:
                # v1: {'level': int, 'owned': bool/count} → v2: {'count': int, 'carry': int, 'speed': int, 'defense': int}
                for ant_id_str, ant_data in data.get('ants', {}).items():
                    if 'carry' in ant_data:
                        continue  # 已经是v2格式
                    # 获取旧数据
                    old_level = ant_data.get('level', 0)
                    old_count = ant_data.get('count', 0)
                    if 'owned' in ant_data and 'count' not in ant_data:
                        old_count = 1 if ant_data.pop('owned') else 0
                    # 迁移：旧等级 → 搬运等级，速度/防御为0
                    data['ants'][ant_id_str] = {
                        'count': old_count,
                        'carry': old_level,
                        'speed': 0,
                        'defense': 0,
                    }
            except Exception:
                logger.exception('Migration v1→v2 failed, skipping')

        if old_version < 3:
            try:
                # v2 → v3：新增关卡星级、任务、成就、签到数据
                data.setdefault('levels', {})
                data.setdefault('daily_tasks', {'date': '', 'tasks': []})
                data.setdefault('weekly_tasks', {'week': '', 'tasks': []})
                data.setdefault('achievements', {})
                data.setdefault('checkin', {
                    'current_day': 0,
                    'last_checkin_date': None,
                    'total_checkins': 0,
                    'streak': 0,
                    'cycles_completed': 0,
                })
                # 回填已通关关卡星级（保守1星）
                from levels_data import get_level, _calc_target_coins
                max_passed = data.get('max_level_passed', 0)
                for lv in range(1, max_passed + 1):
                    key = str(lv)
                    if key not in data['levels']:
                        data['levels'][key] = {
                            'best_stars': 1,
                            'best_coins': _calc_target_coins(lv),
                            'best_time_left': 0,
                            'times_played': 0,
                            'times_won': 1,
                        }
            except Exception:
                logger.exception('Migration v2→v3 failed, skipping')

        if old_version < 4:
            try:
                # v3 → v4：任务系统正式启用，确保字段结构完整
                dt = data.get('daily_tasks', {})
                if not isinstance(dt, dict) or 'date' not in dt:
                    data['daily_tasks'] = {'date': '', 'tasks': []}
                wt = data.get('weekly_tasks', {})
                if not isinstance(wt, dict) or 'week' not in wt:
                    data['weekly_tasks'] = {'week': '', 'tasks': []}
            except Exception:
                logger.exception('Migration v3→v4 failed, skipping')

        if old_version < 5:
            try:
                # v4 → v5：成就系统正式启用，规范化achievements数据结构
                # 旧格式: {id: {'current': int, 'claimed': bool}} 或 {}
                # 新格式: {id: {'progress': int, 'claimed': bool}}（补全所有成就ID）
                from achievements_data import ACHIEVEMENTS
                old_ach = data.get('achievements', {})
                new_ach = {}
                for ach in ACHIEVEMENTS:
                    aid = ach['id']
                    saved_ach = old_ach.get(aid, {})
                    # 兼容旧的 'current' 字段 → 重命名为 'progress'
                    progress = saved_ach.get('progress', saved_ach.get('current', 0))
                    claimed = saved_ach.get('claimed', False)
                    new_ach[aid] = {'progress': int(progress), 'claimed': bool(claimed)}
                data['achievements'] = new_ach
            except Exception:
                logger.exception('Migration v4→v5 failed, skipping')

        data['version'] = SAVE_VERSION
        return data

    # ── 便捷接口 ──

    def get_total_coins(self):
        return self.data.get('total_coins', 0)

    def add_coins(self, amount):
        self.data['total_coins'] = self.data.get('total_coins', 0) + amount
        self.save()

    def spend_coins(self, amount):
        if self.data['total_coins'] < amount:
            return False
        self.data['total_coins'] -= amount
        self.save()
        return True

    def get_max_level(self):
        return self.data.get('max_level_passed', 0)

    def set_max_level(self, level):
        if level > self.data.get('max_level_passed', 0):
            self.data['max_level_passed'] = level
            self.save()

    # ── 蚂蚁拥有数量（分种类独立管理）──

    def is_ant_owned(self, ant_id):
        ant_data = self.data['ants'].get(str(ant_id), {})
        return ant_data.get('count', 0) > 0

    def get_ant_count(self, ant_id):
        ant_data = self.data['ants'].get(str(ant_id), {})
        return ant_data.get('count', 0)

    def buy_ant(self, ant_id, cost):
        """购买一只蚂蚁，返回是否成功"""
        if not self.spend_coins(cost):
            return False
        key = str(ant_id)
        if key not in self.data['ants']:
            self.data['ants'][key] = {'count': 1, 'carry': 0, 'speed': 0, 'defense': 0}
        else:
            self.data['ants'][key]['count'] = self.data['ants'][key].get('count', 0) + 1
        self.save()
        return True

    # ── 多属性升级 ──

    def get_ant_attr(self, ant_id, attr):
        """获取蚂蚁某属性等级（carry/speed/defense）"""
        key = str(ant_id)
        ant_data = self.data['ants'].get(key, {})
        return ant_data.get(attr, 0)

    def set_ant_attr(self, ant_id, attr, value):
        """设置蚂蚁某属性等级"""
        key = str(ant_id)
        if key not in self.data['ants']:
            self.data['ants'][key] = {'count': 1, 'carry': 0, 'speed': 0, 'defense': 0}
        self.data['ants'][key][attr] = value
        self.save()

    def upgrade_ant_attr(self, ant_id, attr, cost):
        """升级蚂蚁某属性，返回是否成功"""
        if not self.is_ant_owned(ant_id):
            return False
        if not self.spend_coins(cost):
            return False
        key = str(ant_id)
        if key not in self.data['ants']:
            self.data['ants'][key] = {'count': 1, 'carry': 0, 'speed': 0, 'defense': 0}
        self.data['ants'][key][attr] = self.data['ants'][key].get(attr, 0) + 1
        self.save()
        return True

    def batch_upgrade_ant_attr(self, ant_id, attr, target_level):
        """批量升级蚂蚁某属性到目标等级（原子操作）

        Args:
            ant_id: 蚂蚁ID
            attr: 属性名（carry/speed/defense）
            target_level: 目标等级，200表示升满

        Returns:
            dict: {
                'success': bool,           # 是否有升级发生
                'levels_up': int,          # 实际升了多少级
                'new_level': int,          # 升级后的等级
                'cost_spent': int,         # 实际花费的金币
            }
        """
        from ants_data import get_upgrade_cost, MAX_ATTR_LEVEL

        if not self.is_ant_owned(ant_id):
            return {'success': False, 'levels_up': 0, 'new_level': 0, 'cost_spent': 0}

        start_level = self.get_ant_attr(ant_id, attr)
        target_level = min(target_level, MAX_ATTR_LEVEL)
        if target_level <= start_level:
            return {'success': False, 'levels_up': 0, 'new_level': start_level, 'cost_spent': 0}

        # 逐级计算费用，直到金币耗尽或达到目标
        total_cost = 0
        actual_target = start_level
        for lv in range(start_level, target_level):
            cost = get_upgrade_cost(ant_id, attr, lv)
            if cost is None:
                break
            if self.data.get('total_coins', 0) < total_cost + cost:
                break
            total_cost += cost
            actual_target = lv + 1

        if actual_target <= start_level:
            return {'success': False, 'levels_up': 0, 'new_level': start_level, 'cost_spent': 0}

        # 一次性扣费并设置等级（原子操作）
        old_coins = self.data.get('total_coins', 0)
        old_level = self.get_ant_attr(ant_id, attr)
        try:
            self.data['total_coins'] = old_coins - total_cost
            self.set_ant_attr(ant_id, attr, actual_target)
            self.save()
        except Exception:
            # 回滚
            self.data['total_coins'] = old_coins
            self.set_ant_attr(ant_id, attr, old_level)
            return {'success': False, 'levels_up': 0, 'new_level': old_level, 'cost_spent': 0}

        return {
            'success': True,
            'levels_up': actual_target - start_level,
            'new_level': actual_target,
            'cost_spent': total_cost,
        }

    # 兼容旧接口
    def get_ant_level(self, ant_id):
        """兼容旧代码，返回搬运属性等级"""
        return self.get_ant_attr(ant_id, 'carry')

    # ── 列表查询 ──

    def get_all_owned_ants(self):
        result = []
        for ant_id_str, ant_data in self.data['ants'].items():
            count = ant_data.get('count', 0)
            for _ in range(count):
                result.append(int(ant_id_str))
        return sorted(result)

    def get_unique_owned_ants(self):
        result = []
        for ant_id_str, ant_data in self.data['ants'].items():
            if ant_data.get('count', 0) > 0:
                result.append(int(ant_id_str))
        return sorted(result)

    def get_owned_count(self):
        total = 0
        for ant_data in self.data['ants'].values():
            total += ant_data.get('count', 0)
        return total

    def get_maxed_count(self, max_level=200):
        """返回搬运属性满级的蚂蚁种类数"""
        count = 0
        for ant_data in self.data['ants'].values():
            if ant_data.get('count', 0) > 0 and ant_data.get('carry', 0) >= max_level:
                count += 1
        return count

    # ── 关卡星级记录（v3新增）──

    def update_level_record(self, level_id, stars, coins, time_left):
        """更新关卡记录（星级只升不降）"""
        key = str(level_id)
        levels = self.data.setdefault('levels', {})
        record = levels.get(key, {
            'best_stars': 0,
            'best_coins': 0,
            'best_time_left': 0,
            'times_played': 0,
            'times_won': 0,
        })

        record['times_played'] = record.get('times_played', 0) + 1

        if stars > 0:
            record['times_won'] = record.get('times_won', 0) + 1
            # 星级只升不降
            if stars > record.get('best_stars', 0):
                record['best_stars'] = stars
            if coins > record.get('best_coins', 0):
                record['best_coins'] = coins
            if time_left > record.get('best_time_left', 0):
                record['best_time_left'] = time_left
        else:
            # 失败也记录挑战次数
            pass

        levels[key] = record
        self.save()

    def get_level_record(self, level_id):
        """获取关卡记录"""
        return self.data.get('levels', {}).get(str(level_id), {})

    def get_level_stars(self, level_id):
        """获取关卡最高星级"""
        return self.get_level_record(level_id).get('best_stars', 0)

    def get_total_stars(self):
        """获取累计总星数"""
        return sum(r.get('best_stars', 0) for r in self.data.get('levels', {}).values())

    def get_total_levels_won(self):
        """获取累计通关次数"""
        return sum(r.get('times_won', 0) for r in self.data.get('levels', {}).values())

    def ensure_starter_ant(self):
        """确保玩家至少拥有1只初始蚂蚁（ant_id=1），防止软锁定

        注意：仅在存档确实为空（非加载失败导致的默认数据）时才写盘，
        避免加载失败时将空白数据写回覆盖真实存档。
        """
        if self.get_owned_count() == 0:
            self.data['ants']['1'] = {'count': 1, 'carry': 0, 'speed': 0, 'defense': 0}
            # 加载失败时禁止写盘，防止将默认数据+1只蚂蚁覆盖真实存档
            # 仅在加载成功（或新玩家首次启动无存档文件）时才写盘
            if not self.load_failed and os.path.exists(SAVE_FILE):
                self.save()

    # ── 任务系统接口（v4新增）──

    def get_daily_tasks_data(self):
        """获取每日任务原始数据 {date, tasks}"""
        return self.data.get('daily_tasks', {'date': '', 'tasks': []})

    def get_weekly_tasks_data(self):
        """获取每周任务原始数据 {week, tasks}"""
        return self.data.get('weekly_tasks', {'week': '', 'tasks': []})

    def get_daily_tasks(self):
        """获取今日任务列表（触发刷新检查后返回）"""
        from tasks_data import refresh_daily_tasks
        dt = self.data.get('daily_tasks', {'date': '', 'tasks': []})
        tasks, date_str = refresh_daily_tasks(dt.get('date', ''))
        if tasks is not None:
            self.data['daily_tasks'] = {'date': date_str, 'tasks': tasks}
            self.save()
            return tasks
        return dt.get('tasks', [])

    def get_weekly_tasks(self):
        """获取本周任务列表（触发刷新检查后返回）"""
        from tasks_data import refresh_weekly_tasks
        wt = self.data.get('weekly_tasks', {'week': '', 'tasks': []})
        tasks, week_str = refresh_weekly_tasks(wt.get('week', ''))
        if tasks is not None:
            self.data['weekly_tasks'] = {'week': week_str, 'tasks': tasks}
            self.save()
            return tasks
        return wt.get('tasks', [])

    def get_tasks_for_ui(self):
        """获取UI消费格式的任务数据"""
        daily = self.get_daily_tasks()
        weekly = self.get_weekly_tasks()
        return {
            'daily': [
                {
                    'id': t['id'],
                    'desc': t['desc'],
                    'current': t['current'],
                    'target': t['target'],
                    'reward': t['reward'],
                    'claimed': t['claimed'],
                }
                for t in daily
            ],
            'weekly': [
                {
                    'id': t['id'],
                    'desc': t['desc'],
                    'current': t['current'],
                    'target': t['target'],
                    'reward': t['reward'],
                    'claimed': t['claimed'],
                }
                for t in weekly
            ],
        }

    def update_task_progress(self, task_type_value, amount=1):
        """更新任务进度（关卡结算时调用）

        Returns:
            是否有任务进度变化
        """
        from tasks_data import update_task_progress
        changed = False
        for key in ('daily_tasks', 'weekly_tasks'):
            data = self.data.get(key, {'date': '', 'tasks': []})
            if update_task_progress(task_type_value, amount, data.get('tasks', [])):
                changed = True
                self.data[key] = data
        if changed:
            self.save()
        return changed

    def check_task_progress(self, **kwargs):
        """根据游戏结算数据检查并更新所有任务进度

        由关卡结算时调用，批量更新，不在每帧追踪。
        """
        from tasks_data import check_task_progress
        changed = False
        for key in ('daily_tasks', 'weekly_tasks'):
            data = self.data.get(key, {'date': '', 'tasks': []})
            if check_task_progress(data.get('tasks', []), **kwargs):
                changed = True
                self.data[key] = data
        if changed:
            self.save()
        return changed

    def claim_task_reward(self, task_id):
        """领取任务奖励，防重复

        Args:
            task_id: 任务ID（如 'D1', 'W2'）

        Returns:
            (success: bool, reward: int)
        """
        for key in ('daily_tasks', 'weekly_tasks'):
            data = self.data.get(key, {'date': '', 'tasks': []})
            for task in data.get('tasks', []):
                if task['id'] == task_id:
                    if task['claimed']:
                        return False, 0
                    if task['current'] < task['target']:
                        return False, 0
                    task['claimed'] = True
                    reward = task['reward']
                    self.data['total_coins'] = self.data.get('total_coins', 0) + reward
                    self.save()
                    return True, reward
        return False, 0

    # ── 成就系统接口（v5新增）──

    def get_achievements(self):
        """获取所有成就的持久化数据

        Returns:
            dict: {achievement_id: {'progress': int, 'claimed': bool}}
        """
        return self.data.get('achievements', {})

    def get_achievement(self, achievement_id):
        """获取单个成就的持久化数据

        Returns:
            dict: {'progress': int, 'claimed': bool}
        """
        return self.data.get('achievements', {}).get(achievement_id, {'progress': 0, 'claimed': False})

    def get_achievement_progress(self, achievement_id):
        """获取成就当前进度"""
        return self.get_achievement(achievement_id).get('progress', 0)

    def is_achievement_claimed(self, achievement_id):
        """判断成就奖励是否已领取"""
        return self.get_achievement(achievement_id).get('claimed', False)

    def update_achievement_progress(self, achievement_id, progress):
        """更新成就进度（由关卡结算/游戏事件触发）

        Args:
            achievement_id: 成就ID（如 'C1', 'H3'）
            progress: 当前进度值（只升不降）

        Returns:
            是否有进度变化
        """
        achievements = self.data.setdefault('achievements', {})
        entry = achievements.get(achievement_id, {'progress': 0, 'claimed': False})
        if progress > entry.get('progress', 0):
            entry['progress'] = progress
            achievements[achievement_id] = entry
            self.save()
            return True
        return False

    def claim_achievement_reward(self, achievement_id):
        """领取成就奖励（防重复领取）

        Args:
            achievement_id: 成就ID（如 'C1', 'H3'）

        Returns:
            (success: bool, reward_coins: int)
        """
        from achievements_data import ACHIEVEMENT_BY_ID
        ach = ACHIEVEMENT_BY_ID.get(achievement_id)
        if not ach:
            return False, 0

        achievements = self.data.setdefault('achievements', {})
        entry = achievements.get(achievement_id, {'progress': 0, 'claimed': False})

        # 已领取 → 拒绝
        if entry.get('claimed', False):
            return False, 0

        # 进度不足 → 拒绝
        if entry.get('progress', 0) < ach['threshold']:
            return False, 0

        # 领取：标记已领取
        entry['claimed'] = True
        achievements[achievement_id] = entry

        # 发放金币奖励
        rewards = ach.get('rewards', {})
        reward_coins = rewards.get('coins', 0)
        self.data['total_coins'] = self.data.get('total_coins', 0) + reward_coins
        self.save()
        return True, reward_coins

    def evaluate_all_achievements(self):
        """评估所有成就，同步进度并返回新增解锁的成就ID列表。

        在关卡结算时调用，检测是否有新成就达成。
        """
        from achievements_data import evaluate_achievements
        stats = evaluate_achievements(self)
        achievements = self.data.setdefault('achievements', {})
        newly_unlocked = []
        for aid, st in stats.items():
            entry = achievements.get(aid, {'progress': 0, 'claimed': False})
            # 同步进度
            if st['current'] > entry.get('progress', 0):
                entry['progress'] = st['current']
            # 新解锁且未领取
            if st['unlocked'] and not entry.get('claimed', False):
                if not entry.get('unlocked_notified', False):
                    entry['unlocked_notified'] = True
                    newly_unlocked.append(aid)
            achievements[aid] = entry
        if newly_unlocked:
            self.save()
        return newly_unlocked

    def get_pending_achievements(self):
        """获取已解锁但未领取的成就ID列表"""
        from achievements_data import ACHIEVEMENT_BY_ID
        achievements = self.data.get('achievements', {})
        pending = []
        for aid, saved in achievements.items():
            if saved.get('unlocked_notified', False) and not saved.get('claimed', False):
                if aid in ACHIEVEMENT_BY_ID:
                    pending.append(aid)
        return pending

    # ── 签到系统接口（v3新增）──

    def get_checkin_data(self):
        """获取签到原始数据"""
        return self.data.get('checkin', {
            'current_day': 0,
            'last_checkin_date': None,
            'total_checkins': 0,
            'streak': 0,
            'cycles_completed': 0,
        })

    def can_checkin_today(self):
        """判断今天是否可以签到

        Returns:
            bool: True 表示今天还没签到，可以签到
        """
        from datetime import date
        today = date.today().isoformat()
        checkin = self.get_checkin_data()
        return checkin.get('last_checkin_date') != today

    def perform_checkin(self):
        """执行签到操作

        委托 checkin_data.perform_checkin 处理核心签到逻辑，
        额外完成金币累加和存档持久化。

        奖励公式：actual_reward = base_reward × (1 + streak_bonus) × cycle_multiplier

        Returns:
            dict: {
                'success': bool,
                'reward': dict or None,    # 奖励信息（含实际奖励金额）
                'day': int,                # 签到的天数（1-7）
                'cycle_completed': bool,   # 是否完成了7天周期
                'new_cycle': bool,         # 是否进入了新周期
            }
        """
        from checkin_data import perform_checkin as _perform_checkin
        from datetime import date

        today = date.today().isoformat()
        checkin = self.get_checkin_data()

        result = _perform_checkin(checkin, today_str=today)

        if result['success']:
            self.data['checkin'] = checkin
            self.data['total_coins'] = self.data.get('total_coins', 0) + result['reward']['amount']
            self.save()

        return result

    def get_checkin_reward_for_day(self, day):
        """获取指定天数的基础签到奖励

        Args:
            day: 天数 (1-7)

        Returns:
            int: 金币奖励（基础值，不含加成）
        """
        from checkin_data import CHECKIN_BASE_REWARDS, CYCLE_LENGTH
        return CHECKIN_BASE_REWARDS[(day - 1) % CYCLE_LENGTH]

    def reset(self):
        self.data = _default_save_data()
        self.save()
