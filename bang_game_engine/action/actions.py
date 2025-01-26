from dataclasses import dataclass


class Action:
    pass


@dataclass
class UseCard(Action):
    card_index: int
    target_player_index: int | None = None


@dataclass
class DropCard(Action):
    card_index: int


@dataclass
class SkipTurn(Action):
    pass
