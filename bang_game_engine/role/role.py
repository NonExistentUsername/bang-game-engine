from dataclasses import dataclass

from bang_game_engine.role.constants import RoleTypes


@dataclass
class Role:
    role_type: RoleTypes

    @property
    def max_bullets_modifier(self) -> int:
        return int(self.role_type == RoleTypes.SHERIFF)
