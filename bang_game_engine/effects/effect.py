from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any, Protocol

from bang_game_engine.shared.events import DomainEvent
from bang_game_engine.shared.types import CardId, PlayerId

if TYPE_CHECKING:
    from bang_game_engine.cards.card import Card


class EffectState(Enum):
    PENDING = "pending"
    AWAITING_RESPONSE = "awaiting"
    RESOLVING = "resolving"
    COMPLETE = "complete"


@dataclass
class ResponseWindow:
    """Defines who must respond and what responses are valid."""

    responding_player_id: PlayerId
    valid_response_types: list[str]  # e.g. ["missed", "bang", "beer", "pass"]
    prompt: str
    timeout_action: str = "pass"


@dataclass
class EffectContext:
    """All information an effect needs to resolve."""

    source_player_id: PlayerId
    card: Card | None = None
    target_player_id: PlayerId | None = None
    choice_index: int | None = None
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class EffectOutcome:
    """What happened when an effect resolved (or partially resolved)."""

    state: EffectState
    events: list[DomainEvent] = field(default_factory=list)
    response_window: ResponseWindow | None = None
    child_effects: list[EffectStackEntry] | None = None
    remaining_targets: list[PlayerId] | None = None


class EffectHandler(Protocol):
    """Protocol for all card effect handlers."""

    @property
    def card_type(self) -> str: ...

    def validate(self, context: EffectContext, game: Any) -> tuple[bool, str]:
        """Can this effect be played in current context?"""
        ...

    def begin(self, context: EffectContext, game: Any) -> EffectOutcome:
        """Start resolving this effect."""
        ...

    def handle_response(
        self,
        context: EffectContext,
        game: Any,
        response_card_id: CardId | None,
        responding_player_id: PlayerId,
    ) -> EffectOutcome:
        """Handle a player's response to this effect."""
        ...


@dataclass
class EffectStackEntry:
    """One entry on the effect resolution stack."""

    handler: EffectHandler
    context: EffectContext
    state: EffectState = EffectState.PENDING
    response_window: ResponseWindow | None = None
    # For multi-target effects
    remaining_targets: list[PlayerId] = field(default_factory=list)
    current_target_id: PlayerId | None = None
    # Metadata
    missed_count_needed: int = 1
    missed_played: int = 0
