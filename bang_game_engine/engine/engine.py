import random

from bang_game_engine.card import Card, GunCard
from bang_game_engine.character import Character
from bang_game_engine.deck import IDeck
from bang_game_engine.engine.state import State
from bang_game_engine.player import Player, Table
from bang_game_engine.role import Role


class Engine:
    def __init__(
        self,
        players: list[Player],
        deck: IDeck,
    ):
        self._players = players
        self._deck = deck

    @property
    def players(self) -> list[Player]:
        return self._players

    def get_player_hand(self, player_index: int) -> list[Card]:
        return self._players[player_index].hand

    def get_player_gun(self, player_index: int) -> GunCard | None:
        return self._players[player_index].gun

    def get_player_table(self, player_index: int) -> Table:
        return self._players[player_index].table

    def get_player_bullets(self, player_index: int) -> int:
        return self._players[player_index].bullets

    def deck_pop_card(self) -> Card:
        return self._deck.draw()

    def __repr__(self):
        return f"Engine(players={self._players}, deck={self._deck})"

    def discard_card(self, player_index: int, card_index: int):
        card = self.get_player_hand(player_index)[card_index]
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

    def perform_check(self) -> Card:
        card = self.deck_pop_card()
        self._deck.discard(card)
        return card
