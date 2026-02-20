"""Expansion protocol and base class."""

from __future__ import annotations

from typing import Protocol

from bang_game_engine.effects.registry import EffectRegistry
from bang_game_engine.expansions.content_pack import ContentPack
from bang_game_engine.expansions.hooks import HookChain
from bang_game_engine.game.turn_rules import TurnRuleEngine


class Expansion(Protocol):
    """Protocol that all expansions must implement."""

    @property
    def name(self) -> str: ...

    @property
    def dependencies(self) -> list[str]: ...

    @property
    def min_players(self) -> int: ...

    @property
    def max_players(self) -> int: ...

    def get_content_pack(self) -> ContentPack: ...

    def register_effects(self, registry: EffectRegistry) -> None: ...

    def register_hooks(self, hook_chain: HookChain) -> None: ...

    def register_turn_rules(self, rule_engine: TurnRuleEngine) -> None: ...
