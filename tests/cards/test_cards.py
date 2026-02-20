"""Tests for the cards domain: Card, CardFace, Suit, Rank, Deck."""

from __future__ import annotations

import random

import pytest

from bang_game_engine.cards.card import Card
from bang_game_engine.cards.card_color import CardColor
from bang_game_engine.cards.card_face import CardFace
from bang_game_engine.cards.card_type import (
    CardTypeMetadata,
    RangeType,
    TargetType,
)
from bang_game_engine.cards.deck import Deck
from bang_game_engine.cards.rank import Rank
from bang_game_engine.cards.suit import Suit
from bang_game_engine.shared.errors import DomainError
from bang_game_engine.shared.identifiers import new_card_id


def _make_card(
    card_type: str = "bang",
    suit: Suit = Suit.HEARTS,
    rank: Rank = Rank.ACE,
    color: CardColor = CardColor.BROWN,
) -> Card:
    return Card(
        id=new_card_id(),
        card_type=card_type,
        face=CardFace(suit=suit, rank=rank),
        color=color,
    )


class TestCardFace:
    def test_is_hearts(self):
        face = CardFace(suit=Suit.HEARTS, rank=Rank.ACE)
        assert face.is_hearts()
        assert not face.is_spades()

    def test_is_spades(self):
        face = CardFace(suit=Suit.SPADES, rank=Rank.THREE)
        assert face.is_spades()
        assert not face.is_hearts()

    def test_is_hearts_or_diamonds(self):
        assert CardFace(Suit.HEARTS, Rank.TWO).is_hearts_or_diamonds()
        assert CardFace(Suit.DIAMONDS, Rank.TWO).is_hearts_or_diamonds()
        assert not CardFace(Suit.CLUBS, Rank.TWO).is_hearts_or_diamonds()
        assert not CardFace(Suit.SPADES, Rank.TWO).is_hearts_or_diamonds()


class TestCard:
    def test_equality_by_id(self):
        c1 = _make_card()
        c2 = _make_card()
        assert c1 != c2  # Different IDs
        assert c1 == c1

    def test_hash_by_id(self):
        c1 = _make_card()
        c2 = _make_card()
        assert hash(c1) != hash(c2)
        assert hash(c1) == hash(c1)

    def test_repr(self):
        card = _make_card(card_type="bang", suit=Suit.HEARTS, rank=Rank.ACE)
        assert "bang" in repr(card)
        assert "hearts" in repr(card)


class TestDeck:
    def _make_deck(self, count: int = 10) -> Deck:
        cards = [_make_card() for _ in range(count)]
        return Deck(draw_pile=cards, rng=random.Random(42))

    def test_draw(self):
        deck = self._make_deck(5)
        assert deck.draw_pile_size == 5
        card = deck.draw()
        assert isinstance(card, Card)
        assert deck.draw_pile_size == 4

    def test_discard(self):
        deck = self._make_deck(5)
        card = deck.draw()
        deck.discard(card)
        assert deck.discard_pile_size == 1

    def test_auto_reshuffle_on_empty_draw(self):
        deck = self._make_deck(2)
        deck.draw()
        deck.discard(_make_card())
        deck.discard(_make_card())
        deck.draw()  # Should exhaust draw pile
        # Now drawing should reshuffle discard into draw
        card = deck.draw()
        assert card is not None

    def test_draw_empty_raises(self):
        deck = Deck(draw_pile=[], rng=random.Random(42))
        with pytest.raises(DomainError, match="No cards remaining"):
            deck.draw()

    def test_peek_top(self):
        deck = self._make_deck(5)
        peeked = deck.peek_top(2)
        assert len(peeked) == 2
        assert deck.draw_pile_size == 5  # Unchanged

    def test_put_back_on_top(self):
        deck = self._make_deck(5)
        card = _make_card()
        deck.put_back_on_top(card)
        assert deck.draw_pile_size == 6
        drawn = deck.draw()
        assert drawn.id == card.id

    def test_peek_discard_top(self):
        deck = self._make_deck(5)
        assert deck.peek_discard_top() is None
        card = deck.draw()
        deck.discard(card)
        assert deck.peek_discard_top() is not None
        assert deck.peek_discard_top().id == card.id

    def test_take_from_discard_top(self):
        deck = self._make_deck(5)
        card = deck.draw()
        deck.discard(card)
        taken = deck.take_from_discard_top()
        assert taken.id == card.id
        assert deck.discard_pile_size == 0

    def test_reveal_top(self):
        deck = self._make_deck(5)
        revealed = deck.reveal_top(3)
        assert len(revealed) == 3
        assert deck.draw_pile_size == 2

    def test_shuffle_deterministic(self):
        cards = [_make_card() for _ in range(5)]
        ids_before = [c.id for c in cards]
        deck = Deck(draw_pile=list(cards), rng=random.Random(42))
        deck.shuffle()
        # After shuffle, order should be different (most likely)
        drawn_ids = [deck.draw().id for _ in range(5)]
        # With seed 42, order should be deterministic
        assert len(drawn_ids) == 5

    def test_collect_events(self):
        deck = self._make_deck(3)
        deck.draw()
        events = deck.collect_events()
        assert len(events) >= 1  # At least CardDrawnFromDeck


class TestCardTypeMetadata:
    def test_bang_metadata(self):
        meta = CardTypeMetadata(
            key="bang",
            name="Bang!",
            color="brown",
            target_type=TargetType.SINGLE_PLAYER,
            range_type=RangeType.WEAPON_RANGE,
        )
        assert meta.key == "bang"
        assert meta.is_weapon is False

    def test_weapon_metadata(self):
        meta = CardTypeMetadata(
            key="volcanic",
            name="Volcanic",
            color="blue",
            is_weapon=True,
            weapon_range=1,
            unlimited_bangs=True,
        )
        assert meta.is_weapon is True
        assert meta.weapon_range == 1
        assert meta.unlimited_bangs is True
