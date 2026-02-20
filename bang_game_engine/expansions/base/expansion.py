"""Base game expansion: the core Bang! experience."""

from __future__ import annotations

from bang_game_engine.effects.base_effects import (
    BangEffectHandler,
    BeerEffectHandler,
    CatBalouEffectHandler,
    PanicEffectHandler,
    SaloonEffectHandler,
    StagecoachEffectHandler,
    WellsFargoEffectHandler,
)
from bang_game_engine.effects.duel import DuelEffectHandler
from bang_game_engine.effects.multi_target import (
    GatlingEffectHandler,
    GeneralStoreEffectHandler,
    IndiansEffectHandler,
)
from bang_game_engine.effects.registry import EffectRegistry
from bang_game_engine.expansions.base.cards import (
    BASE_CARD_TYPES,
    create_base_deck_cards,
    get_base_deck_spec,
)
from bang_game_engine.expansions.base.characters import create_base_characters
from bang_game_engine.expansions.content_pack import ContentPack
from bang_game_engine.expansions.hooks import HookChain
from bang_game_engine.game.turn_rules import (
    GreenCardDelayRule,
    OneBangPerTurnRule,
    TurnRuleEngine,
)


# Role distributions for different player counts (official rules)
_ROLE_DISTRIBUTIONS: dict[int, list[str]] = {
    4: ["sheriff", "renegade", "outlaw", "outlaw"],
    5: ["sheriff", "renegade", "outlaw", "outlaw", "deputy"],
    6: ["sheriff", "renegade", "outlaw", "outlaw", "outlaw", "deputy"],
    7: ["sheriff", "renegade", "outlaw", "outlaw", "outlaw", "deputy", "deputy"],
}


class BaseGameExpansion:
    """
    The base Bang! game, loaded through the expansion system.
    Supports 4-7 players.
    """

    @property
    def name(self) -> str:
        return "base"

    @property
    def dependencies(self) -> list[str]:
        return []  # No dependencies -- this IS the base

    @property
    def min_players(self) -> int:
        return 4

    @property
    def max_players(self) -> int:
        return 7

    def get_content_pack(self) -> ContentPack:
        return ContentPack(
            card_type_metadata=list(BASE_CARD_TYPES),
            deck_cards=get_base_deck_spec(),
            characters=create_base_characters(),
            effect_handlers={
                "bang": lambda: BangEffectHandler(),
                "beer": lambda: BeerEffectHandler(),
                "saloon": lambda: SaloonEffectHandler(),
                "stagecoach": lambda: StagecoachEffectHandler(),
                "wells_fargo": lambda: WellsFargoEffectHandler(),
                "panic": lambda: PanicEffectHandler(),
                "cat_balou": lambda: CatBalouEffectHandler(),
                "indians": lambda: IndiansEffectHandler(),
                "gatling": lambda: GatlingEffectHandler(),
                "duel": lambda: DuelEffectHandler(),
                "general_store": lambda: GeneralStoreEffectHandler(),
            },
            role_distributions=dict(_ROLE_DISTRIBUTIONS),
            config={
                "hand_limit_equals_hp": True,
                "default_weapon_range": 1,
                "default_draw_count": 2,
                "beer_disabled_at_player_count": 2,
            },
        )

    def register_effects(self, registry: EffectRegistry) -> None:
        """Register all base game effect handlers."""
        pack = self.get_content_pack()
        for card_type, factory in pack.effect_handlers.items():
            registry.register(card_type, factory)

    def register_hooks(self, hook_chain: HookChain) -> None:
        """Base game has no hooks -- character abilities are handled directly."""
        pass

    def register_turn_rules(self, rule_engine: TurnRuleEngine) -> None:
        """Register base game turn rules."""
        rule_engine.register_rule(OneBangPerTurnRule())
        rule_engine.register_rule(GreenCardDelayRule())
