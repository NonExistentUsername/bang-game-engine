from __future__ import annotations

from bang_game_engine.action import Action, SkipTurn, UseCard
from bang_game_engine.card import CardTypes
from bang_game_engine.engine import IEngine
from bang_game_engine.state.base import BaseStateNode
from bang_game_engine.state.interfaces import IStateNode


class TryMissNode(BaseStateNode):
    def __init__(
        self,
        engine: IEngine,
        player_index: int,
        initiating_player_index: int | None = None,
        is_done: bool = False,
        is_missed: bool = False,
    ) -> None:
        super().__init__(is_done=is_done)

        self._engine = engine
        self._initiating_player_index = initiating_player_index
        self._player_index = player_index
        self._is_missed = is_missed

    @property
    def missed(self) -> bool:
        return self._is_missed

    def _next(self, user_action: Action | None = None):
        if isinstance(user_action, UseCard):
            card = self._engine.players[self._player_index].hand[user_action.card_index]

            if card.card_type != CardTypes.MISSED:
                raise ValueError("Only missed card can be used to try to miss a bang")

            self._engine.discard_card(
                self._player_index,
                user_action.card_index,
            )
            self._is_missed = True
        elif isinstance(user_action, SkipTurn):
            self._mark_as_done()
        else:
            raise ValueError("User use card or skip turn action is required")

    def __repr__(self) -> str:
        return f"TryMissNode(initiating_player_index={self._initiating_player_index}, player_index={self._player_index}, missed={self._is_missed})"


class BangCardNode(BaseStateNode):
    def __init__(
        self,
        engine: IEngine,
        target_player_index: int,
        initiating_player_index: int | None = None,
        is_done: bool = False,
        miss_node: TryMissNode | None = None,
    ):
        super().__init__(is_done=is_done, child_node=miss_node)

        self._miss_node = miss_node
        self._engine = engine
        self._initiating_player_index = initiating_player_index
        self._target_player_index = target_player_index

    def _next(self, user_action: Action | None = None):
        if not self._miss_node:
            self._miss_node = TryMissNode(
                engine=self._engine,
                player_index=self._target_player_index,
                initiating_player_index=self._initiating_player_index,
            )
            self._set_child_node(self._miss_node)
            return

        if not self._miss_node.missed:
            self._engine.damage_player(self._target_player_index, 1)

        self._mark_as_done()


class BeerCardNode(BaseStateNode):
    def __init__(
        self,
        engine: IEngine,
        player_index: int,
        is_done: bool = False,
    ):
        super().__init__(is_done=is_done)

        self._engine = engine
        self._player_index = player_index

    def _next(self, user_action: Action | None = None) -> None:
        alive_players_count = 0
        for player in self._engine.players:
            if player.is_alive:
                alive_players_count += 1

        if alive_players_count > 2:
            self._engine.heal_player(self._player_index, 1)

        self._mark_as_done()

    def __repr__(self) -> str:
        return f"BeerCardNode(player_index={self._player_index})"
