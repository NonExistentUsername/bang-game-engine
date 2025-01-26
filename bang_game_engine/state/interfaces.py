import abc

from bang_game_engine.action import Action
from bang_game_engine.engine import Engine


class IStateNode(abc.ABC):
    @abc.abstractmethod
    def next(
        self,
        engine: Engine,
        user_action: Action | None = None,
    ) -> None:
        pass
