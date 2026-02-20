"""Content pack: what an expansion contributes to the game."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from bang_game_engine.cards.card_type import CardTypeMetadata
from bang_game_engine.effects.effect import EffectHandler
from bang_game_engine.players.character import Character


@dataclass
class ContentPack:
    """What an expansion adds to the game."""

    # Card definitions
    card_type_metadata: list[CardTypeMetadata] = field(default_factory=list)

    # Cards to add to the deck (card_type, suit, rank tuples)
    deck_cards: list[tuple[str, str, int]] = field(default_factory=list)

    # Characters
    characters: list[Character] = field(default_factory=list)

    # Effect handlers (card_type -> factory)
    effect_handlers: dict[str, Callable[[], EffectHandler]] = field(
        default_factory=dict
    )

    # Role distributions for different player counts
    role_distributions: dict[int, list[str]] = field(default_factory=dict)

    # Any extra configuration
    config: dict[str, Any] = field(default_factory=dict)
