from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class TargetType(Enum):
    """How a card selects its target(s)."""

    NONE = "none"              # No target needed (Beer, Stagecoach)
    SINGLE_PLAYER = "single"   # One other player (Bang!, Panic!)
    ALL_OTHERS = "all_others"  # All other players (Indians!, Gatling)
    SELF = "self"              # Self-only target (equip weapon)
    ANY_PLAYER = "any_player"  # Any player including self (Cat Balou)
    CHOICE = "choice"          # Complex choice (General Store)


class RangeType(Enum):
    """How range is determined for a card."""

    WEAPON_RANGE = "weapon"    # Uses weapon range (Bang!)
    DISTANCE_1 = "dist_1"     # Distance 1 only (Panic!)
    UNLIMITED = "unlimited"    # No range limit (Cat Balou, Duel, Indians!)
    SELF = "self"              # Only self (Beer, Stagecoach)


@dataclass(frozen=True)
class CardTypeMetadata:
    """
    Static metadata about a card type. Registered in the card type registry.

    Uses string key (not enum) so expansions can register new types
    without modifying core code.
    """

    key: str                       # e.g. "bang", "missed", "gatling"
    name: str                      # Display name, e.g. "Bang!"
    color: str                     # "brown", "blue", "green", "orange"
    target_type: TargetType = TargetType.NONE
    range_type: RangeType = RangeType.SELF
    is_weapon: bool = False
    weapon_range: int = 0          # Only for weapons
    unlimited_bangs: bool = False  # Volcanic grants unlimited bangs
    expansion: str = "base"
