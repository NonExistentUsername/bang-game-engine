from __future__ import annotations

from typing import Callable

from bang_game_engine.effects.effect import EffectHandler
from bang_game_engine.shared.errors import DomainError


class EffectRegistry:
    """
    Maps card_type string -> EffectHandler factory.
    Expansions register their effects here instead of modifying a central if/elif.
    """

    def __init__(self) -> None:
        self._handlers: dict[str, Callable[[], EffectHandler]] = {}

    def register(
        self, card_type: str, handler_factory: Callable[[], EffectHandler]
    ) -> None:
        self._handlers[card_type] = handler_factory

    def get_handler(self, card_type: str) -> EffectHandler:
        if card_type not in self._handlers:
            raise DomainError(f"No effect handler registered for card type: {card_type}")
        return self._handlers[card_type]()

    def has_handler(self, card_type: str) -> bool:
        return card_type in self._handlers

    @property
    def registered_types(self) -> list[str]:
        return list(self._handlers.keys())
