from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from bang_game_engine.players.ability import AbilityContext, AbilityTiming
from bang_game_engine.players.seating import Seating
from bang_game_engine.shared.types import PlayerId

if TYPE_CHECKING:
    from bang_game_engine.players.player import Player


class DistanceModifier(Protocol):
    """Expansion hook for modifying distance calculation."""

    def apply(self, distance: int, from_player: Player, to_player: Player) -> int: ...


class DistanceService:
    """
    Calculates effective distance considering:
    - Circular seating arrangement (only alive players)
    - Mustang (+1 for others to reach you)
    - Scope (-1 for you to reach others)
    - Character abilities (Paul Regret, Rose Doolan)
    - Expansion modifiers
    """

    def calculate(
        self,
        seating: Seating,
        from_player: Player,
        to_player: Player,
        modifiers: list[DistanceModifier] | None = None,
    ) -> int:
        base = seating.raw_distance(from_player.id, to_player.id)

        # Target has Mustang: +1 for others to reach them
        if to_player.has_card_type_on_table("mustang"):
            base += 1

        # Attacker has Scope: -1 for them to reach others
        if from_player.has_card_type_on_table("scope"):
            base -= 1

        # Character ability modifiers on target (e.g. Paul Regret: +1 distance seen)
        for ability in to_player.character.get_abilities_for_timing(
            AbilityTiming.ON_DISTANCE_CALC
        ):
            ctx = AbilityContext(player_id=to_player.id, extra={"role": "target"})
            if ability.can_activate(ctx):
                result = ability.activate(ctx)
                if result.modified_value is not None:
                    base += result.modified_value

        # Character ability modifiers on attacker (e.g. Rose Doolan: -1 distance)
        for ability in from_player.character.get_abilities_for_timing(
            AbilityTiming.ON_DISTANCE_CALC
        ):
            ctx = AbilityContext(
                player_id=from_player.id, extra={"role": "attacker"}
            )
            if ability.can_activate(ctx):
                result = ability.activate(ctx)
                if result.modified_value is not None:
                    base += result.modified_value

        # Expansion modifiers
        if modifiers:
            for mod in modifiers:
                base = mod.apply(base, from_player, to_player)

        return max(base, 0)

    def is_in_weapon_range(
        self,
        seating: Seating,
        from_player: Player,
        to_player: Player,
        modifiers: list[DistanceModifier] | None = None,
    ) -> bool:
        dist = self.calculate(seating, from_player, to_player, modifiers)
        return dist <= from_player.weapon_range

    def is_in_range(
        self,
        seating: Seating,
        from_player: Player,
        to_player: Player,
        distance: int,
        modifiers: list[DistanceModifier] | None = None,
    ) -> bool:
        dist = self.calculate(seating, from_player, to_player, modifiers)
        return dist <= distance
