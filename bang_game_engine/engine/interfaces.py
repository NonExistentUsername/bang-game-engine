import abc

from bang_game_engine.card import Card
from bang_game_engine.player import IPlayer


class IEngine(abc.ABC):
    @property
    @abc.abstractmethod
    def players(self) -> list[IPlayer]:
        pass

    @abc.abstractmethod
    def get_player(self, player_index: int) -> IPlayer:
        pass

    @abc.abstractmethod
    def deck_pop_card(self) -> Card:
        pass

    @abc.abstractmethod
    def discard_card(self, player_index: int, card_index: int):
        pass

    @abc.abstractmethod
    def draw_cards(self, player_index: int, amount: int):
        pass

    @abc.abstractmethod
    def damage_player(self, target_index: int, amount: int):
        pass

    @abc.abstractmethod
    def heal_player(self, target_index: int, amount: int):
        pass
