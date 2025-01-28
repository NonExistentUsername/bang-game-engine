from bang_game_engine.card import CardTypes
from bang_game_engine.engine import IEngine
from bang_game_engine.state.effects.miss.effect import MissEffectNode, TryMissNode
from bang_game_engine.state.effects.miss.interfaces import IMissEffectFactory


class BangMissEffectFactory(IMissEffectFactory):
    def create(
        self,
        engine: IEngine,
        target_player_index: int,
        initiating_player_index: int | None = None,
    ) -> MissEffectNode:
        return TryMissNode(
            engine=engine,
            target_player_index=target_player_index,
            initiating_player_index=initiating_player_index,
            miss_card_type=CardTypes.MISSED,
        )


class IndiansMissEffectFactory(IMissEffectFactory):
    def create(
        self,
        engine: IEngine,
        target_player_index: int,
        initiating_player_index: int | None = None,
    ) -> MissEffectNode:
        return TryMissNode(
            engine=engine,
            target_player_index=target_player_index,
            initiating_player_index=initiating_player_index,
            miss_card_type=CardTypes.BANG,
        )


class AbstractMissFactory:
    @staticmethod
    def create(card_type: CardTypes) -> IMissEffectFactory:
        if card_type == CardTypes.BANG:
            return BangMissEffectFactory()

        if card_type == CardTypes.INDIANS:
            return IndiansMissEffectFactory()

        raise ValueError(f"Unsupported card type: {card_type}")
