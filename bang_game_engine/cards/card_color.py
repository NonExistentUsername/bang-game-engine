from __future__ import annotations

from enum import Enum


class CardColor(Enum):
    BROWN = "brown"    # Instant effect, discarded after use
    BLUE = "blue"      # Persistent, stays in play on table
    GREEN = "green"    # Dodge City: persistent but delayed activation (1 turn)
    ORANGE = "orange"  # Armed & Dangerous: requires load tokens
