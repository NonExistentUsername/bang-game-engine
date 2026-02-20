from __future__ import annotations

from dataclasses import dataclass, field

from bang_game_engine.players.ability import AbilityTiming, CharacterAbility


@dataclass
class Character:
    """
    A character card. Each has a name, base HP, and unique abilities.
    """

    character_type: str       # Registry key, e.g. "bart_cassidy"
    name: str                 # Display name, e.g. "Bart Cassidy"
    base_hp: int              # Base hit points (typically 3 or 4)
    abilities: list[CharacterAbility] = field(default_factory=list)
    expansion: str = "base"

    # For Legends expansion: double-sided character cards
    legendary_side: Character | None = None

    def get_abilities_for_timing(
        self, timing: AbilityTiming
    ) -> list[CharacterAbility]:
        return [a for a in self.abilities if a.timing == timing]

    def has_ability(self, ability_name: str) -> bool:
        return any(a.name == ability_name for a in self.abilities)
