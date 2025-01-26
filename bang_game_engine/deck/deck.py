import copy
import random

from bang_game_engine.card import Card
from bang_game_engine.deck.interfaces import IDeck


class Deck(IDeck):
    def __init__(self, cards: list[Card], discard_pile: list[Card] | None = None):
        self._cards = cards
        self._discard_pile = discard_pile or []

    def draw(self) -> Card:
        if not self._cards:
            self.shuffle()

        return self._cards.pop()

    def discard(self, card: Card):
        return self._discard_pile.append(card)

    def shuffle(self):
        self._cards.extend(self._discard_pile)
        self._discard_pile = []

        random.shuffle(self._cards)

    @property
    def cards(self) -> list[Card]:
        return copy.deepcopy(self._cards)

    @property
    def discard_pile(self) -> list[Card]:
        return copy.deepcopy(self._discard_pile)

    def __len__(self) -> int:
        return len(self._cards)

    def __repr__(self):
        return f"Deck(cards={self._cards}, discard_pile={self._discard_pile})"
