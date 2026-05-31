"""测试配置：保存并恢复被mock污染的模块

test_checkin_ui.py 在模块级别替换 sys.modules['config'] 等模块，
导致后续测试拿到 mock 而非真实模块。

解决方案：在 conftest.py 顶层（早于任何测试文件导入）保存真实模块引用，
并在每个测试函数前后恢复。
"""

import sys
import os
from unittest.mock import MagicMock

# conftest.py 比 test_*.py 更早被 pytest 加载，
# 但 test_checkin_ui.py 的模块级代码在文件被 collect 时执行。
# 我们需要在 conftest 顶层保存引用，但此时真实模块可能还没被导入。
# 解决：主动导入真实模块并保存。

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# 确保真实模块已加载
import config as _real_config
import creatures_data as _real_creatures_data

_saved_modules = {
    'config': _real_config,
    'creatures_data': _real_creatures_data,
}

# 尝试导入可能被 mock 的其他模块
for _mod_name in ['creature_sprite', 'creature_manager', 'sweet_zone_manager',
                   'sweet_sprite', 'font_helper', 'region']:
    try:
        mod = __import__(_mod_name)
        _saved_modules[_mod_name] = mod
    except ImportError:
        pass


def pytest_runtest_setup(item):
    """每个测试函数运行前，恢复真实模块"""
    for _name, _mod in _saved_modules.items():
        sys.modules[_name] = _mod


def pytest_runtest_teardown(item):
    """每个测试函数运行后，恢复真实模块"""
    for _name, _mod in _saved_modules.items():
        sys.modules[_name] = _mod
