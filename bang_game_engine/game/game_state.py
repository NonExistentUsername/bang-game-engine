from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from bang_game_engine.cards.deck import Deck
from bang_game_engine.effects.effect_stack import EffectStack
from bang_game_engine.effects.registry import EffectRegistry
from bang_game_engine.game.phase import Phase
from bang_game_engine.game.turn import TurnState
from bang_game_engine.game.turn_rules import TurnRuleEngine
from bang_game_engine.game.win_condition import WinConditionEvaluator
from bang_game_engine.players.distance_service import DistanceService
from bang_game_engine.players.player import Player
from bang_game_engine.players.seating import Seating
from bang_game_engine.shared.events import DomainEvent
from bang_game_engine.shared.types import GameId, PlayerId


class GameState:
    """
    The top-level game state aggregate root.
    Holds references to all game components.
    """

    def __init__(
        self,
        game_id: GameId,
        players: dict[PlayerId, Player],
        seating: Seating,
        deck: Deck,
        effect_stack: EffectStack,
        effect_registry: EffectRegistry,
        turn_rule_engine: TurnRuleEngine,
        win_evaluator: WinConditionEvaluator,
        distance_service: DistanceService,
    ):
        self.game_id = game_id
        self.players = players
        self.seating = seating
        self.deck = deck
        self.effect_stack = effect_stack
        self.effect_registry = effect_registry
        self.turn_rule_engine = turn_rule_engine
        self.win_evaluator = win_evaluator
        self.distance_service = distance_service

        self.current_turn: TurnState | None = None
        self._events: list[DomainEvent] = []
        self._game_result = None

    def get_player(self, player_id: PlayerId) -> Player:
        if player_id not in self.players:
            from bang_game_engine.shared.errors import DomainError

            raise DomainError(f"Player {player_id} not found")
        return self.players[player_id]

    @property
    def alive_count(self) -> int:
        return self.seating.alive_count

    @property
    def is_over(self) -> bool:
        return self._game_result is not None

    @property
    def game_result(self):
        return self._game_result

    def set_game_result(self, result) -> None:
        self._game_result = result

    def other_alive_players_clockwise(
        self, from_player_id: PlayerId
    ) -> list[PlayerId]:
        return self.seating.other_alive_players_clockwise(from_player_id)

    def alive_player_ids(self) -> list[PlayerId]:
        return self.seating.alive_players_in_order()

    def record_event(self, event: DomainEvent) -> None:
        self._events.append(event)

    def collect_events(self) -> list[DomainEvent]:
        """Collect all pending events from all components."""
        events = list(self._events)
        self._events.clear()

        # Collect from deck
        events.extend(self.deck.collect_events())

        # Collect from players
        for player in self.players.values():
            events.extend(player.collect_events())

        return events
