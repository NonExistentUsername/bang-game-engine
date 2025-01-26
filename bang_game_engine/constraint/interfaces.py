import abc

from bang_game_engine.engine import IEngine


class IConstraint(abc.ABC):
    @abc.abstractmethod
    def check(
        self,
        engine: IEngine,
        **options,
    ) -> bool:
        pass
