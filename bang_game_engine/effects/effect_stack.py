from __future__ import annotations

from bang_game_engine.effects.effect import (
    EffectStackEntry,
    EffectState,
    ResponseWindow,
)


class EffectStack:
    """
    LIFO stack for resolving nested effects.

    Example flow:
    1. Player A plays Bang! targeting Player B
       -> Push BangEffect onto stack
    2. BangEffect asks Player B for Missed!
       -> Stack entry state = AWAITING_RESPONSE
    3. Player B plays Missed!
       -> BangEffect.handle_response() called
       -> BangEffect completes, popped from stack

    Nested example (Bang! -> Barrel -> Lucky Duke):
    1. BangEffect pushed
    2. BangEffect triggers Barrel check -> BarrelDrawCheck pushed
    3. BarrelDrawCheck triggers Lucky Duke -> LuckyDukeChoice pushed
    4. Lucky Duke resolves (player picks)
    5. BarrelDrawCheck resolves (Hearts = missed!)
    6. BangEffect resolves (missed, no damage)
    """

    def __init__(self) -> None:
        self._stack: list[EffectStackEntry] = []

    def push(self, entry: EffectStackEntry) -> None:
        self._stack.append(entry)

    def pop(self) -> EffectStackEntry:
        if not self._stack:
            raise IndexError("Effect stack is empty")
        return self._stack.pop()

    def peek(self) -> EffectStackEntry | None:
        return self._stack[-1] if self._stack else None

    @property
    def is_empty(self) -> bool:
        return len(self._stack) == 0

    @property
    def depth(self) -> int:
        return len(self._stack)

    def current_response_window(self) -> ResponseWindow | None:
        top = self.peek()
        if top and top.state == EffectState.AWAITING_RESPONSE:
            return top.response_window
        return None

    def clear(self) -> None:
        self._stack.clear()
