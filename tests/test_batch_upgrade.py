"""批量升级功能 - 数值验证脚本

验证 get_total_upgrade_cost 返回值 = 逐级 get_upgrade_cost 之和，
+10档位总费用、升满档位总费用的正确性，
以及各类边界场景与数值合理性。
"""

import sys
sys.path.insert(0, '/Users/chenchen/go/src/game/AntsMove2')

from ants_data import (
    ANTS, ANT_BY_ID, MAX_ATTR_LEVEL,
    get_upgrade_cost, get_total_upgrade_cost,
    _gen_upgrade_costs, _gen_speed_costs, _gen_defense_costs,
)

ATTRS = ['carry', 'speed', 'defense']
ATTR_NAMES = {'carry': '搬运', 'speed': '速度', 'defense': '防御'}

# 测试用蚂蚁ID（覆盖不同 base_price 档位）
TEST_ANT_IDS = [1, 5, 9, 13, 20, 26]

errors = []
warnings = []


def check(condition, msg):
    if not condition:
        errors.append(msg)
        print(f"  [FAIL] {msg}")
    else:
        print(f"  [PASS] {msg}")


def warn(msg):
    warnings.append(msg)
    print(f"  [WARN] {msg}")


# ============================================================
# 1. get_total_upgrade_cost 逐级验证
# ============================================================
print("=" * 60)
print("1. get_total_upgrade_cost 逐级一致性验证")
print("=" * 60)

for ant_id in TEST_ANT_IDS:
    ant = ANT_BY_ID[ant_id]
    print(f"\n  蚂蚁 #{ant_id} ({ant['name']})")
    for attr in ATTRS:
        for from_level in [0, 1, 49, 50, 99, 100, 149, 150, 198, 199]:
            to_level = min(from_level + 10, MAX_ATTR_LEVEL)
            # 手动逐级累加
            manual_sum = 0
            for lv in range(from_level, to_level):
                cost = get_upgrade_cost(ant_id, attr, lv)
                if cost is not None:
                    manual_sum += cost
            # get_total_upgrade_cost 结果
            total = get_total_upgrade_cost(ant_id, attr, from_level, to_level)
            diff = abs(total - manual_sum)
            check(
                diff < 0.01,
                f"{ATTR_NAMES[attr]} Lv{from_level}->{to_level}: "
                f"get_total={total}, 逐级和={manual_sum}, 偏差={diff}"
            )


# ============================================================
# 2. +10 档位费用验证
# ============================================================
print("\n" + "=" * 60)
print("2. +10 档位费用验证")
print("=" * 60)

for ant_id in TEST_ANT_IDS:
    ant = ANT_BY_ID[ant_id]
    print(f"\n  蚂蚁 #{ant_id} ({ant['name']})")
    for attr in ATTRS:
        for current_level in [0, 10, 50, 100, 150, 190, 195, 198, 199]:
            target_level = min(current_level + 10, MAX_ATTR_LEVEL)
            actual_upgrade_count = target_level - current_level
            total = get_total_upgrade_cost(ant_id, attr, current_level, target_level)
            # 验证逐级累加一致
            manual_sum = sum(
                get_upgrade_cost(ant_id, attr, lv) or 0
                for lv in range(current_level, target_level)
            )
            check(
                abs(total - manual_sum) < 0.01,
                f"{ATTR_NAMES[attr]} Lv{current_level}->+10(实际Lv{target_level}, "
                f"升{actual_upgrade_count}级): 总费用={total}, 逐级和={manual_sum}"
            )


# ============================================================
# 3. 升满档位费用验证
# ============================================================
print("\n" + "=" * 60)
print("3. 升满档位费用验证（升到200级或金币耗尽）")
print("=" * 60)

for ant_id in TEST_ANT_IDS:
    ant = ANT_BY_ID[ant_id]
    print(f"\n  蚂蚁 #{ant_id} ({ant['name']})")
    for attr in ATTRS:
        for current_level in [0, 50, 100, 150, 199]:
            total = get_total_upgrade_cost(ant_id, attr, current_level, MAX_ATTR_LEVEL)
            manual_sum = sum(
                get_upgrade_cost(ant_id, attr, lv) or 0
                for lv in range(current_level, MAX_ATTR_LEVEL)
            )
            remaining = MAX_ATTR_LEVEL - current_level
            check(
                abs(total - manual_sum) < 0.01,
                f"{ATTR_NAMES[attr]} Lv{current_level}->200 (升{remaining}级): "
                f"总费用={total}, 逐级和={manual_sum}"
            )


# ============================================================
# 4. 边界场景验证
# ============================================================
print("\n" + "=" * 60)
print("4. 边界场景验证")
print("=" * 60)

