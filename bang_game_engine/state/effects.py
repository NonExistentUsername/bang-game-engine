from __future__ import annotations

from bang_game_engine.action import Action, SkipTurn, UseCard
from bang_game_engine.card import CardTypes
from bang_game_engine.engine import Engine
from bang_game_engine.state.interfaces import IStateNode


class TryMissNode(IStateNode):
    def __init__(
        self,
        current_player_index: int,
        target_player_index: int | None = None,
    ):
        super().__init__()

        self._current_player_index = current_player_index
        self._target_player_index = target_player_index
        self._is_done = False
        self._is_missed = False

    @property
    def missed(self) -> bool:
        return self._is_missed

    def next(self, engine: Engine, user_action: Action | None = None) -> None:
        if self._is_done:
            raise StopIteration()

        if isinstance(user_action, SkipTurn):
            self._is_done = True
            raise StopIteration()
        elif isinstance(user_action, UseCard):
            card = engine.players[self._current_player_index].hand[
                user_action.card_index
            ]

            if card.card_type != CardTypes.MISSED:
                raise ValueError("Only missed card can be used to try to miss a bang")

            engine.discard_card(self._current_player_index, user_action.card_index)
            self._is_missed = True
            self._is_done = True
        else:
            raise ValueError("User use card or skip turn action is required")

    def __repr__(self) -> str:
        return f"TryMissNode(current_player_index={self._current_player_index}, target_player_index={self._target_player_index}, missed={self._is_missed})"


class BangCardNode(IStateNode):
    def __init__(
        self,
        target_player_index: int,
        current_player_index: int | None = None,
    ):
        super().__init__()

        self._current_player_index = current_player_index
        self._target_player_index = target_player_index
        self._is_done = False
        self._try_miss_node: TryMissNode = TryMissNode(
            current_player_index=self._target_player_index,
            target_player_index=self._current_player_index,
        )

    def next(self, engine: Engine, user_action: Action | None = None) -> None:
        if self._is_done:
            raise StopIteration()

        try:
            self._try_miss_node.next(engine, user_action)
        except StopIteration:
            if self._try_miss_node.missed:
                self._is_done = True
                raise StopIteration()
            else:
                engine.damage_player(self._target_player_index, 1)
                self._is_done = True

    def __repr__(self):
        return f"BangCardNode(target_player_index={self._target_player_index}, try_miss_node={self._try_miss_node})"


class BeerCardNode(IStateNode):
    def __init__(self, current_player_index: int):
        super().__init__()

        self._current_player_index = current_player_index
        self._is_done = False

    def next(self, engine: Engine, user_action: Action | None = None) -> None:
        if self._is_done:
            raise StopIteration()

        engine.heal_player(self._current_player_index, 1)

        self._is_done = True

    def __repr__(self) -> str:
        return f"BeerCardNode(current_player_index={self._current_player_index})"
