from __future__ import annotations


class DomainError(Exception):
    """Base for all domain errors."""


class InvalidActionError(DomainError):
    """Player attempted an action that is not currently valid."""


class NotYourTurnError(InvalidActionError):
    """It is not this player's turn."""


class TargetOutOfRangeError(InvalidActionError):
    """Target player is out of weapon/card range."""


class CardNotPlayableError(InvalidActionError):
    """This card cannot be played right now."""


class GameOverError(DomainError):
    """The game has already ended."""


class GameNotStartedError(DomainError):
    """The game has not started yet."""
