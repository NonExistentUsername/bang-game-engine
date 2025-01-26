from dataclasses import dataclass

from bang_game_engine.card.constants import CardSuits, CardTypes, CardValues


@dataclass
class Card:
    suit: CardSuits
    value: CardValues

    card_type: CardTypes

    def __str__(self):
        return f"{self.card_type.name} ({self.value.name} of {self.suit.name})"

    def __repr__(self):
        return f"Card(suit={self.suit.name}, value={self.value.name}, type={self.card_type.name})"


class EffectCard(Card):
    # TODO: This is not a good way to check if a card is an effect card
    pass


class ModifierCard(Card):
    # TODO: This is not a good way to check if a card is a modifier card
    pass


class GunCard(Card):
    # TODO: This is not a good way to check if a card is a gun card
    pass
