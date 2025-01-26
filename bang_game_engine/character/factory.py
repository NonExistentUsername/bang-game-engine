import random

from bang_game_engine.character.character import Character
from bang_game_engine.character.constants import CharacterTypes
from bang_game_engine.character.interfaces import ICharacterFactory
from bang_game_engine.modifier import Modifier


class CharacterFactory(ICharacterFactory):
    @staticmethod
    def create(character_type: CharacterTypes) -> Character:
        if character_type == CharacterTypes.SLAB_THE_KILLER:
            return Character(
                character_type=CharacterTypes.SLAB_THE_KILLER,
                max_bullets=4,
                modifier=Modifier(),
            )

        if character_type == CharacterTypes.SUZY_LAFAYETTE:
            return Character(
                character_type=CharacterTypes.SUZY_LAFAYETTE,
                max_bullets=4,
                modifier=Modifier(),
            )

        if character_type == CharacterTypes.WILLY_THE_KID:
            return Character(
                character_type=CharacterTypes.WILLY_THE_KID,
                max_bullets=4,
                modifier=Modifier(),
            )

        raise ValueError(f"Character type {character_type} is not supported")
