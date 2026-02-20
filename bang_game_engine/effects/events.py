from __future__ import annotations

from dataclasses import dataclass

from bang_game_engine.cards.card_face import CardFace
from bang_game_engine.shared.events import DomainEvent
from bang_game_engine.shared.types import CardId, PlayerId


@dataclass(frozen=True)
class EffectStarted(DomainEvent):
    card_type: str
    source_player_id: PlayerId
    target_player_id: PlayerId | None = None


@dataclass(frozen=True)
class EffectResolved(DomainEvent):
    card_type: str
    source_player_id: PlayerId
    outcome: str = ""  # "hit", "missed", "avoided", etc.


@dataclass(frozen=True)
class DrawCheckPerformed(DomainEvent):
    player_id: PlayerId
    check_type: str  # "barrel", "jail", "dynamite", etc.
    card_face: CardFace | None = None
    passed: bool = False


@dataclass(frozen=True)
class BeerSavingAttempt(DomainEvent):
    player_id: PlayerId
    success: bool


@dataclass(frozen=True)
class DynamiteExploded(DomainEvent):
    player_id: PlayerId
    damage: int = 3


@dataclass(frozen=True)
class DynamitePassed(DomainEvent):
    from_player_id: PlayerId
    to_player_id: PlayerId


@dataclass(frozen=True)
class JailEscaped(DomainEvent):
    player_id: PlayerId


@dataclass(frozen=True)
class JailKept(DomainEvent):
    """Player failed jail check, turn is skipped."""

    player_id: PlayerId