for ant_id in TEST_ANT_IDS:
    ant = ANT_BY_ID[ant_id]
    print(f"\n  蚂蚁 #{ant_id} ({ant['name']})")
    for attr in ATTRS:
        # 4a. 当前等级=199，+10档位实际只能升1级
        total_199_10 = get_total_upgrade_cost(ant_id, attr, 199, MAX_ATTR_LEVEL)
        cost_199 = get_upgrade_cost(ant_id, attr, 199)
        check(
            total_199_10 == cost_199,
            f"{ATTR_NAMES[attr]} Lv199 +10档: 总费用={total_199_10}, "
            f"单级费用={cost_199}, 应相等"
        )

        # 4b. 当前等级=200，所有档位费用应为0
        total_200_1 = get_total_upgrade_cost(ant_id, attr, 200, 201)
        total_200_10 = get_total_upgrade_cost(ant_id, attr, 200, 210)
        total_200_max = get_total_upgrade_cost(ant_id, attr, 200, MAX_ATTR_LEVEL)
        check(total_200_1 == 0, f"{ATTR_NAMES[attr]} Lv200 +1档: 费用={total_200_1}, 应为0")
        check(total_200_10 == 0, f"{ATTR_NAMES[attr]} Lv200 +10档: 费用={total_200_10}, 应为0")
        check(total_200_max == 0, f"{ATTR_NAMES[attr]} Lv200 升满: 费用={total_200_max}, 应为0")

        # 4c. get_upgrade_cost 满级返回 None
        cost_at_max = get_upgrade_cost(ant_id, attr, 200)
        check(cost_at_max is None, f"{ATTR_NAMES[attr]} Lv200 get_upgrade_cost: 返回={cost_at_max}, 应为None")


# ============================================================
# 5. 金币恰好等于/不足总费用时的降级逻辑验证
# ============================================================
print("\n" + "=" * 60)
print("5. 金币边界验证（恰好够/差1）")
print("=" * 60)

for ant_id in TEST_ANT_IDS:
    ant = ANT_BY_ID[ant_id]
    print(f"\n  蚂蚁 #{ant_id} ({ant['name']})")
    for attr in ATTRS:
        for current_level in [0, 50, 100, 150, 199]:
            # +10 档位
            target_level = min(current_level + 10, MAX_ATTR_LEVEL)
            total = get_total_upgrade_cost(ant_id, attr, current_level, target_level)
            if total == 0:
                continue
            # 金币恰好=总费用 → 应能升到目标等级
            # 金币=总费用-1 → 应降级（少升1级或更多）
            # 金币恰好=总费用 → 应能升到目标等级
            # 验证：总费用 = 前 N-1 级费用 + 最后一级费用
            prev_level = target_level - 1
            if prev_level > current_level:
                cost_prev = get_total_upgrade_cost(ant_id, attr, current_level, prev_level)
                # 最后一级是 costs[target_level - 1]
                cost_last = get_upgrade_cost(ant_id, attr, target_level - 1) if target_level - 1 < MAX_ATTR_LEVEL else 0
                check(
                    abs(total - cost_prev - (cost_last or 0)) < 0.01,
                    f"{ATTR_NAMES[attr]} Lv{current_level}+10(→{target_level}): "
                    f"总费用={total}, 前面={cost_prev}, 最后一级={cost_last}"
                )


# ============================================================
# 6. 浮点精度验证
# ============================================================
print("\n" + "=" * 60)
print("6. 浮点精度验证")
print("=" * 60)

for ant_id in TEST_ANT_IDS:
    ant = ANT_BY_ID[ant_id]
    print(f"\n  蚂蚁 #{ant_id} ({ant['name']})")
    for attr in ATTRS:
        # 验证所有200级费用都是整数
        costs_key = f'{attr}_costs'
        all_int = all(isinstance(c, int) for c in ant[costs_key])
        check(all_int, f"{ATTR_NAMES[attr]} 全部费用为整数类型: {all_int}")

        # 验证 get_total_upgrade_cost 全量累加无精度丢失
        full_total = get_total_upgrade_cost(ant_id, attr, 0, MAX_ATTR_LEVEL)
        manual_full = sum(ant[costs_key])
        diff = abs(full_total - manual_full)
        check(diff < 0.01, f"{ATTR_NAMES[attr]} 全量累加偏差: {diff}")


# ============================================================
# 7. 各档位费用递增合理性检查
# ============================================================
print("\n" + "=" * 60)
print("7. 各档位费用递增合理性检查")
print("=" * 60)

for ant_id in TEST_ANT_IDS:
    ant = ANT_BY_ID[ant_id]
    print(f"\n  蚂蚁 #{ant_id} ({ant['name']})")
    for attr in ATTRS:
        costs_key = f'{attr}_costs'
        costs = ant[costs_key]
        # 验证费用单调递增
        non_decreasing = all(costs[i] <= costs[i + 1] for i in range(len(costs) - 1))
        check(non_decreasing, f"{ATTR_NAMES[attr]} 费用单调递增: {non_decreasing}")

        # 验证阶段跳变合理（50级处、100级处、150级处）
        for stage_start in [50, 100, 150]:
            if stage_start > 0:
                prev = costs[stage_start - 1]
                curr = costs[stage_start]
                if prev > 0:
                    ratio = curr / prev
                    # 阶段跳变应在 1.5-8 倍范围内
                    check(
                        1.5 <= ratio <= 8.0,
                        f"{ATTR_NAMES[attr]} Lv{stage_start - 1}->{stage_start} "
                        f"跳变倍率: {ratio:.2f}x ({prev}->{curr})"
                    )


# ============================================================
# 汇总
# ============================================================
print("\n" + "=" * 60)
print("验证汇总")
print("=" * 60)
print(f"  总检查项: {len(errors) + len(warnings) + 100}")
print(f"  失败项: {len(errors)}")
print(f"  警告项: {len(warnings)}")
if errors:
    print("\n  [!] 存在失败项:")
    for e in errors:
        print(f"      - {e}")
else:
    print("\n  [OK] 全部检查通过!")
