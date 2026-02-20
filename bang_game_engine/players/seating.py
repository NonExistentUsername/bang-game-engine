from __future__ import annotations

from bang_game_engine.shared.errors import DomainError
from bang_game_engine.shared.types import PlayerId


class Seating:
    """
    Manages circular seating arrangement.

    Uses PlayerId references, never indices.
    Properly handles eliminated players for distance calculation.
    """

    def __init__(self, player_ids: list[PlayerId]):
        if len(player_ids) < 2:
            raise DomainError("Need at least 2 players for seating")
        self._order = list(player_ids)
        self._alive: set[PlayerId] = set(player_ids)

    def mark_eliminated(self, player_id: PlayerId) -> None:
        self._alive.discard(player_id)

    def alive_players_in_order(self) -> list[PlayerId]:
        """All alive players in original seating order."""
        return [pid for pid in self._order if pid in self._alive]

    def next_alive_after(self, player_id: PlayerId) -> PlayerId:
        """Next alive player clockwise."""
        alive = self.alive_players_in_order()
        if player_id not in alive:
            raise DomainError(f"Player {player_id} is not alive")
        idx = alive.index(player_id)
        return alive[(idx + 1) % len(alive)]

    def prev_alive_before(self, player_id: PlayerId) -> PlayerId:
        """Previous alive player counter-clockwise."""
        alive = self.alive_players_in_order()
        if player_id not in alive:
            raise DomainError(f"Player {player_id} is not alive")
        idx = alive.index(player_id)
        return alive[(idx - 1) % len(alive)]

    def other_alive_players_clockwise(
        self, from_player_id: PlayerId
    ) -> list[PlayerId]:
        """All other alive players in clockwise order starting from next player."""
        alive = self.alive_players_in_order()
        if from_player_id not in alive:
            return list(alive)
        idx = alive.index(from_player_id)
        n = len(alive)
        return [alive[(idx + i) % n] for i in range(1, n)]

    def raw_distance(self, from_id: PlayerId, to_id: PlayerId) -> int:
        """
        Shortest path distance around the circle,
        counting only alive players between them.
        """
        if from_id == to_id:
            return 0
        alive = self.alive_players_in_order()
        if from_id not in alive or to_id not in alive:
            raise DomainError("Both players must be alive for distance calc")
        n = len(alive)
        i = alive.index(from_id)
        j = alive.index(to_id)
        clockwise = (j - i) % n
        counter = (i - j) % n
        return min(clockwise, counter)

    @property
    def alive_count(self) -> int:
        return len(self._alive)

    def is_alive(self, player_id: PlayerId) -> bool:
        return player_id in self._alive

    @property
    def all_player_ids(self) -> list[PlayerId]:
        return list(self._order)
