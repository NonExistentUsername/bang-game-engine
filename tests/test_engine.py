import pytest

from bang_game_engine.deck import IDeckFactory
from bang_game_engine.engine import Engine, EngineFactory


class TestEngine:
    def test_damage(self, engine: Engine):

        user_bullets = engine.get_player_bullets(0)

        engine.damage_player(0, 1)

        assert (
            engine.get_player_bullets(0) == user_bullets - 1
        ), "Player bullets should be decreased by 1"

    def test_damage_multiple(self, engine: Engine):
        user_bullets = engine.get_player_bullets(0)

        engine.damage_player(0, 3)

        assert (
            engine.get_player_bullets(0) == user_bullets - 3
        ), "Player bullets should be decreased by 3"

    def test_heal(self, engine: Engine):
        user_bullets = engine.get_player_bullets(0)

        engine.damage_player(0, 3)
        engine.heal_player(0, 1)

        assert (
            engine.get_player_bullets(0) == user_bullets - 2
        ), "Player bullets should be decreased by 2"

    def test_draw_cards(self, engine: Engine):
        previous_user_hand_size = len(engine.get_player_hand(0))

        engine.draw_cards(0, 1)

        assert len(engine.get_player_hand(0)) == previous_user_hand_size + 1

    def test_discard_card(self, engine: Engine):
        previous_user_hand_size = len(engine.get_player_hand(0))

        engine.discard_card(0, 0)

        assert len(engine.get_player_hand(0)) == previous_user_hand_size - 1
