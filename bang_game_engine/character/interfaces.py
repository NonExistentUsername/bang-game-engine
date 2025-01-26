import abc

from bang_game_engine.character.character import Character, CharacterTypes


class ICharacterFactory(abc.ABC):
    @abc.abstractmethod
    def create(self, character_type: CharacterTypes) -> Character:
        pass
