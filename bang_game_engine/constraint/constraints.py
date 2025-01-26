from bang_game_engine.constraint.interfaces import IConstraint
from bang_game_engine.engine import IEngine


class AlwaysTrueConstraint(IConstraint):
    def check(self, engine: IEngine, **options) -> bool:
        return True


class ReachableWithGunConstraint(IConstraint):
    def check(self, engine: IEngine, **options) -> bool:
        initiating_player_index = options.get("initiating_player_index")
        target_player_index = options.get("target_player_index")

        if initiating_player_index is None or target_player_index is None:
            raise ValueError(
                f"Initiating and target player indexes are required. Got: options={options}"
            )

        # TODO: Refactor this to be much more flexible
        distance = min(
            abs(initiating_player_index - target_player_index),
            abs(
                initiating_player_index
                - target_player_index
                + len(engine.alive_players)
            ),
        )

        gun = engine.get_player(initiating_player_index).gun
        reachable_distance = gun.distance_range if gun else 1

        return distance <= reachable_distance
