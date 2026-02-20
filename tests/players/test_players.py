"""Tests for the player domain: Player, Role, Character, Seating, Distance."""

from __future__ import annotations

import pytest

from bang_game_engine.cards.card import Card
from bang_game_engine.cards.card_color import CardColor
from bang_game_engine.cards.card_face import CardFace
from bang_game_engine.cards.rank import Rank
from bang_game_engine.cards.suit import Suit
from bang_game_engine.players.character import Character
from bang_game_engine.players.distance_service import DistanceService
from bang_game_engine.players.events import (
    PlayerAtZeroHP,
    PlayerDamaged,
    PlayerEliminated,
    PlayerHealed,
)
from bang_game_engine.players.player import Player
from bang_game_engine.players.role import Role
from bang_game_engine.players.seating import Seating
from bang_game_engine.shared.errors import DomainError
from bang_game_engine.shared.identifiers import new_card_id, new_player_id


def _make_character(name: str = "Test", base_hp: int = 4) -> Character:
    return Character(character_type=name.lower(), name=name, base_hp=base_hp)


def _make_player(
    role: Role = Role.OUTLAW, base_hp: int = 4
) -> Player:
    return Player(
        player_id=new_player_id(),
        role=role,
        character=_make_character(base_hp=base_hp),
    )


def _make_card(
    card_type: str = "bang",
    color: CardColor = CardColor.BROWN,
) -> Card:
    return Card(
        id=new_card_id(),
        card_type=card_type,
        face=CardFace(suit=Suit.HEARTS, rank=Rank.ACE),
        color=color,
    )


class TestRole:
    def test_sheriff_hp_bonus(self):
        assert Role.SHERIFF.hp_bonus == 1

    def test_other_roles_no_bonus(self):
        assert Role.DEPUTY.hp_bonus == 0
        assert Role.OUTLAW.hp_bonus == 0
        assert Role.RENEGADE.hp_bonus == 0

    def test_only_sheriff_is_public(self):
        assert Role.SHERIFF.is_public is True
        assert Role.DEPUTY.is_public is False
        assert Role.OUTLAW.is_public is False
        assert Role.RENEGADE.is_public is False


class TestPlayer:
    def test_initial_state(self):
        player = _make_player(role=Role.SHERIFF, base_hp=4)
        assert player.is_alive
        assert player.max_hp == 5  # 4 + 1 sheriff bonus
        assert player.hp == 5
        assert player.hand_size == 0
        assert player.weapon_range == 1

    def test_take_damage(self):
        player = _make_player()
        events = player.take_damage(2)
        assert player.hp == 2
        assert any(isinstance(e, PlayerDamaged) for e in events)

    def test_take_lethal_damage(self):
        player = _make_player(base_hp=3)
        events = player.take_damage(3)
        assert player.hp == 0
        assert any(isinstance(e, PlayerAtZeroHP) for e in events)

    def test_heal(self):
        player = _make_player()
        player.take_damage(2)
        events = player.heal(1)
        assert player.hp == 3
        assert any(isinstance(e, PlayerHealed) for e in events)

    def test_heal_does_not_exceed_max(self):
        player = _make_player()
        events = player.heal(10)
        assert player.hp == player.max_hp
        assert len(events) == 0  # No change

    def test_eliminate(self):
        player = _make_player(role=Role.OUTLAW)
        events = player.eliminate()
        assert not player.is_alive
        assert any(isinstance(e, PlayerEliminated) for e in events)
        assert events[0].role == Role.OUTLAW

    def test_add_and_remove_from_hand(self):
        player = _make_player()
        card = _make_card()
        player.add_to_hand(card)
        assert player.hand_size == 1
        removed = player.remove_from_hand(card.id)
        assert removed.id == card.id
        assert player.hand_size == 0

    def test_remove_nonexistent_card_raises(self):
        player = _make_player()
        with pytest.raises(DomainError, match="not in hand"):
            player.remove_from_hand(new_card_id())

    def test_play_to_table_blue_card(self):
        player = _make_player()
        barrel = _make_card("barrel", CardColor.BLUE)
        player.play_to_table(barrel)
        assert player.has_card_type_on_table("barrel")

    def test_play_duplicate_blue_card_raises(self):
        player = _make_player()
        barrel1 = _make_card("barrel", CardColor.BLUE)
        barrel2 = _make_card("barrel", CardColor.BLUE)
        player.play_to_table(barrel1)
        with pytest.raises(Exception, match="Already have"):
            player.play_to_table(barrel2)

    def test_weapon_displaces_old_weapon(self):
        player = _make_player()
        schofield = _make_card("schofield", CardColor.BLUE)
        winchester = _make_card("winchester", CardColor.BLUE)
        displaced = player.play_to_table(schofield)
        assert displaced is None
        assert player.weapon_range == 2
        displaced = player.play_to_table(winchester)
        assert displaced.id == schofield.id
        assert player.weapon_range == 5

    def test_hand_limit_equals_hp(self):
        player = _make_player()
        assert player.hand_limit == player.hp
        player.take_damage(2)
        assert player.hand_limit == player.hp

    def test_discard_all(self):
        player = _make_player()
        player.add_to_hand(_make_card())
        player.add_to_hand(_make_card())
        barrel = _make_card("barrel", CardColor.BLUE)
        player.play_to_table(barrel)
        weapon = _make_card("schofield", CardColor.BLUE)
        player.play_to_table(weapon)

        discarded = player.discard_all()
        assert len(discarded) == 4  # 2 hand + 1 table + 1 weapon
        assert player.hand_size == 0
        assert player.weapon is None

    def test_find_cards_in_hand_by_type(self):
        player = _make_player()
        player.add_to_hand(_make_card("bang"))
        player.add_to_hand(_make_card("missed"))
        player.add_to_hand(_make_card("bang"))
        bangs = player.find_cards_in_hand_by_type("bang")
        assert len(bangs) == 2


