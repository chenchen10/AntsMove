"""场景模块：将 GameState 中各状态的 draw/click 逻辑拆分为独立场景类"""

from scenes.base import Scene
from scenes.title import TitleScene
from scenes.level_select import LevelSelectScene
from scenes.team_select import TeamSelectScene
from scenes.playing import PlayingScene
from scenes.paused import PausedScene
from scenes.level_complete import LevelCompleteScene
from scenes.game_over import GameOverScene
from scenes.debug import DebugScene

SCENE_MAP = {
    'title': TitleScene,
    'level_select': LevelSelectScene,
    'team_select': TeamSelectScene,
    'playing': PlayingScene,
    'paused': PausedScene,
    'level_complete': LevelCompleteScene,
    'game_over': GameOverScene,
    'debug': DebugScene,
}
