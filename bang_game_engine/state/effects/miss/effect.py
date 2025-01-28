from bang_game_engine.action import Action, SkipTurn, UseCard
from bang_game_engine.card import CardTypes
from bang_game_engine.engine import IEngine
from bang_game_engine.state.base import BaseStateNode


class MissEffectNode(BaseStateNode):
    def __init__(
        self,
        is_done: bool = False,
        is_missed: bool = False,
    ):
        super().__init__(is_done=is_done, child_node=None)

        self._is_missed = is_missed

    def _set_missed(self):
        self._is_missed = True

    @property
    def missed(self) -> bool:
        return self._is_missed

    def __repr__(self) -> str:
        return f"MissEffectNode(missed={self._is_missed}, parent={super().__repr__()})"


class TryMissNode(MissEffectNode):
    def __init__(
        self,
        engine: IEngine,
        target_player_index: int,
        initiating_player_index: int | None = None,
        is_done: bool = False,
        is_missed: bool = False,
        miss_card_type: CardTypes = CardTypes.MISSED,
    ) -> None:
        super().__init__(is_done=is_done, is_missed=is_missed)

        self._engine = engine
        self._initiating_player_index = initiating_player_index
        self._target_player_index = target_player_index

        self._miss_card_type = miss_card_type

    def _next(self, user_action: Action | None = None):
        if isinstance(user_action, UseCard):
            card = self._engine.players[self._target_player_index].hand[
                user_action.card_index
            ]

            if card.card_type != self._miss_card_type:
                raise ValueError("Only missed card can be used to try to miss a bang")

            self._engine.discard_card(
                self._target_player_index,
                user_action.card_index,
            )
            self._set_missed()
        elif isinstance(user_action, SkipTurn):
            self._mark_as_done()
        else:
            raise ValueError("User use card or skip turn action is required")

    def __repr__(self) -> str:
        return f"TryMissNode(initiating_player_index={self._initiating_player_index}, target_player_index={self._target_player_index}, missed={self.missed})"
