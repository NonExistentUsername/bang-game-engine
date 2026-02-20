from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol

from bang_game_engine.cards.card import Card
from bang_game_engine.cards.card_color import CardColor
from bang_game_engine.game.turn import TurnState

if TYPE_CHECKING:
    from bang_game_engine.players.player import Player


class TurnRule(Protocol):
    def check(
        self,
        card: Card,
        player: Player,
        turn_state: TurnState,
        game: Any,
    ) -> tuple[bool, str]: ...


class TurnRuleEngine:
    """
    Enforces turn rules. Extensible via registered rule checkers.
    """

    def __init__(self) -> None:
        self._rules: list[TurnRule] = []

    def register_rule(self, rule: TurnRule) -> None:
        self._rules.append(rule)

    def can_play_card(
        self,
        card: Card,
        player: Player,
        turn_state: TurnState,
        game: Any,
    ) -> tuple[bool, str]:
        for rule in self._rules:
            allowed, reason = rule.check(card, player, turn_state, game)
            if not allowed:
                return False, reason
        return True, ""


class OneBangPerTurnRule:
    """Only 1 Bang! per turn unless Volcanic or Willy the Kid."""

    def check(
        self, card: Card, player: Any, turn_state: TurnState, game: Any
    ) -> tuple[bool, str]:
        if card.card_type == "bang" and turn_state.bangs_played >= 1:
            if not turn_state.has_unlimited_bangs:
                return False, "Already played a Bang! this turn"
        return True, ""


class GreenCardDelayRule:
    """Green cards cannot be activated the turn they are played."""

    def check(
        self, card: Card, player: Any, turn_state: TurnState, game: Any
    ) -> tuple[bool, str]:
        if (
            card.color == CardColor.GREEN
            and card.turn_played is not None
            and card.turn_played == turn_state.turn_number
        ):
            return False, "Green cards cannot be used the turn they are played"
        return True, ""


class JailCannotTargetSheriffRule:
    """Jail cannot be placed on the Sheriff."""

    def check(
        self, card: Card, player: Any, turn_state: TurnState, game: Any
    ) -> tuple[bool, str]:
        # This is a targeting rule, checked differently
        return True, ""
