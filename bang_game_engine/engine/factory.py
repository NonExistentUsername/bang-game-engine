import random

from bang_game_engine.card import Card, CardSuits, CardTypes, CardValues
from bang_game_engine.character import (
    Character,
    CharacterFactory,
    CharacterTypes,
    ICharacterFactory,
)
from bang_game_engine.deck import IDeckFactory
from bang_game_engine.engine.engine import Engine
from bang_game_engine.player import IPlayer, Player
from bang_game_engine.role import Role, RoleTypes


class EngineFactory:
    @staticmethod
    def create_new_engine(
        players_count: int,
        deck_factory: IDeckFactory,
        characters_factory: ICharacterFactory,
        shuffle_deck: bool = True,
    ) -> Engine:
        deck = deck_factory.create()

        if shuffle_deck:
            deck.shuffle()

        players: list[IPlayer] = EngineFactory.prepare_players(
            players_count, characters_factory
        )

        # Deal cards to players
        for player in players:
            for _ in range(player.bullets):
                player.hand.append(deck.draw())

        return Engine(players, deck)

    @staticmethod
    def prepare_players(
        players_count: int,
        characters_factory: ICharacterFactory,
    ) -> list[IPlayer]:
        if players_count not in [2, 4]:
            raise ValueError("Players count should be 2 or 4")

        players: list[IPlayer] = []

        if players_count == 2:
            sheriff_role = Role(RoleTypes.SHERIFF)
            outlaw_role = Role(RoleTypes.OUTLAW)

            players = [
                Player(
                    sheriff_role,
                    characters_factory.create(
                        CharacterTypes.random(),
                    ),
                ),
                Player(
                    outlaw_role,
                    characters_factory.create(
                        CharacterTypes.random(),
                    ),
                ),
            ]
        else:
            sheriff_role = Role(RoleTypes.SHERIFF)
            outlaw_role = Role(RoleTypes.OUTLAW)
            deputy_role = Role(RoleTypes.DEPUTY)

            players = [
                Player(
                    sheriff_role,
                    characters_factory.create(
                        CharacterTypes.random(),
                    ),
                ),
                Player(
                    outlaw_role,
                    characters_factory.create(
                        CharacterTypes.random(),
                    ),
                ),
                Player(
                    deputy_role,
                    characters_factory.create(
                        CharacterTypes.random(),
                    ),
                ),
                Player(
                    deputy_role,
                    characters_factory.create(
                        CharacterTypes.random(),
                    ),
                ),
            ]

        return players
