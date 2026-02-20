from __future__ import annotations

from typing import NewType
from uuid import UUID

PlayerId = NewType("PlayerId", UUID)
CardId = NewType("CardId", UUID)
GameId = NewType("GameId", UUID)
