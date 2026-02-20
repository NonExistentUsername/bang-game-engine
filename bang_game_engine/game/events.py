from __future__ import annotations

from dataclasses import dataclass, field

from bang_game_engine.game.phase import Phase
from bang_game_engine.players.role import Role
from bang_game_engine.shared.events import DomainEvent
from bang_game_engine.shared.types import GameId, PlayerId


@dataclass(frozen=True)
class GameStarted(DomainEvent):
    game_id: GameId
    player_count: int


@dataclass(frozen=True)
class TurnStarted(DomainEvent):
    turn_number: int
    active_player_id: PlayerId


@dataclass(frozen=True)
class TurnEnded(DomainEvent):
    turn_number: int
    active_player_id: PlayerId


@dataclass(frozen=True)
class PhaseChanged(DomainEvent):
    player_id: PlayerId
    from_phase: Phase
    to_phase: Phase


@dataclass(frozen=True)
class GameEnded(DomainEvent):
    game_id: GameId
    winners: frozenset[Role] = field(default_factory=frozenset)
    winning_player_ids: frozenset[PlayerId] = field(default_factory=frozenset)


@dataclass(frozen=True)
class CardPlayed(DomainEvent):
    player_id: PlayerId
    card_type: str
    target_player_id: PlayerId | None = None
