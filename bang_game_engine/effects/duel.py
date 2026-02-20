"""Duel effect handler."""

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


class DuelEffectHandler:
    """
    Duel - Target must play Bang!, then source, alternating.
    First player who can't (or won't) play Bang! loses 1 HP.
    Unlimited range. Does NOT count as a Bang! play.
    """

    card_type = "duel"

    def __init__(self) -> None:
        self._current_responder: PlayerId | None = None
        self._other_player: PlayerId | None = None

    def validate(self, context: EffectContext, game: Any) -> tuple[bool, str]:
        if context.target_player_id is None:
            return False, "Duel requires a target"
        return True, ""

    def begin(self, context: EffectContext, game: Any) -> EffectOutcome:
        target_id = context.target_player_id
        assert target_id is not None

        # Target responds first
        self._current_responder = target_id
        self._other_player = context.source_player_id

        return EffectOutcome(
            state=EffectState.AWAITING_RESPONSE,
            response_window=ResponseWindow(
                responding_player_id=target_id,
                valid_response_types=["bang", "pass"],
                prompt="Play a Bang! or lose 1 HP (Duel)",
            ),
        )

    def handle_response(
        self,
        context: EffectContext,
        game: Any,
        response_card_id: CardId | None,
        responding_player_id: PlayerId,
    ) -> EffectOutcome:
        if response_card_id is None:
            # This player loses - take 1 damage
            loser = game.get_player(responding_player_id)
            # Damage source is the OTHER player in the duel
            other = (
                self._other_player
                if responding_player_id == self._current_responder
                else self._current_responder
            )
            dmg_events = loser.take_damage(1, other)
            return EffectOutcome(state=EffectState.COMPLETE, events=dmg_events)
        else:
            # Played Bang! - swap responders
            assert self._current_responder is not None
            assert self._other_player is not None

            new_responder = self._other_player
            self._other_player = self._current_responder
            self._current_responder = new_responder

            return EffectOutcome(
                state=EffectState.AWAITING_RESPONSE,
                response_window=ResponseWindow(
                    responding_player_id=new_responder,
                    valid_response_types=["bang", "pass"],
                    prompt="Play a Bang! or lose 1 HP (Duel)",
                ),
            )
