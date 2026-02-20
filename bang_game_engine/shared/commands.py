from __future__ import annotations

from dataclasses import dataclass

from bang_game_engine.shared.types import PlayerId


@dataclass(frozen=True)
class Command:
    """Base for all player commands."""

    player_id: PlayerId
