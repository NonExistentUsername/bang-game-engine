from __future__ import annotations

import enum
import random


class CharacterTypes(enum.StrEnum):
    SUZY_LAFAYETTE = "suzy_lafayette"
    SLAB_THE_KILLER = "slab_the_killer"
    WILLY_THE_KID = "willy_the_kid"

    @staticmethod
    def random() -> CharacterTypes:
        return random.choice(list(CharacterTypes))  # type: ignore
