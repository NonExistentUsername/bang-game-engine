from __future__ import annotations

from dataclasses import dataclass, field

from bang_game_engine.players.role import Role
from bang_game_engine.shared.events import DomainEvent
from bang_game_engine.shared.types import CardId, PlayerId


@dataclass(frozen=True)
class PlayerDamaged(DomainEvent):
    player_id: PlayerId
    amount: int
    new_hp: int
    source_player_id: PlayerId | None = None


@dataclass(frozen=True)
class PlayerAtZeroHP(DomainEvent):
    """Player hit 0 HP - Beer saving window opens before elimination."""

    player_id: PlayerId


@dataclass(frozen=True)
class PlayerHealed(DomainEvent):
    player_id: PlayerId
    amount: int
    new_hp: int


@dataclass(frozen=True)
class PlayerEliminated(DomainEvent):
    player_id: PlayerId
    role: Role


@dataclass(frozen=True)
class CardAddedToHand(DomainEvent):
    player_id: PlayerId
    card_id: CardId


@dataclass(frozen=True)
class CardRemovedFromHand(DomainEvent):
    player_id: PlayerId
    card_id: CardId


@dataclass(frozen=True)
class CardPlayedToTable(DomainEvent):
    player_id: PlayerId
    card_id: CardId
    card_type: str = ""


@dataclass(frozen=True)
class WeaponEquipped(DomainEvent):
    player_id: PlayerId
    card_id: CardId
    weapon_type: str = ""


@dataclass(frozen=True)
class CardStolen(DomainEvent):
    thief_player_id: PlayerId
    victim_player_id: PlayerId
    card_id: CardId
    from_location: str = ""  # "hand", "table", "eliminated"


@dataclass(frozen=True)
class BountyCollected(DomainEvent):
    killer_player_id: PlayerId
    killed_player_id: PlayerId
    cards_drawn: int


@dataclass(frozen=True)
class AllCardsDiscarded(DomainEvent):
    """Sheriff kills Deputy penalty."""

    player_id: PlayerId
    card_count: int


@dataclass(frozen=True)
class AbilityActivated(DomainEvent):
    player_id: PlayerId
    ability_name: str
    character_type: str = ""
