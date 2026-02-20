"""Multi-target effect handlers: Indians!, Gatling, General Store."""

from __future__ import annotations

from typing import Any

from bang_game_engine.effects.effect import (
    EffectContext,
    EffectOutcome,
    EffectState,
    ResponseWindow,
)
from bang_game_engine.shared.events import DomainEvent
from bang_game_engine.shared.types import CardId, PlayerId


class IndiansEffectHandler:
    """
    Indians! - All other players must play a Bang! or lose 1 HP.
    Resolution proceeds clockwise from player left of source.
    """

    card_type = "indians"

    def validate(self, context: EffectContext, game: Any) -> tuple[bool, str]:
        return True, ""

    def begin(self, context: EffectContext, game: Any) -> EffectOutcome:
        targets = game.other_alive_players_clockwise(context.source_player_id)
        if not targets:
            return EffectOutcome(state=EffectState.COMPLETE)

        first_target = targets[0]
        return EffectOutcome(
            state=EffectState.AWAITING_RESPONSE,
            response_window=ResponseWindow(
                responding_player_id=first_target,
                valid_response_types=["bang", "pass"],
                prompt="Play a Bang! or lose 1 HP (Indians!)",
            ),
            remaining_targets=targets[1:],
        )

    def handle_response(
        self,
        context: EffectContext,
        game: Any,
        response_card_id: CardId | None,
        responding_player_id: PlayerId,
    ) -> EffectOutcome:
        events: list[DomainEvent] = []

        if response_card_id is None:
            # Take 1 damage
            player = game.get_player(responding_player_id)
            dmg_events = player.take_damage(1, context.source_player_id)
            events.extend(dmg_events)

        # Check remaining targets from effect stack entry
        # The state machine manages remaining_targets via the stack entry
        # We return COMPLETE; the state machine checks remaining targets
        return EffectOutcome(state=EffectState.COMPLETE, events=events)


class GatlingEffectHandler:
    """
    Gatling - Hit all other players for 1 damage. Each can play Missed!
    Resolution proceeds clockwise.
    """

    card_type = "gatling"

    def validate(self, context: EffectContext, game: Any) -> tuple[bool, str]:
        return True, ""

    def begin(self, context: EffectContext, game: Any) -> EffectOutcome:
        targets = game.other_alive_players_clockwise(context.source_player_id)
        if not targets:
            return EffectOutcome(state=EffectState.COMPLETE)

        first_target = targets[0]
        return EffectOutcome(
            state=EffectState.AWAITING_RESPONSE,
            response_window=ResponseWindow(
                responding_player_id=first_target,
                valid_response_types=["missed", "pass"],
                prompt="Play a Missed! or take 1 damage (Gatling)",
            ),
            remaining_targets=targets[1:],
        )

    def handle_response(
        self,
        context: EffectContext,
        game: Any,
        response_card_id: CardId | None,
        responding_player_id: PlayerId,
    ) -> EffectOutcome:
        events: list[DomainEvent] = []

        if response_card_id is None:
            player = game.get_player(responding_player_id)
            dmg_events = player.take_damage(1, context.source_player_id)
            events.extend(dmg_events)

        return EffectOutcome(state=EffectState.COMPLETE, events=events)


class GeneralStoreEffectHandler:
    """
    General Store - Reveal N cards (N = alive players).
    Each player picks one, starting with the player who played it.
    """

    card_type = "general_store"

    def validate(self, context: EffectContext, game: Any) -> tuple[bool, str]:
        return True, ""

    def begin(self, context: EffectContext, game: Any) -> EffectOutcome:
        n = game.alive_count
        revealed = game.deck.reveal_top(n)

        # Set up the pick order starting with the source player
        pick_order = [context.source_player_id]
        pick_order.extend(
            game.other_alive_players_clockwise(context.source_player_id)
        )

        # Store in turn state for the state machine to manage
        if game.current_turn is not None:
            game.current_turn.general_store_cards = revealed
            game.current_turn.general_store_pickers = pick_order
            game.current_turn.current_phase = (
                __import__(
                    "bang_game_engine.game.phase", fromlist=["Phase"]
                ).Phase.GENERAL_STORE_PICK
            )

        return EffectOutcome(state=EffectState.COMPLETE)

    def handle_response(self, context, game, response_card_id, responding_player_id):
        from bang_game_engine.shared.errors import DomainError

        raise DomainError("General Store pick is handled by the state machine")
