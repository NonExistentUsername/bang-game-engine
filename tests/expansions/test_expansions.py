"""Tests for the expansion system: registry, content packs, base game expansion."""

from __future__ import annotations

import pytest

from bang_game_engine.effects.registry import EffectRegistry
from bang_game_engine.expansions.base.cards import (
    BASE_CARD_TYPES,
    create_base_deck_cards,
)
from bang_game_engine.expansions.base.characters import create_base_characters
from bang_game_engine.expansions.base.expansion import BaseGameExpansion
from bang_game_engine.expansions.content_pack import ContentPack
from bang_game_engine.expansions.hooks import (
    HookChain,
    HookContext,
    HookPoint,
    HookResult,
)
from bang_game_engine.expansions.registry import ExpansionRegistry
from bang_game_engine.game.turn_rules import TurnRuleEngine
from bang_game_engine.shared.errors import DomainError


class TestBaseGameExpansion:
    def test_name(self):
        exp = BaseGameExpansion()
        assert exp.name == "base"

    def test_no_dependencies(self):
        exp = BaseGameExpansion()
        assert exp.dependencies == []

    def test_player_range(self):
        exp = BaseGameExpansion()
        assert exp.min_players == 4
        assert exp.max_players == 7

    def test_content_pack_has_characters(self):
        exp = BaseGameExpansion()
        pack = exp.get_content_pack()
        assert len(pack.characters) == 16

    def test_content_pack_has_card_metadata(self):
        exp = BaseGameExpansion()
        pack = exp.get_content_pack()
        assert len(pack.card_type_metadata) == 22

    def test_content_pack_has_role_distributions(self):
        exp = BaseGameExpansion()
        pack = exp.get_content_pack()
        assert 4 in pack.role_distributions
        assert 7 in pack.role_distributions

    def test_content_pack_has_effect_handlers(self):
        exp = BaseGameExpansion()
        pack = exp.get_content_pack()
        assert "bang" in pack.effect_handlers
        assert "beer" in pack.effect_handlers
        assert "duel" in pack.effect_handlers

    def test_register_effects(self):
        exp = BaseGameExpansion()
        registry = EffectRegistry()
        exp.register_effects(registry)
        assert registry.has_handler("bang")
        assert registry.has_handler("beer")
        assert registry.has_handler("indians")

    def test_register_turn_rules(self):
        exp = BaseGameExpansion()
        engine = TurnRuleEngine()
        exp.register_turn_rules(engine)
        # Can't easily check internal rules, but it shouldn't error
        assert engine is not None


class TestBaseCards:
    def test_80_cards(self):
        cards = create_base_deck_cards()
        assert len(cards) == 80

    def test_unique_card_ids(self):
        cards = create_base_deck_cards()
        ids = {c.id for c in cards}
        assert len(ids) == 80

    def test_card_type_distribution(self):
        cards = create_base_deck_cards()
        from collections import Counter
        counts = Counter(c.card_type for c in cards)
        assert counts["bang"] == 25
        assert counts["missed"] == 12
        assert counts["beer"] == 6
        assert counts["barrel"] == 2

    def test_all_cards_have_valid_faces(self):
        cards = create_base_deck_cards()
        for card in cards:
            assert card.face.suit is not None
            assert card.face.rank is not None

    def test_card_type_metadata_coverage(self):
        cards = create_base_deck_cards()
        types_in_deck = {c.card_type for c in cards}
        metadata_keys = {m.key for m in BASE_CARD_TYPES}
        # Every type in deck should have metadata
        assert types_in_deck.issubset(metadata_keys)


class TestBaseCharacters:
    def test_16_characters(self):
        chars = create_base_characters()
        assert len(chars) == 16

    def test_unique_character_types(self):
        chars = create_base_characters()
        types = {c.character_type for c in chars}
        assert len(types) == 16

    def test_hp_values(self):
        chars = create_base_characters()
        for char in chars:
            assert char.base_hp in (3, 4)

    def test_el_gringo_has_3_hp(self):
        chars = create_base_characters()
        el_gringo = [c for c in chars if c.character_type == "el_gringo"][0]
        assert el_gringo.base_hp == 3

    def test_paul_regret_has_3_hp(self):
        chars = create_base_characters()
        paul = [c for c in chars if c.character_type == "paul_regret"][0]
        assert paul.base_hp == 3

    def test_all_characters_have_abilities(self):
        chars = create_base_characters()
        for char in chars:
            assert len(char.abilities) >= 1, f"{char.name} has no abilities"


class TestExpansionRegistry:
    def test_register_and_activate(self):
        reg = ExpansionRegistry()
        reg.register(BaseGameExpansion())
        reg.activate("base")
        assert "base" in reg.active_expansions

    def test_activate_unregistered_raises(self):
        reg = ExpansionRegistry()
        with pytest.raises(DomainError, match="not registered"):
            reg.activate("nonexistent")

    def test_deactivate(self):
        reg = ExpansionRegistry()
        reg.register(BaseGameExpansion())
        reg.activate("base")
        reg.deactivate("base")
        assert "base" not in reg.active_expansions

    def test_get_all_characters(self):
        reg = ExpansionRegistry()
        reg.register(BaseGameExpansion())
        reg.activate("base")
        chars = reg.get_all_characters()
        assert len(chars) == 16

    def test_merged_content_pack(self):
        reg = ExpansionRegistry()
        reg.register(BaseGameExpansion())
        reg.activate("base")
        pack = reg.get_merged_content_pack()
        assert len(pack.characters) == 16
        assert "bang" in pack.effect_handlers

    def test_max_players(self):
        reg = ExpansionRegistry()
        reg.register(BaseGameExpansion())
        reg.activate("base")
        assert reg.get_max_players() == 7


class TestHookChain:
    def test_empty_chain(self):
        chain = HookChain()
        ctx = HookContext(hook_point=HookPoint.ON_TURN_START, game_state=None)
        events = chain.execute(ctx)
        assert events == []

    def test_execute_with_value(self):
        chain = HookChain()
        ctx = HookContext(
            hook_point=HookPoint.ON_DISTANCE_CALC, game_state=None
        )
        value, events = chain.execute_with_value(ctx, initial_value=3)
        assert value == 3
        assert events == []
