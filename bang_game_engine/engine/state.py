from dataclasses import dataclass


@dataclass
class State:
    current_player_index: int

    action_index: int
    actions: list
