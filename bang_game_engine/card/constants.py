import enum


class CardTypes(enum.StrEnum):
    BANG = "bang"
    MISSED = "missed"
    GATLING = "gatling"
    PANIC = "panic"
    CAT_BALOU = "cat_balou"
    INDIANS = "indians"
    WELLS_FARGO = "wells_fargo"
    GENERAL_STORE = "general_store"
    SALOON = "saloon"
    DILIGENCIA = "diligencia"
    BEER = "beer"
    DUEL = "duel"
    MUSTANG = "mustang"
    APPALOOSA = "appaloosa"
    BARREL = "barrel"
    DYNAMITE = "dynamite"
    JAIL = "jail"
    VOLCANIC = "volcanic"
    SCHOFIELD = "scoofield"
    REMINGTON = "remington"
    CARABINE = "carabine"
    WINCHESTER = "winchester"


class CardSuits(enum.StrEnum):
    HEART = "heart"
    DIAMOND = "diamond"
    CLUB = "club"
    SPADE = "spade"


class CardValues(enum.IntEnum):
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9
    TEN = 10
    JACK = 11
    QUEEN = 12
    KING = 13
    ACE = 14
