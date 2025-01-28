from __future__ import annotations

from bang_game_engine.action import Action, SkipTurn, UseCard
from bang_game_engine.card import CardTypes
from bang_game_engine.engine import IEngine
from bang_game_engine.state.base import BaseStateNode
from bang_game_engine.state.effects.miss.effect import MissEffectNode
from bang_game_engine.state.effects.miss.factories import AbstractMissFactory
from bang_game_engine.state.effects.miss.interfaces import IMissEffectFactory


class DamageEffectNode(BaseStateNode):
    def __init__(
        self,
        engine: IEngine,
        target_player_index: int,
        miss_node_factory: IMissEffectFactory | None = None,
        initiating_player_index: int | None = None,
        amount: int = 1,
        is_done: bool = False,
    ):
        super().__init__(is_done=is_done)

        self._engine = engine
        self._target_player_index = target_player_index
        self._initiating_player_index = initiating_player_index
        self._amount = amount
        self._miss_node: MissEffectNode | None = None

        if miss_node_factory is not None:
            self._miss_node = miss_node_factory.create(
                engine=self._engine,
                target_player_index=self._target_player_index,
                initiating_player_index=self._initiating_player_index,
            )
            self._set_child_node(self._miss_node)

    def _next(self, user_action: Action | None = None) -> None:
        if self._miss_node and self._miss_node.missed:
            self._mark_as_done()
            return

        self._engine.damage_player(self._target_player_index, self._amount)
        self._mark_as_done()

    def __repr__(self) -> str:
        return f"DamageEffectNode(player_index={self._target_player_index}, amount={self._amount}, parent={super().__repr__()})"


class BangEffectNode(DamageEffectNode):
    def __init__(
        self,
        engine: IEngine,
        target_player_index: int,
        initiating_player_index: int | None = None,
        is_done: bool = False,
    ):
        super().__init__(
            engine=engine,
            target_player_index=target_player_index,
            initiating_player_index=initiating_player_index,
            miss_node_factory=AbstractMissFactory.create(card_type=CardTypes.BANG),
            amount=1,
            is_done=is_done,
        )


class BeerEffectNode(BaseStateNode):
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
        if len(self._engine.alive_players) > 2:
            self._engine.heal_player(self._player_index, 1)

        self._mark_as_done()

    def __repr__(self) -> str:
        return f"BeerCardNode(player_index={self._player_index})"


class GatlingEffectNode(BaseStateNode):
    def __init__(
        self,
        engine: IEngine,
        initiating_player_index: int,
        is_done: bool = False,
    ):
        super().__init__(is_done=is_done)

        self._engine = engine
        self._initiating_player_index = initiating_player_index
        self._target_player_index_delta = 1

    def _get_current_player_index(self) -> int:
        return (self._initiating_player_index + self._target_player_index_delta) % len(
            self._engine.players
        )

    def _next(self, user_action: Action | None = None) -> None:
        if self._target_player_index_delta == len(self._engine.players):
            self._mark_as_done()
            return

        # Skip dead players
        while not self._engine.players[self._get_current_player_index()].is_alive:
            self._target_player_index_delta += 1

        if self._target_player_index_delta == len(self._engine.players):
            self._mark_as_done()
            return

        self._set_child_node(
            BangEffectNode(
                engine=self._engine,
                target_player_index=self._get_current_player_index(),
                initiating_player_index=self._initiating_player_index,
            )
        )

    def __repr__(self) -> str:
        return f"GatlingEffectNode(initiating_player_index={self._initiating_player_index})"


