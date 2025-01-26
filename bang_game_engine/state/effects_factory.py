from bang_game_engine.card import CardTypes
from bang_game_engine.engine import IEngine
from bang_game_engine.state.effects import BangCardNode, BeerCardNode
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

            return BangCardNode(
                engine=engine,
                target_player_index=target_player_index,
                initiating_player_index=initiating_player_index,
            )
        elif card_type == CardTypes.BEER:
            if not initiating_player_index:
                raise ValueError("Initiating player index is required for Beer card")

            return BeerCardNode(
                engine=engine,
                player_index=initiating_player_index,
            )
        # elif card_type == CardTypes.GATLING:
        #     return GatlingCardNode()
        # elif card_type == CardTypes.DUEL:
        #     return DuelCardNode()
        # elif card_type == CardTypes.INDIANS:
        #     return IndiansCardNode()
        # elif card_type == CardTypes.SALOON:
        #     return SaloonCardNode()
        # elif card_type == CardTypes.PANIC:
        #     return PanicCardNode()
        # elif card_type == CardTypes.CAT_BALOU:
        #     return CatBalouCardNode()
        else:
            raise ValueError(f"Unsupported card type: {card_type}")
