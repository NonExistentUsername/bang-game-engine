"""Tests for the effects system: EffectStack, EffectRegistry, DrawCheck, base effects."""

from __future__ import annotations

import random

import pytest

from bang_game_engine.cards.card import Card
from bang_game_engine.cards.card_color import CardColor
from bang_game_engine.cards.card_face import CardFace
from bang_game_engine.cards.deck import Deck
from bang_game_engine.cards.rank import Rank
from bang_game_engine.cards.suit import Suit
from bang_game_engine.effects.draw_check import (
    BarrelCondition,
    DrawCheckService,
    DynamiteCondition,
    JailCondition,
)
from bang_game_engine.effects.effect import (
    EffectStackEntry,
    EffectState,
    ResponseWindow,
)
from bang_game_engine.effects.effect_stack import EffectStack
from bang_game_engine.effects.registry import EffectRegistry
from bang_game_engine.shared.identifiers import new_card_id, new_player_id


def _make_card(suit: Suit = Suit.HEARTS, rank: Rank = Rank.ACE) -> Card:
    return Card(
        id=new_card_id(),
        card_type="test",
        face=CardFace(suit=suit, rank=rank),
        color=CardColor.BROWN,
    )


class TestEffectStack:
    def test_empty_stack(self):
        stack = EffectStack()
        assert stack.is_empty
        assert stack.depth == 0
        assert stack.peek() is None

    def test_push_pop(self):
        stack = EffectStack()
        entry = EffectStackEntry(
            handler=None,
            context=None,
            state=EffectState.PENDING,
        )
        stack.push(entry)
        assert not stack.is_empty
        assert stack.depth == 1
        popped = stack.pop()
        assert popped is entry
        assert stack.is_empty

    def test_lifo_order(self):
        stack = EffectStack()
        e1 = EffectStackEntry(handler=None, context=None, state=EffectState.PENDING)
        e2 = EffectStackEntry(handler=None, context=None, state=EffectState.RESOLVING)
        stack.push(e1)
        stack.push(e2)
        assert stack.peek().state == EffectState.RESOLVING
        stack.pop()
        assert stack.peek().state == EffectState.PENDING

    def test_pop_empty_raises(self):
        stack = EffectStack()
        with pytest.raises(IndexError):
            stack.pop()

    def test_current_response_window(self):
        stack = EffectStack()
        rw = ResponseWindow(
            responding_player_id=new_player_id(),
            valid_response_types=["missed"],
            prompt="test",
        )
        entry = EffectStackEntry(
            handler=None,
            context=None,
            state=EffectState.AWAITING_RESPONSE,
            response_window=rw,
        )
        stack.push(entry)
        assert stack.current_response_window() is rw

    def test_clear(self):
        stack = EffectStack()
        stack.push(EffectStackEntry(handler=None, context=None, state=EffectState.PENDING))
        stack.push(EffectStackEntry(handler=None, context=None, state=EffectState.PENDING))
        stack.clear()
        assert stack.is_empty


class TestEffectRegistry:
    def test_register_and_get(self):
        reg = EffectRegistry()

        class FakeHandler:
            card_type = "bang"

        reg.register("bang", lambda: FakeHandler())
        handler = reg.get_handler("bang")
        assert isinstance(handler, FakeHandler)

    def test_has_handler(self):
        reg = EffectRegistry()
        assert not reg.has_handler("bang")
        reg.register("bang", lambda: None)
        assert reg.has_handler("bang")


class TestDrawCheck:
    def _make_deck_with_top(self, suit: Suit, rank: Rank) -> Deck:
        top_card = _make_card(suit, rank)
        bottom = [_make_card() for _ in range(5)]
        return Deck(draw_pile=bottom + [top_card], rng=random.Random(42))

    def test_barrel_condition_hearts_passes(self):
        cond = BarrelCondition()
        face = CardFace(Suit.HEARTS, Rank.FIVE)
        assert cond.evaluate(face) is True

    def test_barrel_condition_spades_fails(self):
        cond = BarrelCondition()
        face = CardFace(Suit.SPADES, Rank.FIVE)
        assert cond.evaluate(face) is False

    def test_jail_condition_hearts_passes(self):
        cond = JailCondition()
        face = CardFace(Suit.HEARTS, Rank.KING)
        assert cond.evaluate(face) is True

    def test_jail_condition_clubs_fails(self):
        cond = JailCondition()
        face = CardFace(Suit.CLUBS, Rank.KING)
        assert cond.evaluate(face) is False

    def test_dynamite_condition_spades_2_9_passes(self):
        cond = DynamiteCondition()
        assert cond.evaluate(CardFace(Suit.SPADES, Rank.TWO)) is True
        assert cond.evaluate(CardFace(Suit.SPADES, Rank.NINE)) is True

    def test_dynamite_condition_spades_10_fails(self):
        cond = DynamiteCondition()
        assert cond.evaluate(CardFace(Suit.SPADES, Rank.TEN)) is False

    def test_dynamite_condition_hearts_fails(self):
        cond = DynamiteCondition()
        assert cond.evaluate(CardFace(Suit.HEARTS, Rank.FIVE)) is False

    def test_perform_check_with_barrel(self):
        svc = DrawCheckService()
        deck = self._make_deck_with_top(Suit.HEARTS, Rank.SEVEN)
        result = svc.perform_check(deck, BarrelCondition())
        assert result.passed is True
        assert result.card_drawn.face.suit == Suit.HEARTS

    def test_perform_check_barrel_fails(self):
        svc = DrawCheckService()
        deck = self._make_deck_with_top(Suit.CLUBS, Rank.SEVEN)
        result = svc.perform_check(deck, BarrelCondition())
        assert result.passed is False
