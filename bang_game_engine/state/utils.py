import logging

from bang_game_engine.state.interfaces import IStateNode

logger = logging.getLogger(__name__)


class PushFullNextNodeDecorator(IStateNode):
    def __init__(
        self,
        node: IStateNode,
    ):
        self._node = node

    def next(self, user_action=None):
        logger.debug(f"PushFullNextNodeDecorator.next(user_action={user_action})")
        self._node.next(user_action)

        while True:
            logger.debug(f"PushFullNextNodeDecorator.next: looping")
            try:
                self._node.next()
            except (StopIteration, ValueError):
                break

    def __repr__(self):
        return f"PushFullNextNodeDecorator(node={self._node})"


class PlayerIterator:
    def __init__(
        self,
        current_player_index: int,
        players_count: int,
    ):
        self._current_player_index = current_player_index
        self._players_count = players_count

    @property
    def current(self) -> int:
        return self._current_player_index

    def __iter__(self) -> "PlayerIterator":
        return self

    def __next__(self) -> int:
        self._current_player_index = (
            self._current_player_index + 1
        ) % self._players_count
        return self._current_player_index
