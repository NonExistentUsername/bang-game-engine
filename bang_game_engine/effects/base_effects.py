"""Base game effect handlers for brown cards."""

from __future__ import annotations

from typing import Any

from bang_game_engine.effects.effect import (
    EffectContext,
    EffectOutcome,
    EffectState,
    ResponseWindow,
)
from bang_game_engine.players.events import PlayerAtZeroHP, PlayerDamaged, PlayerHealed
from bang_game_engine.shared.events import DomainEvent
from bang_game_engine.shared.types import CardId, PlayerId


class BangEffectHandler:
    """
    Bang! - Deal 1 damage to target. Target can respond with Missed!
    Slab the Killer: target needs 2 Missed!
    Barrel: target auto-checks first (handled by state machine).
    """

    card_type = "bang"

    def validate(self, context: EffectContext, game: Any) -> tuple[bool, str]:
        if context.target_player_id is None:
            return False, "Bang! requires a target"
        return True, ""

    def begin(self, context: EffectContext, game: Any) -> EffectOutcome:
        target_id = context.target_player_id
        assert target_id is not None

        # Determine how many Missed! cards needed
        source = game.get_player(context.source_player_id)
        missed_needed = 1
        from bang_game_engine.players.ability import AbilityContext, AbilityTiming

        for ability in source.character.get_abilities_for_timing(
            AbilityTiming.ON_MISSED_REQUIRED
        ):
            ctx = AbilityContext(player_id=source.id)
            if ability.can_activate(ctx):
                result = ability.activate(ctx)
                if result.modified_value is not None:
                    missed_needed = result.modified_value

        return EffectOutcome(
            state=EffectState.AWAITING_RESPONSE,
            response_window=ResponseWindow(
                responding_player_id=target_id,
                valid_response_types=["missed", "pass"],
                prompt=f"Play {'a' if missed_needed == 1 else str(missed_needed)} Missed! or take 1 damage",
            ),
        )

    def handle_response(
        self,
        context: EffectContext,
        game: Any,
        response_card_id: CardId | None,
        responding_player_id: PlayerId,
    ) -> EffectOutcome:
        target_id = context.target_player_id
        assert target_id is not None

        if response_card_id is None:
            # Take damage
            player = game.get_player(target_id)
            dmg_events = player.take_damage(1, context.source_player_id)
            return EffectOutcome(state=EffectState.COMPLETE, events=dmg_events)
        else:
            # Played Missed! - attack avoided
            return EffectOutcome(state=EffectState.COMPLETE)


class BeerEffectHandler:
    """Beer - Heal 1 HP. No effect with only 2 players remaining."""

    card_type = "beer"

    def validate(self, context: EffectContext, game: Any) -> tuple[bool, str]:
        if game.alive_count <= 2:
            return False, "Beer has no effect with only 2 players remaining"
        return True, ""

    def begin(self, context: EffectContext, game: Any) -> EffectOutcome:
        player = game.get_player(context.source_player_id)
        heal_events = player.heal(1)
        return EffectOutcome(state=EffectState.COMPLETE, events=heal_events)

    def handle_response(self, context, game, response_card_id, responding_player_id):
        from bang_game_engine.shared.errors import DomainError

        raise DomainError("Beer does not require a response")


class SaloonEffectHandler:
    """Saloon - All players (including you) recover 1 HP."""

    card_type = "saloon"

    def validate(self, context: EffectContext, game: Any) -> tuple[bool, str]:
        return True, ""

    def begin(self, context: EffectContext, game: Any) -> EffectOutcome:
        events: list[DomainEvent] = []
        for pid in game.alive_player_ids():
            player = game.get_player(pid)
            heal_events = player.heal(1)
            events.extend(heal_events)
        return EffectOutcome(state=EffectState.COMPLETE, events=events)

    def handle_response(self, context, game, response_card_id, responding_player_id):
        from bang_game_engine.shared.errors import DomainError

        raise DomainError("Saloon does not require a response")


class StagecoachEffectHandler:
    """Stagecoach - Draw 2 cards."""

    card_type = "stagecoach"

    def validate(self, context: EffectContext, game: Any) -> tuple[bool, str]:
        return True, ""

    def begin(self, context: EffectContext, game: Any) -> EffectOutcome:
        player = game.get_player(context.source_player_id)
        for _ in range(2):
            card = game.deck.draw()
            player.add_to_hand(card)
        return EffectOutcome(state=EffectState.COMPLETE)

    def handle_response(self, context, game, response_card_id, responding_player_id):
        from bang_game_engine.shared.errors import DomainError

        raise DomainError("Stagecoach does not require a response")


class WellsFargoEffectHandler:
    """Wells Fargo - Draw 3 cards."""

    card_type = "wells_fargo"

    def validate(self, context: EffectContext, game: Any) -> tuple[bool, str]:
        return True, ""

    def begin(self, context: EffectContext, game: Any) -> EffectOutcome:
        player = game.get_player(context.source_player_id)
        for _ in range(3):
            card = game.deck.draw()
            player.add_to_hand(card)
        return EffectOutcome(state=EffectState.COMPLETE)

    def handle_response(self, context, game, response_card_id, responding_player_id):
        from bang_game_engine.shared.errors import DomainError

        raise DomainError("Wells Fargo does not require a response")


class PanicEffectHandler:
    """Panic! - Steal 1 card from a player at distance 1."""

    card_type = "panic"

    def validate(self, context: EffectContext, game: Any) -> tuple[bool, str]:
        if context.target_player_id is None:
            return False, "Panic! requires a target"
        return True, ""

    def begin(self, context: EffectContext, game: Any) -> EffectOutcome:
        target = game.get_player(context.target_player_id)
        source = game.get_player(context.source_player_id)

        # Steal a random card from hand (or a card from table)
        all_cards = target.get_all_cards()
        if not all_cards:
            return EffectOutcome(state=EffectState.COMPLETE)

        # For simplicity, steal first card from hand, or first table card
        if target.hand:
            import random as _rng

            card = target._hand[_rng.randint(0, len(target._hand) - 1)]
            target.remove_from_hand(card.id)
            source.add_to_hand(card)
        elif target.table_cards:
            card = target.table_cards[0]
            target.remove_from_table(card.id)
            source.add_to_hand(card)

        return EffectOutcome(state=EffectState.COMPLETE)

    def handle_response(self, context, game, response_card_id, responding_player_id):
        from bang_game_engine.shared.errors import DomainError

        raise DomainError("Panic! does not require a response")


class CatBalouEffectHandler:
    """Cat Balou - Force any player to discard 1 card."""

    card_type = "cat_balou"

    def validate(self, context: EffectContext, game: Any) -> tuple[bool, str]:
        if context.target_player_id is None:
            return False, "Cat Balou requires a target"
        return True, ""

    def begin(self, context: EffectContext, game: Any) -> EffectOutcome:
        target = game.get_player(context.target_player_id)

        all_cards = target.get_all_cards()
        if not all_cards:
            return EffectOutcome(state=EffectState.COMPLETE)

        # Discard random card from hand, or first table card
        if target.hand:
            import random as _rng

            card = target._hand[_rng.randint(0, len(target._hand) - 1)]
            target.remove_from_hand(card.id)
            game.deck.discard(card)
        elif target.table_cards:
            card = target.table_cards[0]
            target.remove_from_table(card.id)
            game.deck.discard(card)

        return EffectOutcome(state=EffectState.COMPLETE)

    def handle_response(self, context, game, response_card_id, responding_player_id):
        from bang_game_engine.shared.errors import DomainError

        raise DomainError("Cat Balou does not require a response")
