from bang_game_engine.action import Action, DropCard, SkipTurn, TargetedUseCard, UseCard
from bang_game_engine.engine import IEngine
from bang_game_engine.state.base import BaseStateNode
from bang_game_engine.state.effects_factory import EffectsFactory
from bang_game_engine.state.interfaces import IStateNode
from bang_game_engine.state.utils import PlayerIterator


class GameCycleNode(IStateNode):
    def __init__(
        self,
        engine: IEngine,
        payer_turn_node: IStateNode | None = None,
        current_player_index: int | None = None,
    ):
        super().__init__()

        self._engine = engine
        self._player_iterator = PlayerIterator(
            current_player_index=current_player_index or 0,
            players_count=len(engine.players),
        )
        self._payer_turn_node = payer_turn_node

    def next(
        self,
        user_action: Action | None = None,
    ) -> None:
        if not self._payer_turn_node:
            # TODO: Use factory to create payer turn node
            self._payer_turn_node = PlayerTurnNode(
                engine=self._engine,
                current_player_index=self._player_iterator.current,
            )

        try:
            self._payer_turn_node.next(user_action)
        except StopIteration:
            next(self._player_iterator)
            self._payer_turn_node = None  # reset payer turn node

    def __repr__(self):
        return f"GameCycleNode(current_player_index={self._player_iterator.current}, payer_turn_node={self._payer_turn_node})"


class DrawCardsNode(BaseStateNode):
    def __init__(
        self,
        engine: IEngine,
        player_index: int,
        amount: int = 2,
        is_applied: bool = False,
    ):
        super().__init__(is_done=is_applied)

        self._engine = engine
        self._player_index = player_index
        self._amount = amount

    def _next(self, user_action: Action | None = None):
        self._engine.draw_cards(self._player_index, self._amount)
        self._mark_as_done()

    def __repr__(self):
        return f"DrawCardsNode(player_index={self._player_index}, amount={self._amount}, is_applied={self.is_done})"


class PlayCardsNode(BaseStateNode):
    def __init__(
        self,
        engine: IEngine,
        player_index: int,
        is_done: bool = False,
        effect: IStateNode | None = None,
    ):
        super().__init__(
            is_done=is_done,
            child_node=effect,
        )

        self._engine = engine
        self._player_index = player_index

    def _next(self, user_action: Action | None = None) -> None:
        if isinstance(user_action, UseCard):
            card = self._engine.players[self._player_index].hand[user_action.card_index]
            effect = EffectsFactory.create(
                engine=self._engine,
                card_type=card.card_type,
                target_player_index=(
                    user_action.target_player_index
                    if isinstance(user_action, TargetedUseCard)
                    else None
                ),
                initiating_player_index=self._player_index,
            )
            self._engine.discard_card(self._player_index, user_action.card_index)
            self._set_child_node(effect)
        elif isinstance(user_action, SkipTurn):
            self._mark_as_done()
        else:
            raise ValueError("User action is required")

    def __repr__(self):
        return f"PlayCardsNode(player_index={self._player_index}, parent={super().__repr__()})"


class DiscardCardsNode(BaseStateNode):
    def __init__(
        self,
        engine: IEngine,
        current_player_index: int,
        is_done: bool = False,
    ):
        super().__init__(is_done=is_done)

        self._engine = engine
        self._current_player_index = current_player_index
        self._is_done = False

    def _next(self, user_action: Action | None = None) -> None:
        if isinstance(user_action, DropCard):
            self._engine.discard_card(
                self._current_player_index, user_action.card_index
            )

            if len(self._engine.players[self._current_player_index].hand) == 0:
                self._mark_as_done()

        elif isinstance(user_action, SkipTurn):
            self._mark_as_done()
        else:
            raise ValueError("User action is required")

    def __repr__(self):
        return f"DiscardCardsNode(current_player_index={self._current_player_index})"


class PlayerTurnNode(BaseStateNode):
    def __init__(
        self,
        engine: IEngine,
        current_player_index: int,
        current_node_index: int = 0,
    ):
        super().__init__()

        self._nodes: list[IStateNode] = [
            DrawCardsNode(engine, current_player_index),
            PlayCardsNode(engine, current_player_index),
            DiscardCardsNode(engine, current_player_index),
        ]
        self._current_node_index = min(current_node_index, len(self._nodes) - 1)
        self._engine = engine

    def _next(self, user_action: Action | None = None) -> None:
        if self._current_node_index >= len(self._nodes):
            self._mark_as_done()
            return
        else:
            self._set_child_node(self._nodes[self._current_node_index])
            self._current_node_index += 1

    def __repr__(self):
        return f"PlayerTurnNode(current_node_index={self._current_node_index}, current_node={self._nodes[self._current_node_index]})"
