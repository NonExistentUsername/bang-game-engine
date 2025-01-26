import abc

from bang_game_engine.card import Card


class IDeck(abc.ABC):
    @abc.abstractmethod
    def draw(self) -> Card:
        pass

    @abc.abstractmethod
    def discard(self, card: Card):
        pass

    @abc.abstractmethod
    def shuffle(self):
        pass

    @property
    @abc.abstractmethod
    def cards(self) -> list[Card]:
        pass

    @property
    @abc.abstractmethod
    def discard_pile(self) -> list[Card]:
        pass

    @abc.abstractmethod
    def __len__(self) -> int:
        pass


class IDeckFactory(abc.ABC):
    @abc.abstractmethod
    def create(self) -> IDeck:
        pass
