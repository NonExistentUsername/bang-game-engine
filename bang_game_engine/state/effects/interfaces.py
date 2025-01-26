import abc

from bang_game_engine.engine import IEngine
from bang_game_engine.state.effects.effects import MissEffectNode


class IMissEffectFactory(abc.ABC):
    @abc.abstractmethod
    def create(
        self,
        engine: IEngine,
        initiating_player_index: int,
        target_player_index: int,
    ) -> MissEffectNode:
        pass
