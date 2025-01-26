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
