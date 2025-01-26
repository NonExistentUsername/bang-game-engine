import pytest

from bang_game_engine.card import Card, CardSuits, CardTypes, CardValues, ModifierCard
from bang_game_engine.character import Character, CharacterFactory, CharacterTypes
from bang_game_engine.player import Player, Table
from bang_game_engine.role import Role, RoleTypes


class TestTable:
    def test_cannot_place_same_card_twice(self):
        table = Table()

        card1 = ModifierCard(
            suit=CardSuits.HEART,
            value=CardValues.ACE,
            card_type=CardTypes.MUSTANG,
        )
        card2 = ModifierCard(
            suit=CardSuits.CLUB,
            value=CardValues.TEN,
            card_type=CardTypes.MUSTANG,
        )

        assert len(table) == 0, "Table should be empty"

        table.add(card1)

        assert len(table) == 1, "Table should have 1 card"

        with pytest.raises(ValueError):
            table.add(card1)

        assert len(table) == 1, "Table should still have 1 card"

        with pytest.raises(ValueError):
            table.add(card2)

        assert len(table) == 1, "Table should still have 1 card"


class TestPlayer:
    def test_cannot_have_more_bullets_than_max_bullets(self):
        character = CharacterFactory.create(CharacterTypes.SUZY_LAFAYETTE)
        role = Role(RoleTypes.OUTLAW)

        with pytest.raises(ValueError):
            Player(
                role=role,
                character=character,
                bullets=character.max_bullets + 1,
            )

        player = Player(role=role, character=character, bullets=character.max_bullets)

        assert player.bullets == character.max_bullets, "Player should have max bullets"

        player.heal(1)

        assert (
            player.bullets == character.max_bullets
        ), "Player should still have max bullets after healing"

    def test_player_is_dead_when_bullets_is_zero(self):
        character = CharacterFactory.create(CharacterTypes.SUZY_LAFAYETTE)
        role = Role(RoleTypes.OUTLAW)

        player = Player(role=role, character=character, bullets=1)

        assert player.is_alive, "Player should be alive"

        player.damage(1)

        assert not player.is_alive, "Player should be dead"

    def test_sheriff_have_max_bullets_greater_by_one(self):
        character = CharacterFactory.create(CharacterTypes.SUZY_LAFAYETTE)
        role = Role(RoleTypes.SHERIFF)

        player = Player(role=role, character=character)

        assert (
            player.max_bullets == character.max_bullets + 1
        ), "Sheriff should have max bullets + 1"
        assert (
            player.bullets == character.max_bullets + 1
        ), "Sheriff should have max bullets + 1"

        player.heal(1)

        assert (
            player.bullets == character.max_bullets + 1
        ), "Sheriff should still have max bullets + 1 after healing"
