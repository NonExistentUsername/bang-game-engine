from __future__ import annotations

from dataclasses import dataclass, field

from bang_game_engine.game.phase import Phase
from bang_game_engine.shared.types import PlayerId


@dataclass
class TurnState:
    """All mutable state for the current turn."""

    turn_number: int
    active_player_id: PlayerId
    current_phase: Phase
    bangs_played: int = 0
    has_unlimited_bangs: bool = False
    cards_drawn: int = 0
    is_jailed: bool = False
    skip_turn: bool = False

    # For event cards (High Noon / A Fistful of Cards)
    active_event_card: str | None = None

    # For General Store: revealed cards waiting to be picked
    general_store_cards: list = field(default_factory=list)
    general_store_pickers: list = field(default_factory=list)
