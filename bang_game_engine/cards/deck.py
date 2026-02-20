from __future__ import annotations

import random

from bang_game_engine.cards.card import Card
from bang_game_engine.cards.events import (
    CardDiscardedToPile,
    CardDrawnFromDeck,
    DeckShuffled,
    DiscardReshuffledIntoDeck,
    DrawCheckCardRevealed,
)
from bang_game_engine.shared.errors import DomainError
from bang_game_engine.shared.events import EventCollector


class Deck(EventCollector):
    """
    Aggregate managing draw pile and discard pile.

    Invariant: when draw pile is empty, shuffle discard pile into draw pile.
    """

    def __init__(
        self,
        draw_pile: list[Card],
        discard_pile: list[Card] | None = None,
        rng: random.Random | None = None,
    ):
        super().__init__()
        self._draw_pile = list(draw_pile)
        self._discard_pile = list(discard_pile) if discard_pile else []
        self._rng = rng or random.Random()

    def draw(self) -> Card:
        """Draw a card from the top of the draw pile."""
        if not self._draw_pile:
            if not self._discard_pile:
                raise DomainError("No cards remaining in deck or discard pile")
            self._reshuffle()
        card = self._draw_pile.pop()
        self._record_event(CardDrawnFromDeck(card_id=card.id))
        return card

    def draw_for_check(self) -> Card:
        """
        Draw for 'draw!' check (Barrel, Jail, Dynamite).
        Card is revealed and then discarded.
        """
        card = self.draw()
        self._record_event(DrawCheckCardRevealed(card_id=card.id, face=card.face))
        return card

    def discard(self, card: Card) -> None:
        """Place a card on the discard pile."""
        self._discard_pile.append(card)
        self._record_event(CardDiscardedToPile(card_id=card.id))

    def peek_top(self, count: int) -> list[Card]:
        """Look at top N cards without removing (Kit Carlson)."""
        return list(self._draw_pile[-count:])

    def put_back_on_top(self, card: Card) -> None:
        """Put a card back on top of draw pile (Kit Carlson)."""
        self._draw_pile.append(card)

    def take_from_top_without_event(self, count: int) -> list[Card]:
        """Remove top N cards without draw events (Kit Carlson internal)."""
        cards = []
        for _ in range(count):
            if not self._draw_pile:
                if not self._discard_pile:
                    break
                self._reshuffle()
            cards.append(self._draw_pile.pop())
        return cards

    def peek_discard_top(self) -> Card | None:
        """Look at top of discard pile (Pedro Ramirez)."""
        return self._discard_pile[-1] if self._discard_pile else None

    def take_from_discard_top(self) -> Card | None:
        """Take top card of discard pile (Pedro Ramirez)."""
        if not self._discard_pile:
            return None
        return self._discard_pile.pop()

    def reveal_top(self, count: int) -> list[Card]:
        """
        Reveal and remove top N cards (General Store).
        Cards are removed from draw pile but NOT discarded.
        """
        cards = []
        for _ in range(count):
            if not self._draw_pile:
                if not self._discard_pile:
                    break
                self._reshuffle()
            cards.append(self._draw_pile.pop())
        return cards

    def shuffle(self) -> None:
        """Shuffle the draw pile."""
        self._rng.shuffle(self._draw_pile)
        self._record_event(DeckShuffled())

    def _reshuffle(self) -> None:
        """Shuffle discard pile into draw pile when draw pile is empty."""
        self._draw_pile = list(self._discard_pile)
        self._discard_pile.clear()
        self._rng.shuffle(self._draw_pile)
        self._record_event(DiscardReshuffledIntoDeck())

    @property
    def draw_pile_size(self) -> int:
        return len(self._draw_pile)

    @property
    def discard_pile_size(self) -> int:
        return len(self._discard_pile)

    @property
    def total_size(self) -> int:
        return len(self._draw_pile) + len(self._discard_pile)
