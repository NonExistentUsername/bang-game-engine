from dataclasses import dataclass


class Action:
    pass


@dataclass
class UseCard(Action):
    card_index: int


@dataclass
class TargetedUseCard(UseCard):
    target_player_index: int


@dataclass
class DropCard(Action):
    card_index: int


@dataclass
class SkipTurn(Action):
    pass
