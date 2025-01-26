import pytest

from bang_game_engine.card import Card, CardSuits, CardTypes, CardValues
from bang_game_engine.engine import Engine
from bang_game_engine.state import (
    DropCard,
    GameCycleNode,
    IStateNode,
    PushFullNextNodeDecorator,
    SkipTurn,
    UseCard,
)


class TestStates:
    def test_game_can_bang_and_miss(self, engine: Engine):
        game_cycle_node: PushFullNextNodeDecorator = PushFullNextNodeDecorator(
            GameCycleNode()
        )

        first_player_hand_size = len(engine.players[0].hand)

        game_cycle_node.next(engine)

        assert len(engine.players[0].hand) == first_player_hand_size + 2

        engine.players[0].hand[0] = Card(
            CardSuits.HEART, CardValues.TWO, CardTypes.BANG
        )
        game_cycle_node.next(engine, UseCard(0, 1))

        assert len(engine.players[0].hand) == first_player_hand_size + 1
        assert len(engine._deck.discard_pile) == 1

        second_player_bullets = engine.players[1].bullets
        game_cycle_node.next(engine, SkipTurn())  # Take damage

        assert len(engine.players[0].hand) == first_player_hand_size + 1
        assert second_player_bullets == engine.players[1].bullets + 1

        game_cycle_node.next(engine, SkipTurn())  # Played cards, go to discard phase

        second_player_hand_size = len(engine.players[1].hand)
        game_cycle_node.next(
            engine, DropCard(0)
        )  # Drop card, because we can't have more card than our health/bullets

        assert len(engine.players[0].hand) == first_player_hand_size
        assert len(engine.players[1].hand) == second_player_hand_size + 2

        engine.players[1].hand[0] = Card(
            CardSuits.HEART, CardValues.TWO, CardTypes.BANG
        )
        game_cycle_node.next(engine, UseCard(0, 0))
        assert len(engine.players[1].hand) == second_player_hand_size + 1

        engine.players[0].hand[0] = Card(
            CardSuits.HEART, CardValues.TWO, CardTypes.MISSED
        )
        first_player_bullets = engine.players[0].bullets
        game_cycle_node.next(engine, UseCard(0))  # Missed

        assert (
            len(engine.players[0].hand) == first_player_hand_size - 1
        )  # We used missed card
        assert first_player_bullets == engine.players[0].bullets
