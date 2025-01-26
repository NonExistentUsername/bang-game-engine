from bang_game_engine.card import CardTypes
from bang_game_engine.engine import IEngine
from bang_game_engine.state.effects.effects import MissEffectNode, TryMissNode
from bang_game_engine.state.effects.interfaces import IMissEffectFactory


class BangMissEffectFactory(IMissEffectFactory):
    def create(
        self,
        engine: IEngine,
        initiating_player_index: int,
        target_player_index: int,
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
        initiating_player_index: int,
        target_player_index: int,
    ) -> MissEffectNode:
        return TryMissNode(
            engine=engine,
            target_player_index=target_player_index,
            initiating_player_index=initiating_player_index,
            miss_card_type=CardTypes.BANG,
        )
