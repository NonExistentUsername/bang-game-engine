from __future__ import annotations

from dataclasses import dataclass

from bang_game_engine.cards.rank import Rank
from bang_game_engine.cards.suit import Suit


@dataclass(frozen=True)
class CardFace:
    """The poker identity of a card (suit + rank). Determines draw! check outcomes."""

    suit: Suit
    rank: Rank

    def is_hearts(self) -> bool:
        return self.suit == Suit.HEARTS

    def is_spades(self) -> bool:
        return self.suit == Suit.SPADES

    def is_diamonds(self) -> bool:
        return self.suit == Suit.DIAMONDS

    def is_hearts_or_diamonds(self) -> bool:
        return self.suit in (Suit.HEARTS, Suit.DIAMONDS)
