"""Base game card definitions: all 80 cards with their suit/rank assignments."""

from __future__ import annotations

from bang_game_engine.cards.card import Card
from bang_game_engine.cards.card_color import CardColor
from bang_game_engine.cards.card_face import CardFace
from bang_game_engine.cards.card_type import (
    CardTypeMetadata,
    RangeType,
    TargetType,
)
from bang_game_engine.cards.rank import Rank
from bang_game_engine.cards.suit import Suit
from bang_game_engine.shared.identifiers import new_card_id


# --- Card Type Metadata ---

BASE_CARD_TYPES: list[CardTypeMetadata] = [
    # Brown cards (instant)
    CardTypeMetadata(
        key="bang",
        name="Bang!",
        color="brown",
        target_type=TargetType.SINGLE_PLAYER,
        range_type=RangeType.WEAPON_RANGE,
    ),
    CardTypeMetadata(
        key="missed",
        name="Missed!",
        color="brown",
        target_type=TargetType.NONE,
        range_type=RangeType.SELF,
    ),
    CardTypeMetadata(
        key="beer",
        name="Beer",
        color="brown",
        target_type=TargetType.NONE,
        range_type=RangeType.SELF,
    ),
    CardTypeMetadata(
        key="saloon",
        name="Saloon",
        color="brown",
        target_type=TargetType.NONE,
        range_type=RangeType.SELF,
    ),
    CardTypeMetadata(
        key="stagecoach",
        name="Stagecoach",
        color="brown",
        target_type=TargetType.NONE,
        range_type=RangeType.SELF,
    ),
    CardTypeMetadata(
        key="wells_fargo",
        name="Wells Fargo",
        color="brown",
        target_type=TargetType.NONE,
        range_type=RangeType.SELF,
    ),
    CardTypeMetadata(
        key="panic",
        name="Panic!",
        color="brown",
        target_type=TargetType.SINGLE_PLAYER,
        range_type=RangeType.DISTANCE_1,
    ),
    CardTypeMetadata(
        key="cat_balou",
        name="Cat Balou",
        color="brown",
        target_type=TargetType.ANY_PLAYER,
        range_type=RangeType.UNLIMITED,
    ),
    CardTypeMetadata(
        key="indians",
        name="Indians!",
        color="brown",
        target_type=TargetType.ALL_OTHERS,
        range_type=RangeType.UNLIMITED,
    ),
    CardTypeMetadata(
        key="gatling",
        name="Gatling",
        color="brown",
        target_type=TargetType.ALL_OTHERS,
        range_type=RangeType.UNLIMITED,
    ),
    CardTypeMetadata(
        key="duel",
        name="Duel",
        color="brown",
        target_type=TargetType.SINGLE_PLAYER,
        range_type=RangeType.UNLIMITED,
    ),
    CardTypeMetadata(
        key="general_store",
        name="General Store",
        color="brown",
        target_type=TargetType.CHOICE,
        range_type=RangeType.UNLIMITED,
    ),
    # Blue cards (persistent)
    CardTypeMetadata(
        key="barrel",
        name="Barrel",
        color="blue",
        target_type=TargetType.SELF,
        range_type=RangeType.SELF,
    ),
    CardTypeMetadata(
        key="mustang",
        name="Mustang",
        color="blue",
        target_type=TargetType.SELF,
        range_type=RangeType.SELF,
    ),
    CardTypeMetadata(
        key="scope",
        name="Scope",
        color="blue",
        target_type=TargetType.SELF,
        range_type=RangeType.SELF,
    ),
    CardTypeMetadata(
        key="jail",
        name="Jail",
        color="blue",
        target_type=TargetType.SINGLE_PLAYER,
        range_type=RangeType.UNLIMITED,
    ),
    CardTypeMetadata(
        key="dynamite",
        name="Dynamite",
        color="blue",
        target_type=TargetType.SELF,
        range_type=RangeType.SELF,
    ),
    # Weapons (blue, equipment)
    CardTypeMetadata(
        key="volcanic",
        name="Volcanic",
        color="blue",
        target_type=TargetType.SELF,
        range_type=RangeType.SELF,
        is_weapon=True,
        weapon_range=1,
        unlimited_bangs=True,
    ),
    CardTypeMetadata(
        key="schofield",
        name="Schofield",
        color="blue",
        target_type=TargetType.SELF,
        range_type=RangeType.SELF,
        is_weapon=True,
        weapon_range=2,
    ),
    CardTypeMetadata(
        key="remington",
        name="Remington",
        color="blue",
        target_type=TargetType.SELF,
        range_type=RangeType.SELF,
        is_weapon=True,
        weapon_range=3,
    ),
    CardTypeMetadata(
        key="rev_carabine",
        name="Rev. Carabine",
        color="blue",
        target_type=TargetType.SELF,
        range_type=RangeType.SELF,
        is_weapon=True,
        weapon_range=4,
    ),
    CardTypeMetadata(
        key="winchester",
        name="Winchester",
        color="blue",
        target_type=TargetType.SELF,
        range_type=RangeType.SELF,
        is_weapon=True,
        weapon_range=5,
    ),
]


