from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

from bang_game_engine.shared.events import DomainEvent
from bang_game_engine.shared.types import PlayerId

if TYPE_CHECKING:
    from bang_game_engine.cards.card import Card


class AbilityTiming(Enum):
    """When in the game flow an ability can activate."""

    ON_DRAW_PHASE = "on_draw_phase"
    ON_TAKE_DAMAGE = "on_take_damage"
    ON_PLAY_CARD = "on_play_card"
    ON_DRAW_CHECK = "on_draw_check"
    ON_HAND_EMPTY = "on_hand_empty"
    ON_PLAYER_ELIMINATED = "on_player_eliminated"
    ON_DISTANCE_CALC = "on_distance_calc"
    ON_DEFENSIVE_CHECK = "on_defensive_check"
    ON_MISSED_REQUIRED = "on_missed_required"
    ON_DISCARD_PHASE = "on_discard_phase"
    ON_CARD_PLAYED_AS = "on_card_played_as"
    ON_TURN_START = "on_turn_start"
    ON_BEER_EFFECT = "on_beer_effect"
    PASSIVE = "passive"


@dataclass
class AbilityContext:
    """All information an ability might need."""

    player_id: PlayerId
    trigger_event: DomainEvent | None = None
    source_player_id: PlayerId | None = None
    card: Card | None = None
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class AbilityResult:
    """What an ability produces."""

    events: list[DomainEvent] = field(default_factory=list)
    modified_value: Any = None
    cancel_trigger: bool = False
    requires_choice: bool = False
    choice_prompt: str = ""


@runtime_checkable
class CharacterAbility(Protocol):
    """Protocol all character abilities must implement."""

    @property
    def timing(self) -> AbilityTiming: ...

    @property
    def name(self) -> str: ...

    def can_activate(self, context: AbilityContext) -> bool: ...

    def activate(self, context: AbilityContext) -> AbilityResult: ...
