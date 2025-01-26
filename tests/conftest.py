import pytest

from bang_game_engine.character import CharacterFactory, ICharacterFactory
from bang_game_engine.deck import IDeckFactory
from bang_game_engine.engine import Engine, EngineFactory
from tests.utils import BangAndMissDeckFactory


@pytest.fixture
def deck_factory() -> IDeckFactory:
    return BangAndMissDeckFactory()


@pytest.fixture
def character_factory() -> CharacterFactory:
    return CharacterFactory()


@pytest.fixture
def engine(
    deck_factory: IDeckFactory,
    character_factory: ICharacterFactory,
) -> Engine:
    return EngineFactory.create_new_engine(
        players_count=2,
        deck_factory=deck_factory,
        characters_factory=character_factory,
        shuffle_deck=True,
    )
