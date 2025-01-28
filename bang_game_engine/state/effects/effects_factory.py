from bang_game_engine.card import CardTypes
from bang_game_engine.constraint import IConstraint, ReachableWithGunConstraint
from bang_game_engine.engine import IEngine
from bang_game_engine.player import IPlayer
from bang_game_engine.state.effects.effects import (
    BangEffectNode,
    BeerEffectNode,
    DuelEffectNode,
    GatlingEffectNode,
    IndiansEffectNode,
)
from bang_game_engine.state.effects.miss.factories import (
    BangMissEffectFactory,
    IndiansMissEffectFactory,
)
from bang_game_engine.state.effects.miss.interfaces import IMissEffectFactory
from bang_game_engine.state.interfaces import IStateNode


class EffectsFactory:
    @staticmethod
    def create(
        card_type: CardTypes,
        engine: IEngine,
        target_player_index: int | None = None,
        initiating_player_index: int | None = None,
    ) -> IStateNode:
        if card_type == CardTypes.BANG:
            if target_player_index is None:
                raise ValueError("Target player index is required for Bang card")

            # TODO: Refactor to be more flexible
            if not ReachableWithGunConstraint().check(
                engine=engine,
                initiating_player_index=initiating_player_index,
                target_player_index=target_player_index,
            ):
                raise ValueError("Target player is not reachable")

            return BangEffectNode(
                engine=engine,
                target_player_index=target_player_index,
                initiating_player_index=initiating_player_index,
            )
        elif card_type == CardTypes.BEER:
            if initiating_player_index is None:
                raise ValueError("Initiating player index is required for Beer card")

            return BeerEffectNode(
                engine=engine,
                player_index=initiating_player_index,
            )
        elif card_type == CardTypes.GATLING:
            if initiating_player_index is None:
                raise ValueError("Initiating player index is required for Gatling card")

            return GatlingEffectNode(
                engine=engine,
                initiating_player_index=initiating_player_index,
            )
        elif card_type == CardTypes.DUEL:
            if initiating_player_index is None or target_player_index is None:
                raise ValueError(
                    "Initiating and target player indexes are required for Duel card"
                )

            return DuelEffectNode(
                engine=engine,
                initiating_player_index=initiating_player_index,
                target_player_index=target_player_index,
            )
        elif card_type == CardTypes.INDIANS:
            if initiating_player_index is None:
                raise ValueError("Initiating player index is required for Indians card")

            return IndiansEffectNode(
                engine=engine,
                initiating_player_index=initiating_player_index,
            )
        # elif card_type == CardTypes.SALOON:
        #     return SaloonCardNode()
        # elif card_type == CardTypes.PANIC:
        #     return PanicCardNode()
        # elif card_type == CardTypes.CAT_BALOU:
        #     return CatBalouCardNode()
        else:
            raise ValueError(f"Unsupported card type: {card_type}")
