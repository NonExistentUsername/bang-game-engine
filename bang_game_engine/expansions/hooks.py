"""Hook system for extensibility. Character abilities and expansions plug in here."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Protocol

from bang_game_engine.shared.events import DomainEvent


class HookPoint(Enum):
    """All extension points in the game flow."""

    ON_TURN_START = "on_turn_start"
    ON_DRAW_PHASE = "on_draw_phase"
    ON_PLAY_CARD = "on_play_card"
    ON_CARD_EFFECT_BEGIN = "on_card_effect_begin"
    ON_DAMAGE_DEALT = "on_damage_dealt"
    ON_TAKE_DAMAGE = "on_take_damage"
    ON_HEAL = "on_heal"
    ON_PLAYER_ELIMINATED = "on_player_eliminated"
    ON_DRAW_CHECK = "on_draw_check"
    ON_DEFENSIVE_CHECK = "on_defensive_check"
    ON_MISSED_REQUIRED = "on_missed_required"
    ON_HAND_EMPTY = "on_hand_empty"
    ON_DISCARD_PHASE = "on_discard_phase"
    ON_DISTANCE_CALC = "on_distance_calc"
    ON_BEER_EFFECT = "on_beer_effect"
    ON_TURN_END = "on_turn_end"
    ON_CARD_PLAYED_AS = "on_card_played_as"


@dataclass
class HookContext:
    """Context provided to hook handlers."""

    hook_point: HookPoint
    game_state: Any  # GameState
    data: dict[str, Any] = field(default_factory=dict)


@dataclass
class HookResult:
    """Result from a hook handler."""

    events: list[DomainEvent] = field(default_factory=list)
    modified_value: Any = None
    cancel: bool = False
    skip_remaining: bool = False


class HookHandler(Protocol):
    """Protocol for hook handlers."""

    def priority(self) -> int:
        """Lower priority runs first. Default 50."""
        ...

    def handle(self, context: HookContext) -> HookResult: ...


class HookChain:
    """
    Manages a chain of hook handlers for each hook point.
    Handlers are executed in priority order (lowest first).
    """

    def __init__(self) -> None:
        self._handlers: dict[HookPoint, list[tuple[int, HookHandler]]] = {}

    def register(self, hook_point: HookPoint, handler: HookHandler) -> None:
        if hook_point not in self._handlers:
            self._handlers[hook_point] = []
        priority = handler.priority()
        self._handlers[hook_point].append((priority, handler))
        self._handlers[hook_point].sort(key=lambda x: x[0])

    def execute(self, context: HookContext) -> list[DomainEvent]:
        """Execute all handlers for the given hook point."""
        handlers = self._handlers.get(context.hook_point, [])
        all_events: list[DomainEvent] = []

        for _priority, handler in handlers:
            result = handler.handle(context)
            all_events.extend(result.events)
            if result.skip_remaining:
                break
            if result.cancel:
                break

        return all_events

    def execute_with_value(
        self, context: HookContext, initial_value: Any
    ) -> tuple[Any, list[DomainEvent]]:
        """Execute handlers that modify a value (e.g., distance, draw count)."""
        handlers = self._handlers.get(context.hook_point, [])
        value = initial_value
        all_events: list[DomainEvent] = []

        for _priority, handler in handlers:
            result = handler.handle(context)
            all_events.extend(result.events)
            if result.modified_value is not None:
                value = result.modified_value
            if result.skip_remaining or result.cancel:
                break

        return value, all_events