class IndiansEffectNode(BaseStateNode):
    def __init__(
        self,
        engine: IEngine,
        initiating_player_index: int,
        is_done: bool = False,
    ):
        super().__init__(is_done=is_done)

        self._engine = engine
        self._initiating_player_index = initiating_player_index
        self._target_player_index_delta = 1

    def _get_current_player_index(self) -> int:
        return (self._initiating_player_index + self._target_player_index_delta) % len(
            self._engine.players
        )

    def _next(self, user_action: Action | None = None) -> None:
        if self._target_player_index_delta == len(self._engine.players):
            self._mark_as_done()
            return

        # Skip dead players
        while not self._engine.players[self._get_current_player_index()].is_alive:
            self._target_player_index_delta += 1

        if self._target_player_index_delta == len(self._engine.players):
            self._mark_as_done()
            return

        self._set_child_node(
            DamageEffectNode(
                engine=self._engine,
                target_player_index=self._get_current_player_index(),
                initiating_player_index=self._initiating_player_index,
                miss_node_factory=AbstractMissFactory.create(
                    card_type=CardTypes.INDIANS
                ),
                amount=1,
            )
        )

    def __repr__(self) -> str:
        return f"GatlingEffectNode(initiating_player_index={self._initiating_player_index})"


class DuelEffectNode(BaseStateNode):
    def __init__(
        self,
        engine: IEngine,
        initiating_player_index: int,
        target_player_index: int,
        is_done: bool = False,
    ):
        super().__init__(is_done=is_done)

        self._engine = engine
        self._initiating_player_index = initiating_player_index
        self._target_player_index = target_player_index

        self._current_player_that_must_provide_bang = target_player_index

    def _next(self, user_action: Action | None = None) -> None:
        if isinstance(user_action, SkipTurn):
            self._set_child_node(
                DamageEffectNode(
                    engine=self._engine,
                    target_player_index=self._current_player_that_must_provide_bang,
                    initiating_player_index=self._initiating_player_index,
                )
            )
            self._mark_as_done()
            return
        elif isinstance(user_action, UseCard):
            card = self._engine.players[
                self._current_player_that_must_provide_bang
            ].hand[user_action.card_index]

            if card.card_type != CardTypes.BANG:
                raise ValueError("Only bang card can be used in a duel")

            self._engine.discard_card(
                self._current_player_that_must_provide_bang,
                user_action.card_index,
            )

            self._current_player_that_must_provide_bang = (
                self._initiating_player_index
                if self._current_player_that_must_provide_bang
                == self._target_player_index
                else self._target_player_index
            )
        else:
            raise ValueError("User action is required")

    def __repr__(self) -> str:
        return f"DuelEffectNode(initiating_player_index={self._initiating_player_index}, target_player_index={self._target_player_index})"


class SaloonEffectNode(BaseStateNode):
    def __init__(
        self,
        engine: IEngine,
        initiating_player_index: int,
        is_done: bool = False,
    ):
        super().__init__(is_done=is_done)

        self._engine = engine
        self._initiating_player_index = initiating_player_index

    def _next(self, user_action: Action | None = None) -> None:
        for player_index in range(len(self._engine.players)):
            self._engine.heal_player(player_index, 1)
        self._mark_as_done()

    def __repr__(self) -> str:
        return (
            f"SaloonEffectNode(initiating_player_index={self._initiating_player_index})"
        )


class DiligenciaEffectNode(BaseStateNode):
    def __init__(
        self,
        engine: IEngine,
        initiating_player_index: int,
        is_done: bool = False,
    ):
        super().__init__(is_done=is_done)

        self._engine = engine
        self._initiating_player_index = initiating_player_index

    def _next(self, user_action: Action | None = None) -> None:
        self._engine.draw_cards(self._initiating_player_index, 2)
        self._mark_as_done()

    def __repr__(self) -> str:
        return f"DiligenciaEffectNode(initiating_player_index={self._initiating_player_index})"


class WellsFargoEffectNode(BaseStateNode):
    def __init__(
        self,
        engine: IEngine,
        initiating_player_index: int,
        is_done: bool = False,
    ):
        super().__init__(is_done=is_done)

        self._engine = engine
        self._initiating_player_index = initiating_player_index

    def _next(self, user_action: Action | None = None) -> None:
        self._engine.draw_cards(self._initiating_player_index, 3)
        self._mark_as_done()

    def __repr__(self) -> str:
        return f"WellsFargoEffectNode(initiating_player_index={self._initiating_player_index})"
