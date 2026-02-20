from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from bang_game_engine.cards.card import Card
from bang_game_engine.cards.card_face import CardFace
from bang_game_engine.cards.deck import Deck
from bang_game_engine.cards.rank import Rank
from bang_game_engine.cards.suit import Suit


class DrawCondition(Protocol):
    """Condition for a draw! check."""

    def evaluate(self, face: CardFace) -> bool: ...


class BarrelCondition:
    """Hearts = success (shot is missed)."""

    def evaluate(self, face: CardFace) -> bool:
        return face.suit == Suit.HEARTS


class JailCondition:
    """Hearts = escape from jail."""

    def evaluate(self, face: CardFace) -> bool:
        return face.suit == Suit.HEARTS


class DynamiteCondition:
    """Spades 2-9 = dynamite explodes."""

    def evaluate(self, face: CardFace) -> bool:
        return face.suit == Suit.SPADES and Rank.TWO <= face.rank <= Rank.NINE


@dataclass(frozen=True)
class DrawCheckResult:
    card_drawn: Card
    passed: bool


class DrawCheckService:
    """
    Handles the "draw!" mechanic: flip top card, check suit/rank condition.
    Used by Barrel, Jail, Dynamite, and expansion cards (Rattlesnake, etc.).
    """

    def perform_check(
        self,
        deck: Deck,
        condition: DrawCondition,
    ) -> DrawCheckResult:
        card = deck.draw_for_check()
        passed = condition.evaluate(card.face)
        deck.discard(card)
        return DrawCheckResult(card_drawn=card, passed=passed)

    def perform_lucky_duke_check(
        self,
        deck: Deck,
    ) -> tuple[Card, Card]:
        """Draw 2 cards for Lucky Duke. Caller chooses which result to use."""
        card1 = deck.draw_for_check()
        card2 = deck.draw_for_check()
        return card1, card2
