"""Factory for creating and initializing complete games."""

from __future__ import annotations

import random

from bang_game_engine.cards.card import Card
from bang_game_engine.cards.card_color import CardColor
from bang_game_engine.cards.card_face import CardFace
from bang_game_engine.cards.deck import Deck
from bang_game_engine.cards.rank import Rank
from bang_game_engine.cards.suit import Suit
from bang_game_engine.effects.effect_stack import EffectStack
from bang_game_engine.effects.registry import EffectRegistry
from bang_game_engine.expansions.base.cards import create_base_deck_cards
from bang_game_engine.expansions.base.characters import create_base_characters
from bang_game_engine.expansions.base.expansion import BaseGameExpansion
from bang_game_engine.expansions.registry import ExpansionRegistry
from bang_game_engine.game.game_state import GameState
from bang_game_engine.game.state_machine import GameStateMachine
from bang_game_engine.game.turn_rules import TurnRuleEngine
from bang_game_engine.game.win_condition import WinConditionEvaluator
from bang_game_engine.players.character import Character
from bang_game_engine.players.distance_service import DistanceService
from bang_game_engine.players.player import Player
from bang_game_engine.players.role import Role
from bang_game_engine.players.seating import Seating
from bang_game_engine.shared.errors import DomainError
from bang_game_engine.shared.identifiers import new_game_id, new_player_id
from bang_game_engine.shared.types import GameId, PlayerId


_ROLE_MAP = {
    "sheriff": Role.SHERIFF,
    "deputy": Role.DEPUTY,
    "outlaw": Role.OUTLAW,
    "renegade": Role.RENEGADE,
}


class GameFactory:
    """
    Creates a fully initialized game.

    Usage:
        factory = GameFactory()
        machine = factory.create_game(player_count=5)
        events = machine.start_game()
    """

    def create_game(
        self,
        player_count: int,
        rng: random.Random | None = None,
        expansion_names: list[str] | None = None,
    ) -> GameStateMachine:
        """
        Create a new game with the given number of players.

        Args:
            player_count: Number of players (4-7 for base game)
            rng: Optional random source for deterministic testing
            expansion_names: Which expansions to activate. Defaults to ["base"].
        """
        rng = rng or random.Random()
        expansion_names = expansion_names or ["base"]

        # 1. Set up expansion registry
        exp_registry = ExpansionRegistry()
        exp_registry.register(BaseGameExpansion())

        for name in expansion_names:
            exp_registry.activate(name)

        # 2. Get merged content pack
        content_pack = exp_registry.get_merged_content_pack()

        # 3. Validate player count
        role_dist = content_pack.role_distributions.get(player_count)
        if role_dist is None:
            raise DomainError(
                f"No role distribution for {player_count} players"
            )

        # 4. Assign roles (shuffle)
        role_strings = list(role_dist)
        rng.shuffle(role_strings)
        roles = [_ROLE_MAP[r] for r in role_strings]

        # 5. Assign characters (pick N from pool, shuffle)
        all_characters = list(content_pack.characters)
        rng.shuffle(all_characters)
        if len(all_characters) < player_count:
            raise DomainError("Not enough characters for player count")
        selected_characters = all_characters[:player_count]

        # 6. Create players
        players: dict[PlayerId, Player] = {}
        player_ids: list[PlayerId] = []
        sheriff_id: PlayerId | None = None

        for i in range(player_count):
            pid = new_player_id()
            player = Player(
                player_id=pid,
                role=roles[i],
                character=selected_characters[i],
            )
            players[pid] = player
            player_ids.append(pid)
            if roles[i] == Role.SHERIFF:
                sheriff_id = pid

        # 7. Arrange seating (Sheriff first, then others clockwise)
        if sheriff_id is not None:
            sheriff_idx = player_ids.index(sheriff_id)
            ordered_ids = (
                player_ids[sheriff_idx:]
                + player_ids[:sheriff_idx]
            )
        else:
            ordered_ids = player_ids

        seating = Seating(ordered_ids)

        # 8. Create deck from cards
        deck_cards = create_base_deck_cards()
        rng.shuffle(deck_cards)
        deck = Deck(draw_pile=deck_cards, rng=rng)

        # 9. Create game infrastructure
        effect_stack = EffectStack()
        effect_registry = EffectRegistry()
        turn_rule_engine = TurnRuleEngine()
        win_evaluator = WinConditionEvaluator()
        distance_service = DistanceService()

        # 10. Let expansions register their effects and rules
        exp_registry.setup_effect_registry(effect_registry)
        exp_registry.setup_turn_rules(turn_rule_engine)

        # 11. Create game state
        game_id = new_game_id()
        game_state = GameState(
            game_id=game_id,
            players=players,
            seating=seating,
            deck=deck,
            effect_stack=effect_stack,
            effect_registry=effect_registry,
            turn_rule_engine=turn_rule_engine,
            win_evaluator=win_evaluator,
            distance_service=distance_service,
        )

        # 12. Create state machine
        return GameStateMachine(game_state)

    def create_game_with_setup(
        self,
        roles: list[Role],
        characters: list[Character],
        deck_cards: list[Card] | None = None,
        rng: random.Random | None = None,
    ) -> GameStateMachine:
        """
        Create a game with specific setup -- useful for testing.

        Args:
            roles: Exact role assignment per seat position
            characters: Exact character assignment per seat position
            deck_cards: Optional pre-built deck (not shuffled)
            rng: Optional random source
        """
        rng = rng or random.Random()
        player_count = len(roles)

        if len(characters) != player_count:
            raise DomainError("Must provide same number of characters as roles")

        # Create players
        players: dict[PlayerId, Player] = {}
        player_ids: list[PlayerId] = []

        for i in range(player_count):
            pid = new_player_id()
            player = Player(
                player_id=pid,
                role=roles[i],
                character=characters[i],
            )
            players[pid] = player
            player_ids.append(pid)

        seating = Seating(player_ids)

        # Create deck
        if deck_cards is None:
            deck_cards = create_base_deck_cards()
            rng.shuffle(deck_cards)
        deck = Deck(draw_pile=deck_cards, rng=rng)

        # Set up base game effects and rules
        base = BaseGameExpansion()
        effect_registry = EffectRegistry()
        base.register_effects(effect_registry)

        turn_rule_engine = TurnRuleEngine()
        base.register_turn_rules(turn_rule_engine)

        game_state = GameState(
            game_id=new_game_id(),
            players=players,
            seating=seating,
            deck=deck,
            effect_stack=EffectStack(),
            effect_registry=effect_registry,
            turn_rule_engine=turn_rule_engine,
            win_evaluator=WinConditionEvaluator(),
            distance_service=DistanceService(),
        )

        return GameStateMachine(game_state)
