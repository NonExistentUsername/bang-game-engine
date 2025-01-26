from bang_game_engine.state.interfaces import IStateNode


class PushFullNextNodeDecorator(IStateNode):
    def __init__(self, node: IStateNode):
        self._node = node

    def next(self, engine, user_action=None):
        self._node.next(engine, user_action)

        while True:
            try:
                self._node.next(engine)
            except (StopIteration, ValueError):
                break

    def __repr__(self):
        return f"PushFullNextNodeDecorator(node={self._node})"
