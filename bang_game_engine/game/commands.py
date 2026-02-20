from __future__ import annotations

from dataclasses import dataclass, field

from bang_game_engine.shared.commands import Command
from bang_game_engine.shared.types import CardId, PlayerId


@dataclass(frozen=True)
class PlayCardCommand(Command):
    """Play a card from hand during Play phase."""

    card_id: CardId
    target_player_id: PlayerId | None = None


@dataclass(frozen=True)
class RespondToEffectCommand(Command):
    """Respond to an effect (play Missed!, Bang! for duel/Indians, or pass)."""

    card_id: CardId | None = None  # None = decline/pass


@dataclass(frozen=True)
class EndPhaseCommand(Command):
    """Player explicitly ends current phase."""

    pass


@dataclass(frozen=True)
class DiscardCardCommand(Command):
    """Discard a card during discard phase."""

    card_id: CardId


@dataclass(frozen=True)
class DrawPhaseChoiceCommand(Command):
    """For characters with draw phase abilities."""

    choice: str  # "deck", "player_hand", "discard_pile"
    target_player_id: PlayerId | None = None


@dataclass(frozen=True)
class KitCarlsonChoiceCommand(Command):
    """Kit Carlson: choose which card to put back on deck."""

    card_id_to_return: CardId


@dataclass(frozen=True)
class GeneralStorePickCommand(Command):
    """Pick a card from General Store reveal."""

    card_id: CardId


@dataclass(frozen=True)
class SidKetchumHealCommand(Command):
    """Sid Ketchum: discard 2 cards to heal 1 HP."""

    card_id_1: CardId
    card_id_2: CardId


@dataclass(frozen=True)
class PlayBeerWhenDyingCommand(Command):
    """Out-of-turn Beer play when about to be eliminated."""

    card_id: CardId
