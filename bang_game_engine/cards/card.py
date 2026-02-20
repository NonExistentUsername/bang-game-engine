from __future__ import annotations

from dataclasses import dataclass, field

from bang_game_engine.cards.card_color import CardColor
from bang_game_engine.cards.card_face import CardFace
from bang_game_engine.shared.types import CardId


@dataclass
class Card:
    """
    A single physical card in the game.

    Has a unique CardId because two cards with the same type/suit/rank
    are still distinct physical objects that can be tracked independently.
    """

    id: CardId
    card_type: str        # Registry key, e.g. "bang", "missed", "barrel"
    face: CardFace
    color: CardColor

    # Mutable state for green/orange cards
    turn_played: int | None = field(default=None, compare=False)  # When green card was placed
    load_tokens: int = field(default=0, compare=False)            # For orange cards

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Card):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)

    def __repr__(self) -> str:
        return f"Card({self.card_type}, {self.face.suit.value} {self.face.rank.name})"
