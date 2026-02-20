from __future__ import annotations

from enum import Enum


class Role(Enum):
    SHERIFF = "sheriff"
    DEPUTY = "deputy"
    OUTLAW = "outlaw"
    RENEGADE = "renegade"

    @property
    def hp_bonus(self) -> int:
        """Sheriff gets +1 HP."""
        return 1 if self == Role.SHERIFF else 0

    @property
    def is_public(self) -> bool:
        """Only the Sheriff's role is revealed at game start."""
        return self == Role.SHERIFF
