from bang_game_engine.card import Card, CardSuits, CardTypes, CardValues
from bang_game_engine.deck import Deck, IDeck, IDeckFactory


class BangAndMissDeckFactory(IDeckFactory):
    def create(self) -> IDeck:
        deck: list[Card] = []

        deck.extend(
            Card(
                suit=CardSuits.HEART,
                value=CardValues.TWO,
                card_type=CardTypes.BANG,
            )
            for _ in range(10)
        )

        deck.extend(
            Card(
                suit=CardSuits.HEART,
                value=CardValues.TWO,
                card_type=CardTypes.MISSED,
            )
            for _ in range(10)
        )

        return Deck(deck)
