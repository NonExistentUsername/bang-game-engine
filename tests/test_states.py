import pytest

from bang_game_engine.action import TargetedUseCard
from bang_game_engine.card import Card, CardSuits, CardTypes, CardValues, GunCard
from bang_game_engine.character import CharacterFactory, ICharacterFactory
from bang_game_engine.deck import IDeckFactory
from bang_game_engine.engine import Engine, EngineFactory
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
            GameCycleNode(engine=engine)
        )

        first_player_hand_size = len(engine.players[0].hand)

        game_cycle_node.next()  # Start game and draw cards

        assert (
            len(engine.players[0].hand) == first_player_hand_size + 2
        ), "Draw cards, add 2 cards to player hand"

        engine.players[0].hand[0] = Card(
            CardSuits.HEART, CardValues.TWO, CardTypes.BANG
        )
        print(game_cycle_node)

        game_cycle_node.next(TargetedUseCard(0, 1))
        print(game_cycle_node)

        assert (
            len(engine.players[0].hand) == first_player_hand_size + 1
        ), "Card bang used"
        assert (
            len(engine._deck.discard_pile) == 1
        ), "Bang card should be in discard pile"

        second_player_bullets = engine.players[1].bullets
        game_cycle_node.next(SkipTurn())  # Take damage

        assert len(engine.players[0].hand) == first_player_hand_size + 1
        assert second_player_bullets == engine.players[1].bullets + 1

        game_cycle_node.next(SkipTurn())  # Played cards, go to discard phase

        second_player_hand_size = len(engine.players[1].hand)
        game_cycle_node.next(
            DropCard(0)
        )  # Drop card, because we can't have more card than our health/bullets
        game_cycle_node.next(SkipTurn())  # Finish discard phase

        assert (
            len(engine.players[0].hand) == first_player_hand_size
        ), "First player hand must be the same"
        assert (
            len(engine.players[1].hand) == second_player_hand_size + 2
        ), "Draw cards for second player"

        engine.players[1].hand[0] = Card(
            CardSuits.HEART, CardValues.TWO, CardTypes.BANG
        )
        game_cycle_node.next(TargetedUseCard(0, 0))
        assert len(engine.players[1].hand) == second_player_hand_size + 1

        engine.players[0].hand[0] = Card(
            CardSuits.HEART, CardValues.TWO, CardTypes.MISSED
        )
        first_player_bullets = engine.players[0].bullets
        game_cycle_node.next(UseCard(0))  # Missed

        assert (
            len(engine.players[0].hand) == first_player_hand_size - 1
        )  # We used missed card
        assert first_player_bullets == engine.players[0].bullets

    def test_cannot_bang_if_cannot_reach(
        self,
        deck_factory: IDeckFactory,
        character_factory: ICharacterFactory,
    ):
        engine = EngineFactory.create_new_engine(
            players_count=4,
            deck_factory=deck_factory,
            characters_factory=character_factory,
            shuffle_deck=True,
        )
        game_cycle_node: PushFullNextNodeDecorator = PushFullNextNodeDecorator(
            GameCycleNode(engine=engine)
        )

        game_cycle_node.next()  # Start game and draw cards

        engine.players[0].hand[0] = Card(
            CardSuits.HEART, CardValues.TWO, CardTypes.BANG
        )

        with pytest.raises(
            ValueError
        ):  # Player 0 can't reach player 2, because player 1 (or 3) is in the way
            game_cycle_node.next(TargetedUseCard(0, 2))

        engine.players[0].gun = GunCard(
            CardSuits.HEART,
            CardValues.TWO,
            CardTypes.SCHOFIELD,
            distance_range=2,
        )

        game_cycle_node.next(TargetedUseCard(0, 2))  # Player 0 can reach player 2

        game_cycle_node.next(SkipTurn())  # Take damage

        assert (
            engine.players[2].bullets == engine.players[2].max_bullets - 1
        ), "Player 2 took damage"

    def test_gatling(self, engine: Engine):
        game_cycle_node: PushFullNextNodeDecorator = PushFullNextNodeDecorator(
            GameCycleNode(engine=engine)
        )

        game_cycle_node.next()

        engine.players[0].hand = [
            Card(CardSuits.HEART, CardValues.TWO, CardTypes.GATLING)
        ]

        game_cycle_node.next(UseCard(0))

        assert len(engine.players[0].hand) == 0

        for player_index in range(1, len(engine.players)):
            game_cycle_node.next(SkipTurn())  # Take damage

            assert (
                engine.players[player_index].bullets
                == engine.players[player_index].max_bullets - 1
            )

    def test_gatling_can_be_missed(self, engine: Engine):
        game_cycle_node: PushFullNextNodeDecorator = PushFullNextNodeDecorator(
            GameCycleNode(engine=engine)
        )

        game_cycle_node.next()

        engine.players[0].hand = [
            Card(CardSuits.HEART, CardValues.TWO, CardTypes.MISSED)
        ]
        engine.players[1].hand = [
            Card(CardSuits.HEART, CardValues.TWO, CardTypes.GATLING)
        ]

        game_cycle_node.next(SkipTurn())  # Skip player 0

        game_cycle_node.next(SkipTurn())  # Skip discard phase

        game_cycle_node.next(UseCard(0))  # Player 1 used gatling

        assert (
            len(engine.players[1].hand) == 2
        )  # Player 1 have 2 cards, because he draw 2 cards before gatling

        game_cycle_node.next(UseCard(0))  # Use missed card

        assert (
            engine.players[0].bullets == engine.players[0].max_bullets
        ), "Player 0 didn't take damage"

    def test_indians(self, engine: Engine):
        game_cycle_node: PushFullNextNodeDecorator = PushFullNextNodeDecorator(
            GameCycleNode(engine=engine)
        )

        game_cycle_node.next()

        engine.players[0].hand = [
            Card(CardSuits.HEART, CardValues.TWO, CardTypes.INDIANS)
        ]

        game_cycle_node.next(UseCard(0))

        assert len(engine.players[0].hand) == 0

        for player_index in range(1, len(engine.players)):
            game_cycle_node.next(SkipTurn())  # Take damage

            assert (
                engine.players[player_index].bullets
                == engine.players[player_index].max_bullets - 1
            )

    def test_indians_can_be_missed(self, engine: Engine):
        game_cycle_node: PushFullNextNodeDecorator = PushFullNextNodeDecorator(
            GameCycleNode(engine=engine)
        )

        game_cycle_node.next()

        engine.players[0].hand = [Card(CardSuits.HEART, CardValues.TWO, CardTypes.BANG)]
        engine.players[1].hand = [
            Card(CardSuits.HEART, CardValues.TWO, CardTypes.INDIANS)
        ]

        game_cycle_node.next(SkipTurn())  # Skip player 0

        game_cycle_node.next(SkipTurn())  # Skip discard phase

        game_cycle_node.next(UseCard(0))  # Player 1 used indians

        assert (
            len(engine.players[1].hand) == 2
        )  # Player 1 have 2 cards, because he draw 2 cards before indians

        game_cycle_node.next(UseCard(0))  # Use bang card to miss indians

        assert (
            engine.players[0].bullets == engine.players[0].max_bullets
        ), "Player 0 didn't take damage"

    def test_duel(self, engine: Engine):
        game_cycle_node: PushFullNextNodeDecorator = PushFullNextNodeDecorator(
            GameCycleNode(engine=engine)
        )

        game_cycle_node.next()  # Start game and draw cards

        engine.players[0].hand = [
            Card(CardSuits.HEART, CardValues.TWO, CardTypes.DUEL),
            Card(CardSuits.HEART, CardValues.TWO, CardTypes.BANG),
        ]
        engine.players[1].hand = [Card(CardSuits.HEART, CardValues.TWO, CardTypes.BANG)]

        game_cycle_node.next(TargetedUseCard(0, 1)), "Player 0 used duel card"

        assert len(engine.players[0].hand) == 1, "Player 0 used duel card, 1 card left"

        game_cycle_node.next(UseCard(0)), "Player 1 used bang card"

        assert len(engine.players[0].hand) == 1, "Player 0 have same amount of cards"
        assert len(engine.players[1].hand) == 0, "Player 1 lost all cards"

        game_cycle_node.next(UseCard(0)), "Player 0 used bang card"

        assert len(engine.players[0].hand) == 0, "Player 0 lost all cards"

        game_cycle_node.next(SkipTurn())  # Take damage

        assert (
            engine.players[1].bullets == engine.players[1].max_bullets - 1
        ), "Player 1 took damage"

    def test_saloon(self, engine: Engine):
        game_cycle_node: PushFullNextNodeDecorator = PushFullNextNodeDecorator(
            GameCycleNode(engine=engine)
        )

        game_cycle_node.next()  # Start game and draw cards

        engine.players[0].bullets = 1
        engine.players[1].bullets = 1

        engine.players[0].hand = [
            Card(CardSuits.HEART, CardValues.TWO, CardTypes.SALOON),
        ]
        engine.players[1].hand = [Card(CardSuits.HEART, CardValues.TWO, CardTypes.BANG)]

        game_cycle_node.next(UseCard(0)), "Player 0 used saloon card"

        assert engine.players[0].bullets == 2, "Player 0 healed"
        assert engine.players[1].bullets == 2, "Player 1 healed"

    def test_deligencia(self, engine: Engine):
        game_cycle_node: PushFullNextNodeDecorator = PushFullNextNodeDecorator(
            GameCycleNode(engine=engine)
        )

        game_cycle_node.next()  # Start game and draw cards

        engine.players[0].hand = [
            Card(CardSuits.HEART, CardValues.TWO, CardTypes.DILIGENCIA),
        ]

        game_cycle_node.next(UseCard(0)), "Player 0 used deligencia card"

        assert len(engine.players[0].hand) == 2, "Player 0 draw 2 cards"

    def test_wells_fargo(self, engine: Engine):
        game_cycle_node: PushFullNextNodeDecorator = PushFullNextNodeDecorator(
            GameCycleNode(engine=engine)
        )

        game_cycle_node.next()  # Start game and draw cards

        engine.players[0].hand = [
            Card(CardSuits.HEART, CardValues.TWO, CardTypes.WELLS_FARGO),
        ]

        game_cycle_node.next(UseCard(0)), "Player 0 used deligencia card"

        assert len(engine.players[0].hand) == 3, "Player 0 draw 3 cards"

    def test_general_store(self, engine: Engine):
        game_cycle_node: PushFullNextNodeDecorator = PushFullNextNodeDecorator(
            GameCycleNode(engine=engine)
        )

        game_cycle_node.next()  # Start game and draw cards

        engine.players[0].hand = [
            Card(CardSuits.HEART, CardValues.TWO, CardTypes.GENERAL_STORE),
        ]
        engine.players[1].hand = []

        game_cycle_node.next(UseCard(0)), "Player 0 used general store card"

        assert (
            len(engine.players[0].hand) == 0
        ), "Player 0 have 0 cards, because he used general store"

        game_cycle_node.next(UseCard(1)), "Player 0 took second card from general store"

        assert len(engine.players[0].hand) == 1, "Player 0 have 3 cards"

        game_cycle_node.next(UseCard(0)), "Player 1 took first card from general store"

        assert len(engine.players[0].hand) == 1, "Player 0 have 3 cards"
        assert len(engine.players[1].hand) == 1, "Player 1 have 1 card"

        game_cycle_node.next(SkipTurn())  # Finish playing cards

        game_cycle_node.next(SkipTurn())  # Skip discard phase

        assert len(engine.players[0].hand) == 1, "Player 0 have 3 cards"
        assert len(engine.players[1].hand) == 3, "Player 1 have 1 card"

    def test_panic(self, engine: Engine):
        game_cycle_node: PushFullNextNodeDecorator = PushFullNextNodeDecorator(
            GameCycleNode(engine=engine)
        )

        game_cycle_node.next()  # Start game and draw cards

        engine.players[0].hand = [
            Card(CardSuits.HEART, CardValues.TWO, CardTypes.PANIC),
        ]
        engine.players[1].hand = [
            Card(CardSuits.HEART, CardValues.TWO, CardTypes.BANG),
        ]

        game_cycle_node.next(TargetedUseCard(0, 1)), "Player 0 used panic card"

        assert len(engine.players[0].hand) == 0, "Player 0 used panic card"

        game_cycle_node.next(UseCard(0)), "Player 0 took bang card from player 1"

        assert len(engine.players[0].hand) == 1, "Player 0 took bang card from player 1"
        assert len(engine.players[1].hand) == 0, "Player 1 lost bang card"

        assert (
            engine.players[0].hand[0].card_type == CardTypes.BANG
        ), "Player 0 took bang card from player 1"

    def test_cannot_panic_if_cannot_reach(
        self,
        deck_factory: IDeckFactory,
        character_factory: ICharacterFactory,
    ):
        engine = EngineFactory.create_new_engine(
            players_count=4,
            deck_factory=deck_factory,
            characters_factory=character_factory,
            shuffle_deck=True,
        )
        game_cycle_node: PushFullNextNodeDecorator = PushFullNextNodeDecorator(
            GameCycleNode(engine=engine)
        )

        game_cycle_node.next()  # Start game and draw cards

        engine.players[0].hand = [
            Card(CardSuits.HEART, CardValues.TWO, CardTypes.PANIC),
        ]

        with pytest.raises(ValueError):
            game_cycle_node.next(TargetedUseCard(0, 2)), "Player 0 can't reach player 2"
