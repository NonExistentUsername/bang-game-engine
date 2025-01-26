from bang_game_engine.card import Card
from bang_game_engine.deck import IDeck
from bang_game_engine.engine.interfaces import IEngine
from bang_game_engine.player import IPlayer


class Engine(IEngine):
    def __init__(
        self,
        players: list[IPlayer],
        deck: IDeck,
    ):
        self._players = players
        self._deck = deck

    @property
    def players(self) -> list[IPlayer]:
        return self._players

    @property
    def alive_players(self) -> list[IPlayer]:
        return [player for player in self._players if player.is_alive]

    def get_player(self, player_index: int) -> IPlayer:
        return self._players[player_index]

    def deck_pop_card(self) -> Card:
        return self._deck.draw()

    def __repr__(self):
        return f"Engine(players={self._players}, deck={self._deck})"

    def discard_card(self, player_index: int, card_index: int):
        card = self.get_player(player_index).hand[card_index]
        self._players[player_index].hand.remove(card)
        self._deck.discard(card)

    def draw_cards(self, player_index: int, amount: int):
        for _ in range(amount):
            card = self.deck_pop_card()
            self._players[player_index].hand.append(card)

    def damage_player(self, target_index: int, amount: int):
        self._players[target_index].damage(amount)

    def heal_player(self, target_index: int, amount: int):
        self._players[target_index].heal(amount)
