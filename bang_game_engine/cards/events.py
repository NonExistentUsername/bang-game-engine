from __future__ import annotations

from dataclasses import dataclass

from bang_game_engine.cards.card_face import CardFace
from bang_game_engine.shared.events import DomainEvent
from bang_game_engine.shared.types import CardId


@dataclass(frozen=True)
class CardDrawnFromDeck(DomainEvent):
    card_id: CardId


@dataclass(frozen=True)
class DrawCheckCardRevealed(DomainEvent):
    card_id: CardId
    face: CardFace


@dataclass(frozen=True)
class CardDiscardedToPile(DomainEvent):
    card_id: CardId


@dataclass(frozen=True)
class DeckShuffled(DomainEvent):
    pass


@dataclass(frozen=True)
class DiscardReshuffledIntoDeck(DomainEvent):
    pass