class TestCharacter:
    def test_character_creation(self):
        char = _make_character("Bart Cassidy", 4)
        assert char.name == "Bart Cassidy"
        assert char.base_hp == 4

    def test_has_ability(self):
        from bang_game_engine.expansions.base.characters import (
            BartCassidyAbility,
        )
        char = Character(
            character_type="bart_cassidy",
            name="Bart Cassidy",
            base_hp=4,
            abilities=[BartCassidyAbility()],
        )
        assert char.has_ability("bart_cassidy")
        assert not char.has_ability("nonexistent")


class TestSeating:
    def _make_seating(self, count: int = 5) -> tuple[Seating, list]:
        pids = [new_player_id() for _ in range(count)]
        return Seating(pids), pids

    def test_minimum_players(self):
        with pytest.raises(DomainError):
            Seating([new_player_id()])

    def test_alive_players_in_order(self):
        seating, pids = self._make_seating(4)
        assert seating.alive_players_in_order() == pids

    def test_next_alive_after(self):
        seating, pids = self._make_seating(4)
        assert seating.next_alive_after(pids[0]) == pids[1]
        assert seating.next_alive_after(pids[3]) == pids[0]  # Wraps

    def test_prev_alive_before(self):
        seating, pids = self._make_seating(4)
        assert seating.prev_alive_before(pids[0]) == pids[3]  # Wraps
        assert seating.prev_alive_before(pids[2]) == pids[1]

    def test_mark_eliminated(self):
        seating, pids = self._make_seating(5)
        seating.mark_eliminated(pids[2])
        alive = seating.alive_players_in_order()
        assert len(alive) == 4
        assert pids[2] not in alive

    def test_next_alive_skips_eliminated(self):
        seating, pids = self._make_seating(5)
        seating.mark_eliminated(pids[1])
        assert seating.next_alive_after(pids[0]) == pids[2]

    def test_raw_distance(self):
        seating, pids = self._make_seating(5)
        # In a circle of 5: distance(0,1)=1, distance(0,2)=2, distance(0,3)=2
        assert seating.raw_distance(pids[0], pids[1]) == 1
        assert seating.raw_distance(pids[0], pids[2]) == 2
        assert seating.raw_distance(pids[0], pids[3]) == 2
        assert seating.raw_distance(pids[0], pids[4]) == 1

    def test_raw_distance_with_eliminated(self):
        seating, pids = self._make_seating(5)
        seating.mark_eliminated(pids[1])
        # Now 4 alive: 0, 2, 3, 4. Distance(0, 2) = 1
        assert seating.raw_distance(pids[0], pids[2]) == 1

    def test_other_alive_clockwise(self):
        seating, pids = self._make_seating(4)
        others = seating.other_alive_players_clockwise(pids[0])
        assert others == [pids[1], pids[2], pids[3]]


class TestDistanceService:
    def _setup(self):
        pids = [new_player_id() for _ in range(5)]
        seating = Seating(pids)
        players = {}
        for i, pid in enumerate(pids):
            players[pid] = Player(
                player_id=pid,
                role=Role.SHERIFF if i == 0 else Role.OUTLAW,
                character=_make_character(base_hp=4),
            )
        return seating, players, pids

    def test_basic_distance(self):
        seating, players, pids = self._setup()
        svc = DistanceService()
        d = svc.calculate(seating, players[pids[0]], players[pids[1]])
        assert d == 1

    def test_mustang_increases_distance_for_target(self):
        seating, players, pids = self._setup()
        mustang = _make_card("mustang", CardColor.BLUE)
        players[pids[1]].play_to_table(mustang)
        svc = DistanceService()
        d = svc.calculate(seating, players[pids[0]], players[pids[1]])
        assert d == 2  # 1 base + 1 mustang

    def test_scope_decreases_distance_for_attacker(self):
        seating, players, pids = self._setup()
        scope = _make_card("scope", CardColor.BLUE)
        players[pids[0]].play_to_table(scope)
        svc = DistanceService()
        d = svc.calculate(seating, players[pids[0]], players[pids[2]])
        assert d == 1  # 2 base - 1 scope

    def test_weapon_range_check(self):
        seating, players, pids = self._setup()
        svc = DistanceService()
        # Default weapon range is 1
        assert svc.is_in_weapon_range(seating, players[pids[0]], players[pids[1]])
        assert not svc.is_in_weapon_range(seating, players[pids[0]], players[pids[2]])

    def test_weapon_range_with_schofield(self):
        seating, players, pids = self._setup()
        schofield = _make_card("schofield", CardColor.BLUE)
        players[pids[0]].play_to_table(schofield)
        svc = DistanceService()
        assert svc.is_in_weapon_range(seating, players[pids[0]], players[pids[2]])
