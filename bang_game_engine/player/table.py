from bang_game_engine.card import Card, GunCard, ModifierCard


class Table:
    def __init__(self) -> None:
        self._cards: list[ModifierCard] = []

    def add(self, card: ModifierCard):
        for existing_card in self._cards:
            if existing_card.card_type == card.card_type:
                raise ValueError(
                    f"Card of type {card.card_type} already placed on the table"
                )

        self._cards.append(card)

    @property
    def cards(self) -> list[ModifierCard]:
        return self._cards

    def __len__(self) -> int:
        return len(self._cards)

    def __repr__(self):
        return f"Table(cards={self._cards})"
