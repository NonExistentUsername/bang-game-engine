"""All 16 base game characters with their abilities."""

from __future__ import annotations

from bang_game_engine.players.ability import (
    AbilityContext,
    AbilityResult,
    AbilityTiming,
)
from bang_game_engine.players.character import Character


# --- Ability Implementations ---


class BartCassidyAbility:
    """Draws a card each time he loses a life point."""

    @property
    def timing(self) -> AbilityTiming:
        return AbilityTiming.ON_TAKE_DAMAGE

    @property
    def name(self) -> str:
        return "bart_cassidy"

    def can_activate(self, context: AbilityContext) -> bool:
        return True

    def activate(self, context: AbilityContext) -> AbilityResult:
        return AbilityResult(modified_value="draw_on_damage")


class BlackJackAbility:
    """Shows 2nd drawn card; if Hearts/Diamonds, draws an extra card."""

    @property
    def timing(self) -> AbilityTiming:
        return AbilityTiming.ON_DRAW_PHASE

    @property
    def name(self) -> str:
        return "black_jack"

    def can_activate(self, context: AbilityContext) -> bool:
        return True

    def activate(self, context: AbilityContext) -> AbilityResult:
        return AbilityResult(modified_value="black_jack_draw")


class CalamityJanetAbility:
    """Can use Bang! as Missed! and vice versa."""

    @property
    def timing(self) -> AbilityTiming:
        return AbilityTiming.ON_CARD_PLAYED_AS

    @property
    def name(self) -> str:
        return "calamity_janet"

    def can_activate(self, context: AbilityContext) -> bool:
        return True

    def activate(self, context: AbilityContext) -> AbilityResult:
        return AbilityResult(modified_value="swap_bang_missed")


class ElGringoAbility:
    """Draws a card from the hand of the player who damaged him."""

    @property
    def timing(self) -> AbilityTiming:
        return AbilityTiming.ON_TAKE_DAMAGE

    @property
    def name(self) -> str:
        return "el_gringo"

    def can_activate(self, context: AbilityContext) -> bool:
        return context.source_player_id is not None

    def activate(self, context: AbilityContext) -> AbilityResult:
        return AbilityResult(modified_value="draw_from_attacker")


class JesseJonesAbility:
    """May draw first card from any player's hand instead of deck."""

    @property
    def timing(self) -> AbilityTiming:
        return AbilityTiming.ON_DRAW_PHASE

    @property
    def name(self) -> str:
        return "jesse_jones"

    def can_activate(self, context: AbilityContext) -> bool:
        return True

    def activate(self, context: AbilityContext) -> AbilityResult:
        return AbilityResult(
            requires_choice=True,
            choice_prompt="Draw first card from deck or a player's hand?",
        )


class JourdonnaisAbility:
    """Has a permanent Barrel (auto draw! check on each Bang!)."""

    @property
    def timing(self) -> AbilityTiming:
        return AbilityTiming.ON_DEFENSIVE_CHECK

    @property
    def name(self) -> str:
        return "jourdonnais"

    def can_activate(self, context: AbilityContext) -> bool:
        return True

    def activate(self, context: AbilityContext) -> AbilityResult:
        return AbilityResult(modified_value="innate_barrel")


class KitCarlsonAbility:
    """Looks at top 3 cards, chooses 2, puts 1 back on top."""

    @property
    def timing(self) -> AbilityTiming:
        return AbilityTiming.ON_DRAW_PHASE

    @property
    def name(self) -> str:
        return "kit_carlson"

    def can_activate(self, context: AbilityContext) -> bool:
        return True

    def activate(self, context: AbilityContext) -> AbilityResult:
        return AbilityResult(
            requires_choice=True,
            choice_prompt="Choose which card to put back on deck",
        )


class LuckyDukeAbility:
    """Draws 2 cards for each draw! check and chooses the preferred one."""

    @property
    def timing(self) -> AbilityTiming:
        return AbilityTiming.ON_DRAW_CHECK

    @property
    def name(self) -> str:
        return "lucky_duke"

    def can_activate(self, context: AbilityContext) -> bool:
        return True

    def activate(self, context: AbilityContext) -> AbilityResult:
        return AbilityResult(modified_value="draw_two_choose_one")


class PaulRegretAbility:
    """Seen at distance +1 by all other players (permanent Mustang)."""

    @property
    def timing(self) -> AbilityTiming:
        return AbilityTiming.ON_DISTANCE_CALC

    @property
    def name(self) -> str:
        return "paul_regret"

    def can_activate(self, context: AbilityContext) -> bool:
        return context.extra.get("role") == "target"

    def activate(self, context: AbilityContext) -> AbilityResult:
        return AbilityResult(modified_value=1)  # +1 distance


class PedroRamirezAbility:
    """May draw first card from the top of the discard pile."""

    @property
    def timing(self) -> AbilityTiming:
        return AbilityTiming.ON_DRAW_PHASE

    @property
    def name(self) -> str:
        return "pedro_ramirez"

    def can_activate(self, context: AbilityContext) -> bool:
        return True

    def activate(self, context: AbilityContext) -> AbilityResult:
        return AbilityResult(
            requires_choice=True,
            choice_prompt="Draw first card from deck or discard pile?",
        )


