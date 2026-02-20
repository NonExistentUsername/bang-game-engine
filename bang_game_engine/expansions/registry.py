"""Expansion registry: manages loading and composing expansions."""

from __future__ import annotations

from typing import Any

from bang_game_engine.effects.registry import EffectRegistry
from bang_game_engine.expansions.content_pack import ContentPack
from bang_game_engine.expansions.expansion import Expansion
from bang_game_engine.expansions.hooks import HookChain
from bang_game_engine.game.turn_rules import TurnRuleEngine
from bang_game_engine.players.character import Character
from bang_game_engine.shared.errors import DomainError


class ExpansionRegistry:
    """
    Manages expansion registration, dependency validation,
    and content pack merging.
    """

    def __init__(self) -> None:
        self._registered: dict[str, Expansion] = {}
        self._active: list[str] = []

    def register(self, expansion: Expansion) -> None:
        self._registered[expansion.name] = expansion

    def activate(self, name: str) -> None:
        if name not in self._registered:
            raise DomainError(f"Expansion not registered: {name}")

        expansion = self._registered[name]

        # Check dependencies
        for dep in expansion.dependencies:
            if dep not in self._active:
                raise DomainError(
                    f"Expansion '{name}' requires '{dep}' to be active"
                )

        if name not in self._active:
            self._active.append(name)

    def deactivate(self, name: str) -> None:
        if name in self._active:
            # Check no other active expansion depends on this
            for other_name in self._active:
                if other_name == name:
                    continue
                other = self._registered[other_name]
                if name in other.dependencies:
                    raise DomainError(
                        f"Cannot deactivate '{name}': '{other_name}' depends on it"
                    )
            self._active.remove(name)

    @property
    def active_expansions(self) -> list[str]:
        return list(self._active)

    def get_merged_content_pack(self) -> ContentPack:
        """Merge content packs from all active expansions."""
        merged = ContentPack()
        for name in self._active:
            expansion = self._registered[name]
            pack = expansion.get_content_pack()
            merged.card_type_metadata.extend(pack.card_type_metadata)
            merged.deck_cards.extend(pack.deck_cards)
            merged.characters.extend(pack.characters)
            merged.effect_handlers.update(pack.effect_handlers)
            for count, roles in pack.role_distributions.items():
                merged.role_distributions[count] = roles
            merged.config.update(pack.config)
        return merged

    def get_all_characters(self) -> list[Character]:
        """Get all characters from active expansions."""
        characters: list[Character] = []
        for name in self._active:
            expansion = self._registered[name]
            pack = expansion.get_content_pack()
            characters.extend(pack.characters)
        return characters

    def setup_effect_registry(self, registry: EffectRegistry) -> None:
        """Register effects from all active expansions."""
        for name in self._active:
            self._registered[name].register_effects(registry)

    def setup_hook_chain(self, hook_chain: HookChain) -> None:
        """Register hooks from all active expansions."""
        for name in self._active:
            self._registered[name].register_hooks(hook_chain)

    def setup_turn_rules(self, rule_engine: TurnRuleEngine) -> None:
        """Register turn rules from all active expansions."""
        for name in self._active:
            self._registered[name].register_turn_rules(rule_engine)

    def get_max_players(self) -> int:
        """Maximum player count supported by active expansions."""
        max_p = 0
        for name in self._active:
            expansion = self._registered[name]
            max_p = max(max_p, expansion.max_players)
        return max_p
