from bang_game_engine.card import Card, GunCard
from bang_game_engine.character import Character
from bang_game_engine.player.table import Table
from bang_game_engine.role import Role


class Player:
    def __init__(
        self,
        role: Role,
        character: Character,
        hand: list[Card] | None = None,
        bullets: int | None = None,
        gun: GunCard | None = None,
        table: Table | None = None,
    ):
        self.role = role
        self.character = character

        self.hand = hand or []
        self.gun = gun
        self.table = table or Table()
        self._bullets = bullets or self.max_bullets

        if self._bullets > self.max_bullets:
            raise ValueError(
                f"Player cannot have more bullets than their character's max bullets"
            )

    def __str__(self) -> str:
        return f"Player {self.role} ({self.character.character_type}) with {self._bullets} bullets"

    def __repr__(self) -> str:
        return f"Player(role={self.role}, character={self.character}, hand={self.hand}, bullets={self._bullets}, gun={self.gun}, table={self.table})"

    def heal(self, amount: int):
        self._bullets = min(self._bullets + amount, self.max_bullets)

    def damage(self, amount: int):
        self._bullets = max(self._bullets - amount, 0)

    @property
    def max_bullets(self) -> int:
        return self.character.max_bullets + self.role.max_bullets_modifier

    @property
    def is_alive(self) -> bool:
        return self._bullets > 0

    @property
    def bullets(self) -> int:
        return self._bullets
