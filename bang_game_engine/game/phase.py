from __future__ import annotations

from enum import Enum


class Phase(Enum):
    NOT_STARTED = "not_started"

    # Pre-turn checks (resolved in order)
    DYNAMITE_CHECK = "dynamite_check"
    JAIL_CHECK = "jail_check"

    # Standard turn phases
    DRAW_PHASE = "draw_phase"
    PLAY_PHASE = "play_phase"
    DISCARD_PHASE = "discard_phase"

    # Special phases
    AWAITING_RESPONSE = "awaiting_response"
    GENERAL_STORE_PICK = "general_store_pick"

    GAME_OVER = "game_over"
