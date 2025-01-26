import abc

from bang_game_engine.card import Card


class IPlayer(abc.ABC):
    @abc.abstractmethod
    def heal(self, amount: int):
        pass

    @abc.abstractmethod
    def damage(self, amount: int):
        pass

    @property
    @abc.abstractmethod
    def max_bullets(self) -> int:
        pass

    @property
    @abc.abstractmethod
    def is_alive(self) -> bool:
        pass

    @property
    @abc.abstractmethod
    def bullets(self) -> int:
        pass

    @property
    @abc.abstractmethod
    def hand(self) -> list[Card]:
        pass

    @hand.setter
    @abc.abstractmethod
    def hand(self, hand: list[Card]):
        pass
