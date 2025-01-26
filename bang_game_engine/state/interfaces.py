import abc

from bang_game_engine.action import Action


class IStateNode(abc.ABC):
    @abc.abstractmethod
    def next(
        self,
        user_action: Action | None = None,
    ) -> None:
        pass
