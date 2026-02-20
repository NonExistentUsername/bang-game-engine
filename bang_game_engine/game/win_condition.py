from __future__ import annotations

from dataclasses import dataclass, field

from bang_game_engine.players.player import Player
from bang_game_engine.players.role import Role
from bang_game_engine.players.seating import Seating
from bang_game_engine.shared.types import PlayerId


@dataclass(frozen=True)
class GameResult:
    winners: frozenset[Role]
    winning_player_ids: frozenset[PlayerId]


class WinConditionEvaluator:
    """
    Checks if any faction has won after each elimination.
    Returns the winning result or None if game continues.
    """

    def evaluate(
        self,
        players: dict[PlayerId, Player],
        seating: Seating,
    ) -> GameResult | None:
        alive = {pid: p for pid, p in players.items() if p.is_alive}
        alive_roles = [p.role for p in alive.values()]

        sheriff_alive = Role.SHERIFF in alive_roles
        outlaws_alive = any(r == Role.OUTLAW for r in alive_roles)
        renegades_alive = any(r == Role.RENEGADE for r in alive_roles)

        # Sheriff eliminated
        if not sheriff_alive:
            # Renegade wins if they are the ONLY one alive
            if len(alive) == 1 and alive_roles[0] == Role.RENEGADE:
                return GameResult(
                    winners=frozenset({Role.RENEGADE}),
                    winning_player_ids=frozenset(alive.keys()),
                )
            # Otherwise Outlaws win (even dead outlaws win - they achieved their goal)
            return GameResult(
                winners=frozenset({Role.OUTLAW}),
                winning_player_ids=frozenset(
                    pid for pid, p in players.items() if p.role == Role.OUTLAW
                ),
            )

        # All outlaws and renegades eliminated -> Sheriff + Deputies win
        if not outlaws_alive and not renegades_alive:
            return GameResult(
                winners=frozenset({Role.SHERIFF, Role.DEPUTY}),
                winning_player_ids=frozenset(
                    pid
                    for pid, p in players.items()
                    if p.role in (Role.SHERIFF, Role.DEPUTY)
                ),
            )

        return None  # Game continues