# --- Card Color Mapping ---

_COLOR_MAP: dict[str, CardColor] = {
    "brown": CardColor.BROWN,
    "blue": CardColor.BLUE,
    "green": CardColor.GREEN,
    "orange": CardColor.ORANGE,
}


def _card(card_type: str, suit: Suit, rank: Rank) -> Card:
    """Helper to create a card with the right color from type metadata."""
    color = CardColor.BROWN  # default
    for meta in BASE_CARD_TYPES:
        if meta.key == card_type:
            color = _COLOR_MAP.get(meta.color, CardColor.BROWN)
            break
    return Card(
        id=new_card_id(),
        card_type=card_type,
        face=CardFace(suit=suit, rank=rank),
        color=color,
    )


# --- The 80-card base deck ---
# Card distributions follow the official Bang! base game rulebook.
# Format: (card_type, suit, rank)

_BASE_DECK_SPEC: list[tuple[str, Suit, Rank]] = [
    # === Bang! (25 cards) ===
    ("bang", Suit.HEARTS, Rank.ACE),
    ("bang", Suit.HEARTS, Rank.QUEEN),
    ("bang", Suit.HEARTS, Rank.KING),
    ("bang", Suit.DIAMONDS, Rank.TWO),
    ("bang", Suit.DIAMONDS, Rank.THREE),
    ("bang", Suit.DIAMONDS, Rank.FOUR),
    ("bang", Suit.DIAMONDS, Rank.FIVE),
    ("bang", Suit.DIAMONDS, Rank.SIX),
    ("bang", Suit.DIAMONDS, Rank.SEVEN),
    ("bang", Suit.DIAMONDS, Rank.EIGHT),
    ("bang", Suit.DIAMONDS, Rank.NINE),
    ("bang", Suit.DIAMONDS, Rank.TEN),
    ("bang", Suit.DIAMONDS, Rank.JACK),
    ("bang", Suit.DIAMONDS, Rank.QUEEN),
    ("bang", Suit.DIAMONDS, Rank.ACE),
    ("bang", Suit.CLUBS, Rank.TWO),
    ("bang", Suit.CLUBS, Rank.THREE),
    ("bang", Suit.CLUBS, Rank.FOUR),
    ("bang", Suit.CLUBS, Rank.FIVE),
    ("bang", Suit.CLUBS, Rank.SIX),
    ("bang", Suit.CLUBS, Rank.SEVEN),
    ("bang", Suit.CLUBS, Rank.EIGHT),
    ("bang", Suit.CLUBS, Rank.NINE),
    ("bang", Suit.SPADES, Rank.ACE),
    ("bang", Suit.SPADES, Rank.QUEEN),
    # === Missed! (12 cards) ===
    ("missed", Suit.CLUBS, Rank.TEN),
    ("missed", Suit.CLUBS, Rank.JACK),
    ("missed", Suit.CLUBS, Rank.QUEEN),
    ("missed", Suit.CLUBS, Rank.KING),
    ("missed", Suit.CLUBS, Rank.ACE),
    ("missed", Suit.SPADES, Rank.TWO),
    ("missed", Suit.SPADES, Rank.THREE),
    ("missed", Suit.SPADES, Rank.FOUR),
    ("missed", Suit.SPADES, Rank.FIVE),
    ("missed", Suit.SPADES, Rank.SIX),
    ("missed", Suit.SPADES, Rank.SEVEN),
    ("missed", Suit.SPADES, Rank.EIGHT),
    # === Beer (6 cards) ===
    ("beer", Suit.HEARTS, Rank.SIX),
    ("beer", Suit.HEARTS, Rank.SEVEN),
    ("beer", Suit.HEARTS, Rank.EIGHT),
    ("beer", Suit.HEARTS, Rank.NINE),
    ("beer", Suit.HEARTS, Rank.TEN),
    ("beer", Suit.HEARTS, Rank.JACK),
    # === Saloon (1 card) ===
    ("saloon", Suit.HEARTS, Rank.FIVE),
    # === Stagecoach (2 cards) ===
    ("stagecoach", Suit.SPADES, Rank.NINE),
    ("stagecoach", Suit.SPADES, Rank.NINE),
    # === Wells Fargo (1 card) ===
    ("wells_fargo", Suit.HEARTS, Rank.THREE),
    # === Panic! (4 cards) ===
    ("panic", Suit.HEARTS, Rank.ACE),
    ("panic", Suit.HEARTS, Rank.QUEEN),
    ("panic", Suit.DIAMONDS, Rank.EIGHT),
    ("panic", Suit.HEARTS, Rank.JACK),
    # === Cat Balou (4 cards) ===
    ("cat_balou", Suit.DIAMONDS, Rank.NINE),
    ("cat_balou", Suit.DIAMONDS, Rank.TEN),
    ("cat_balou", Suit.DIAMONDS, Rank.JACK),
    ("cat_balou", Suit.HEARTS, Rank.KING),
    # === Indians! (2 cards) ===
    ("indians", Suit.DIAMONDS, Rank.ACE),
    ("indians", Suit.DIAMONDS, Rank.KING),
    # === Gatling (1 card) ===
    ("gatling", Suit.HEARTS, Rank.TEN),
    # === Duel (3 cards) ===
    ("duel", Suit.CLUBS, Rank.EIGHT),
    ("duel", Suit.SPADES, Rank.JACK),
    ("duel", Suit.DIAMONDS, Rank.QUEEN),
    # === General Store (2 cards) ===
    ("general_store", Suit.CLUBS, Rank.NINE),
    ("general_store", Suit.SPADES, Rank.QUEEN),
    # === Barrel (2 cards) ===
    ("barrel", Suit.SPADES, Rank.QUEEN),
    ("barrel", Suit.SPADES, Rank.KING),
    # === Mustang (2 cards) ===
    ("mustang", Suit.HEARTS, Rank.EIGHT),
    ("mustang", Suit.HEARTS, Rank.NINE),
    # === Scope (1 card) ===
    ("scope", Suit.SPADES, Rank.ACE),
    # === Jail (3 cards) ===
    ("jail", Suit.SPADES, Rank.TEN),
    ("jail", Suit.SPADES, Rank.JACK),
    ("jail", Suit.HEARTS, Rank.FOUR),
    # === Dynamite (1 card) ===
    ("dynamite", Suit.HEARTS, Rank.TWO),
    # === Volcanic (2 cards) ===
    ("volcanic", Suit.CLUBS, Rank.TEN),
    ("volcanic", Suit.SPADES, Rank.TEN),
    # === Schofield (3 cards) ===
    ("schofield", Suit.CLUBS, Rank.JACK),
    ("schofield", Suit.CLUBS, Rank.QUEEN),
    ("schofield", Suit.SPADES, Rank.KING),
    # === Remington (1 card) ===
    ("remington", Suit.CLUBS, Rank.KING),
    # === Rev. Carabine (1 card) ===
    ("rev_carabine", Suit.CLUBS, Rank.ACE),
    # === Winchester (1 card) ===
    ("winchester", Suit.SPADES, Rank.EIGHT),
]


def create_base_deck_cards() -> list[Card]:
    """Create all 80 base game cards as Card instances."""
    return [_card(ct, suit, rank) for ct, suit, rank in _BASE_DECK_SPEC]


def get_base_deck_spec() -> list[tuple[str, str, int]]:
    """Get the deck spec as (card_type, suit_value, rank_value) tuples for ContentPack."""
    return [
        (ct, suit.value, rank.value) for ct, suit, rank in _BASE_DECK_SPEC
    ]
