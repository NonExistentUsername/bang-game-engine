from bang_game_engine.action import Action, DropCard, SkipTurn, UseCard
from bang_game_engine.engine import Engine
from bang_game_engine.state.effects_factory import EffectsFactory
from bang_game_engine.state.interfaces import IStateNode


class GameCycleNode(IStateNode):
    def __init__(
        self,
        current_player_index: int | None = None,
        payer_turn_node: IStateNode | None = None,
    ):
        super().__init__()

        self._current_player_index = current_player_index or 0
        self._payer_turn_node = payer_turn_node

    def next(self, engine: Engine, user_action: Action | None = None) -> None:
        if not self._payer_turn_node:
            self._payer_turn_node = PlayerTurnNode(
                current_player_index=self._current_player_index
            )

        try:
            self._payer_turn_node.next(engine, user_action)
        except StopIteration:
            self._current_player_index = (self._current_player_index + 1) % len(
                engine.players
            )
            self._payer_turn_node = None

    def __repr__(self):
        return f"GameCycleNode(current_player_index={self._current_player_index}, payer_turn_node={self._payer_turn_node})"


class DrawCardsNode(IStateNode):
    def __init__(
        self,
        current_player_index: int,
    ):
        super().__init__()

        self._current_player_index = current_player_index
        self._is_done = False

    def next(self, engine: Engine, user_action: Action | None = None) -> None:
        if not self._is_done:
            self._is_done = True
            engine.draw_cards(self._current_player_index, 2)

        raise StopIteration()

    def __repr__(self):
        return f"DrawCardsNode(current_player_index={self._current_player_index})"


class PlayCardsNode(IStateNode):
    def __init__(
        self,
        current_player_index: int,
        is_done: bool = False,
    ):
        super().__init__()

        self._current_player_index = current_player_index
        self._effect: IStateNode | None = None
        self._is_done = is_done

    def next(self, engine: Engine, user_action: Action | None = None) -> None:
        if self._is_done:
            raise StopIteration()

        if self._effect:
            try:
                self._effect.next(engine, user_action)
            except StopIteration:
                self._effect = None

            return

        if isinstance(user_action, UseCard):
            card = engine.players[self._current_player_index].hand[
                user_action.card_index
            ]
            effect = EffectsFactory.create(
                card_type=card.card_type,
                target_player_index=user_action.target_player_index,
                current_player_index=self._current_player_index,
            )
            self._effect = effect
            engine.discard_card(self._current_player_index, user_action.card_index)
        elif isinstance(user_action, SkipTurn):
            self._is_done = True
            raise StopIteration()
        else:
            raise ValueError("User action is required")

    def __repr__(self):
        return f"PlayCardsNode(current_player_index={self._current_player_index}, effect={self._effect})"


class DiscardCardsNode(IStateNode):
    def __init__(self, current_player_index: int, is_done: bool = False):
        super().__init__()

        self._current_player_index = current_player_index
        self._is_done = False

    def next(self, engine: Engine, user_action: Action | None = None) -> None:
        if self._is_done:
            raise StopIteration()

        if isinstance(user_action, DropCard):
            engine.discard_card(self._current_player_index, user_action.card_index)

            if engine.players[self._current_player_index].bullets == len(
                engine.players[self._current_player_index].hand
            ):
                self._is_done = True
                raise StopIteration()
        else:
            raise ValueError("User action is required")

    def __repr__(self):
        return f"DiscardCardsNode(current_player_index={self._current_player_index})"


class PlayerTurnNode(IStateNode):
    def __init__(self, current_player_index: int, current_node_index: int = 0):
        super().__init__()

        self._nodes: list[IStateNode] = [
            DrawCardsNode(current_player_index),
            PlayCardsNode(current_player_index),
            DiscardCardsNode(current_player_index),
        ]
        self._current_node_index = min(current_node_index, len(self._nodes) - 1)

    def next(self, engine: Engine, user_action: Action | None = None) -> None:
        if self._current_node_index == len(self._nodes):
            raise StopIteration()

        try:
            self._nodes[self._current_node_index].next(engine, user_action)
        except StopIteration:
            self._current_node_index += 1

    def __repr__(self):
        return f"PlayerTurnNode(current_node_index={self._current_node_index}, nodes={self._nodes})"
