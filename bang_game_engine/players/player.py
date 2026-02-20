from __future__ import annotations

from typing import TYPE_CHECKING

from bang_game_engine.cards.card import Card
from bang_game_engine.cards.card_color import CardColor
from bang_game_engine.players.character import Character
from bang_game_engine.players.events import (
    CardAddedToHand,
    CardPlayedToTable,
    CardRemovedFromHand,
    PlayerAtZeroHP,
    PlayerDamaged,
    PlayerEliminated,
    PlayerHealed,
    WeaponEquipped,
)
from bang_game_engine.players.role import Role
from bang_game_engine.shared.errors import CardNotPlayableError, DomainError
from bang_game_engine.shared.events import DomainEvent, EventCollector
from bang_game_engine.shared.types import CardId, PlayerId

# Card types that are weapons
WEAPON_TYPES = frozenset(
    {"volcanic", "schofield", "remington", "rev_carabine", "winchester"}
)


class Player(EventCollector):
    """
    Player entity. Identified by PlayerId (UUID), never by index.
    Tracks all mutable state for a player in the game.
    """

    def __init__(
        self,
        player_id: PlayerId,
        role: Role,
        character: Character,
        max_hp: int | None = None,
    ):
        super().__init__()
        self._id = player_id
        self._role = role
        self._character = character
        self._max_hp = max_hp or (character.base_hp + role.hp_bonus)
        self._hp = self._max_hp
        self._hand: list[Card] = []
        self._table: list[Card] = []
        self._weapon: Card | None = None
        self._is_alive = True

        # Expansion state
        self._gold_nuggets: int = 0
        self._load_tokens: int = 0
        self._is_ghost: bool = False

    # --- Properties ---

    @property
    def id(self) -> PlayerId:
        return self._id

    @property
    def role(self) -> Role:
        return self._role

    @property
    def character(self) -> Character:
        return self._character

    @property
    def hp(self) -> int:
        return self._hp

    @property
    def max_hp(self) -> int:
        return self._max_hp

    @property
    def is_alive(self) -> bool:
        return self._is_alive

    @property
    def hand(self) -> list[Card]:
        return list(self._hand)

    @property
    def hand_size(self) -> int:
        return len(self._hand)

    @property
    def table_cards(self) -> list[Card]:
        return list(self._table)

    @property
    def weapon(self) -> Card | None:
        return self._weapon

    @property
    def weapon_range(self) -> int:
        """Range of current weapon. Default Colt .45 = 1."""
        if self._weapon is None:
            return 1
        return self._weapon_range_value

    @property
    def hand_limit(self) -> int:
        """Cards player can keep at end of turn. Default = current HP."""
        return self._hp

    @property
    def gold_nuggets(self) -> int:
        return self._gold_nuggets

    @property
    def is_ghost(self) -> bool:
        return self._is_ghost

    # --- Internal weapon range storage ---

    @property
    def _weapon_range_value(self) -> int:
        if self._weapon is None:
            return 1
        # Weapon ranges by card type
        ranges = {
            "volcanic": 1,
            "schofield": 2,
            "remington": 3,
            "rev_carabine": 4,
            "winchester": 5,
        }
        return ranges.get(self._weapon.card_type, 1)

    # --- Damage & Healing ---

    def take_damage(
        self, amount: int, source_player_id: PlayerId | None = None
    ) -> list[DomainEvent]:
        """Apply damage. Does NOT handle Beer saving -- that is the effect layer."""
        events: list[DomainEvent] = []
        self._hp = max(0, self._hp - amount)
        events.append(
            PlayerDamaged(
                player_id=self._id,
                amount=amount,
                new_hp=self._hp,
                source_player_id=source_player_id,
            )
        )
        if self._hp == 0:
            events.append(PlayerAtZeroHP(player_id=self._id))
        return events

    def heal(self, amount: int) -> list[DomainEvent]:
        old_hp = self._hp
        self._hp = min(self._hp + amount, self._max_hp)
        actual = self._hp - old_hp
        if actual > 0:
            return [
                PlayerHealed(
                    player_id=self._id, amount=actual, new_hp=self._hp
                )
            ]
        return []

    def eliminate(self) -> list[DomainEvent]:
        self._is_alive = False
        return [PlayerEliminated(player_id=self._id, role=self._role)]

    # --- Hand Management ---

    def add_to_hand(self, card: Card) -> None:
        self._hand.append(card)
        self._record_event(CardAddedToHand(player_id=self._id, card_id=card.id))

    def remove_from_hand(self, card_id: CardId) -> Card:
        for i, c in enumerate(self._hand):
            if c.id == card_id:
                card = self._hand.pop(i)
                self._record_event(
                    CardRemovedFromHand(player_id=self._id, card_id=card.id)
                )
                return card
        raise DomainError(f"Card {card_id} not in hand")

    def get_card_from_hand(self, card_id: CardId) -> Card | None:
        for c in self._hand:
            if c.id == card_id:
                return c
        return None

    # --- Table Management ---

    def play_to_table(self, card: Card) -> Card | None:
        """
        Place a blue/green/orange card on table.
        Returns displaced card if any (e.g. old weapon).
        """
        displaced = None
        if card.card_type in WEAPON_TYPES:
            displaced = self._weapon
            self._weapon = card
            self._record_event(
                WeaponEquipped(
                    player_id=self._id,
                    card_id=card.id,
                    weapon_type=card.card_type,
                )
            )
        else:
            for tc in self._table:
                if tc.card_type == card.card_type:
                    raise CardNotPlayableError(
                        f"Already have {card.card_type} in play"
                    )
            self._table.append(card)
            self._record_event(
                CardPlayedToTable(
                    player_id=self._id,
                    card_id=card.id,
                    card_type=card.card_type,
                )
            )
        return displaced

    def remove_from_table(self, card_id: CardId) -> Card:
        for i, c in enumerate(self._table):
            if c.id == card_id:
                return self._table.pop(i)
        if self._weapon and self._weapon.id == card_id:
            w = self._weapon
            self._weapon = None
            return w
        raise DomainError(f"Card {card_id} not on table")

    def get_card_from_table(self, card_id: CardId) -> Card | None:
        for c in self._table:
            if c.id == card_id:
                return c
        if self._weapon and self._weapon.id == card_id:
            return self._weapon
        return None

    def has_card_type_on_table(self, card_type: str) -> bool:
        if self._weapon and self._weapon.card_type == card_type:
            return True
        return any(c.card_type == card_type for c in self._table)

    def has_card_type_in_hand(self, card_type: str) -> bool:
        return any(c.card_type == card_type for c in self._hand)

    def find_cards_in_hand_by_type(self, card_type: str) -> list[Card]:
        return [c for c in self._hand if c.card_type == card_type]

    # --- Bulk Operations ---

    def discard_all(self) -> list[Card]:
        """Sheriff kills deputy penalty: discard everything."""
        cards = list(self._hand) + list(self._table)
        if self._weapon:
            cards.append(self._weapon)
            self._weapon = None
        self._hand.clear()
        self._table.clear()
        return cards

    def get_all_cards(self) -> list[Card]:
        """Get all cards owned by this player (hand + table + weapon)."""
        cards = list(self._hand) + list(self._table)
        if self._weapon:
            cards.append(self._weapon)
        return cards

    # --- Expansion Methods ---

    def add_gold(self, amount: int) -> None:
        self._gold_nuggets += amount

    def spend_gold(self, amount: int) -> None:
        if self._gold_nuggets < amount:
            raise DomainError("Not enough gold nuggets")
        self._gold_nuggets -= amount

    def set_ghost(self, is_ghost: bool) -> None:
        self._is_ghost = is_ghost
