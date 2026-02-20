from __future__ import annotations

import uuid

from bang_game_engine.shared.types import CardId, GameId, PlayerId


def new_player_id() -> PlayerId:
    return PlayerId(uuid.uuid4())


def new_card_id() -> CardId:
    return CardId(uuid.uuid4())


def new_game_id() -> GameId:
    return GameId(uuid.uuid4())
