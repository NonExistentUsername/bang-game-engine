from bang_game_engine.character.constants import CharacterTypes
from bang_game_engine.modifier import Modifier


class Character:
    def __init__(
        self,
        character_type: CharacterTypes,
        max_bullets: int,
        modifier: Modifier,
    ):
        self.character_type = character_type
        self.max_bullets = max_bullets
        self.modifier = modifier

    def __repr__(self):
        return f"Character(type={self.character_type}, max_bullets={self.max_bullets}, modifier={self.modifier})"