class RoseDoolanAbility:
    """Sees all other players at distance -1 (permanent Scope)."""

    @property
    def timing(self) -> AbilityTiming:
        return AbilityTiming.ON_DISTANCE_CALC

    @property
    def name(self) -> str:
        return "rose_doolan"

    def can_activate(self, context: AbilityContext) -> bool:
        return context.extra.get("role") == "attacker"

    def activate(self, context: AbilityContext) -> AbilityResult:
        return AbilityResult(modified_value=-1)  # -1 distance


class SidKetchumAbility:
    """May discard 2 cards to regain 1 life point at any time."""

    @property
    def timing(self) -> AbilityTiming:
        return AbilityTiming.ON_DISCARD_PHASE

    @property
    def name(self) -> str:
        return "sid_ketchum"

    def can_activate(self, context: AbilityContext) -> bool:
        return True

    def activate(self, context: AbilityContext) -> AbilityResult:
        return AbilityResult(modified_value="discard_two_heal_one")


class SlabTheKillerAbility:
    """Players need 2 Missed! to cancel his Bang! cards."""

    @property
    def timing(self) -> AbilityTiming:
        return AbilityTiming.ON_MISSED_REQUIRED

    @property
    def name(self) -> str:
        return "slab_the_killer"

    def can_activate(self, context: AbilityContext) -> bool:
        return True

    def activate(self, context: AbilityContext) -> AbilityResult:
        return AbilityResult(modified_value=2)  # Need 2 Missed!


class SuzyLafayetteAbility:
    """Draws a card from the deck when her hand becomes empty."""

    @property
    def timing(self) -> AbilityTiming:
        return AbilityTiming.ON_HAND_EMPTY

    @property
    def name(self) -> str:
        return "suzy_lafayette"

    def can_activate(self, context: AbilityContext) -> bool:
        return True

    def activate(self, context: AbilityContext) -> AbilityResult:
        return AbilityResult(modified_value="draw_when_empty")


class VultureSamAbility:
    """Takes all cards from eliminated players."""

    @property
    def timing(self) -> AbilityTiming:
        return AbilityTiming.ON_PLAYER_ELIMINATED

    @property
    def name(self) -> str:
        return "vulture_sam"

    def can_activate(self, context: AbilityContext) -> bool:
        return True

    def activate(self, context: AbilityContext) -> AbilityResult:
        return AbilityResult(modified_value="take_eliminated_cards")


class WillyTheKidAbility:
    """Can play any number of Bang! cards."""

    @property
    def timing(self) -> AbilityTiming:
        return AbilityTiming.ON_PLAY_CARD

    @property
    def name(self) -> str:
        return "willy_the_kid"

    def can_activate(self, context: AbilityContext) -> bool:
        return True

    def activate(self, context: AbilityContext) -> AbilityResult:
        return AbilityResult(modified_value="unlimited_bangs")


# --- Character Definitions ---


def create_base_characters() -> list[Character]:
    """Create all 16 base game characters."""
    return [
        Character(
            character_type="bart_cassidy",
            name="Bart Cassidy",
            base_hp=4,
            abilities=[BartCassidyAbility()],
        ),
        Character(
            character_type="black_jack",
            name="Black Jack",
            base_hp=4,
            abilities=[BlackJackAbility()],
        ),
        Character(
            character_type="calamity_janet",
            name="Calamity Janet",
            base_hp=4,
            abilities=[CalamityJanetAbility()],
        ),
        Character(
            character_type="el_gringo",
            name="El Gringo",
            base_hp=3,
            abilities=[ElGringoAbility()],
        ),
        Character(
            character_type="jesse_jones",
            name="Jesse Jones",
            base_hp=4,
            abilities=[JesseJonesAbility()],
        ),
        Character(
            character_type="jourdonnais",
            name="Jourdonnais",
            base_hp=4,
            abilities=[JourdonnaisAbility()],
        ),
        Character(
            character_type="kit_carlson",
            name="Kit Carlson",
            base_hp=4,
            abilities=[KitCarlsonAbility()],
        ),
        Character(
            character_type="lucky_duke",
            name="Lucky Duke",
            base_hp=4,
            abilities=[LuckyDukeAbility()],
        ),
        Character(
            character_type="paul_regret",
            name="Paul Regret",
            base_hp=3,
            abilities=[PaulRegretAbility()],
        ),
        Character(
            character_type="pedro_ramirez",
            name="Pedro Ramirez",
            base_hp=4,
            abilities=[PedroRamirezAbility()],
        ),
        Character(
            character_type="rose_doolan",
            name="Rose Doolan",
            base_hp=4,
            abilities=[RoseDoolanAbility()],
        ),
        Character(
            character_type="sid_ketchum",
            name="Sid Ketchum",
            base_hp=4,
            abilities=[SidKetchumAbility()],
        ),
        Character(
            character_type="slab_the_killer",
            name="Slab the Killer",
            base_hp=4,
            abilities=[SlabTheKillerAbility()],
        ),
        Character(
            character_type="suzy_lafayette",
            name="Suzy Lafayette",
            base_hp=4,
            abilities=[SuzyLafayetteAbility()],
        ),
        Character(
            character_type="vulture_sam",
            name="Vulture Sam",
            base_hp=4,
            abilities=[VultureSamAbility()],
        ),
        Character(
            character_type="willy_the_kid",
            name="Willy the Kid",
            base_hp=4,
            abilities=[WillyTheKidAbility()],
        ),
    ]
